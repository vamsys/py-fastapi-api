# KPI-One API

FastAPI application with PASETO authentication and multi-environment configuration support.

## Environment Configuration

### Local Development

1. Copy the development environment template:
   ```bash
   cp config/.env.example config/.env.development
   ```

2. Update the values in `config/.env.development` with your local configuration.

3. Run the application using the custom CLI (recommended):
   ```bash
   python run.py --environment development --reload
   ```

   Or use the shorthand:
   ```bash
   python run.py --env development --reload
   ```

   Or use uvicorn directly with environment variable:
   ```bash
   export APP_ENV=development
   uvicorn app.main:app --reload
   ```

### Environment-Specific Configuration

The application supports multiple environments:
- **development** - Local development (uses `.env.development`)
- **staging** - Staging environment (uses `.env.staging`)
- **production** - Production environment (uses `.env.production`)

#### Using the Custom CLI (Recommended)

The `run.py` script provides a convenient way to set the environment:

```bash
# Development with auto-reload
python run.py --env development --reload

# Staging
python run.py --env staging --host 0.0.0.0 --port 8000

# Production with multiple workers
python run.py --env production --host 0.0.0.0 --port 8000 --workers 4

# With custom log level
python run.py --env development --reload --log-level debug
```

#### Using Uvicorn Directly

Alternatively, set the `APP_ENV` environment variable manually:
```bash
export APP_ENV=production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### AWS Secrets Manager Integration

For production deployments, you can use AWS Secrets Manager to securely store sensitive configuration values.

#### Setup AWS Secrets Manager

1. Create a secret in AWS Secrets Manager with key-value pairs:
   ```json
   {
     "DATABASE_URL": "postgresql+psycopg://user:pass@host:5432/db",
     "PASETO_SECRET_KEY": "your-32-byte-secret-key",
     "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
     "CORS_ORIGINS": "https://example.com"
   }
   ```

2. Install boto3:
   ```bash
   pip install boto3
   ```

3. Enable AWS Secrets Manager in your environment file (e.g., `config/.env.production`):
   ```bash
   AWS_SECRETS_ENABLED=True
   AWS_SECRET_NAME=kpi-one/prod
   AWS_REGION=us-east-1
   ```

4. Configure AWS credentials:
   - Use IAM roles (recommended for EC2/ECS/Lambda)
   - Or set AWS credentials via environment variables:
     ```bash
     export AWS_ACCESS_KEY_ID=your_access_key
     export AWS_SECRET_ACCESS_KEY=your_secret_key
     ```

#### AWS Secrets Override Behavior

When `AWS_SECRETS_ENABLED=True`:
1. Application loads configuration from `.env.{APP_ENV}` file
2. AWS Secrets Manager values override the file-based configuration
3. Values not found in AWS Secrets Manager retain their file-based values

This allows you to:
- Keep non-sensitive config in environment files
- Store only sensitive data in AWS Secrets Manager
- Easily switch between local and cloud configuration

### Generate Secure Keys

Generate a new PASETO secret key (32 bytes):
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Project Structure

```
app/
├── main.py              # FastAPI application entry point
├── config.py            # Configuration management with AWS Secrets Manager
├── models/              # Database models and ORM
├── routers/             # API endpoints
├── schemas/             # Pydantic schemas
└── utils/               # Utilities (auth, helpers, etc.)
```

## Authentication

The API uses PASETO v4 local tokens for authentication.

### Login

```bash
POST /login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=yourpassword
```

Response:
```json
{
  "access_token": "v4.local.xxx...",
  "token_type": "bearer",
  "username": "user@example.com"
}
```

### Protected Endpoints
python run.py --env development --reload
```

Or with uvicorn directly:
```bash
export APP_ENV=development

Include the token in the Authorization header:
```bash
Authorization: Bearer v4.local.xxx...
```

## Development

Install dependencies:
```bash
pip install -r requirements.txt
```

Run database migrations:
```bash
alembic upgrade head
```

Start the development server:
```bash
uvicorn app.main:app --reload
```

## Deployment

### Environment Variables

For production deployments, ensure these environment variables are set:
- `APP_ENV=production`
- `DEBUG=False`
- `DATABASE_ECHO=False`
- `AWS_SECRETS_ENABLED=True` (if using AWS Secrets Manager)

### Docker Deployment

Set environment variables in your Docker Compose or Kubernetes configuration:
```yaml
environment:
  - APP_ENV=production
  - AWS_SECRETS_ENABLED=True
  - AWS_SECRET_NAME=kpi-one/prod
  - AWS_REGION=us-east-1
```

### AWS ECS/Lambda Deployment

Attach an IAM role with `secretsmanager:GetSecretValue` permission to your service.
