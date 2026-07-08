"""
Semantic Caching — FastAPI + SSE Streaming Web App
HW9 — Data 236 Distributed Systems

Stack:
  Embeddings : SentenceTransformers  (all-MiniLM-L6-v2, 384-dim)
  Vector DB  : Redis native Vector Sets (VADD / VSIM / VSETATTR)
  LLM        : Ollama  (llama3.2:latest)
  Web        : FastAPI + SSE streaming
"""

import json
import time
import uuid
import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
import ollama
import redis
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from sentence_transformers import SentenceTransformer

# ──────────────────────────────────────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────────────────────────────────────
REDIS_HOST        = "localhost"
REDIS_PORT        = 6379
VSET_KEY          = "semantic_cache"
EMBEDDING_MODEL   = "all-MiniLM-L6-v2"
EMBEDDING_DIM     = 384
SIMILARITY_THRESH = 0.85
OLLAMA_MODEL      = "llama3.2:latest"

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Singletons
# ──────────────────────────────────────────────────────────────────────────────
_redis_client: Optional[redis.Redis] = None
_encoder:      Optional[SentenceTransformer] = None

# Running metrics (in-process; resets on server restart)
_stats = {"total": 0, "hits": 0, "misses": 0,
          "total_cached_ms": 0.0, "total_live_ms": 0.0}


def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT,
                                    decode_responses=False)
        _redis_client.ping()
    return _redis_client


def get_encoder() -> SentenceTransformer:
    global _encoder
    if _encoder is None:
        log.info("Loading embedding model '%s' …", EMBEDDING_MODEL)
        _encoder = SentenceTransformer(EMBEDDING_MODEL)
        log.info("Embedding model ready.")
    return _encoder


# ──────────────────────────────────────────────────────────────────────────────
# Redis Vector Set helpers
# ──────────────────────────────────────────────────────────────────────────────

def embed(text: str) -> np.ndarray:
    return get_encoder().encode(text, normalize_embeddings=True).astype(np.float32)


def vset_size() -> int:
    try:
        return int(get_redis().execute_command("VCARD", VSET_KEY))
    except Exception:
        return 0


def vset_add(query: str, response: str, vec: np.ndarray) -> None:
    r   = get_redis()
    key = uuid.uuid4().hex
    r.execute_command("VADD", VSET_KEY, "FP32", vec.tobytes(), key)
    r.execute_command("VSETATTR", VSET_KEY, key,
                      json.dumps({"query": query[:500], "response": response}))


def vset_search(vec: np.ndarray) -> tuple[Optional[str], float, str]:
    """Return (response | None, similarity, matched_query)."""
    r   = get_redis()
    raw = r.execute_command(
        "VSIM", VSET_KEY, "FP32", vec.tobytes(), "COUNT", 1, "WITHSCORES"
    )
    if not raw:
        return None, 0.0, ""
    element    = raw[0].decode()
    similarity = float(raw[1])
    attr_raw   = r.execute_command("VGETATTR", VSET_KEY, element)
    if attr_raw is None:
        return None, similarity, ""
    attrs = json.loads(attr_raw.decode())
    if similarity >= SIMILARITY_THRESH:
        return attrs.get("response", ""), similarity, attrs.get("query", "")
    return None, similarity, attrs.get("query", "")


def flush_cache() -> int:
    """Delete the vector set; return how many entries were in it."""
    size = vset_size()
    get_redis().delete(VSET_KEY)
    return size


# ──────────────────────────────────────────────────────────────────────────────
# SSE helpers
# ──────────────────────────────────────────────────────────────────────────────

def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


# ──────────────────────────────────────────────────────────────────────────────
# Streaming query pipeline
# ──────────────────────────────────────────────────────────────────────────────

