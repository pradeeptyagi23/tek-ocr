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

```env
git clone https://github.com/yourusername/yourrepository.git
cd yourrepository
```
