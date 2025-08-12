
import pytest
import json
from src.core.app import create_app
from src.core.validation import (
    EquitiesListSchema, OptionsPositionsSchema, AgentsConfigSchema, 
    AgentsRunSchema, CommoditiesDetailSchema, CommoditiesCorrelationsSchema,
    PinsLocksUpdateSchema
)

@pytest.fixture
def app():
    """Create test Flask app"""
    app = create_app()
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

class TestEquitiesValidation:
    """Test equities endpoint validation"""
    
    def test_equities_list_valid_params(self, client):
        """Test valid parameters for equities list"""
        response = client.get('/api/equities/list?sector=IT&minPrice=100&maxPrice=5000&limit=25')
        assert response.status_code == 200
        
    def test_equities_list_invalid_price_range(self, client):
        """Test invalid price range (min > max)"""
        response = client.get('/api/equities/list?minPrice=5000&maxPrice=100')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'validation_error'
        assert 'minPrice cannot be greater than maxPrice' in str(data['details'])
        
    def test_equities_list_negative_price(self, client):
        """Test negative price values"""
        response = client.get('/api/equities/list?minPrice=-100')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'validation_error'
        
    def test_equities_list_invalid_limit(self, client):
        """Test invalid limit values"""
        response = client.get('/api/equities/list?limit=0')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'validation_error'
        
        response = client.get('/api/equities/list?limit=101')
        assert response.status_code == 400

class TestOptionsValidation:
    """Test options endpoint validation"""
    
    def test_options_positions_valid_params(self, client):
        """Test valid parameters for options positions"""
        response = client.get('/api/options/positions?symbol=TCS&strategy=strangle&status=open&limit=10')
        assert response.status_code == 200
        
    def test_options_positions_invalid_strategy(self, client):
        """Test invalid strategy value"""
        response = client.get('/api/options/positions?strategy=invalid_strategy')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'validation_error'
        
    def test_options_positions_invalid_status(self, client):
        """Test invalid status value"""
        response = client.get('/api/options/positions?status=invalid_status')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'validation_error'
        
    def test_options_positions_invalid_limit(self, client):
        """Test invalid limit values"""
        response = client.get('/api/options/positions?limit=0')
        assert response.status_code == 400
        
        response = client.get('/api/options/positions?limit=101')
        assert response.status_code == 400

