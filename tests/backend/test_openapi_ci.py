
import subprocess
import pytest
from pathlib import Path

def test_openapi_validates_with_swagger_cli():
    """Test that OpenAPI spec validates with swagger-cli"""
    repo_root = Path(__file__).parent.parent.parent
    openapi_path = repo_root / 'openapi.yaml'
    
    try:
        # Run swagger-cli validate
        result = subprocess.run(
            ['swagger-cli', 'validate', str(openapi_path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            pytest.fail(f"OpenAPI spec validation failed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")
            
        print(f"✅ OpenAPI spec validation passed: {result.stdout}")
        
    except FileNotFoundError:
        pytest.skip("swagger-cli not found. Install with: npm install -g swagger-cli")
    except subprocess.TimeoutExpired:
        pytest.fail("swagger-cli validation timed out")
    except Exception as e:
        pytest.fail(f"Error running swagger-cli validation: {e}")

def test_openapi_bundle_generates():
    """Test that OpenAPI spec can be bundled (resolves all refs)"""
    repo_root = Path(__file__).parent.parent.parent
    openapi_path = repo_root / 'openapi.yaml'
    
    try:
        # Run swagger-cli bundle to test ref resolution
        result = subprocess.run(
            ['swagger-cli', 'bundle', str(openapi_path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            pytest.fail(f"OpenAPI spec bundling failed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")
            
        # Should output valid JSON
        import json
        try:
            bundled_spec = json.loads(result.stdout)
            assert 'openapi' in bundled_spec
            assert 'info' in bundled_spec
            assert 'paths' in bundled_spec
        except json.JSONDecodeError:
            pytest.fail("swagger-cli bundle did not produce valid JSON")
            
    except FileNotFoundError:
        pytest.skip("swagger-cli not found. Install with: npm install -g swagger-cli")
    except subprocess.TimeoutExpired:
        pytest.fail("swagger-cli bundling timed out")
    except Exception as e:
        pytest.fail(f"Error running swagger-cli bundle: {e}")
