"""
kafka_geval_evaluator.py
─────────────────────────────────────────────────────────────────────────────
Consumes from the 'final' Kafka topic (full pipeline trace linked by
correlation_id) and evaluates each stage with GEval using a local Ollama
model as the judge.

Metrics
  • Plan-Quality             — is the Planner's plan structured and actionable?
  • Writer-Helpfulness       — does the draft directly answer the question?
  • Reviewer-Helpfulness     — does the final answer improve on the draft?
  • Final-vs-Draft-Improvement — did the Reviewer meaningfully improve it?

Usage
    python kafka_geval_evaluator.py
    python kafka_geval_evaluator.py --timeout 30
"""

import argparse
import json
import time

import ollama as ollama_client
from kafka import KafkaConsumer

from deepeval.models.base_model import DeepEvalBaseLLM
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

BOOTSTRAP_SERVERS = "localhost:29092"
JUDGE_MODEL = "llama3.2"


# ── Ollama wrapper for GEval ───────────────────────────────────────────────
class OllamaJudge(DeepEvalBaseLLM):
    def __init__(self, model: str = JUDGE_MODEL):
        self._model = model

    def load_model(self):
        return self._model

    def generate(self, prompt: str, schema=None) -> str:
        kwargs = {"model": self._model, "messages": [{"role": "user", "content": prompt}]}
        if schema is not None:
            kwargs["format"] = "json"
        response = ollama_client.chat(**kwargs)
        return response["message"]["content"]

    async def a_generate(self, prompt: str, schema=None) -> str:
        return self.generate(prompt, schema=schema)

    def get_model_name(self) -> str:
        return f"ollama/{self._model}"


# ── GEval metric definitions ───────────────────────────────────────────────
def build_metrics(judge: OllamaJudge) -> dict:
    return {
        "plan_quality": GEval(
            name="Plan-Quality",
            criteria=(
                "Evaluate whether the ACTUAL_OUTPUT is a clear, numbered, actionable "
                "step-by-step plan that would help someone answer the INPUT question. "
                "Penalise vague, circular, or missing steps."
            ),
            evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
            model=judge,
        ),
        "writer_helpfulness": GEval(
            name="Writer-Helpfulness",
            criteria=(
                "Determine whether the ACTUAL_OUTPUT directly and completely answers "
                "the INPUT question in clear, concise language. "
                "Penalise off-topic content, missing key facts, or unnecessary filler."
            ),
            evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
            model=judge,
        ),
        "reviewer_helpfulness": GEval(
            name="Reviewer-Helpfulness",
            criteria=(
                "Determine whether the ACTUAL_OUTPUT (Reviewer's final answer) "
                "directly and completely addresses the INPUT question. "
                "Score higher if it is accurate, clear, and well-organised."
            ),
            evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
            model=judge,
        ),
        "draft_improvement": GEval(
            name="Final-vs-Draft-Improvement",
            evaluation_steps=[
                "EXPECTED_OUTPUT is the Writer's draft answer.",
                "ACTUAL_OUTPUT is the Reviewer's final answer.",
                "Check if the final answer is more accurate, clearer, or more complete than the draft.",
                "Score 1.0 if clearly improved, 0.5 if same quality, 0.0 if worse.",
            ],
            evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
            model=judge,
        ),
    }


# ── Collect messages from Kafka ────────────────────────────────────────────
def collect_messages(topic: str, timeout_s: int) -> list:
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        group_id=f"geval-evaluator-{int(time.time())}",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        consumer_timeout_ms=timeout_s * 1000,
    )
    messages = []
    print(f"[Evaluator] Consuming from '{topic}' for up to {timeout_s}s...", flush=True)
    for msg in consumer:
        data = msg.value
        # Skip incomplete traces (from HW8 backend or old runs)
        if not all([data.get("plan"), data.get("draft"), data.get("question")]):
            continue
        cid = data.get("correlation_id", "unknown")
        print(f"  <- [{cid[:8]}] {data.get('question', '')[:60]}", flush=True)
        messages.append(data)
    consumer.close()
    return messages


