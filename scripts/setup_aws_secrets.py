#!/usr/bin/env python3
"""
Script to create/update AWS Secrets Manager secret for KPI-One application.

Usage:
    python scripts/setup_aws_secrets.py --environment production --region us-east-1

Prerequisites:
    - AWS CLI configured with appropriate credentials
    - boto3 installed: pip install boto3
    - IAM permissions for secretsmanager:CreateSecret and secretsmanager:PutSecretValue
"""

import argparse
import json
import sys

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    print("Error: boto3 is not installed. Install it with: pip install boto3")
    sys.exit(1)


def create_or_update_secret(secret_name: str, secret_data: dict, region: str):
    """
    Create or update a secret in AWS Secrets Manager.
    
    Args:
        secret_name: Name of the secret (e.g., 'kpi-one/prod')
        secret_data: Dictionary containing secret key-value pairs
        region: AWS region (e.g., 'us-east-1')
    """
    client = boto3.client('secretsmanager', region_name=region)
    
    try:
        # Try to create the secret
        response = client.create_secret(
            Name=secret_name,
            Description=f'KPI-One application secrets for {secret_name.split("/")[-1]} environment',
            SecretString=json.dumps(secret_data)
        )
        print(f"✓ Created secret: {secret_name}")
        print(f"  ARN: {response['ARN']}")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceExistsException':
            # Secret exists, update it instead
            response = client.put_secret_value(
                SecretId=secret_name,
                SecretString=json.dumps(secret_data)
            )
            print(f"✓ Updated secret: {secret_name}")
            print(f"  ARN: {response['ARN']}")
        else:
            print(f"✗ Error managing secret: {e}")
            sys.exit(1)


def get_secret_template():
    """Return a template for the secret data."""
    return {
        "DATABASE_URL": "postgresql+psycopg://user:password@host:5432/database",
        "PASETO_SECRET_KEY": "generate-with-python-c-import-secrets-print-secrets-token-hex-32",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
        "CORS_ORIGINS": "https://example.com,https://www.example.com"
    }


def main():
    parser = argparse.ArgumentParser(
        description='Create or update AWS Secrets Manager secret for KPI-One'
    )
    parser.add_argument(
        '--environment',
        required=True,
        choices=['development', 'staging', 'production'],
        help='Environment name (development, staging, production)'
    )
    parser.add_argument(
        '--region',
        default='us-east-1',
        help='AWS region (default: us-east-1)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show the secret template without creating/updating'
    )
    
    args = parser.parse_args()
    
    secret_name = f"kpi-one/{args.environment}"
    secret_data = get_secret_template()
    
    if args.dry_run:
        print(f"Secret template for: {secret_name}")
        print(json.dumps(secret_data, indent=2))
        print("\n⚠️  This is a template. Update the values before creating the secret.")
        return
    
    print(f"Creating/updating secret: {secret_name}")
    print("⚠️  Warning: This will use template values. Update them after creation!")
    print("\nSecret data:")
    print(json.dumps(secret_data, indent=2))
    
    # Ask for confirmation
    response = input("\nDo you want to proceed? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Cancelled.")
        sys.exit(0)
    
    create_or_update_secret(secret_name, secret_data, args.region)
    
    print(f"\n✓ Done! Update the secret values in AWS Console or using AWS CLI:")
    print(f"  aws secretsmanager put-secret-value --secret-id {secret_name} \\")
    print(f"    --secret-string '{{\"DATABASE_URL\": \"your-value\", ...}}'")


if __name__ == '__main__':
    main()
