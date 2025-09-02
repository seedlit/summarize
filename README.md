# Document Summarization API

A scalable FastAPI-based web service that provides intelligent document summarization using OpenAI's language models via LangChain. The application supports multiple document formats and is containerized for easy deployment with Kubernetes orchestration.

## Features

- 📄 **Multi-format Support**: Process PDF files and plain text documents
- 🤖 **AI-Powered Summarization**: Leverages OpenAI's GPT models through LangChain
- 🚀 **High Performance**: Built with FastAPI for async processing and high throughput
- 🐳 **Containerized**: Docker-ready with Kubernetes manifests for scalable deployment
- 🔧 **Production Ready**: Includes proper error handling, logging, and environment configuration
- 📊 **Interactive API**: Swagger UI documentation available at `/docs`
- ⚡ **Fast**: Async processing with uvicorn ASGI server
- 🔒 **Secure**: Environment-based configuration for API keys

## Quick Start

### Prerequisites

- Python 3.13+
- Docker (optional, for containerized deployment)
- Minikube (optional, for Kubernetes deployment)
- OpenAI API key

### 1. Local Development

#### Clone and Setup
```bash
git clone https://github.com/seedlit/summarize.git
cd summarize
```

#### Install Dependencies
Using uv (recommended):
```bash
uv sync --all-groups
```

#### Environment Configuration
Create a `.env` file in the project root:
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

#### Run the Application
```bash
# Using uv
uv run uvicorn src.app:app --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 2. Docker Deployment

#### Build the Docker Image
```bash
docker build -t summarize-app:latest .
```

#### Run with Docker
```bash
docker run -it -p 8000:8000 --env-file .env summarize-app:latest
```

### 3. Kubernetes Deployment

#### Prerequisites
```bash
# Install minikube (macOS)
brew install minikube

# Start minikube
minikube start
```

#### Deploy to Kubernetes
```bash
# Create secret for environment variables
kubectl create secret generic summarize-env --from-env-file=.env

# Load Docker image into minikube
minikube image load summarize-app:latest

# Deploy the application
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Check deployment status
kubectl get pods
kubectl get services

# Access the application
minikube service summarize-service --url
```

## API Usage

### Summarize Document

**Endpoint**: `POST /summarize`

**Description**: Upload a document (PDF or text file) and receive an AI-generated summary.

#### Example using curl:
```bash
curl -X POST "http://localhost:8000/summarize" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@your_document.pdf"
```

#### Example using Python:
```python
import requests

with open("document.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/summarize",
        files={"file": f}
    )

summary = response.json()
print(summary["summary"])
```

#### Response Format:
```json
{
  "summary": "Generated summary text here..."
}
```

## Development

### Code Quality Tools

The project includes pre-commit hooks for code quality:

```bash
# Install pre-commit hooks
uv run pre-commit install

# Run all checks
uv run pre-commit run --all-files
```

### Running Tests
```bash
# Run tests with coverage
uv run pytest --cov=src tests/

# Run specific test file
uv run pytest tests/test_summarize_document.py -v
```

### Project Structure
```
summarize/
├── src/
│   ├── app.py                 # FastAPI application
│   ├── summarize_document.py  # Core summarization logic
│   ├── utils.py              # Utility functions
│   ├── constants.py          # Application constants
│   └── exceptions.py         # Custom exception classes
├── tests/                    # Tests
├── k8s/                     # Kubernetes manifests
│   ├── deployment.yaml      # Application deployment
│   └── service.yaml        # Service configuration
├── Dockerfile              # Container definition
├── pyproject.toml         # Project configuration
└── README.md              # This file
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for language model access | Yes |
|  |

## Scaling and Production

### Kubernetes Features
- **Auto-scaling**: Configured for 3 replicas by default
- **Load balancing**: Built-in Kubernetes service load balancing
- **Health checks**: Ready for liveness and readiness probes
- **Secret management**: Environment variables stored as Kubernetes secrets

### Performance Considerations
- Async request processing with FastAPI
- Containerized for horizontal scaling
- Stateless design for easy load balancing
- Efficient PDF processing with PyPDF

## Error Handling

The API provides comprehensive error handling:
- **4XX**: Bad Request (invalid file format, missing filename)
- **5XX**: Internal Server Error (summarization failures, API issues)

All errors return structured JSON responses with descriptive messages.

## Supported File Formats

- **PDF**: Binary PDF files with text content
- **Text Files**: Plain text files (.txt)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and pre-commit hooks
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Roadmap

- [ ] Support for additional file formats (DOCX, RTF)
- [ ] Batch processing capabilities
- [ ] Caching layer for improved performance
- [ ] Monitoring and metrics (Prometheus, Grafana)
- [ ] Enhanced logging and error tracking (Sentry)
- [ ] Web UI for document upload
- [ ] Multi-language support
- [ ] Custom summarization parameters
