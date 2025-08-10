
"""
Meta API endpoints for system status and last updated timestamps
"""

import json
import os
from datetime import datetime
from flask import Blueprint, jsonify
from src.common_repository.config.runtime import get_market_tz
from src.common_repository.storage.json_store import json_store

meta_bp = Blueprint('meta', __name__, url_prefix='/api/meta')

# Storage for last updated timestamps
LAST_UPDATED_FILE = 'data/runtime/last_updated.json'

def get_last_updated_data():
    """Get last updated timestamps for all pages"""
    try:
        return json_store.load('last_updated', {
            'dashboard': {'auto': None, 'manual': None},
            'equities': {'auto': None, 'manual': None},
            'options': {'auto': None, 'manual': None},
            'commodities': {'auto': None, 'manual': None}
        })
    except Exception:
        return {
            'dashboard': {'auto': None, 'manual': None},
            'equities': {'auto': None, 'manual': None},
            'options': {'auto': None, 'manual': None},
            'commodities': {'auto': None, 'manual': None}
        }

def update_last_updated(page: str, refresh_type: str):
    """Update last updated timestamp for a page"""
    try:
        ist = get_market_tz()
        now_ist = datetime.now(ist)
        timestamp = now_ist.isoformat()
        
        data = get_last_updated_data()
        
        if page not in data:
            data[page] = {'auto': None, 'manual': None}
        
        data[page][refresh_type] = timestamp
        
        json_store.save('last_updated', data)
        return True
        
    except Exception as e:
        print(f"Error updating last updated: {e}")
        return False

@meta_bp.route('/last_updated')
def get_last_updated():
    """Get last updated timestamps for all pages"""
    try:
        data = get_last_updated_data()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@meta_bp.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(get_market_tz()).isoformat(),
        'market_hours': is_market_hours_now()
    })