def stream_query(query: str):
    """Generator that yields SSE events for one query."""
    global _stats
    t0 = time.perf_counter()

    # ── Phase 1: embed ────────────────────────────────────────────────────────
    yield sse("phase", {"phase": "embed", "message": "Computing query embedding…"})
    t_emb = time.perf_counter()
    vec   = embed(query)
    emb_ms = (time.perf_counter() - t_emb) * 1000
    yield sse("embed_done", {"embed_ms": round(emb_ms, 1)})

    # ── Phase 2: cache search ─────────────────────────────────────────────────
    yield sse("phase", {"phase": "search", "message": "Searching Redis vector cache…"})
    t_search   = time.perf_counter()
    cache_size = vset_size()

    if cache_size == 0:
        response, similarity, matched_query = None, 0.0, ""
    else:
        response, similarity, matched_query = vset_search(vec)
    search_ms = (time.perf_counter() - t_search) * 1000

    is_cached = response is not None
    _stats["total"] += 1

    yield sse("cache_result", {
        "is_cached":     is_cached,
        "similarity":    round(similarity, 4),
        "threshold":     SIMILARITY_THRESH,
        "matched_query": matched_query,
        "cache_size":    cache_size,
        "search_ms":     round(search_ms, 1),
    })

    # ── Phase 3a: cache hit ───────────────────────────────────────────────────
    if is_cached:
        _stats["hits"] += 1
        total_ms = (time.perf_counter() - t0) * 1000
        _stats["total_cached_ms"] += total_ms
        log.info("CACHE HIT  | sim=%.4f | %s", similarity, query[:60])
        yield sse("result", {
            "response":   response,
            "is_cached":  True,
            "similarity": round(similarity, 4),
            "total_ms":   round(total_ms, 1),
        })

    # ── Phase 3b: cache miss → Ollama ─────────────────────────────────────────
    else:
        _stats["misses"] += 1
        log.info("CACHE MISS | best_sim=%.4f | %s", similarity, query[:60])
        yield sse("phase", {"phase": "ollama",
                             "message": f"Cache miss — querying {OLLAMA_MODEL}…"})
        t_llm = time.perf_counter()
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": query}],
        )["message"]["content"].strip()
        llm_ms = (time.perf_counter() - t_llm) * 1000

        vset_add(query, response, vec)
        total_ms = (time.perf_counter() - t0) * 1000
        _stats["total_live_ms"] += total_ms

        yield sse("result", {
            "response":  response,
            "is_cached": False,
            "similarity": round(similarity, 4),
            "llm_ms":    round(llm_ms, 1),
            "total_ms":  round(total_ms, 1),
        })

    # ── Phase 4: running stats ────────────────────────────────────────────────
    t   = _stats["total"]
    h   = _stats["hits"]
    m   = _stats["misses"]
    avg_cached_ms = _stats["total_cached_ms"] / h if h else 0
    avg_live_ms   = _stats["total_live_ms"]   / m if m else 0
    speedup       = avg_live_ms / avg_cached_ms if avg_cached_ms else 0

    yield sse("stats", {
        "total":          t,
        "hits":           h,
        "misses":         m,
        "hit_rate":       f"{h/t*100:.1f}%" if t else "0%",
        "cache_size":     vset_size(),
        "avg_cached_ms":  round(avg_cached_ms, 1),
        "avg_live_ms":    round(avg_live_ms, 1),
        "speedup":        round(speedup, 1),
    })


# ──────────────────────────────────────────────────────────────────────────────
# FastAPI app
# ──────────────────────────────────────────────────────────────────────────────
app = FastAPI(title="Semantic Cache Demo")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])



@app.get("/api/query")
async def api_query(q: str = ""):
    if not q.strip():
        return {"error": "No query provided"}

    def gen():
        try:
            yield from stream_query(q.strip())
        except Exception as e:
            yield sse("error", {"message": str(e)})

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache",
                                      "X-Accel-Buffering": "no"})


@app.get("/api/stats")
async def api_stats():
    t = _stats["total"]
    h = _stats["hits"]
    m = _stats["misses"]
    avg_c = _stats["total_cached_ms"] / h if h else 0
    avg_l = _stats["total_live_ms"]   / m if m else 0
    return {
        "total": t, "hits": h, "misses": m,
        "hit_rate": f"{h/t*100:.1f}%" if t else "0%",
        "cache_size": vset_size(),
        "avg_cached_ms": round(avg_c, 1),
        "avg_live_ms":   round(avg_l, 1),
        "speedup":       round(avg_l / avg_c, 1) if avg_c else 0,
        "model":         OLLAMA_MODEL,
        "threshold":     SIMILARITY_THRESH,
    }


@app.post("/api/cache/flush")
async def api_flush():
    n = flush_cache()
    _stats.update({"total": 0, "hits": 0, "misses": 0,
                   "total_cached_ms": 0.0, "total_live_ms": 0.0})
    return {"flushed": n}


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML


