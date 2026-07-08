import json
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
import time
import requests
import numpy as np
import pandas as pd
from llama_index.core import Document, VectorStoreIndex
from llama_index.core.vector_stores import SimpleVectorStore
from llama_index.core.node_parser import TokenTextSplitter, SemanticSplitterNodeParser, SentenceWindowNodeParser
from llama_index.embeddings.huggingface import HuggingFaceEmbedding


llm = ChatOllama(
    model="smollm:1.7b",
    temperature=0.7,
    num_predict=256
)
prompt = "Message here"
resp = llm.invoke([HumanMessage(content=prompt)])
data = json.loads(resp.content)


def router_logic(state: AgentState) -> Literal["run_planning", "run_review", "END"]:
    turn = state.get("turn_count", 0)
    has_proposal = bool(state.get("planner_proposal"))
    has_reviewer_issues_key = "reviewer_has_issues" in state
    reviewer_has_issues = state.get("reviewer_has_issues", None) if has_reviewer_issues_key else None

    print(f"[Router] turn={turn}, has_proposal={has_proposal}, reviewer_has_issues={reviewer_has_issues}")

    if turn > 6:
        print(f"[Router] -> END (turn > 6)")
        return "END"

    if not has_proposal:
        print(f"[Router] -> run_planning (no proposal)")
        return "run_planning"

    # If reviewer_has_issues is True, go back to planning
    if reviewer_has_issues is True:
        print(f"[Router] -> run_planning (reviewer has issues)")
        return "run_planning"

    # If reviewer_has_issues is False, end workflow
    if reviewer_has_issues is False:
        print(f"[Router] -> END (reviewer has no issues)")
        return "END"

    # For None, run the review again.
    print(f"[Router] -> run_review (has proposal, review needed)")
    return "run_review"




documents = [Document(text=text)]

# Token-based splitting
splitter = TokenTextSplitter(
    chunk_size=chunk_size,
    chunk_overlap=chunk_overlap
)

nodes = splitter.get_nodes_from_documents(documents)

# Build index with SimpleVectorStore
vector_store = SimpleVectorStore()
index = VectorStoreIndex(nodes, vector_store=vector_store, embed_model=embed_model)


splitter = SemanticSplitterNodeParser(
    buffer_size=buffer_size,
    embed_model=embed_model
)

# Sentence window splitting
splitter = SentenceWindowNodeParser(
    window_size=window_size
)


