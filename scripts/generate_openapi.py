#!/usr/bin/env python3
"""
Script to generate OpenAPI specification and save to docs/openapi.yaml
"""
import os
import sys
import json
import yaml

# Add api directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))

from app.main import app


def generate_openapi_spec():
    """Generate OpenAPI spec and save to file"""
    print("Generating OpenAPI specification...")
    
    # Get OpenAPI schema from FastAPI
    openapi_schema = app.openapi()
    
    # Ensure docs directory exists
    docs_dir = os.path.join(os.path.dirname(__file__), '..', 'docs')
    os.makedirs(docs_dir, exist_ok=True)
    
    # Save as JSON
    json_path = os.path.join(docs_dir, 'openapi.json')
    with open(json_path, 'w') as f:
        json.dump(openapi_schema, f, indent=2)
    print(f"✓ Saved OpenAPI JSON to {json_path}")
    
    # Save as YAML
    yaml_path = os.path.join(docs_dir, 'openapi.yaml')
    with open(yaml_path, 'w') as f:
        yaml.dump(openapi_schema, f, sort_keys=False, default_flow_style=False)
    print(f"✓ Saved OpenAPI YAML to {yaml_path}")
    
    print("\nOpenAPI spec generated successfully!")
    print(f"  - Version: {openapi_schema['info']['version']}")
    print(f"  - Title: {openapi_schema['info']['title']}")
    print(f"  - Endpoints: {len(openapi_schema['paths'])}")


if __name__ == "__main__":
    try:
        generate_openapi_spec()
    except Exception as e:
        print(f"Error generating OpenAPI spec: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
