
import pytest
import json
import yaml
import os
from pathlib import Path

def test_openapi_spec_exists():
    """Test that openapi.yaml exists at repo root"""
    repo_root = Path(__file__).parent.parent.parent
    openapi_path = repo_root / 'openapi.yaml'
    assert openapi_path.exists(), "openapi.yaml file should exist at repo root"

def test_openapi_spec_is_valid_yaml():
    """Test that openapi.yaml is valid YAML"""
    repo_root = Path(__file__).parent.parent.parent
    openapi_path = repo_root / 'openapi.yaml'
    
    with open(openapi_path, 'r') as f:
        try:
            spec = yaml.safe_load(f)
            assert spec is not None, "OpenAPI spec should not be empty"
        except yaml.YAMLError as e:
            pytest.fail(f"OpenAPI spec is not valid YAML: {e}")

def test_openapi_spec_has_required_fields():
    """Test that openapi.yaml has required OpenAPI fields"""
    repo_root = Path(__file__).parent.parent.parent
    openapi_path = repo_root / 'openapi.yaml'
    
    with open(openapi_path, 'r') as f:
        spec = yaml.safe_load(f)
    
    # Required OpenAPI 3.0 fields
    assert 'openapi' in spec, "OpenAPI spec must have 'openapi' field"
    assert 'info' in spec, "OpenAPI spec must have 'info' field"
    assert 'paths' in spec, "OpenAPI spec must have 'paths' field"
    
    # Check version format
    assert spec['openapi'].startswith('3.'), "OpenAPI version should be 3.x"
    
    # Check info fields
    info = spec['info']
    assert 'title' in info, "Info section must have 'title'"
    assert 'version' in info, "Info section must have 'version'"

def test_openapi_spec_has_fusion_endpoints():
    """Test that key Fusion API endpoints are documented"""
    repo_root = Path(__file__).parent.parent.parent
    openapi_path = repo_root / 'openapi.yaml'
    
    with open(openapi_path, 'r') as f:
        spec = yaml.safe_load(f)
    
    paths = spec.get('paths', {})
    
    # Key endpoints that should be documented
    required_endpoints = [
        '/health',
        '/api/fusion/dashboard',
        '/api/equities/list',
        '/api/options/strangle/candidates',
        '/api/commodities/signals',
        '/api/pins',
        '/api/locks'
    ]
    
    for endpoint in required_endpoints:
        assert endpoint in paths, f"Endpoint {endpoint} should be documented in OpenAPI spec"

def test_swagger_ui_accessible(client):
    """Test that Swagger UI is accessible at /docs"""
    response = client.get('/docs/')
    assert response.status_code == 200
    assert b'swagger-ui' in response.data.lower() or b'swagger' in response.data.lower()

def test_openapi_json_endpoint_accessible(client):
    """Test that OpenAPI JSON is accessible at /api"""
    response = client.get('/api')
    assert response.status_code == 200
    
    # Should return valid JSON
    spec = response.get_json()
    assert spec is not None
    assert 'openapi' in spec
    assert 'info' in spec
    assert 'paths' in spec

def test_openapi_spec_validates_responses():
    """Test that documented endpoints have proper response schemas"""
    repo_root = Path(__file__).parent.parent.parent
    openapi_path = repo_root / 'openapi.yaml'
    
    with open(openapi_path, 'r') as f:
        spec = yaml.safe_load(f)
    
    paths = spec.get('paths', {})
    
    for path, path_spec in paths.items():
        for method, method_spec in path_spec.items():
            if method in ['get', 'post', 'put', 'delete']:
                responses = method_spec.get('responses', {})
                assert responses, f"Endpoint {method.upper()} {path} should have responses defined"
                
                # Should have at least a 200 response for GET endpoints
                if method == 'get':
                    assert '200' in responses, f"GET {path} should have a 200 response defined"

@pytest.fixture
def client():
    """Create test client"""
    import sys
    from pathlib import Path
    
    # Add src to path
    src_path = Path(__file__).parent.parent.parent / 'src'
    sys.path.insert(0, str(src_path))
    
    from core.app import create_app
    app = create_app()
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        yield client
