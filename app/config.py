import os
import json
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database Configuration
    database_url: str
    database_echo: bool = True
    
    # Security & Authentication
    paseto_secret_key: str
    access_token_expire_minutes: int = 30
    
    # Application Settings
    app_env: str = "development"
    debug: bool = True
    
    # CORS Settings
    cors_origins: str = "http://localhost:3000,http://localhost:8080"
    
    # API Settings
    api_v1_prefix: str = "/api/v1"
    
    # AWS Secrets Manager (optional)
    aws_secrets_enabled: bool = False
    aws_secret_name: Optional[str] = None
    aws_region: str = "us-east-1"
    
    class Config:
        # Dynamically load environment-specific .env file from config/ directory
        env_file = f"config/.env.{os.getenv('APP_ENV', 'development')}"
        # Fallback to .env if environment-specific file doesn't exist
        env_file_encoding = 'utf-8'
        case_sensitive = False


def load_secrets_from_aws(settings_obj: Settings) -> Settings:
    """
    Load secrets from AWS Secrets Manager and override settings.
    
    Args:
        settings_obj: Settings instance to update
        
    Returns:
        Updated settings with values from AWS Secrets Manager
    """
    if not settings_obj.aws_secrets_enabled or not settings_obj.aws_secret_name:
        return settings_obj
    
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        # Create a Secrets Manager client
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=settings_obj.aws_region
        )
        
        try:
            get_secret_value_response = client.get_secret_value(
                SecretId=settings_obj.aws_secret_name
            )
        except ClientError as e:
            print(f"Error fetching secret from AWS: {e}")
            return settings_obj
        
        # Parse the secret
        if 'SecretString' in get_secret_value_response:
            secret = json.loads(get_secret_value_response['SecretString'])
            
            # Override settings with values from AWS Secrets Manager
            # Map AWS secret keys to settings attributes
            secret_mapping = {
                'DATABASE_URL': 'database_url',
                'PASETO_SECRET_KEY': 'paseto_secret_key',
                'ACCESS_TOKEN_EXPIRE_MINUTES': 'access_token_expire_minutes',
                'CORS_ORIGINS': 'cors_origins',
            }
            
            for aws_key, settings_attr in secret_mapping.items():
                if aws_key in secret:
                    setattr(settings_obj, settings_attr, secret[aws_key])
            
            print("✓ Loaded secrets from AWS Secrets Manager")
        
    except ImportError:
        print("Warning: boto3 not installed. Install with: pip install boto3")
    except Exception as e:
        print(f"Error loading AWS secrets: {e}")
    
    return settings_obj


def get_settings() -> Settings:
    """
    Get settings instance with optional AWS Secrets Manager integration.
    
    Returns:
        Settings instance with all configuration loaded
    """
    # First, check if environment-specific file exists, otherwise use .env
    app_env = os.getenv('APP_ENV', 'development')
    env_file = f"config/.env.{app_env}"
    
    if not os.path.exists(env_file):
        env_file = "config/.env"
    
    # Load settings from environment file
    settings = Settings(_env_file=env_file)
    
    # Override with AWS Secrets Manager if enabled
    if settings.aws_secrets_enabled:
        settings = load_secrets_from_aws(settings)
    
    return settings


# Create a global settings instance
settings = get_settings()