# ──────────────────────────────────────────────────────────────────────────────
# HTML UI
# ──────────────────────────────────────────────────────────────────────────────
HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Semantic Cache Demo</title>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#08080a;--s1:#101013;--s2:#17171b;--s3:#1f1f25;--b1:#27272e;--b2:#35353d;
  --t1:#ededf0;--t2:#9e9eab;--t3:#66666f;
  --acc:#c4ee60;--acc2:#9fd030;--accd:rgba(196,238,96,.07);
  --hit:#4fd1c5;--miss:#5b9cf5;--red:#f07068;--amber:#f5be3a;
  --r:14px;--rs:9px;
  --f:'system-ui',sans-serif;--m:'ui-monospace','Menlo',monospace;
}
body{background:var(--bg);color:var(--t1);font-family:var(--f);line-height:1.6}
.shell{max-width:860px;margin:0 auto;padding:2rem 1.5rem 5rem}

header{text-align:center;padding:3.5rem 0 2rem}
h1{font-size:clamp(1.8rem,4.5vw,3rem);font-weight:700;letter-spacing:-.04em;margin-bottom:.5rem}
h1 em{font-style:normal;color:var(--acc)}
.sub{color:var(--t2);font-size:.9rem;max-width:520px;margin:.4rem auto 0}
.tags{display:flex;justify-content:center;flex-wrap:wrap;gap:.35rem;margin-top:1.2rem}
.tag{font-size:.65rem;font-weight:500;padding:.22rem .55rem;border-radius:99px;
     border:1px solid var(--b1);color:var(--t3);background:var(--s1)}
.tag.on{border-color:rgba(196,238,96,.4);color:var(--acc);background:var(--accd)}

/* input */
.iw{background:var(--s1);border:1px solid var(--b1);border-radius:var(--r);
    padding:.85rem 1rem;margin:2rem 0 .75rem;transition:border-color .2s}
.iw:focus-within{border-color:var(--acc)}
.iw textarea{width:100%;background:none;border:none;outline:none;resize:none;
             color:var(--t1);font-family:var(--f);font-size:.95rem;line-height:1.5;
             min-height:42px;max-height:140px}
.iw textarea::placeholder{color:var(--t3)}
.iw-f{display:flex;align-items:center;justify-content:space-between;margin-top:.55rem;gap:.5rem}
.iw-f .ht{font-size:.68rem;color:var(--t3)}
.row-btns{display:flex;gap:.45rem}
.btn{display:inline-flex;align-items:center;gap:.35rem;padding:.45rem 1.1rem;
     border-radius:99px;border:none;cursor:pointer;font-family:var(--f);
     font-size:.78rem;font-weight:600;transition:all .15s;flex-shrink:0}
.btn-go{background:var(--acc);color:var(--bg)}
.btn-go:hover{transform:translateY(-1px);box-shadow:0 6px 20px rgba(196,238,96,.2)}
.btn-go:active{transform:scale(.97)}
.btn-go:disabled{opacity:.35;cursor:not-allowed;transform:none;box-shadow:none}
.btn-flush{background:var(--s3);color:var(--t2);border:1px solid var(--b2)}
.btn-flush:hover{color:var(--red);border-color:var(--red)}

/* stats bar */
.sbar{display:grid;grid-template-columns:repeat(4,1fr);gap:.4rem;margin-bottom:1rem}
.sc{background:var(--s1);border:1px solid var(--b1);border-radius:var(--rs);
    padding:.5rem .7rem;text-align:center}
.sc .v{font-size:1.1rem;font-weight:700;color:var(--t1)}
.sc .l{font-size:.58rem;color:var(--t3);text-transform:uppercase;letter-spacing:.06em;margin-top:.05rem}

/* phase bar */
.pbar{display:flex;align-items:center;gap:.6rem;padding:.55rem .85rem;
      border-radius:var(--r);background:var(--s1);border:1px solid var(--b1);
      margin-bottom:.7rem;animation:fadeIn .2s ease both}
.pbar .dot{width:7px;height:7px;border-radius:50%;flex-shrink:0;animation:blink 1s ease infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.25}}
.pbar.embed .dot{background:var(--amber)}
.pbar.search .dot{background:var(--acc)}
.pbar.ollama .dot{background:var(--miss)}
.pbar .msg{font-size:.78rem;color:var(--t2)}

