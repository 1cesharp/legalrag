"""
Supabase Court Documents Query Module
Replacement for Gemini RAG with permanent vector storage
"""
import os
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv
from supabase import create_client, Client
from sentence_transformers import SentenceTransformer

# Try to import streamlit for cloud deployment
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

# Load environment (for local development)
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

# Initialize Supabase client (cached)
_supabase_client = None
_embedding_model = None

def get_supabase_client() -> Client:
    """Get or create Supabase client (singleton pattern)"""
    global _supabase_client

    if _supabase_client is None:
        # Try Streamlit secrets first (cloud deployment), then fall back to env vars (local)
        if STREAMLIT_AVAILABLE and hasattr(st, 'secrets'):
            try:
                supabase_url = st.secrets.get('SUPABASE_URL')
                supabase_key = st.secrets.get('SUPABASE_SERVICE_KEY')
            except:
                supabase_url = os.getenv('SUPABASE_URL')
                supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
        else:
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

        if not supabase_url or not supabase_key:
            raise ValueError("Missing Supabase credentials. Configure in Streamlit Cloud secrets or .env file")

        _supabase_client = create_client(supabase_url, supabase_key)

    return _supabase_client

def get_embedding_model() -> SentenceTransformer:
    """Get or create embedding model (singleton pattern)"""
    global _embedding_model

    if _embedding_model is None:
        _embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    return _embedding_model

def query_supabase_rag(
    query: str,
    match_threshold: float = 0.3,
    match_count: int = 20,
    document_type: Optional[str] = None
) -> Dict:
    """
    Query Supabase vector database for court documents

    Args:
        query: Search query text
        match_threshold: Minimum similarity score (0-1)
        match_count: Maximum number of results to return
        document_type: Filter by document type (e.g., 'affidavit', 'court_order')

    Returns:
        Dict with status, results, and metadata
    """
    try:
        # Get clients
        supabase = get_supabase_client()
        model = get_embedding_model()

        # Generate query embedding
        query_embedding = model.encode(query).tolist()

        # Call Supabase search function
        result = supabase.rpc(
            'search_court_documents',
            {
                'query_embedding': query_embedding,
                'match_threshold': match_threshold,
                'match_count': match_count,
                'filter_document_type': document_type
            }
        ).execute()

        if not result.data:
            return {
                'status': 'SUCCESS',
                'results': 'No matching documents found. Try broadening your search terms or lowering the similarity threshold.',
                'documents_searched': 288,
                'total_in_index': 288,
                'chunks_found': 0
            }

        # Format results for display
        formatted_results = format_search_results(result.data, query)

        return {
            'status': 'SUCCESS',
            'results': formatted_results,
            'documents_searched': 288,
            'total_in_index': 288,
            'chunks_found': len(result.data),
            'raw_results': result.data
        }

    except Exception as e:
        return {
            'status': 'ERROR',
            'error': str(e),
            'documents_searched': 0,
            'total_in_index': 288,
            'chunks_found': 0
        }

def format_search_results(results: List[Dict], query: str) -> str:
    """Format search results as markdown"""

    if not results:
        return "No results found."

    # Group results by document
    docs = {}
    for result in results:
        filename = result['filename']
        if filename not in docs:
            docs[filename] = {
                'type': result['document_type'],
                'chunks': [],
                'metadata': result.get('metadata', {})
            }
        docs[filename]['chunks'].append({
            'content': result['content'],
            'similarity': result['similarity'],
            'chunk_index': result['chunk_index'],
            'total_chunks': result['total_chunks']
        })

    # Build markdown output
    output = []
    output.append(f"# Search Results for: {query}\n")
    output.append(f"**Found {len(results)} relevant passages from {len(docs)} documents**\n")
    output.append("---\n")

    # Sort documents by max similarity score
    sorted_docs = sorted(
        docs.items(),
        key=lambda x: max(chunk['similarity'] for chunk in x[1]['chunks']),
        reverse=True
    )

    for doc_num, (filename, doc_data) in enumerate(sorted_docs, 1):
        # Document header
        doc_type = doc_data['type'].replace('_', ' ').title()
        max_similarity = max(chunk['similarity'] for chunk in doc_data['chunks'])

        output.append(f"## {doc_num}. {filename}")
        output.append(f"**Type:** {doc_type} | **Relevance:** {max_similarity:.1%}\n")

        # Sort chunks by similarity
        sorted_chunks = sorted(
            doc_data['chunks'],
            key=lambda x: x['similarity'],
            reverse=True
        )

        # Show top chunks (limit to 3 per document)
        for chunk in sorted_chunks[:3]:
            chunk_label = f"Chunk {chunk['chunk_index'] + 1}/{chunk['total_chunks']}"
            similarity = f"{chunk['similarity']:.1%}"

            output.append(f"### {chunk_label} (Similarity: {similarity})\n")
            output.append(f"{chunk['content']}\n")
            output.append("---\n")

    return "\n".join(output)

def get_database_stats() -> Dict:
    """Get database statistics"""
    try:
        supabase = get_supabase_client()

        result = supabase.rpc('get_document_stats').execute()

        if result.data and len(result.data) > 0:
            return {
                'status': 'SUCCESS',
                'stats': result.data[0]
            }
        else:
            return {
                'status': 'ERROR',
                'error': 'No statistics available'
            }
    except Exception as e:
        return {
            'status': 'ERROR',
            'error': str(e)
        }
