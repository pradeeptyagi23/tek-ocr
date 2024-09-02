# FastAPI Application

This FastAPI application is designed for file uploads, OCR processing, and querying embeddings using Pinecone. It integrates with AWS Cognito for authentication, Redis for caching, and utilizes AI models for embedding creation.

## Features

- **User Authentication:** Integrates with AWS Cognito for user registration, login, and confirmation.
- **File Upload:** Supports uploading files to AWS S3 with asynchronous processing.
- **OCR Processing:** Processes OCR data, generates embeddings using OpenAI models, and upserts them into a Pinecone vector database.
- **Querying:** Allows querying the embedded data with rate limiting and caching mechanisms.

## Getting Started

### Prerequisites

Before you begin, ensure you have the following:

- Docker & Docker Compose
- An AWS account with Cognito, S3, and Pinecone set up
- Redis for caching
- A `.env` file with necessary configurations

### Environment Variables

Create a `.env` file in the root directory of your project. The file should contain the following environment variables:

```env
AWS_ACCESS_KEY_ID=<your_aws_access_key>
AWS_SECRET_ACCESS_KEY=<your_aws_secret_key>
AWS_REGION=<your_aws_region>
COGNITO_USER_POOL_ID=<your_cognito_user_pool_id>
COGNITO_CLIENT_ID=<your_cognito_client_id>
PINECONE_API_KEY=<your_pinecone_api_key>
PINECONE_ENV=<your_pinecone_environment>
REDIS_HOST=redis-server
REDIS_PORT=6379
```

### Clone the repository

```bash
git clone https://github.com/pradeeptyagi23/tek-ocr.git
cd tek-ocr
```

### Build and start the application
```bash
docker-compose up --build
```

# Endpoints 
The application provides the following endpoints:

## Authentication Endpoints
- **POST /auth/register** : Register a new user.
- **POST /auth/confirm** : Confirm a user registration with a confirmation code.
- **POST /auth/login** : Login with username and password to obtain a JWT token.

## File Upload Endpoints
- **POST /files/upload-files/** : Upload files to S3 and retrieve signed URLs.

## OCR Processing Endpoints
- **POST /ocr/processOCR** : Process an OCR document, generate embeddings, and store them in Pinecone.
- **POST /ocr/queryOCR/** : Query OCR data by providing a search string.

# Running Tests
To run linting and type checking tests using `pytest`, use the following command:
```bash
pytest
```

# Configuration for Linting and Type Checking
This project uses flake8 for linting and mypy for type checking. The configurations are set in pytest.ini as follows:

```bash
[pytest]
pythonpath = .
addopts = --mypy --flake8
python_files = *.py

[flake8]
max-line-length = 88
exclude = .git,__pycache__,old,build,dist

[mypy]
python_version = 3.11
ignore_missing_imports = True
strict = True
```

# Additional Information
- **Docker Compose Version**: 3.8
- **Python Version**: 3.11
For further details on each module, refer to the source code documentation.

