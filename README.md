# NDA Validator AI Assistant

An AI-powered tool for validating Non-Disclosure Agreements (NDAs) for Huber + Suhner.

## Features

- Upload NDA documents in Word format
- AI-powered analysis of NDA clauses
- Redline version generation with suggested changes
- Clean version generation with accepted changes
- Corporate design matching Huber + Suhner guidelines

## Architecture

The application follows a modern microservices architecture with the following components:

### Frontend (React)
- Single-page application built with React
- Material-UI for consistent and professional UI components
- Real-time document processing status updates
- Secure file upload and download functionality

### Backend (FastAPI)
- RESTful API built with FastAPI
- Document processing pipeline:
  1. Document parsing and text extraction
  2. AI-powered clause analysis
  3. Pattern matching for problematic clauses
  4. Risk assessment and categorization
  5. Document modification with suggested changes

### AI Processing Pipeline
1. **Document Analysis**
   - Text extraction from Word documents
   - Paragraph segmentation and processing
   - Semantic analysis using Sentence Transformers

2. **Clause Detection**
   - Pattern matching for problematic clauses
   - Category classification (confidentiality, duration, scope, etc.)
   - Risk level assessment for each clause

3. **Document Generation**
   - Redline version with suggested changes
   - Clean version with accepted modifications
   - Corporate design compliance

### Training System
The application includes a sophisticated training system that learns from expert-reviewed NDAs:

1. **Training Data Processing**
   - Analyzes redline versions of previously reviewed NDAs
   - Extracts patterns from accepted changes and modifications
   - Identifies common problematic clauses and their corrections

2. **Pattern Learning**
   - Automatic extraction of problematic patterns
   - Context-aware pattern matching
   - Category-based pattern organization
   - Suggestion generation based on historical corrections

3. **Continuous Improvement**
   - System learns from new document reviews
   - Pattern database automatically updates
   - Improved accuracy over time
   - Maintains consistency in suggestions

## Project Structure

```
nda-validator/
├── backend/         # Python FastAPI backend
│   ├── app/
│   │   ├── routes/     # API endpoints
│   │   ├── services/   # Business logic and AI processing
│   │   └── models/     # Data models
├── frontend/        # React frontend
│   ├── src/
│   │   ├── components/ # UI components
│   │   ├── services/   # API integration
│   │   └── styles/     # Styling
└── docker-compose.yml
```

## Setup Instructions

1. Ensure you have Docker and Docker Compose installed
2. Clone this repository
3. Run `docker-compose up --build`
4. Access the application at `http://localhost:3000`

## Development

### Backend
- Python 3.9+
- FastAPI
- LangChain
- python-docx
- Sentence Transformers for AI processing

### Frontend
- React
- Material-UI
- Axios for API communication

## License

Proprietary - Huber + Suhner 