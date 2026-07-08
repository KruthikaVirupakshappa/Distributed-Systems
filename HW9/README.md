# Semantic-Cache
Semantic caching system using Redis Vector Sets, SentenceTransformers (all-MiniLM-L6-v2), and Ollama (llama3.2). Stores LLM responses in Redis with cosine similarity search (threshold 0.85) to serve cached responses for duplicate or paraphrased queries. Includes FastAPI + SSE streaming web demo. Built for Data 236 Distributed Systems HW9.
