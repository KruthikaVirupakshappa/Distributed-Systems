# Chunking Strategies Comparison with LlamaIndex

This assignment implements and compares three chunking strategies on the Tiny Shakespeare dataset using LlamaIndex.

## Chunking Techniques Implemented

1. **Token-based Chunking** - Uses TokenTextSplitter with fixed chunk size and overlap
2. **Semantic Chunking** - Uses SemanticSplitterNodeParser to find semantically coherent boundaries
3. **Sentence-window Chunking** - Uses SentenceWindowNodeParser with context windows

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install llama-index llama-index-embeddings-huggingface sentence-transformers faiss-cpu numpy pandas requests
```

### 2. Run the Script

```bash
python chunking_comparison.py
```

## What the Script Does

1. **Downloads Dataset**: Fetches the Tiny Shakespeare text from the official repository
2. **Initializes Embedding Model**: Uses `sentence-transformers/all-MiniLM-L6-v2` from HuggingFace
3. **Implements Three Pipelines**: 
   - Each pipeline chunks the text using a different strategy
   - Builds an in-memory VectorStoreIndex
   - Prepares for retrieval
4. **Runs Queries**: Tests on multiple queries:
   - "Who are the two feuding houses?" (primary query)
   - "Who is Romeo in love with?" (optional)
   - "Which play contains the line 'To be, or not to be'?" (optional)
5. **Analyzes Results**: For each query and technique, the script:
   - Computes and prints query embedding stats
   - Retrieves top-5 relevant chunks
   - Computes cosine similarity for each chunk
   - Prints diagnostic table with rank, scores, chunk length, and preview
   - Measures retrieval latency
6. **Generates Report**: Compares techniques on:
   - Retrieval quality (top-1 and mean@5 cosine similarity)
   - Chunking statistics (number and average length)
   - Retrieval latency

## Output

The script produces:

1. **Setup Information**: Shows chunking configuration and statistics
2. **Per-Query Retrieval Results**: Detailed table for each technique showing:
   - Rank of retrieved chunks
   - Store score (if available)
   - Cosine similarity
   - Chunk length
   - Text preview

3. **Comparison Report**: Summary table comparing all techniques for the primary query
4. **Observations**: Analysis of why certain methods performed better
5. **Conclusion**: Overall recommendation for the best technique

## Key Parameters

- **Token-based**: chunk_size=256, chunk_overlap=32
- **Semantic**: buffer_size=1 (uses embedding model to find boundaries)
- **Sentence-window**: window_size=3 (includes 3 neighboring sentences)
- **Retrieval**: k=5 (top-5 results)
- **Embedding Model**: sentence-transformers/all-MiniLM-L6-v2 (384-dimensional vectors)

## Notes

- The script uses an in-memory vector store for simplicity and speed
- All embeddings are computed using the HuggingFace sentence transformer model
- Cosine similarity is explicitly computed for each retrieved chunk
- The comparison focuses on retrieval quality, chunk coherence, and latency