/* result card */
#feed{display:flex;flex-direction:column;gap:.8rem}
.card{background:var(--s1);border:1px solid var(--b1);border-radius:var(--r);
      overflow:hidden;animation:fadeIn .3s ease both}
@keyframes fadeIn{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
.ch{display:flex;align-items:center;gap:.5rem;padding:.65rem .9rem;
    border-bottom:1px solid var(--b1);background:var(--s2)}
.lbl{font-size:.76rem;font-weight:600;flex:1;color:var(--t1)}
.badge{font-size:.6rem;padding:.15rem .42rem;border-radius:99px;font-weight:600;
       font-family:var(--m);white-space:nowrap}
.b-hit{background:rgba(79,209,197,.12);color:var(--hit)}
.b-miss{background:rgba(91,156,245,.12);color:var(--miss)}
.b-tm{background:var(--s3);color:var(--t3)}
.b-sim{background:var(--accd);color:var(--acc);border:1px solid rgba(196,238,96,.2)}
.cb{padding:.8rem .9rem;color:var(--t2);font-size:.83rem;line-height:1.65}
.cb p{margin-bottom:.3rem}
.cb .resp{color:var(--t1);white-space:pre-wrap;word-break:break-word}
.cb .mq{font-size:.72rem;color:var(--t3);margin-top:.4rem;font-style:italic}

/* timing grid */
.tg{display:grid;grid-template-columns:repeat(3,1fr);gap:.35rem;margin-top:.5rem}
.ti{background:var(--s2);border:1px solid var(--b1);border-radius:var(--rs);
    padding:.4rem .6rem;text-align:center}
.ti .tv{font-size:.95rem;font-weight:700;color:var(--t1)}
.ti .tl{font-size:.56rem;color:var(--t3);text-transform:uppercase;letter-spacing:.05em}

footer{text-align:center;color:var(--t3);font-size:.65rem;padding:2rem 0 .5rem}
@media(max-width:560px){.sbar{grid-template-columns:1fr 1fr}.tg{grid-template-columns:1fr 1fr}}
</style>
</head>
<body>
<div class="shell">
  <header>
    <h1>Semantic <em>Cache</em></h1>
    <p class="sub">Redis Vector Sets · SentenceTransformers · Ollama · FastAPI SSE</p>
    <div class="tags">
      <span class="tag on">Redis VectorSet</span>
      <span class="tag on">all-MiniLM-L6-v2</span>
      <span class="tag on">Ollama llama3.2</span>
      <span class="tag on">Cosine ≥ 0.85</span>
      <span class="tag on">SSE Streaming</span>
    </div>
  </header>

  <!-- stats bar -->
  <div class="sbar">
    <div class="sc"><div class="v" id="st-total">0</div><div class="l">Queries</div></div>
    <div class="sc"><div class="v" id="st-hit">0%</div><div class="l">Hit Rate</div></div>
    <div class="sc"><div class="v" id="st-cached">—</div><div class="l">Avg Cache ms</div></div>
    <div class="sc"><div class="v" id="st-live">—</div><div class="l">Avg Ollama ms</div></div>
  </div>

  <!-- input -->
  <div class="iw">
    <textarea id="q" rows="2" placeholder="Ask anything — try the same question twice, or rephrase it…"></textarea>
    <div class="iw-f">
      <span class="ht">Exact or paraphrased queries hit the cache · New queries call Ollama</span>
      <div class="row-btns">
        <button class="btn btn-flush" onclick="flush()">⌫ Flush Cache</button>
        <button class="btn btn-go" id="goBtn" onclick="run()">▶ Ask</button>
      </div>
    </div>
  </div>

  <div id="pbarWrap"></div>
  <div id="feed"></div>
  <footer>HW9 · Data 236 Distributed Systems · Semantic Caching with Redis + Ollama</footer>
</div>

<script>
const $  = id => document.getElementById(id);
const esc = s => { const d=document.createElement('div'); d.textContent=s; return d.innerHTML; };

function updateStats(d) {
  $('st-total').textContent  = d.total;
  $('st-hit').textContent    = d.hit_rate;
  $('st-cached').textContent = d.avg_cached_ms ? d.avg_cached_ms + ' ms' : '—';
  $('st-live').textContent   = d.avg_live_ms   ? d.avg_live_ms   + ' ms' : '—';
}

function setPhase(d) {
  $('pbarWrap').innerHTML =
    `<div class="pbar ${d.phase}"><div class="dot"></div><span class="msg">${esc(d.message)}</span></div>`;
}

function run() {
  const query = $('q').value.trim();
  if (!query) return;
  $('goBtn').disabled = true;
  $('pbarWrap').innerHTML = '';

  const card = document.createElement('div');
  card.className = 'card';
  card.innerHTML = `
    <div class="ch">
      <span class="lbl">${esc(query)}</span>
      <span class="badge b-tm" id="card-status">…</span>
    </div>
    <div class="cb" id="card-body">
      <p style="color:var(--t3);font-size:.78rem">Waiting for response…</p>
    </div>`;
  $('feed').prepend(card);

  const src = new EventSource('/api/query?q=' + encodeURIComponent(query));

  src.addEventListener('phase', e => {
    const d = JSON.parse(e.data);
    setPhase(d);
  });

  src.addEventListener('embed_done', e => {});

  src.addEventListener('cache_result', e => {
    const d = JSON.parse(e.data);
    const simPct = (d.similarity * 100).toFixed(1);
    if (d.is_cached) {
      $('pbarWrap').innerHTML = '';
      card.querySelector('#card-status').outerHTML =
        `<span class="badge b-hit">CACHE HIT</span>
         <span class="badge b-sim">sim ${simPct}%</span>`;
    }
  });

  src.addEventListener('result', e => {
    const d = JSON.parse(e.data);
    $('pbarWrap').innerHTML = '';

    const isHit   = d.is_cached;
    const simPct  = (d.similarity * 100).toFixed(1);
    const statusBadge = isHit
      ? `<span class="badge b-hit">CACHE HIT</span><span class="badge b-sim">sim ${simPct}%</span>`
      : `<span class="badge b-miss">OLLAMA LIVE</span>`;
    const timeBadge = `<span class="badge b-tm">${d.total_ms} ms</span>`;

    // update card header
    card.querySelector('.ch').innerHTML =
      `<span class="lbl">${esc(query)}</span>${statusBadge}${timeBadge}`;

    // timing grid
    let timingHTML = '';
    if (isHit) {
      timingHTML = `<div class="tg">
        <div class="ti"><div class="tv">${d.total_ms} ms</div><div class="tl">Total (cached)</div></div>
        <div class="ti"><div class="tv">${(d.similarity*100).toFixed(1)}%</div><div class="tl">Similarity</div></div>
        <div class="ti"><div class="tv">0.85</div><div class="tl">Threshold</div></div>
      </div>`;
    } else {
      timingHTML = `<div class="tg">
        <div class="ti"><div class="tv">${d.llm_ms} ms</div><div class="tl">Ollama</div></div>
        <div class="ti"><div class="tv">${d.total_ms} ms</div><div class="tl">Total</div></div>
        <div class="ti"><div class="tv">${(d.similarity*100).toFixed(1)}%</div><div class="tl">Best Sim Found</div></div>
      </div>`;
    }

    card.querySelector('#card-body').innerHTML =
      `<p class="resp">${esc(d.response)}</p>${timingHTML}`;
  });

  src.addEventListener('stats', e => {
    updateStats(JSON.parse(e.data));
    $('goBtn').disabled = false;
    src.close();
  });

  src.addEventListener('error', e => {
    try {
      const d = JSON.parse(e.data);
      card.querySelector('#card-body').innerHTML =
        `<p style="color:var(--red)">${esc(d.message)}</p>`;
    } catch(_) {}
    $('pbarWrap').innerHTML = '';
    $('goBtn').disabled = false;
    src.close();
  });

  src.onerror = () => { $('pbarWrap').innerHTML=''; $('goBtn').disabled=false; src.close(); };
}

async function flush() {
  await fetch('/api/cache/flush', {method:'POST'});
  $('st-total').textContent='0';
  $('st-hit').textContent='0%';
  $('st-cached').textContent='—';
  $('st-live').textContent='—';
  $('feed').innerHTML='';
  alert('Cache flushed!');
}

$('q').addEventListener('keydown', e => {
  if (e.key==='Enter' && !e.shiftKey) { e.preventDefault(); run(); }
});
$('q').addEventListener('input', function() {
  this.style.height='auto'; this.style.height=this.scrollHeight+'px';
});
</script>
</body>
</html>"""


if __name__ == "__main__":
    print("\n  Semantic Cache API — http://localhost:8000\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
