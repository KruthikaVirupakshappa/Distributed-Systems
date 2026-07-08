import time
import requests
import numpy as np
import pandas as pd
from llama_index.core import Document, VectorStoreIndex
from llama_index.core.vector_stores import SimpleVectorStore
from llama_index.core.node_parser import TokenTextSplitter, SemanticSplitterNodeParser, SentenceWindowNodeParser
from llama_index.embeddings.huggingface import HuggingFaceEmbedding


def download_dataset(url):
    """Download the Tiny Shakespeare dataset."""
    response = requests.get(url)
    response.raise_for_status()
    text = response.text
    print(f"Dataset downloaded. Size: {len(text)} characters")
    print(f"Preview (first 200 chars):\n{text[:200]}\n")
    return text


def compute_cosine_similarity(vec1, vec2):
    """Cosine similarity between two vectors."""
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot_product / (norm1 * norm2)


def retrieve_and_analyze(
    query,
    index,
    embed_model,
    technique_name,
    k=5
):
    """Retrieve documents and analyze retrieval quality."""
    print(f"\n{'='*80}")
    print(f"TECHNIQUE: {technique_name}")
    print(f"{'='*80}")
    print(f"Query: {query}\n")
    
    # Compute query embedding
    query_embedding = embed_model.get_text_embedding(query)
    print(f"Query embedding dimension: {len(query_embedding)}")
    print(f"First 8 values: {query_embedding[:8]}\n")
    
    # Retrieve documents with timing
    retriever = index.as_retriever(similarity_top_k=k)
    
    start_time = time.time()
    retrieved_nodes = retriever.retrieve(query)
    latency_ms = (time.time() - start_time) * 1000
    
    print(f"Retrieved {len(retrieved_nodes)} nodes in {latency_ms:.2f}ms\n")
    
    # Prepare results table
    results = []
    cosine_scores = []
    
    for rank, node in enumerate(retrieved_nodes, 1):
        # Get node text and metadata
        node_text = node.get_content()
        chunk_len = len(node_text)
        preview = node_text[:160].replace('\n', ' ')
        
        # Compute cosine similarity
        node_embedding = embed_model.get_text_embedding(node_text)
        cosine_sim = compute_cosine_similarity(
            np.array(query_embedding),
            np.array(node_embedding)
        )
        cosine_scores.append(cosine_sim)
        
        # Store score from retriever (if available)
        store_score = node.score if hasattr(node, 'score') else None
        
        results.append({
            'rank': rank,
            'store_score': store_score,
            'cosine_sim': cosine_sim,
            'chunk_len': chunk_len,
            'preview': preview
        })
    
    # Print table
    df = pd.DataFrame(results)
    print("Retrieval Results Table:")
    print(df.to_string(index=False))
    
    # Print shape information
    query_vec_shape = (len(query_embedding),)
    if len(results) > 0:
        doc_vecs = np.array([embed_model.get_text_embedding(r['preview']) for r in results])
        doc_vecs_shape = doc_vecs.shape
        print(f"\nQuery vector shape: {query_vec_shape}")
        print(f"Document vectors shape: {doc_vecs_shape}")
    
    return results, latency_ms, cosine_scores


def get_chunking_stats(nodes):
    """Compute chunking statistics."""
    chunk_lengths = [len(node.get_content()) for node in nodes]
    return {
        'num_chunks': len(nodes),
        'avg_chunk_length': np.mean(chunk_lengths),
        'min_chunk_length': np.min(chunk_lengths),
        'max_chunk_length': np.max(chunk_lengths)
    }


def token_based_chunking(text, embed_model, chunk_size=256, chunk_overlap=32):
    """Token-based chunking using TokenTextSplitter."""
    print("\n" + "="*80)
    print("TOKEN-BASED CHUNKING SETUP")
    print("="*80)
    
    # Create document
    documents = [Document(text=text)]
    
    # Token-based splitting
    splitter = TokenTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    
    nodes = splitter.get_nodes_from_documents(documents)
    print(f"Token-based chunking: {len(nodes)} chunks created")
    print(f"Chunk size: {chunk_size}, overlap: {chunk_overlap}")
    
    stats = get_chunking_stats(nodes)
    print(f"Stats: {stats}\n")
    
    # Build index with SimpleVectorStore
    vector_store = SimpleVectorStore()
    index = VectorStoreIndex(nodes, vector_store=vector_store, embed_model=embed_model)
    
    return index, stats, nodes


