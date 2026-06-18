"""
Document parsing module using unstructured library.
Extracts text and table elements with metadata.
"""

from pathlib import Path
from typing import List, Dict, Any
from unstructured.partition.auto import partition
from unstructured.partition.pdf import partition_pdf


def parse_document(file_path: str) -> List[Dict[str, Any]]:
    """
    Parse a document (PDF or DOCX) and extract structured elements.

    Args:
        file_path: Path to the document file

    Returns:
        List of structured elements: [
            {
                'type': 'text' | 'table',
                'content': str,
                'page_number': int,
                'source_file': str,
                'metadata': dict
            }
        ]
    """
    file_path_obj = Path(file_path)
    elements = []

    # Use hi_res strategy for better table extraction
    try:
        if file_path_obj.suffix.lower() == '.pdf':
            raw_elements = partition_pdf(file_path, strategy="hi_res")
        else:
            raw_elements = partition(file_path, strategy="hi_res")
    except Exception as e:
        print(f"Warning: Failed to parse {file_path} with hi_res, falling back to auto: {e}")
        raw_elements = partition(file_path, strategy="auto")

    for element in raw_elements:
        element_type = type(element).__name__

        # Extract text elements
        if element_type in ["Title", "NarrativeText", "ListItem"]:
            elements.append({
                "type": "text",
                "content": str(element),
                "page_number": getattr(element.metadata, "page_number", 1),
                "source_file": file_path_obj.name,
                "metadata": element.metadata.to_dict() if hasattr(element.metadata, "to_dict") else {}
            })

        # Extract table elements (keep whole)
        elif element_type == "Table":
            # Try to get HTML or text representation
            table_content = element.metadata.text_as_html if hasattr(element.metadata, "text_as_html") else str(element)
            print(f"[DEBUG] Found table element in {file_path_obj.name}")
            elements.append({
                "type": "table",
                "content": table_content,
                "page_number": getattr(element.metadata, "page_number", 1),
                "source_file": file_path_obj.name,
                "metadata": element.metadata.to_dict() if hasattr(element.metadata, "to_dict") else {}
            })
        else:
            # Log unexpected element types
            print(f"[DEBUG] Skipping element type: {element_type}")

            elements.append({
                "type": "table",
                "content": table_content,
                "page_number": getattr(element.metadata, "page_number", 1),
                "source_file": file_path_obj.name,
                "metadata": element.metadata.to_dict() if hasattr(element.metadata, "to_dict") else {}
            })

    return elements
