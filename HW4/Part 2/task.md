## Goal
Implement three chunking strategies in LlamaIndex using the Tiny Shakespeare dataset, build in-memory vector indexes, run retrieval-only queries, and compare retrieval quality with simple metrics + short written observations.
Chunking techniques to implement
1. Token-based chunking — TokenTextSplitter
2. Semantic chunking — SemanticSplitterNodeParser
3. Sentence-window chunking — SentenceWindowNodeParser

## Dataset
Use this raw text file:
Tiny Shakespeare: https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt

## Environment & Setup
Install:
● llama-index
● llama-index-embeddings-huggingface
● sentence-transformers
● faiss-cpu
● numpy
● Pandas

## Embedding model:
● Use a public sentence embedding model from Hugging Face (example):
○ sentence-transformers/all-MiniLM-L6-v2

## What you must build
1) One retrieval-only pipeline per technique
For each chunker (Token / Semantic / Sentence-window), do:
A. Chunking
● TokenTextSplitter: choose sensible chunk_size and chunk_overlap.
● SemanticSplitterNodeParser: choose buffer_size; use the same embed model to find semantically coherent boundaries.
● SentenceWindowNodeParser: split into sentences and attach a context window (neighbor sentences) in metadata so surrounding context is available.
B. Indexing (in-memory)
● Build a VectorStoreIndex using an in-memory vector store (e.g., SimpleVectorStore) to keep everything local and fast.
2) Retrieval-only helper function (required)
Write a helper function:
Input: query, k, and the technique’s retriever/index Output: printed diagnostics + a ranked table
For a given query:
1. Compute the query embedding
○ Print: embedding dimension and first 8 values
2. Retrieve top-k nodes
3. For each retrieved node, compute and print:
○ store similarity score (if your retriever exposes it)
○ cosine similarity between query embedding and the chunk embedding (explicitly compute embeddings of returned chunks)
○ chunk length (characters is fine)
○ preview (first ~160 characters)
4. Print:
○ query vector shape
○ stacked document vectors shape
Your printed output must clearly label the technique and show a table:
rank
store_score
cosine_sim
chunk_len
preview
Query (must use for all three)
Use this query for all pipelines:
● Query: Who are the two feuding houses?
Optional (to strengthen your comparison), add 1–2 more queries such as:
● “Who is Romeo in love with?”
● “Which play contains the line ‘To be, or not to be’?”
Comparison metrics (report section)
After running all three pipelines, report for each technique:
1. Retrieval quality
○ top-1 cosine (highest cosine among top-k)
○ mean@k cosine (average cosine over top-k)
2. Chunking stats
○ #chunks produced
○ avg chunk length (characters or tokens)
3. Latency
○ retrieval latency in milliseconds (simple timer around the similarity search)
Write-up requirements
Observations (1–2 short paragraphs)
Explain why one method performed better for the required query. Discuss factors like:
● coherence of chunks
● boundary quality (semantic splitting)
● token budget alignment
● context preserved via sentence window metadata
If results differ across optional extra queries, mention it.
Conclusion (2–5 sentences)
State which technique you judge best for this corpus and why.


## Instructions

- Use the env which is activated in the terminal
- Make sure to have the code in the same style as in the other HW folders of python file
- Don't add too much complicated code or production ready level.
- This is for an assignment and it should feel like more human effort and less of vibe coding.
