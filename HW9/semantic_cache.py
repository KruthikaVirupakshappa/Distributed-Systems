"""
Semantic Caching with Redis (Vector Sets) and Ollama
HW9 — Data 236 Distributed Systems

Architecture:
  - Embeddings : SentenceTransformers  (all-MiniLM-L6-v2, 384-dim, normalised)
  - Vector store: Redis native Vector Sets (VADD / VSIM / VSETATTR / VGETATTR)
  - LLM backend : Ollama  (llama3.2:latest)
  - Similarity  : Cosine, threshold = 0.85
  - Tracking    : is_cached flag + timestamps for every query
"""

import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import ollama
import redis
from sentence_transformers import SentenceTransformer

# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────
REDIS_HOST        = "localhost"
REDIS_PORT        = 6379
VSET_KEY          = "semantic_cache"          # Redis Vector Set key
EMBEDDING_MODEL   = "all-MiniLM-L6-v2"       # 384-dim, fast, high quality
EMBEDDING_DIM     = 384
SIMILARITY_THRESH = 0.85                      # cosine similarity ≥ this → cache hit
OLLAMA_MODEL      = "llama3.2:latest"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Initialise Redis client and embedding model (module-level singletons)
# ──────────────────────────────────────────────────────────────────────────────
_redis_client: Optional[redis.Redis] = None
_encoder:      Optional[SentenceTransformer] = None


def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT,
                                    decode_responses=False)
        _redis_client.ping()          # fail fast if Redis is unavailable
    return _redis_client


def get_encoder() -> SentenceTransformer:
    global _encoder
    if _encoder is None:
        log.info("Loading embedding model '%s' …", EMBEDDING_MODEL)
        _encoder = SentenceTransformer(EMBEDDING_MODEL)
        log.info("Embedding model ready.")
    return _encoder


def embed(text: str) -> np.ndarray:
    """Return a normalised float32 embedding vector."""
    vec = get_encoder().encode(text, normalize_embeddings=True)
    return vec.astype(np.float32)


# ──────────────────────────────────────────────────────────────────────────────
# Redis Vector Set helpers
# ──────────────────────────────────────────────────────────────────────────────

def _vset_add(query: str, response: str, embedding: np.ndarray) -> None:
    """Store an embedding + metadata in the Redis Vector Set."""
    r   = get_redis()
    key = uuid.uuid4().hex          # unique element name inside the vset
    # VADD <vset_key> FP32 <raw_bytes> <element_name>
    r.execute_command("VADD", VSET_KEY, "FP32", embedding.tobytes(), key)
    # Attach the original query + response as JSON attributes
    attrs = json.dumps({"query": query[:500], "response": response})
    r.execute_command("VSETATTR", VSET_KEY, key, attrs)
    log.debug("Stored entry '%s' in vector set.", key)


def _vset_search(embedding: np.ndarray, k: int = 1) -> list[dict]:
    """
    Return up to *k* most-similar entries from the Redis Vector Set.
    Each dict has keys: element, similarity, query, response.
    """
    r = get_redis()
    # VSIM <vset_key> FP32 <raw_bytes> COUNT <k> WITHSCORES
    raw = r.execute_command(
        "VSIM", VSET_KEY, "FP32", embedding.tobytes(), "COUNT", k, "WITHSCORES"
    )
    # raw = [element_bytes, score_bytes, element_bytes, score_bytes, …]
    results = []
    for i in range(0, len(raw), 2):
        element   = raw[i].decode()
        similarity = float(raw[i + 1])
        attr_raw  = r.execute_command("VGETATTR", VSET_KEY, element)
        if attr_raw is None:
            continue
        attrs = json.loads(attr_raw.decode())
        results.append({
            "element":    element,
            "similarity": similarity,
            "query":      attrs.get("query", ""),
            "response":   attrs.get("response", ""),
        })
    return results


def _vset_size() -> int:
    """Number of entries currently in the vector set (0 if key absent)."""
    r = get_redis()
    try:
        return int(r.execute_command("VCARD", VSET_KEY))
    except Exception:
        return 0


def flush_cache() -> None:
    """Delete the entire vector set (useful between test runs)."""
    get_redis().delete(VSET_KEY)
    log.info("Cache flushed.")


# ──────────────────────────────────────────────────────────────────────────────
# Ollama helper
# ──────────────────────────────────────────────────────────────────────────────

def call_ollama(prompt: str) -> str:
    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response["message"]["content"].strip()


# ──────────────────────────────────────────────────────────────────────────────
# Core query handler
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class QueryResult:
    query:         str
    response:      str
    is_cached:     bool
    similarity:    float          # best cosine similarity found (0 if empty cache)
    response_time: float          # wall-clock seconds


