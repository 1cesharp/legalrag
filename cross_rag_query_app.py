"""
Cross-RAG Query Interface - Unified Streamlit App
Queries both Gemini RAG (Court Documents) and GraphRAG (Communications) simultaneously
"""
import streamlit as st
import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Load environment
project_root = Path(__file__).resolve().parents[1]
env_path = project_root.parent / '.env'
load_dotenv(env_path)

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "Communications"))

# Import query functions
from supabase_query import query_supabase_rag
from cross_rag_orchestrator_FIXED import (
    query_graphrag_pass2
)

# Import SIMPLE lawyer-ready synthesis (user feedback: 3 sections only)
from simple_lawyer_synthesis import simple_synthesis

# Cached query wrappers for performance
@st.cache_data(ttl=3600, show_spinner=False)
def cached_supabase_query(query: str, match_count: int = 20) -> dict:
    """Cached wrapper for Supabase RAG queries (1 hour TTL)"""
    return query_supabase_rag(query=query, match_count=match_count)

@st.cache_data(ttl=3600, show_spinner=False)
def cached_graphrag_query(topic: str, query: str, method: str) -> dict:
    """Cached wrapper for GraphRAG queries (1 hour TTL)"""
    return query_graphrag_pass2(topic=topic, query=query)

@st.cache_data(ttl=3600, show_spinner=False)
def cached_synthesis(query: str, affidavit_data: dict, communications_data: dict) -> dict:
    """Cached wrapper for SIMPLE 3-section lawyer-ready synthesis (1 hour TTL)"""
    # Convert dicts to JSON strings for hashing
    import json
    aff_str = json.dumps(affidavit_data, sort_keys=True)
    comm_str = json.dumps(communications_data, sort_keys=True)
    return simple_synthesis(query=query, affidavit_data=affidavit_data, communications_data=communications_data)

