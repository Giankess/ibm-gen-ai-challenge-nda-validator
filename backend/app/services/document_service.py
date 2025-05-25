from docx import Document
from docx.shared import RGBColor, Pt
from docx.enum.text import WD_COLOR_INDEX, WD_PARAGRAPH_ALIGNMENT, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import os
from typing import List, Dict, Tuple
import copy
import shutil
import tempfile

class DocumentService:
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = upload_dir
        os.makedirs(upload_dir, exist_ok=True)

    def parse_document(self, file_path: str) -> Tuple[List[str], Document]:
        """
        Parse a Word document and return its paragraphs and the document object
        """
        try:
            print(f"Opening document at path: {file_path}")
            doc = Document(file_path)
            print(f"Successfully opened document. Number of paragraphs: {len(doc.paragraphs)}")
            paragraphs = [p.text for p in doc.paragraphs]
            print(f"Extracted {len(paragraphs)} paragraphs")
            return paragraphs, doc
        except Exception as e:
            print(f"Error parsing document: {str(e)}")
            print(f"Error type: {type(e)}")
            raise

    def _copy_document(self, doc: Document) -> Document:
        """
        Create a copy of a document while preserving all formatting
        """
        # Save the original document to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp_file:
            doc.save(temp_file.name)
            # Create a new document from the temporary file
            new_doc = Document(temp_file.name)
            # Clean up the temporary file
            os.unlink(temp_file.name)
            return new_doc

    def create_redline_document(self, original_doc: Document, changes: List[Dict]) -> Document:
        """
        Create a redline version of the document with suggested changes
        """
        # Create a copy of the original document
        redline_doc = self._copy_document(original_doc)
        
        # Process each paragraph to add redline changes
        for paragraph in redline_doc.paragraphs:
            for run in paragraph.runs:
                # Check if this run contains any changes
                is_changed = any(
                    change['original_text'] in run.text 
                    for change in changes
                )
                
                if is_changed:
                    # Add strikethrough for original text
                    run.font.strike = True
                    run.font.color.rgb = RGBColor(255, 0, 0)  # Red color
                    
                    # Add suggested text
                    for change in changes:
                        if change['original_text'] in run.text:
                            suggestion = paragraph.add_run(f" → {change['suggested_text']}")
                            suggestion.font.color.rgb = RGBColor(255, 0, 0)  # Red color

        return redline_doc

    def create_clean_document(self, original_doc: Document, changes: List[Dict]) -> Document:
        """
        Create a clean version of the document with changes applied
        """
        # Create a copy of the original document
        clean_doc = self._copy_document(original_doc)
        
        # Process each paragraph to apply changes
        for paragraph in clean_doc.paragraphs:
            for run in paragraph.runs:
                # Check if this run contains any changes
                is_changed = any(
                    change['original_text'] in run.text 
                    for change in changes
                )
                
                if is_changed:
                    # Apply suggested changes
                    for change in changes:
                        if change['original_text'] in run.text:
                            run.text = run.text.replace(
                                change['original_text'], 
                                change['suggested_text']
                            )

        return clean_doc

    def save_document(self, doc: Document, file_path: str) -> str:
        """
        Save a document to the specified path
        """
        doc.save(file_path)
        return file_path 