def handle_query(query: str) -> QueryResult:
    """
    1. Generate embedding for the incoming query.
    2. Search Redis Vector Set for the most similar cached entry.
    3a. Cache HIT  (similarity ≥ threshold): return cached response.
    3b. Cache MISS : call Ollama, store result in Redis.
    Returns a QueryResult with is_cached flag and timing.
    """
    t_start = time.perf_counter()
    query_emb = embed(query)

    # ── Search cache ──────────────────────────────────────────────────────────
    is_cached  = False
    similarity = 0.0
    response   = ""

    if _vset_size() > 0:
        hits = _vset_search(query_emb, k=1)
        if hits:
            best = hits[0]
            similarity = best["similarity"]
            if similarity >= SIMILARITY_THRESH:
                is_cached = True
                response  = best["response"]
                log.info(
                    "CACHE HIT  | sim=%.4f | query='%s'",
                    similarity, query[:70],
                )

    # ── Cache miss → Ollama ───────────────────────────────────────────────────
    if not is_cached:
        log.info(
            "CACHE MISS | best_sim=%.4f | query='%s'",
            similarity, query[:70],
        )
        response = call_ollama(query)
        _vset_add(query, response, query_emb)

    t_end = time.perf_counter()
    return QueryResult(
        query         = query,
        response      = response,
        is_cached     = is_cached,
        similarity    = similarity,
        response_time = t_end - t_start,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Test suite  (10+ diverse queries)
# ──────────────────────────────────────────────────────────────────────────────

TEST_QUERIES = [
    # ── Group A: Machine Learning ─────────────────────────────────
    "What is machine learning?",                              # 1 — new
    "What is machine learning?",                             # 2 — EXACT duplicate
    "Can you explain machine learning to me?",               # 3 — paraphrase of 1

    # ── Group B: Photosynthesis ───────────────────────────────────
    "How does photosynthesis work?",                         # 4 — new
    "Explain the process of photosynthesis",                 # 5 — paraphrase of 4

    # ── Group C: Capital cities ───────────────────────────────────
    "What is the capital of France?",                        # 6 — new
    "Tell me the capital city of France",                    # 7 — paraphrase of 6

    # ── Group D: Coffee ───────────────────────────────────────────
    "How do I make a good cup of coffee?",                   # 8 — new
    "What is the best way to brew coffee?",                  # 9 — paraphrase of 8

    # ── Group E: Completely new / unique topics ───────────────────
    "What is quantum computing?",                            # 10 — new
    "How does the TCP/IP protocol stack work?",              # 11 — new
    "What are the main causes of climate change?",           # 12 — new
]


def run_tests() -> None:
    print("\n" + "=" * 72)
    print("  Semantic Cache Test — Redis Vector Sets + Ollama")
    print(f"  Model: {OLLAMA_MODEL}  |  Embeddings: {EMBEDDING_MODEL}")
    print(f"  Threshold: {SIMILARITY_THRESH}  |  Queries: {len(TEST_QUERIES)}")
    print("=" * 72 + "\n")

    # Fresh cache for reproducible results
    flush_cache()

    results: list[QueryResult] = []

    for idx, query in enumerate(TEST_QUERIES, 1):
        print(f"[{idx:02d}/{len(TEST_QUERIES)}] {query}")
        r = handle_query(query)
        results.append(r)

        status = "HIT " if r.is_cached else "MISS"
        print(f"        Status : {status}  |  sim={r.similarity:.4f}"
              f"  |  time={r.response_time:.3f}s")
        # Print a short preview of the response
        preview = r.response.replace("\n", " ")[:120]
        print(f"        Preview: {preview}…" if len(r.response) > 120 else
              f"        Preview: {preview}")
        print()

    # ── Performance metrics ───────────────────────────────────────────────────
    cached_results   = [r for r in results if     r.is_cached]
    uncached_results = [r for r in results if not r.is_cached]

    total          = len(results)
    hits           = len(cached_results)
    misses         = len(uncached_results)
    hit_rate       = hits / total * 100

    avg_cached_t   = (sum(r.response_time for r in cached_results)   / hits
                      if hits   else 0.0)
    avg_uncached_t = (sum(r.response_time for r in uncached_results) / misses
                      if misses else 0.0)
    speedup        = avg_uncached_t / avg_cached_t if avg_cached_t else float("inf")

    print("=" * 72)
    print("  PERFORMANCE SUMMARY")
    print("=" * 72)
    print(f"  Total queries   : {total}")
    print(f"  Cache hits      : {hits}  ({hit_rate:.1f}%)")
    print(f"  Cache misses    : {misses}")
    print(f"  Avg time (hit)  : {avg_cached_t*1000:.1f} ms")
    print(f"  Avg time (miss) : {avg_uncached_t*1000:.1f} ms")
    print(f"  Speed-up factor : {speedup:.1f}×  (cache vs Ollama)")
    print()

    print("  Per-query breakdown:")
    print(f"  {'#':>3}  {'Status':<6}  {'Sim':>6}  {'Time(ms)':>9}  Query")
    print("  " + "-" * 65)
    for idx, r in enumerate(results, 1):
        status = "HIT " if r.is_cached else "MISS"
        print(f"  {idx:>3}  {status:<6}  {r.similarity:>6.4f}"
              f"  {r.response_time*1000:>9.1f}  {r.query[:45]}")
    print("=" * 72 + "\n")


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    run_tests()
