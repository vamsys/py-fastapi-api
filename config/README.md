# Environment Configuration Files

This directory contains all environment-specific configuration files for the KPI-One application.

## Files

- `.env` - Active environment file (auto-loaded based on APP_ENV)
- `.env.development` - Development environment configuration
- `.env.example` - Template for new developers
- `.env.staging.example` - Staging environment template  
- `.env.production.example` - Production environment template

## Usage

The application automatically loads the appropriate `.env` file based on the `APP_ENV` environment variable:

```bash
# Development (loads config/.env.development)
python run.py --env development --reload

# Staging (loads config/.env.staging)
python run.py --env staging

# Production (loads config/.env.production)
python run.py --env production
```

## Setup

### For New Developers

1. Copy the example file:
   ```bash
   cp config/.env.example config/.env.development
   ```

2. Update the values in `config/.env.development` with your local settings

3. Generate a new PASETO secret key:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

### For Staging/Production

1. Copy the appropriate template:
   ```bash
   cp config/.env.staging.example config/.env.staging
   # or
   cp config/.env.production.example config/.env.production
   ```

2. Update all placeholder values with actual credentials

3. **Never commit actual `.env` files to git** - only the `.example` templates

## AWS Secrets Manager

For production deployments, you can enable AWS Secrets Manager to load sensitive values:

```bash
# In config/.env.production
AWS_SECRETS_ENABLED=True
AWS_SECRET_NAME=kpi-one/prod
AWS_REGION=us-east-1
```

AWS Secrets Manager values will override file-based configuration for:
- `DATABASE_URL`
- `PASETO_SECRET_KEY`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `CORS_ORIGINS`

## Security Notes

- All actual `.env*` files (except `.example` templates) are gitignored
- Use different secret keys for each environment
- Enable AWS Secrets Manager for production
- Rotate keys regularly