class TestAgentsValidation:
    """Test agents endpoint validation"""
    
    def test_agents_config_valid_data(self, client):
        """Test valid agent config data"""
        data = {
            "agent_id": "test_agent",
            "enabled": True,
            "config": {"param1": "value1"},
            "interval_minutes": 60
        }
        response = client.post('/api/agents/config', 
                             data=json.dumps(data), 
                             content_type='application/json')
        assert response.status_code == 200
        
    def test_agents_config_missing_agent_id(self, client):
        """Test missing required agent_id"""
        data = {"enabled": True}
        response = client.post('/api/agents/config', 
                             data=json.dumps(data), 
                             content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'validation_error'
        
    def test_agents_config_empty_agent_id(self, client):
        """Test empty agent_id"""
        data = {"agent_id": "   "}
        response = client.post('/api/agents/config', 
                             data=json.dumps(data), 
                             content_type='application/json')
        assert response.status_code == 400
        
    def test_agents_config_invalid_interval(self, client):
        """Test invalid interval_minutes"""
        data = {"agent_id": "test_agent", "interval_minutes": 0}
        response = client.post('/api/agents/config', 
                             data=json.dumps(data), 
                             content_type='application/json')
        assert response.status_code == 400
        
        data = {"agent_id": "test_agent", "interval_minutes": 1441}
        response = client.post('/api/agents/config', 
                             data=json.dumps(data), 
                             content_type='application/json')
        assert response.status_code == 400
        
    def test_agents_run_valid_data(self, client):
        """Test valid agent run data"""
        data = {
            "agent_id": "test_agent",
            "force_refresh": True,
            "timeout_seconds": 120
        }
        response = client.post('/api/agents/run', 
                             data=json.dumps(data), 
                             content_type='application/json')
        assert response.status_code == 200
        
    def test_agents_run_invalid_timeout(self, client):
        """Test invalid timeout_seconds"""
        data = {"agent_id": "test_agent", "timeout_seconds": 0}
        response = client.post('/api/agents/run', 
                             data=json.dumps(data), 
                             content_type='application/json')
        assert response.status_code == 400
        
        data = {"agent_id": "test_agent", "timeout_seconds": 301}
        response = client.post('/api/agents/run', 
                             data=json.dumps(data), 
                             content_type='application/json')
        assert response.status_code == 400

class TestCommoditiesValidation:
    """Test commodities endpoint validation"""
    
    def test_commodities_detail_valid_params(self, client):
        """Test valid parameters for commodities detail"""
        response = client.get('/api/commodities/GOLD/detail?tf=30D')
        assert response.status_code == 200
        
    def test_commodities_detail_invalid_timeframe(self, client):
        """Test invalid timeframe value"""
        response = client.get('/api/commodities/GOLD/detail?tf=invalid_tf')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'validation_error'
        
    def test_commodities_correlations_valid_params(self, client):
        """Test valid parameters for commodities correlations"""
        response = client.get('/api/commodities/correlations?symbol=GOLD')
        assert response.status_code == 200
        
    def test_commodities_correlations_missing_symbol(self, client):
        """Test missing required symbol"""
        response = client.get('/api/commodities/correlations')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'validation_error'
        
    def test_commodities_correlations_empty_symbol(self, client):
        """Test empty symbol"""
        response = client.get('/api/commodities/correlations?symbol=')
        assert response.status_code == 400

class TestPinsLocksValidation:
    """Test pins/locks endpoint validation"""
    
    def test_pins_valid_data(self, client):
        """Test valid pins update data"""
        data = {
            "type": "EQUITY",
            "symbol": "TCS",
            "action": "pin"
        }
        response = client.post('/api/pins', 
                             data=json.dumps(data), 
                             content_type='application/json')
        assert response.status_code == 200
        
    def test_pins_invalid_type(self, client):
        """Test invalid product type"""
        data = {
            "type": "INVALID_TYPE",
            "symbol": "TCS",
            "action": "pin"
        }
        response = client.post('/api/pins', 
                             data=json.dumps(data), 
                             content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'validation_error'
        
    def test_pins_invalid_action(self, client):
        """Test invalid action"""
        data = {
            "type": "EQUITY",
            "symbol": "TCS",
            "action": "invalid_action"
        }
        response = client.post('/api/pins', 
                             data=json.dumps(data), 
                             content_type='application/json')
        assert response.status_code == 400
        
    def test_pins_empty_symbol(self, client):
        """Test empty symbol"""
        data = {
            "type": "EQUITY",
            "symbol": "   ",
            "action": "pin"
        }
        response = client.post('/api/pins', 
                             data=json.dumps(data), 
                             content_type='application/json')
        assert response.status_code == 400

class TestRateLimiting:
    """Test rate limiting functionality"""
    
    def test_rate_limit_enforcement(self, client):
        """Test that rate limiting is enforced"""
        # Make many requests quickly to trigger rate limit
        responses = []
        for i in range(65):  # Exceed 60 per minute limit
            response = client.get('/api/equities/list')
            responses.append(response.status_code)
            
        # Should eventually get 429 (Too Many Requests)
        assert 429 in responses
        
    def test_rate_limit_headers(self, client):
        """Test that rate limiting headers are present"""
        response = client.get('/api/equities/list')
        # Flask-Limiter should add rate limit headers
        assert 'X-RateLimit-Limit' in response.headers or 'Retry-After' in response.headers

class TestContentLengthValidation:
    """Test max content length validation"""
    
    def test_max_content_length_enforcement(self, client):
        """Test that requests exceeding max content length are rejected"""
        # Create a large payload (> 16MB)
        large_data = {
            "agent_id": "test",
            "config": {"large_field": "x" * (17 * 1024 * 1024)}  # 17MB
        }
        
        response = client.post('/api/agents/config', 
                             data=json.dumps(large_data), 
                             content_type='application/json')
        assert response.status_code == 413  # Request Entity Too Large

class TestSchemaObjects:
    """Test marshmallow schema objects directly"""
    
    def test_equities_schema_validation(self):
        """Test EquitiesListSchema validation"""
        schema = EquitiesListSchema()
        
        # Valid data
        valid_data = {"sector": "IT", "minPrice": 100, "maxPrice": 5000, "limit": 25}
        result = schema.load(valid_data)
        assert result == valid_data
        
        # Invalid data - price range
        invalid_data = {"minPrice": 5000, "maxPrice": 100}
        with pytest.raises(Exception):
            schema.load(invalid_data)
            
    def test_agents_schema_validation(self):
        """Test AgentsConfigSchema validation"""
        schema = AgentsConfigSchema()
        
        # Valid data
        valid_data = {"agent_id": "test_agent", "enabled": True, "interval_minutes": 60}
        result = schema.load(valid_data)
        assert result == valid_data
        
        # Invalid data - missing agent_id
        invalid_data = {"enabled": True}
        with pytest.raises(Exception):
            schema.load(invalid_data)
