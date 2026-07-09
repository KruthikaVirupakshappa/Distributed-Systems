# RAG widget — local demo

Two pieces, mirroring the real architecture:

- `backend/` — a mock FastAPI gateway (stands in for your real
  gateway → RAG Cloud Run call). Canned answers + citations, in-memory
  session tracking.
- `widget/widget.js` — the actual widget bundle. Vanilla JS, no build
  step, defines a `<rag-widget>` custom element with Shadow DOM isolation.
- `host.html` — a sample "existing website" with intentionally clashing
  CSS, to prove the widget doesn't inherit it.

## Run it

**1. Start the backend**

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Leave that running. Check it's alive: open http://localhost:8000/api/health
— you should see `{"status":"ok"}`.

**2. Open the host page**

Just double-click `host.html`, or serve it so it behaves closer to a real
site:

```bash
# from the project root, in a second terminal
python3 -m http.server 5500
```

Then visit http://localhost:5500/host.html

**3. Try it**

- Type "What is the refund policy?" into the inline search box — you'll
  get a canned answer with two clickable citations. Click a citation to
  expand its snippet.
- Click the floating launcher (bottom-right) to open the chat popup
  version — same backend, same session logic, different UI shape.
- Open devtools → Network tab and watch the actual `POST /api/query`
  calls happen, exactly like calling FastAPI from any other frontend.
- Open devtools → Elements tab, find `<rag-widget>`, and expand it — you'll
  see `#shadow-root (open)` containing the widget's own DOM, completely
  separate from the host page's DOM tree.

## What to look at to connect this back to the design

- `widget.js` → `attachShadow({ mode: "open" })` — this is the isolation
  boundary discussed earlier, made concrete.
- `customElements.define("rag-widget", ...)` — this is what lets host.html
  just write `<rag-widget>` as if it were a native HTML tag.
- `fetch(`${this.apiBase}/api/query`, ...)` — this is the ordinary part;
  once mounted, it's a normal API call, same as any SPA you've built.
- `main.py` → `CORSMiddleware` — necessary here because the host page
  (port 5500) and the API (port 8000) are different origins. In production
  this becomes your per-tenant domain allowlist instead of `"*"`.
- `SESSIONS` dict in `main.py` — today it's a Python dict; swap it for
  Redis with a TTL and you have the real session design.

## Next steps toward production

- Replace the in-memory `SESSIONS` dict with real Redis
- Replace `CANNED_ANSWERS` with the actual Vertex AI Search / Gemini call
- Bundle `widget.js` through Vite (library mode) once you want React
  inside the shadow root instead of vanilla JS
- Host `widget.js` on a CDN and swap `src="widget/widget.js"` for the
  CDN URL in any real host page