# ── Evaluate one pipeline trace ────────────────────────────────────────────
def evaluate_trace(data: dict, metrics: dict) -> dict:
    question     = data.get("question", "")
    plan         = data.get("plan", "")
    draft        = data.get("draft", "")
    final_answer = data.get("final_answer", draft)
    cid          = data.get("correlation_id", "?")

    results = {"correlation_id": cid, "question": question}

    print(f"\n{'='*70}", flush=True)
    print(f"  correlation_id : {cid}", flush=True)
    print(f"  question       : {question}", flush=True)
    print(f"{'='*70}", flush=True)

    # 1. Plan Quality
    print(f"\n  [Planner] Plan:\n  {plan[:200]}", flush=True)
    metrics["plan_quality"].measure(LLMTestCase(input=question, actual_output=plan))
    score = float(metrics["plan_quality"].score or 0)
    results["Plan-Quality"] = score
    print(f"  Plan-Quality                 = {score:.2f}", flush=True)
    print(f"  Reason: {(metrics['plan_quality'].reason or '')[:200]}", flush=True)

    # 2. Writer Helpfulness
    print(f"\n  [Writer] Draft:\n  {draft[:200]}", flush=True)
    metrics["writer_helpfulness"].measure(LLMTestCase(input=question, actual_output=draft))
    score = float(metrics["writer_helpfulness"].score or 0)
    results["Writer-Helpfulness"] = score
    print(f"  Writer-Helpfulness           = {score:.2f}", flush=True)
    print(f"  Reason: {(metrics['writer_helpfulness'].reason or '')[:200]}", flush=True)

    # 3. Reviewer Helpfulness
    print(f"\n  [Reviewer] Final Answer:\n  {final_answer[:200]}", flush=True)
    metrics["reviewer_helpfulness"].measure(LLMTestCase(input=question, actual_output=final_answer))
    score = float(metrics["reviewer_helpfulness"].score or 0)
    results["Reviewer-Helpfulness"] = score
    print(f"  Reviewer-Helpfulness         = {score:.2f}", flush=True)
    print(f"  Reason: {(metrics['reviewer_helpfulness'].reason or '')[:200]}", flush=True)

    # 4. Final-vs-Draft Improvement
    metrics["draft_improvement"].measure(
        LLMTestCase(input=question, actual_output=final_answer, expected_output=draft)
    )
    score = float(metrics["draft_improvement"].score or 0)
    results["Final-vs-Draft-Improvement"] = score
    print(f"\n  Final-vs-Draft-Improvement   = {score:.2f}", flush=True)
    print(f"  Reason: {(metrics['draft_improvement'].reason or '')[:200]}", flush=True)

    return results


# ── Summary ────────────────────────────────────────────────────────────────
def print_summary(all_results: list):
    keys = ["Plan-Quality", "Writer-Helpfulness", "Reviewer-Helpfulness", "Final-vs-Draft-Improvement"]
    print(f"\n{'='*70}", flush=True)
    print("  AGGREGATE SUMMARY", flush=True)
    print(f"{'='*70}", flush=True)
    for k in keys:
        vals = [r[k] for r in all_results if k in r]
        if vals:
            print(f"  {k:<36} avg={sum(vals)/len(vals):.2f}  n={len(vals)}", flush=True)

    outpath = "geval_results.json"
    with open(outpath, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n  Results saved -> {outpath}\n", flush=True)


# ── Main ───────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", default="final")
    parser.add_argument("--timeout", type=int, default=20)
    args = parser.parse_args()

    print(f"\n[Evaluator] Judge model: ollama/{JUDGE_MODEL}", flush=True)
    judge = OllamaJudge(model=JUDGE_MODEL)
    metrics = build_metrics(judge)

    messages = collect_messages(args.topic, args.timeout)
    if not messages:
        print("[Evaluator] No messages found. Run send_question.py and the agents first.", flush=True)
        return

    print(f"\n[Evaluator] Evaluating {len(messages)} pipeline trace(s)...\n", flush=True)
    all_results = [evaluate_trace(data, metrics) for data in messages]
    print_summary(all_results)
    print("[Evaluator] Done.", flush=True)


if __name__ == "__main__":
    main()
