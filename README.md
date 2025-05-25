# NDA Validator AI Assistant

An AI-powered tool for validating Non-Disclosure Agreements (NDAs) for Huber + Suhner.

## Features

- Upload NDA documents in Word format
- AI-powered analysis of NDA clauses
- Redline version generation with suggested changes
- Clean version generation with accepted changes
- Corporate design matching Huber + Suhner guidelines

## Project Structure

```
nda-validator/
├── backend/         # Python FastAPI backend
├── frontend/        # React frontend
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

### Frontend
- React
- Material-UI
- Axios

## License

Proprietary - Huber + Suhner 