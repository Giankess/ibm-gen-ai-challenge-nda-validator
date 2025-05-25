from docx import Document
from docx.shared import RGBColor
from docx.enum.text import WD_COLOR_INDEX
import os
from typing import List, Dict, Tuple

class DocumentService:
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = upload_dir
        os.makedirs(upload_dir, exist_ok=True)

    def parse_document(self, file_path: str) -> Tuple[List[str], Document]:
        """
        Parse a Word document and return its paragraphs and the document object
        """
        doc = Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs]
        return paragraphs, doc

    def create_redline_document(self, original_doc: Document, changes: List[Dict]) -> Document:
        """
        Create a redline version of the document with suggested changes
        """
        redline_doc = Document()
        
        # Copy document properties
        redline_doc.core_properties = original_doc.core_properties
        
        # Process each paragraph
        for paragraph in original_doc.paragraphs:
            new_paragraph = redline_doc.add_paragraph()
            
            # Copy paragraph formatting
            new_paragraph.style = paragraph.style
            
            # Process runs (text with specific formatting)
            for run in paragraph.runs:
                # Check if this run contains any changes
                is_changed = any(
                    change['original_text'] in run.text 
                    for change in changes
                )
                
                if is_changed:
                    # Add strikethrough for original text
                    new_run = new_paragraph.add_run(run.text)
                    new_run.font.strike = True
                    new_run.font.color.rgb = RGBColor(255, 0, 0)  # Red color
                    
                    # Add suggested text
                    for change in changes:
                        if change['original_text'] in run.text:
                            suggestion = new_paragraph.add_run(f" → {change['suggested_text']}")
                            suggestion.font.color.rgb = RGBColor(255, 0, 0)  # Red color
                else:
                    # Copy original text without changes
                    new_run = new_paragraph.add_run(run.text)
                    new_run.font.name = run.font.name
                    new_run.font.size = run.font.size
                    new_run.font.bold = run.font.bold
                    new_run.font.italic = run.font.italic

        return redline_doc

    def create_clean_document(self, original_doc: Document, changes: List[Dict]) -> Document:
        """
        Create a clean version of the document with changes applied
        """
        clean_doc = Document()
        
        # Copy document properties
        clean_doc.core_properties = original_doc.core_properties
        
        # Process each paragraph
        for paragraph in original_doc.paragraphs:
            new_paragraph = clean_doc.add_paragraph()
            new_paragraph.style = paragraph.style
            
            # Process runs
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
                            new_text = run.text.replace(
                                change['original_text'], 
                                change['suggested_text']
                            )
                            new_run = new_paragraph.add_run(new_text)
                            new_run.font.name = run.font.name
                            new_run.font.size = run.font.size
                            new_run.font.bold = run.font.bold
                            new_run.font.italic = run.font.italic
                else:
                    # Copy original text without changes
                    new_run = new_paragraph.add_run(run.text)
                    new_run.font.name = run.font.name
                    new_run.font.size = run.font.size
                    new_run.font.bold = run.font.bold
                    new_run.font.italic = run.font.italic

        return clean_doc

    def save_document(self, doc: Document, file_path: str) -> str:
        """
        Save a document to the specified path
        """
        doc.save(file_path)
        return file_path 