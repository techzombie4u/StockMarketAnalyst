
from flask import Blueprint, jsonify, request

meta_bp = Blueprint('meta', __name__, url_prefix='/api/meta')

@meta_bp.route('/status', methods=['GET'])
def meta_status():
    """Get meta system status"""
    return jsonify({
        "status": "active",
        "module": "meta",
        "endpoints": [
            "/api/meta/status",
            "/api/meta/info"
        ]
    })

@meta_bp.route('/info', methods=['GET'])
def meta_info():
    """Get meta information"""
    return jsonify({
        "message": "Meta info endpoint",
        "version": "1.7.5",
        "features": ["kpi", "predictions", "fusion"]
    })
