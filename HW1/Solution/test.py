import json
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage

schema = {
    "type": "object",
    "properties": {
        "tags": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 3,
            "maxItems": 3
        },
        "summary": {"type": "string", "maxwords": 25}
    },
    "required": ["tags", "summary"],
    "additionalProperties": False
}

llm = ChatOllama(
    model="smollm:1.7b",
    temperature=0,
    format=schema,
    num_predict=160
)

text = """Artificial intelligence systems are increasingly used to assist with analysis,
decision making, and creative tasks across many fields. Modern language models
can process text, identify patterns, and generate structured outputs when given
clear instructions. Their effectiveness depends on prompt clarity, available
context, and computational resources. Smaller models are useful for fast
experimentation and local deployment, while larger models offer deeper reasoning
at the cost of speed and memory. Designing modular agent pipelines helps
separate reasoning, validation, and formatting steps, making systems easier to
debug, extend, and reuse across different applications."""

prompt = f"""Extract exactly 3 relevant tags and write a 1-2 sentence summary of max 25 words.

Tasks:
1. Extract exactly 3 relevant tags
2. Write an abstractive summary

Rules for summary:
- Maximum 25 words total
- 1 sentence only
- Do NOT copy sentences from the text
- Rephrase ideas using different wording
- Avoid starting with the same words as the text
- Use the TITLE to decide importance
- High-level and abstract

Rules for tags:
- Short (1-3 words)
- Conceptual, not copied phrases

Return only JSON matching the schema.

TEXT:
{text}
"""

resp = llm.invoke([HumanMessage(content=prompt)])
data = json.loads(resp.content)

print(data["tags"])      # ["...", "...", "..."]
print(data["summary"])   # "..."
