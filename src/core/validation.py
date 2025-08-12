
from marshmallow import Schema, fields, ValidationError, validates_schema
from flask import jsonify, request, g

class EquitiesListSchema(Schema):
    """Schema for /api/equities/list endpoint"""
    sector = fields.Str(required=False, allow_none=True)
    minPrice = fields.Float(required=False, allow_none=True, validate=lambda x: x >= 0)
    maxPrice = fields.Float(required=False, allow_none=True, validate=lambda x: x >= 0)
    limit = fields.Int(required=False, allow_none=True, validate=lambda x: 1 <= x <= 100, missing=50)
    
    @validates_schema
    def validate_price_range(self, data, **kwargs):
        min_price = data.get('minPrice')
        max_price = data.get('maxPrice')
        if min_price is not None and max_price is not None and min_price > max_price:
            raise ValidationError("minPrice cannot be greater than maxPrice")

class OptionsPositionsSchema(Schema):
    """Schema for /api/options/positions endpoint"""
    symbol = fields.Str(required=False, allow_none=True)
    strategy = fields.Str(required=False, allow_none=True, validate=lambda x: x in ['strangle', 'straddle', 'iron_condor', 'covered_call'])
    status = fields.Str(required=False, allow_none=True, validate=lambda x: x in ['open', 'closed', 'pending'])
    limit = fields.Int(required=False, allow_none=True, validate=lambda x: 1 <= x <= 100, missing=20)

class AgentsConfigSchema(Schema):
    """Schema for /api/agents/config endpoint"""
    agent_id = fields.Str(required=True, validate=lambda x: len(x.strip()) > 0)
    enabled = fields.Bool(required=False, allow_none=True)
    config = fields.Dict(required=False, allow_none=True)
    interval_minutes = fields.Int(required=False, allow_none=True, validate=lambda x: 1 <= x <= 1440)

class AgentsRunSchema(Schema):
    """Schema for /api/agents/run endpoint"""
    agent_id = fields.Str(required=True, validate=lambda x: len(x.strip()) > 0)
    force_refresh = fields.Bool(required=False, missing=False)
    timeout_seconds = fields.Int(required=False, allow_none=True, validate=lambda x: 1 <= x <= 300)

class CommoditiesDetailSchema(Schema):
    """Schema for /api/commodities/{symbol}/detail endpoint"""
    tf = fields.Str(required=False, missing='30D', validate=lambda x: x in ['1D', '5D', '10D', '30D', '90D'])

class CommoditiesCorrelationsSchema(Schema):
    """Schema for /api/commodities/correlations endpoint"""
    symbol = fields.Str(required=True, validate=lambda x: len(x.strip()) > 0)

class PinsLocksUpdateSchema(Schema):
    """Schema for pins/locks update endpoints"""
    type = fields.Str(required=True, validate=lambda x: x.upper() in ['EQUITY', 'OPTIONS', 'COMMODITY'])
    symbol = fields.Str(required=True, validate=lambda x: len(x.strip()) > 0)
    action = fields.Str(required=True, validate=lambda x: x in ['pin', 'unpin', 'lock', 'unlock'])

def validate_request_data(schema_class, location='json'):
    """
    Decorator to validate request data using marshmallow schema
    
    Args:
        schema_class: Marshmallow schema class to use for validation
        location: Where to get data from ('json', 'args', 'form')
    """
    def decorator(f):
        def wrapper(*args, **kwargs):
            try:
                schema = schema_class()
                
                if location == 'json':
                    data = request.get_json() or {}
                elif location == 'args':
                    data = request.args.to_dict()
                elif location == 'form':
                    data = request.form.to_dict()
                else:
                    return jsonify({
                        "success": False,
                        "error": "invalid_validation_location",
                        "message": f"Invalid validation location: {location}"
                    }), 400
                
                # Validate the data
                validated_data = schema.load(data)
                
                # Add validated data to request context
                g.validated_data = validated_data
                
                return f(*args, **kwargs)
                
            except ValidationError as e:
                return jsonify({
                    "success": False,
                    "error": "validation_error",
                    "message": "Invalid input data",
                    "details": e.messages
                }), 400
            except Exception as e:
                return jsonify({
                    "success": False,
                    "error": "validation_internal_error",
                    "message": str(e)
                }), 500
                
        return wrapper
    return decorator

def get_validated_data():
    """Get validated data from request context"""
    return getattr(g, 'validated_data', {})