def semantic_chunking(text, embed_model, buffer_size=1):
    """Semantic chunking using SemanticSplitterNodeParser."""
    print("\n" + "="*80)
    print("SEMANTIC CHUNKING SETUP")
    print("="*80)
    
    # Create document
    documents = [Document(text=text)]
    
    # Semantic splitting
    splitter = SemanticSplitterNodeParser(
        buffer_size=buffer_size,
        embed_model=embed_model
    )
    
    nodes = splitter.get_nodes_from_documents(documents)
    print(f"Semantic chunking: {len(nodes)} chunks created")
    print(f"Buffer size: {buffer_size}")
    
    stats = get_chunking_stats(nodes)
    print(f"Stats: {stats}\n")
    
    # Build index with SimpleVectorStore
    vector_store = SimpleVectorStore()
    index = VectorStoreIndex(nodes, vector_store=vector_store, embed_model=embed_model)
    
    return index, stats, nodes


def sentence_window_chunking(text, embed_model, window_size=3):
    """Sentence-window chunking using SentenceWindowNodeParser."""
    print("\n" + "="*80)
    print("SENTENCE-WINDOW CHUNKING SETUP")
    print("="*80)
    
    # Create document
    documents = [Document(text=text)]
    
    # Sentence window splitting
    splitter = SentenceWindowNodeParser(
        window_size=window_size
    )
    
    nodes = splitter.get_nodes_from_documents(documents)
    print(f"Sentence-window chunking: {len(nodes)} chunks created")
    print(f"Window size: {window_size} sentences")
    
    stats = get_chunking_stats(nodes)
    print(f"Stats: {stats}\n")
    
    # Build index with SimpleVectorStore
    vector_store = SimpleVectorStore()
    index = VectorStoreIndex(nodes, vector_store=vector_store, embed_model=embed_model)
    
    return index, stats, nodes


def main():
    print("="*80)
    print("CHUNKING STRATEGIES COMPARISON")
    print("="*80)
    
    # Download dataset
    url = "https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt"
    text = download_dataset(url)
    
    # Setup embedding model
    print("\nInitializing embedding model...")
    embed_model = HuggingFaceEmbedding(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    print("Embedding model initialized\n")
    
    # Implement three chunking strategies
    token_index, token_stats, token_nodes = token_based_chunking(text, embed_model, chunk_size=256, chunk_overlap=32)
    semantic_index, semantic_stats, semantic_nodes = semantic_chunking(text, embed_model, buffer_size=1)
    sentence_index, sentence_stats, sentence_nodes = sentence_window_chunking(text, embed_model, window_size=3)
    
    # Queries to run
    queries = [
        "Who are the two feuding houses?",
        "Who is Romeo in love with?",
        "Which play contains the line 'To be, or not to be'?"
    ]
    
    # Run retrieval for each query and technique
    all_results = {}
    
    for query in queries:
        print(f"\n\n{'#'*80}")
        print(f"QUERY: {query}")
        print(f"{'#'*80}")
        
        token_results, token_latency, token_cosines = retrieve_and_analyze(
            query, token_index, embed_model, "Token-based Chunking", k=5
        )
        
        semantic_results, semantic_latency, semantic_cosines = retrieve_and_analyze(
            query, semantic_index, embed_model, "Semantic Chunking", k=5
        )
        
        sentence_results, sentence_latency, sentence_cosines = retrieve_and_analyze(
            query, sentence_index, embed_model, "Sentence-window Chunking", k=5
        )
        
        all_results[query] = {
            'token': {
                'results': token_results,
                'latency': token_latency,
                'cosines': token_cosines
            },
            'semantic': {
                'results': semantic_results,
                'latency': semantic_latency,
                'cosines': semantic_cosines
            },
            'sentence': {
                'results': sentence_results,
                'latency': sentence_latency,
                'cosines': sentence_cosines
            }
        }
    
    # Comparison report
    print(f"\n\n{'#'*80}")
    print("COMPARISON REPORT")
    print(f"{'#'*80}\n")
    
    # Focus on primary query
    primary_query = queries[0]
    primary_results = all_results[primary_query]
    
    comparison_data = []
    
    for technique_name, technique_key in [
        ("Token-based", "token"),
        ("Semantic", "semantic"),
        ("Sentence-window", "sentence")
    ]:
        data = primary_results[technique_key]
        cosines = data['cosines']
        
        if technique_key == "token":
            stats = token_stats
        elif technique_key == "semantic":
            stats = semantic_stats
        else:
            stats = sentence_stats
        
        comparison_data.append({
            'Technique': technique_name,
            '#Chunks': stats['num_chunks'],
            'Avg Chunk Len': f"{stats['avg_chunk_length']:.1f}",
            'Top-1 Cosine': f"{cosines[0]:.4f}" if cosines else "N/A",
            'Mean@5 Cosine': f"{np.mean(cosines):.4f}" if cosines else "N/A",
            'Latency (ms)': f"{data['latency']:.2f}"
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    print("Comparison Metrics for Primary Query:")
    print(f"Query: '{primary_query}'")
    print(comparison_df.to_string(index=False))


if __name__ == "__main__":
    main()
