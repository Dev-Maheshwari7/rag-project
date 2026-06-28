import os
os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR\tessdata"
os.environ["PATH"] += r";C:\Program Files\Tesseract-OCR"
from dotenv import load_dotenv
load_dotenv()
from unstructured.partition.pdf import partition_pdf
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# Ensure the output directory exists
import json
from typing import List

# Unstructured for document parsing
from unstructured.partition.pdf import partition_pdf
from unstructured.chunking.title import chunk_by_title

# LangChain components
from langchain_core.documents import Document

from langchain_chroma import Chroma
from langchain_core.messages import HumanMessage

# Fixed the double .pdf extension typo
file_path = 'rag_test_benchmark_corpus.pdf'

elements = partition_pdf(
    filename=file_path,
    infer_table_structure=True,
    strategy="hi_res",
   
    chunking_strategy="by_title",
    max_characters=10000,
    combine_text_under_n_chars=2000,
    new_after_n_chars=6000,
)

tables = [element for element in elements if element.category == 'Table']
print(f"Found {len(tables)} tables")

def separate_content_types(chunk):
    """Analyze what types of content are in a chunk"""
    content_data = {
        'text': chunk.text,
        'tables': [],
        
        'types': ['text']
    }
    
    # Check for tables and images in original elements
    if hasattr(chunk, 'metadata') and hasattr(chunk.metadata, 'orig_elements'):
        for element in chunk.metadata.orig_elements:
            element_type = type(element).__name__
            
            # Handle tables
            if element_type == 'Table':
                content_data['types'].append('table')
                table_html = getattr(element.metadata, 'text_as_html', element.text)
                content_data['tables'].append(table_html)
            
            # Handle images
            
    
    content_data['types'] = list(set(content_data['types']))
    return content_data


from langchain_groq import ChatGroq
def create_ai_enhanced_summary(text: str, tables: List[str]) -> str:
    """Create AI-enhanced searchable summary for text + tables"""

    try:
        llm = ChatGroq(
                model="qwen/qwen3-32b",
                temperature=0,
                reasoning_format="hidden",
                reasoning_effort="none",
            )

        prompt_text = f"""
You are creating a searchable description for a document retrieval / RAG system.

CONTENT TO ANALYZE:

TEXT CONTENT:
{text}

"""

        if tables:
            prompt_text += "TABLES:\n"
            for i, table in enumerate(tables):
                prompt_text += f"\nTable {i+1}:\n{table}\n"

        prompt_text += """
YOUR TASK:
Generate a comprehensive searchable description of the above content.

Include:
1. Key facts, names, dates, times, numbers, locations, organizations, and roles.
2. Important values from tables.
3. Main topics and concepts discussed.
4. Questions this content could answer.
5. Alternative search terms users might use.
6. Keywords that would improve retrieval.

IMPORTANT OUTPUT RULES:
- Do NOT include reasoning.
- Do NOT include your thought process.
- Do NOT include <think> tags.
- Do NOT say "Okay", "Let's analyze", or explain what you are doing.
- Do NOT mention that you are an AI.
- Only output the final searchable description.
- Start directly with: SEARCHABLE DESCRIPTION:
- Keep the output detailed but clean.
- Prioritize retrieval/searchability over beautiful writing.

SEARCHABLE DESCRIPTION:
"""

        message = HumanMessage(content=prompt_text)
        response = llm.invoke([message])

        return response.content.strip()

    except Exception as e:
        print(f"     ❌ AI summary failed: {e}")

        summary = f"{text[:300]}..."
        if tables:
            summary += f" [Contains {len(tables)} table(s)]"

        return summary
    
def summarise_chunks(chunks):
    """Process all chunks with AI Summaries"""
    print("🧠 Processing chunks with AI Summaries...")
    
    langchain_documents = []
    total_chunks = len(chunks)
    
    for i, chunk in enumerate(chunks):
        current_chunk = i + 1
        print(f"   Processing chunk {current_chunk}/{total_chunks}")
        
        # Analyze chunk content
        content_data = separate_content_types(chunk)
        
        # Debug prints
        print(f"     Types found: {content_data['types']}")
        print(f"     Tables: {len(content_data['tables'])}")
        
        # Create AI-enhanced summary if chunk has tables/images
        if content_data['tables']:
            print(f"     → Creating AI summary for mixed content...")
            try:
                enhanced_content = create_ai_enhanced_summary(
                    content_data['text'],
                    content_data['tables'], 
                )
                print(f"     → AI summary created successfully")
                print(f"     → Enhanced content preview: {enhanced_content[:200]}...")
            except Exception as e:
                print(f"     ❌ AI summary failed: {e}")
                enhanced_content = content_data['text']
        else:
            print(f"     → Using raw text (no tables)")
            enhanced_content = content_data['text']
        
        # Create LangChain Document with rich metadata
        doc = Document(
            page_content=enhanced_content,
            metadata={
                "original_content": json.dumps({
                    "raw_text": content_data['text'],
                    "tables_html": content_data['tables'],
                })
            }
        )
        
        langchain_documents.append(doc)
    
    print(f"✅ Processed {len(langchain_documents)} chunks")
    return langchain_documents


# Process chunks with AI
processed_chunks = summarise_chunks(elements)

def export_chunks_to_json(chunks, filename="chunks_export.json"):
    """Export processed chunks to clean JSON format"""
    export_data = []
    
    for i, doc in enumerate(chunks):
        chunk_data = {
            "chunk_id": i + 1,
            "enhanced_content": doc.page_content,
            "metadata": {
                "original_content": json.loads(doc.metadata.get("original_content", "{}"))
            }
        }
        export_data.append(chunk_data)
    
    # Save to file
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Exported {len(export_data)} chunks to {filename}")
    return export_data

# Export your chunks
json_data = export_chunks_to_json(processed_chunks)

from langchain_huggingface import HuggingFaceEmbeddings

def create_vector_store(documents, persist_directory="dbv1/chroma_db"):
    """Create and persist ChromaDB vector store"""
    print("🔮 Creating embeddings and storing in ChromaDB...")

    embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    encode_kwargs={"normalize_embeddings": True},
    )    
    
    
    # Create ChromaDB vector store
    print("--- Creating vector store ---")
    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embedding_model,
        persist_directory=persist_directory, 
        collection_metadata={"hnsw:space": "cosine"}
    )
    print("--- Finished creating vector store ---")
    
    print(f"✅ Vector store created and saved to {persist_directory}")
    return vectorstore

# Create the vector store
db = create_vector_store(processed_chunks)

# After your retrieval
query = "what is location and the date"
retriever = db.as_retriever(search_kwargs={"k": 3})
chunks = retriever.invoke(query)

# Export to JSON
export_chunks_to_json(chunks, "rag_results.json")