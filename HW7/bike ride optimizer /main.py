"""
FastAPI application — Bike-Share Pass Optimizer (Gemini backend)
POST /api/run  →  SSE stream of ReAct agent events
GET  /         →  serves static/index.html
"""
import asyncio
import json
import os
import tempfile
from pathlib import Path

import duckdb
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from agent import run_react_agent

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Bike-Share Pass Optimizer", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
async def index():
    return (STATIC_DIR / "index.html").read_text()


@app.post("/api/run")
async def run_analysis(
    csv_file: UploadFile = File(..., description="Monthly Citi Bike trip CSV"),
    pricing_url: str = Form(..., description="Official pricing page URL"),
    model: str = Form("gemini-1.5-flash", description="Gemini model name"),
):
    if not pricing_url.startswith("http"):
        raise HTTPException(status_code=400, detail="pricing_url must be a valid http/https URL")

    csv_bytes = await csv_file.read()
    if not csv_bytes:
        raise HTTPException(status_code=400, detail="Uploaded CSV file is empty")

    async def event_stream():
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="wb") as fh:
                fh.write(csv_bytes)
                tmp_path = fh.name

            conn = duckdb.connect()
            try:
                conn.execute(
                    f"CREATE TABLE trips AS SELECT * FROM read_csv_auto('{tmp_path}', header=true)"
                )
                row_count = conn.execute("SELECT COUNT(*) FROM trips").fetchone()[0]
                yield _sse({"type": "init", "row_count": row_count, "model": model})
            except Exception as exc:
                yield _sse({"type": "error", "content": f"Failed to parse CSV: {exc}"})
                return

            async for event in run_react_agent(pricing_url, conn, model, row_count):
                yield _sse(event)
                await asyncio.sleep(0)

            yield _sse({"type": "done"})

        except Exception as exc:
            yield _sse({"type": "error", "content": str(exc)})
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
