#!/usr/bin/env python3
"""
Custom CLI to run the FastAPI application with environment management.

Usage:
    python run.py --environment development --reload
    python run.py --env production --host 0.0.0.0 --port 8000
    python run.py --env staging --workers 4
"""

import argparse
import os
import sys


def main():
    parser = argparse.ArgumentParser(
        description='Run KPI-One FastAPI application with environment configuration'
    )
    
    # Custom environment argument
    parser.add_argument(
        '--environment', '--env',
        dest='environment',
        choices=['development', 'staging', 'production'],
        default='development',
        help='Application environment (default: development)'
    )
    
    # Uvicorn arguments
    parser.add_argument(
        '--host',
        default='127.0.0.1',
        help='Host to bind (default: 127.0.0.1)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='Port to bind (default: 8000)'
    )
    parser.add_argument(
        '--reload',
        action='store_true',
        help='Enable auto-reload on code changes'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=1,
        help='Number of worker processes (default: 1, ignored with --reload)'
    )
    parser.add_argument(
        '--log-level',
        choices=['critical', 'error', 'warning', 'info', 'debug', 'trace'],
        default='info',
        help='Log level (default: info)'
    )
    
    args = parser.parse_args()
    
    # Set APP_ENV environment variable before importing the app
    os.environ['APP_ENV'] = args.environment
    
    print(f"🚀 Starting KPI-One API")
    print(f"   Environment: {args.environment}")
    print(f"   Host: {args.host}:{args.port}")
    print(f"   Reload: {args.reload}")
    if not args.reload and args.workers > 1:
        print(f"   Workers: {args.workers}")
    print()
    
    # Import uvicorn after setting environment variable
    try:
        import uvicorn
    except ImportError:
        print("Error: uvicorn is not installed. Install it with: pip install uvicorn")
        sys.exit(1)
    
    # Configure uvicorn
    config = {
        'app': 'app.main:app',
        'host': args.host,
        'port': args.port,
        'log_level': args.log_level,
    }
    
    if args.reload:
        # Development mode with reload
        config['reload'] = True
    else:
        # Production mode with workers
        config['workers'] = args.workers
    
    # Run the application
    uvicorn.run(**config)


if __name__ == '__main__':
    main()