# Page config
st.set_page_config(
    page_title="Cross-RAG Query Interface",
    page_icon="🔍",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .source-box {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .result-header {
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .stats-box {
        background-color: #e8f4f8;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .error-box {
        background-color: #ffe6e6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #ff4444;
    }
    .success-box {
        background-color: #e6ffe6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #44ff44;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">🔍 Cross-RAG Query Interface</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Query Court Documents (Supabase) + Communications (GraphRAG) simultaneously</div>', unsafe_allow_html=True)

# Sidebar - Query Configuration
with st.sidebar:
    st.header("⚙️ Query Configuration")

    # Query mode
    query_mode = st.radio(
        "Query Mode",
        ["Dual Query", "Court Documents Only", "Communications Only", "Contradiction Analysis"],
        help="Choose what to query"
    )

    st.divider()

    # Supabase settings
    st.subheader("📄 Court Documents (Supabase)")
    supabase_enabled = query_mode in ["Dual Query", "Court Documents Only", "Contradiction Analysis"]
    match_count = st.slider("Max results to return", 5, 50, 20, 5, disabled=not supabase_enabled,
                         help="Number of most relevant document chunks to return. More results = more comprehensive search.")

    st.divider()

    # GraphRAG settings
    st.subheader("💬 Communications (GraphRAG)")
    graphrag_enabled = query_mode in ["Dual Query", "Communications Only", "Contradiction Analysis"]
    graphrag_method = st.selectbox(
        "Query method",
        ["global", "local"],
        help="Global: Community-based analysis. Local: Entity-based search.",
        disabled=not graphrag_enabled
    )

    st.divider()

    # Contradiction synthesis
    st.subheader("🔄 Contradiction Analysis")
    enable_synthesis = st.checkbox(
        "Enable contradiction synthesis",
        value=(query_mode == "Contradiction Analysis"),
        disabled=(query_mode != "Contradiction Analysis"),
        help="Use Claude to analyze contradictions between sources"
    )

    st.divider()

    # API status
    st.subheader("🔑 API Status")
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')

    st.write("Supabase:", "✅ Connected" if (supabase_url and supabase_key) else "❌ Missing")
    st.write("Anthropic API:", "✅ Connected" if anthropic_key else "❌ Missing")

    st.divider()

    # Cache management
    st.subheader("🗄️ Cache Management")
    st.write("Queries cached for 1 hour")
    if st.button("🔄 Clear Cache", help="Force refresh all cached queries"):
        st.cache_data.clear()
        st.success("Cache cleared!")

    st.divider()

    # Query history
    st.subheader("📜 Query History")
    if st.session_state.get('query_history'):
        st.write(f"{len(st.session_state.query_history)} recent queries")

        # Show last 5 queries with clickable buttons
        for idx, hist in enumerate(st.session_state.query_history[:5]):
            query_preview = hist['query'][:50] + "..." if len(hist['query']) > 50 else hist['query']
            timestamp = datetime.fromisoformat(hist['timestamp']).strftime("%H:%M")

            if st.button(
                f"🔄 {timestamp}: {query_preview}",
                key=f"history_{idx}",
                help=f"Click to re-run: {hist['query']}"
            ):
                # Set query text and rerun
                st.session_state.rerun_query = hist['query']
                st.rerun()
    else:
        st.write("No queries yet")

# Initialize session state for query history and templates
if 'query_history' not in st.session_state:
    st.session_state.query_history = []
if 'template_query' not in st.session_state:
    st.session_state.template_query = ""

# Main query interface
st.header("📝 Enter Your Query")

# Handle query history rerun or template selection
default_query = ""
if 'rerun_query' in st.session_state:
    default_query = st.session_state.rerun_query
    del st.session_state.rerun_query
elif st.session_state.template_query:
    default_query = st.session_state.template_query
    st.session_state.template_query = ""  # Clear after using

# Query input
query_text = st.text_area(
    "Query",
    value=default_query,
    height=100,
    placeholder="Example: Find all references to cannabis use, medical treatment, and safety concerns...",
    help="Enter your search query. Be specific for better results."
)

# Quick query templates
st.write("**Quick Templates:**")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🌿 Cannabis"):
        st.session_state.template_query = "Find all references to cannabis, marijuana, drug use, or substance abuse."
        st.rerun()

with col2:
    if st.button("👨‍👧 Parenting"):
        st.session_state.template_query = "Find all information about parenting involvement, care-giving responsibilities, and daily parenting tasks."
        st.rerun()

with col3:
    if st.button("🏠 Stability"):
        st.session_state.template_query = "Find all claims about housing stability, employment stability, emotional stability, or concerns about instability."
        st.rerun()

# Execute query button
if st.button("🔍 Execute Query", type="primary", disabled=not query_text):

    # Initialize session state for results
    if 'results' not in st.session_state:
        st.session_state.results = {}

    # Add to query history
    st.session_state.query_history.insert(0, {
        'query': query_text,
        'timestamp': datetime.now().isoformat(),
        'mode': query_mode
    })
    # Keep only last 10 queries
    st.session_state.query_history = st.session_state.query_history[:10]

    # Check if we should run queries in parallel (Dual Query or Contradiction Analysis)
    run_parallel = supabase_enabled and graphrag_enabled and query_mode in ["Dual Query", "Contradiction Analysis"]

    if run_parallel:
        # PARALLEL EXECUTION for Dual Query mode
        st.info("⚡ Running queries in parallel for faster results...")

        # Define thread-safe query functions (NO UI ELEMENTS)
        def run_supabase_query():
            """Run Supabase query in thread - NO Streamlit UI calls"""
            try:
                result = cached_supabase_query(
                    query=query_text,
                    match_count=match_count
                )
                return result
            except Exception as e:
                return {'status': 'ERROR', 'error': str(e)}

        def run_graphrag_query():
            """Run GraphRAG query in thread - NO Streamlit UI calls"""
            try:
                result = cached_graphrag_query(
                    topic="custom_query",
                    query=query_text,
                    method=graphrag_method
                )
                return result
            except Exception as e:
                return {'status': 'ERROR', 'error': str(e)}

        # Show status indicators
        supabase_status = st.empty()
        graphrag_status = st.empty()

        with supabase_status:
            st.write("📄 Court Documents: Querying...")
        with graphrag_status:
            st.write("💬 Communications: Querying...")

        # Execute queries in parallel (queries only, no UI)
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_supabase = executor.submit(run_supabase_query)
            future_graphrag = executor.submit(run_graphrag_query)

            # Wait for both to complete
            supabase_result = future_supabase.result()
            graphrag_result = future_graphrag.result()

            # Store results
            st.session_state.results['supabase'] = supabase_result
            st.session_state.results['graphrag'] = graphrag_result

        # Update status with results (in main thread)
        with supabase_status:
            if supabase_result.get('status') == 'SUCCESS':
                chunks_found = supabase_result.get('chunks_found', 0)
                st.success(f"✅ Court Documents complete ({chunks_found} chunks found)")
            else:
                st.error(f"❌ Court Documents failed: {supabase_result.get('error', 'Unknown error')}")

        with graphrag_status:
            if graphrag_result.get('status') == 'SUCCESS':
                st.success(f"✅ Communications complete ({graphrag_method} method)")
            else:
                st.error(f"❌ Communications failed: {graphrag_result.get('error', 'Unknown error')}")

        st.success("⚡ Parallel queries completed!")

    else:
        # SEQUENTIAL EXECUTION for single-source queries
        with st.spinner("Querying RAG systems..."):

            # Query Supabase RAG (Court Documents)
            if supabase_enabled:
                with st.status("📄 Querying Court Documents (Supabase)...", expanded=True) as status:
                    st.write(f"🔍 Searching 288 court documents (7,074 chunks)...")
                    st.write("⏳ Vector similarity search in progress...")

                    try:
                        st.write("📊 Querying permanent vector database...")
                        supabase_result = cached_supabase_query(
                            query=query_text,
                            match_count=match_count
                        )

                        if supabase_result.get('status') == 'SUCCESS':
                            chunks_found = supabase_result.get('chunks_found', 0)
                            st.write(f"✅ Found {chunks_found} relevant passages")
                            st.write(f"📈 Query completed (instant with cache)")
                            st.session_state.results['supabase'] = supabase_result
                            status.update(label=f"✅ Court Documents complete ({chunks_found} chunks)", state="complete")
                        else:
                            st.error(f"Error: {supabase_result.get('error', 'Unknown error')}")
                            st.session_state.results['supabase'] = supabase_result
                            status.update(label="❌ Court Documents query failed", state="error")

                    except Exception as e:
                        st.error(f"Exception: {str(e)}")
                        st.session_state.results['supabase'] = {
                            'status': 'ERROR',
                            'error': str(e)
                        }
                        status.update(label="❌ Court Documents query failed", state="error")

            # Query GraphRAG (Communications)
            if graphrag_enabled:
                with st.status("💬 Querying Communications (GraphRAG)...", expanded=True) as status:
                    st.write(f"🔍 Using {graphrag_method} query method...")
                    st.write("⏳ Analyzing 23,784 entities and relationships...")

                    try:
                        st.write("📊 Searching messages, emails, and communication patterns...")
                        graphrag_result = cached_graphrag_query(
                            topic="custom_query",
                            query=query_text,
                            method=graphrag_method
                        )

                        if graphrag_result.get('status') == 'SUCCESS':
                            st.write("✅ Successfully analyzed communications")
                            st.write("📈 Query completed in ~15-20 seconds")
                            st.session_state.results['graphrag'] = graphrag_result
                            status.update(label=f"✅ Communications complete ({graphrag_method} method)", state="complete")
                        else:
                            st.error(f"Error: {graphrag_result.get('error', 'Unknown error')}")
                            st.session_state.results['graphrag'] = graphrag_result
                            status.update(label="❌ Communications query failed", state="error")

                    except Exception as e:
                        st.error(f"Exception: {str(e)}")
                        st.session_state.results['graphrag'] = {
                            'status': 'ERROR',
                            'error': str(e)
                        }
                        status.update(label="❌ Communications query failed", state="error")

        # Synthesize contradictions (if enabled)
        if enable_synthesis and 'supabase' in st.session_state.results and 'graphrag' in st.session_state.results:
            with st.status("🔄 Synthesizing contradiction analysis...", expanded=True) as status:
                st.write("🤖 Analyzing results with Claude AI...")
                st.write("⏳ This may take 45-60 seconds...")

                try:
                    st.write("🔍 Producing simple 3-section lawyer-ready analysis...")
                    st.write("📚 Loading smoking gun evidence database...")
                    synthesis_result = cached_synthesis(
                        query=query_text,
                        affidavit_data=st.session_state.results['supabase'],
                        communications_data=st.session_state.results['graphrag']
                    )

                    if synthesis_result.get('status') == 'SUCCESS':
                        st.write("✅ Successfully generated 3-section analysis")
                        st.write("📝 Sections: Melissa's Claims, Counter-Evidence (with dates), Cross-Exam Questions")
                        st.session_state.results['synthesis'] = synthesis_result
                        status.update(label="✅ 3-section analysis complete", state="complete")
                    else:
                        st.error(f"Error: {synthesis_result.get('error', 'Unknown error')}")
                        st.session_state.results['synthesis'] = synthesis_result
                        status.update(label="❌ Analysis failed", state="error")

                except Exception as e:
                    st.error(f"Exception: {str(e)}")
                    st.session_state.results['synthesis'] = {
                        'status': 'ERROR',
                        'error': str(e)
                    }
                    status.update(label="❌ Analysis failed", state="error")

# Display results
if 'results' in st.session_state and st.session_state.results:

    st.divider()
    st.header("📊 Query Results")

    # Create tabs for different views
    if enable_synthesis and 'synthesis' in st.session_state.results:
        tab1, tab2, tab3, tab4 = st.tabs([
            "🔄 Contradiction Analysis",
            "📄 Court Documents",
            "💬 Communications",
            "📥 Export"
        ])
    else:
        tab1, tab2, tab3 = st.tabs([
            "📄 Court Documents",
            "💬 Communications",
            "📥 Export"
        ])
        tab4 = None

    # Contradiction Analysis Tab (if enabled)
    if enable_synthesis and 'synthesis' in st.session_state.results:
        with tab1:
            synthesis = st.session_state.results.get('synthesis', {})

            if synthesis.get('status') == 'SUCCESS':
                st.markdown('<div class="success-box">✅ Contradiction analysis completed successfully</div>', unsafe_allow_html=True)

                # Display synthesis report
                st.markdown("### Analysis Report")
                st.markdown(synthesis.get('report', 'No report generated'))

            else:
                st.markdown(f'<div class="error-box">❌ Error: {synthesis.get("error", "Unknown error")}</div>', unsafe_allow_html=True)

    # Court Documents Tab
    target_tab = tab1 if not enable_synthesis else tab2
    with target_tab:
        supabase = st.session_state.results.get('supabase', {})

        if supabase.get('status') == 'SUCCESS':
            # Stats
            st.markdown('<div class="stats-box">', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Chunks Found", supabase.get('chunks_found', 0))
            with col2:
                st.metric("Total in Index", supabase.get('total_in_index', 0))
            st.markdown('</div>', unsafe_allow_html=True)

            # Results
            st.markdown("### Results from Court Documents")
            results_text = supabase.get('results', 'No results returned')
            st.markdown(results_text)

        elif supabase.get('status') == 'ERROR':
            st.markdown(f'<div class="error-box">❌ Error: {supabase.get("error", "Unknown error")}</div>', unsafe_allow_html=True)
        else:
            st.info("Court documents not queried in this mode")

    # Communications Tab
    target_tab = tab2 if not enable_synthesis else tab3
    with target_tab:
        graphrag = st.session_state.results.get('graphrag', {})

        if graphrag.get('status') == 'SUCCESS':
            st.markdown('<div class="success-box">✅ Query completed successfully</div>', unsafe_allow_html=True)

            # Results
            st.markdown("### Results from Communications")
            results_text = graphrag.get('results', 'No results returned')
            st.markdown(results_text)

        elif graphrag.get('status') == 'ERROR':
            st.markdown(f'<div class="error-box">❌ Error: {graphrag.get("error", "Unknown error")}</div>', unsafe_allow_html=True)
        else:
            st.info("Communications not queried in this mode")

    # Export Tab
    target_tab = tab3 if not enable_synthesis else tab4
    if target_tab:
        with target_tab:
            st.markdown("### Export Results")

            # Prepare export data
            export_data = {
                'query': query_text,
                'timestamp': datetime.now().isoformat(),
                'results': st.session_state.results
            }

            # JSON export
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="📥 Download as JSON",
                    data=json.dumps(export_data, indent=2),
                    file_name=f"cross_rag_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )

            # Markdown export
            with col2:
                markdown_export = f"""# Cross-RAG Query Results

**Query:** {query_text}
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

"""

                if 'synthesis' in st.session_state.results:
                    markdown_export += f"""## Contradiction Analysis

{st.session_state.results['synthesis'].get('report', 'No report')}

---

"""

                if 'supabase' in st.session_state.results:
                    markdown_export += f"""## Court Documents Results

{st.session_state.results['supabase'].get('results', 'No results')}

---

"""

                if 'graphrag' in st.session_state.results:
                    markdown_export += f"""## Communications Results

{st.session_state.results['graphrag'].get('results', 'No results')}
"""

                st.download_button(
                    label="📥 Download as Markdown",
                    data=markdown_export,
                    file_name=f"cross_rag_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown"
                )

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9rem;'>
    <p><strong>Cross-RAG Query Interface v3.0.0 (Supabase + GraphRAG)</strong> | Legal Case Preparation</p>
    <p>Queries: <strong>Supabase Vector DB</strong> (288 PDFs, 7,074 chunks, PERMANENT storage) + <strong>GraphRAG Pass 2</strong> (23,784 entities, raw messages with dates)</p>
    <p><em>⚖️ Format: (1) Melissa's Claims, (2) Counter-Evidence with dates/sources, (3) Cross-Exam Questions</em></p>
    <p><em>⚡ New: Permanent storage (no 48hr expiration), vector similarity search, faster queries, 1-hour caching</em></p>
</div>
""", unsafe_allow_html=True)
