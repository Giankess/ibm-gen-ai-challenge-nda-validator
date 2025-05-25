from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from typing import Optional, Dict
import os
from datetime import datetime
from ..services.document_service import DocumentService
from ..services.ai_service import AIService

router = APIRouter(prefix="/api/documents", tags=["documents"])

# Initialize services
document_service = DocumentService()
ai_service = AIService()

# Store document processing status
document_status: Dict[str, Dict] = {}

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload an NDA document for validation
    """
    if not file.filename.endswith(('.docx', '.doc')):
        raise HTTPException(status_code=400, detail="Only Word documents are allowed")
    
    # Create unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(document_service.upload_dir, filename)
    
    print(f"Saving file to: {file_path}")
    
    # Save the file
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
    except Exception as e:
        print(f"Error saving file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")
    
    # Initialize document status
    document_status[filename] = {
        "status": "processing",
        "analysis": None,
        "redline_path": None,
        "clean_path": None
    }
    
    # Process the document
    try:
        print("Parsing document...")
        # Parse document
        paragraphs, doc = document_service.parse_document(file_path)
        
        print("Analyzing document...")
        # Analyze document
        analysis = ai_service.analyze_nda(paragraphs)
        
        print("Creating redline version...")
        # Create redline version
        redline_doc = document_service.create_redline_document(doc, analysis["changes"])
        redline_path = os.path.join(document_service.upload_dir, f"redline_{filename}")
        document_service.save_document(redline_doc, redline_path)
        
        # Update status
        document_status[filename].update({
            "status": "completed",
            "analysis": analysis,
            "redline_path": redline_path
        })
        
    except Exception as e:
        print(f"Error processing document: {str(e)}")
        document_status[filename]["status"] = "error"
        document_status[filename]["error"] = str(e)
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")
    
    return {
        "filename": filename,
        "message": "Document uploaded and processed successfully",
        "analysis": analysis
    }

@router.post("/generate-clean/{filename}")
async def generate_clean_version(filename: str):
    """
    Generate a clean version of the document with suggested changes applied
    """
    if filename not in document_status:
        raise HTTPException(status_code=404, detail="Document not found")
    
    status = document_status[filename]
    if status["status"] != "completed":
        raise HTTPException(status_code=400, detail="Document processing not completed")
    
    try:
        # Get the original document path
        original_path = os.path.join(document_service.upload_dir, filename)
        if not os.path.exists(original_path):
            raise HTTPException(status_code=404, detail="Original document not found")
        
        # Parse the original document
        paragraphs, doc = document_service.parse_document(original_path)
        
        # Create clean version
        clean_doc = document_service.create_clean_document(doc, status["analysis"]["changes"])
        clean_path = os.path.join(document_service.upload_dir, f"clean_{filename}")
        document_service.save_document(clean_doc, clean_path)
        
        # Update status
        document_status[filename]["clean_path"] = clean_path
        
        return {
            "message": "Clean version generated successfully",
            "clean_path": clean_path
        }
        
    except Exception as e:
        print(f"Error generating clean version: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating clean version: {str(e)}")

@router.get("/status/{filename}")
async def get_document_status(filename: str):
    """
    Get the processing status of a document
    """
    if filename not in document_status:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document_status[filename]

@router.get("/download/{filename}")
async def download_document(filename: str, version: str = "redline"):
    """
    Download a processed document (redline or clean version)
    """
    if filename not in document_status:
        raise HTTPException(status_code=404, detail="Document not found")
    
    status = document_status[filename]
    if status["status"] != "completed":
        raise HTTPException(status_code=400, detail="Document processing not completed")
    
    if version == "clean" and not status["clean_path"]:
        raise HTTPException(status_code=400, detail="Clean version not generated yet. Please generate it first.")
    
    file_path = status["redline_path"] if version == "redline" else status["clean_path"]
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Processed document not found")
    
    return FileResponse(
        path=file_path,
        filename=os.path.basename(file_path),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

@router.get("/analysis/{filename}")
async def get_document_analysis(filename: str):
    """
    Get the detailed analysis of a document
    """
    if filename not in document_status:
        raise HTTPException(status_code=404, detail="Document not found")
    
    status = document_status[filename]
    if status["status"] != "completed":
        raise HTTPException(status_code=400, detail="Document processing not completed")
    
    return {
        "analysis": status["analysis"],
        "risk_level": status["analysis"]["overall_risk_level"],
        "missing_clauses": status["analysis"]["missing_clauses"],
        "clause_categories": status["analysis"]["clause_categories"]
    } 