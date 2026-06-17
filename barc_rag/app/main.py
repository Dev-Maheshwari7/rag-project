"""
Streamlit UI for the BARC RAG system.
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.rag_pipeline import RAGPipeline
from ingest.ingest_pipeline import IngestPipeline
from db.postgres_client import PostgresDB
from config import DOCS_DIR


def initialize_session_state():
    """Initialize session state variables."""
    if "pipeline" not in st.session_state:
        st.session_state.pipeline = RAGPipeline()
    if "ingest_pipeline" not in st.session_state:
        st.session_state.ingest_pipeline = IngestPipeline()


def get_db_stats():
    """Get statistics from database."""
    try:
        postgres = PostgresDB()
        return postgres.get_stats()
    except Exception as e:
        return {"error": str(e)}


def run_ingestion():
    """Run document ingestion."""
    try:
        with st.spinner("Ingesting documents..."):
            stats = st.session_state.ingest_pipeline.ingest_directory(DOCS_DIR)
            st.success(
                f"✓ Ingestion complete!\n"
                f"  • Ingested: {stats['ingested_files']} files\n"
                f"  • Total chunks: {stats['total_chunks']}\n"
                f"  • Failed: {len(stats['failed_files'])} files"
            )
            if stats["failed_files"]:
                st.warning("Failed files:")
                for filepath, error in stats["failed_files"]:
                    st.write(f"  - {filepath}: {error}")
    except Exception as e:
        st.error(f"Ingestion error: {str(e)}")


def display_sources(source_chunks):
    """Display source chunks in expandable sections."""
    st.subheader("📚 Sources")
    for i, chunk in enumerate(source_chunks, 1):
        payload = chunk.get("payload", {})
        chunk_type = payload.get("type", "text").upper()
        source_file = payload.get("source_file", "unknown")
        page_num = payload.get("page_number", "unknown")
        content = payload.get("content", "")

        with st.expander(f"[{chunk_type}] {source_file} (Page {page_num})"):
            st.text(content[:500] + "..." if len(content) > 500 else content)
            if "rerank_score" in chunk:
                st.caption(f"Rerank Score: {chunk['rerank_score']:.4f}")


def main():
    """Main Streamlit app."""
    st.set_page_config(page_title="BARC RAG System", layout="wide")

    # Initialize
    initialize_session_state()

    # Title
    st.title("🚀 BARC Multimodal RAG System")
    st.markdown("A local RAG system with Grok LLM, Qdrant vectors, and PostgreSQL metadata.")

    # Sidebar
    with st.sidebar:
        st.header("📊 System Status")

        # Database stats
        stats = get_db_stats()
        if "error" not in stats:
            st.metric("Total Documents", stats.get("total_documents", 0))
            st.metric("Total Chunks", stats.get("total_chunks", 0))
        else:
            st.warning(f"Could not fetch stats: {stats['error']}")

        st.divider()

        st.header("📥 Document Ingestion")
        st.write(f"Documents directory: `{DOCS_DIR}`")

        if st.button("🔄 Start Ingestion", key="ingest_button"):
            run_ingestion()

        st.info(
            "Place PDF and DOCX files in the documents folder, "
            "then click 'Start Ingestion' to index them."
        )

    # Main query interface
    st.header("💬 Query Interface")

    with st.form("query_form"):
        query = st.text_area(
            "Enter your question:",
            placeholder="Ask a question about your documents...",
            height=100
        )
        submitted = st.form_submit_button("Search & Generate Answer", use_container_width=True)

    if submitted and query:
        with st.spinner("Processing query..."):
            try:
                result = st.session_state.pipeline.query(query)

                # Display answer
                st.subheader("💡 Answer")
                st.write(result["answer"])

                # Display sources if available
                if result["source_chunks"]:
                    st.divider()
                    display_sources(result["source_chunks"])
                else:
                    st.info("No source chunks retrieved.")

                # Document IDs
                if result["doc_ids"]:
                    st.divider()
                    st.subheader("📄 Referenced Documents")
                    st.write(", ".join(result["doc_ids"]))

            except Exception as e:
                st.error(f"Error processing query: {str(e)}")
    elif submitted:
        st.warning("Please enter a question.")


if __name__ == "__main__":
    main()
