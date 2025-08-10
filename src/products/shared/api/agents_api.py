"""
AI Agents Framework API Endpoints
"""

import logging
from flask import Blueprint, jsonify, request
from ....agents.core.registry import agent_registry
from ....agents.orchestrator import agent_orchestrator
from ....agents.store.agent_outputs_repo import agent_outputs_repo
from src.common_repository.config.feature_flags import feature_flags
from src.common_repository.utils.date_utils import get_ist_now

logger = logging.getLogger(__name__)

# Create blueprint
agents_bp = Blueprint('agents', __name__, url_prefix='/api/agents')

@agents_bp.route('/list', methods=['GET'])
def list_agents():
    """List enabled agents and their specifications"""
    try:
        if not feature_flags.is_enabled('enable_agents_framework'):
            return jsonify({
                'success': False,
                'error': 'Agents framework is disabled'
            }), 400

        enabled_agents = agent_registry.get_enabled_agents()
        agent_specs = {}

        for agent_name in enabled_agents:
            spec = agent_registry.get_agent_spec(agent_name)
            if spec:
                agent_specs[agent_name] = {
                    'name': spec.name,
                    'purpose': spec.purpose,
                    'inputs': spec.inputs,
                    'outputs': spec.outputs,
                    'run_policy': spec.run_policy,
                    'enabled': spec.enabled
                }

        return jsonify({
            'success': True,
            'data': {
                'enabled_agents': enabled_agents,
                'specifications': agent_specs,
                'framework_enabled': True
            }
        })

    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@agents_bp.route('/run', methods=['POST'])
def run_agent():
    """Manually trigger agent execution"""
    try:
        if not feature_flags.is_enabled('enable_agents_framework'):
            return jsonify({
                'success': False,
                'error': 'Agents framework is disabled'
            }), 400

        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400

        agent_name = data.get('agent')
        scope_data = data.get('scope', {})
        context_overrides = data.get('context_overrides', {})

        if not agent_name:
            return jsonify({
                'success': False,
                'error': 'Agent name is required'
            }), 400

        if not agent_registry.is_agent_enabled(agent_name):
            return jsonify({
                'success': False,
                'error': f'Agent {agent_name} is not enabled'
            }), 400

        # Build context
        context = {
            'manual_trigger': True,
            'scope_data': scope_data,
            **context_overrides
        }

        # Build scope string
        product = scope_data.get('product', 'general')
        timeframe = scope_data.get('timeframe', 'default')
        symbol = scope_data.get('symbol', '')

        scope = f"{product}_{timeframe}"
        if symbol:
            scope += f"_{symbol}"

        # Enqueue execution
        job_id = agent_orchestrator.enqueue_agent_run(agent_name, context, scope)

        return jsonify({
            'success': True,
            'data': {
                'job_id': job_id,
                'status': 'accepted',
                'agent': agent_name,
                'scope': scope
            }
        })

    except Exception as e:
        logger.error(f"Error running agent: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@agents_bp.route('/latest', methods=['GET'])
def get_latest_output():
    """Get latest output for an agent and scope"""
    try:
        agent = request.args.get('agent')
        scope = request.args.get('scope', 'default')

        if not agent:
            return jsonify({
                'success': False,
                'error': 'Agent parameter is required'
            }), 400

        # Build scope if additional parameters provided
        product = request.args.get('product')
        timeframe = request.args.get('timeframe')
        symbol = request.args.get('symbol')

        if product and timeframe:
            scope = f"{product}_{timeframe}"
            if symbol:
                scope += f"_{symbol}"

        # Load latest output
        output_data = agent_outputs_repo.load_latest(agent, scope)

        if output_data:
            return jsonify({
                'success': True,
                'data': output_data
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No output found for the specified agent and scope'
            }), 404

    except Exception as e:
        logger.error(f"Error getting latest output: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@agents_bp.route('/history', methods=['GET'])
def get_agent_history():
    """Get agent execution history"""
    try:
        agent_name = request.args.get('agent', 'all')
        limit = int(request.args.get('limit', 10))

        from src.agents.store.agent_outputs_repo import AgentOutputsRepository
        outputs_repo = AgentOutputsRepository()

        if agent_name == 'all':
            # Get recent outputs from all agents
            history = outputs_repo.get_recent_outputs(limit=limit)
        else:
            # Get outputs from specific agent
            history = outputs_repo.get_agent_outputs(agent_name, limit=limit)

        return jsonify({
            'status': 'success',
            'agent': agent_name,
            'outputs': history,
            'timestamp': get_ist_now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting agent history: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': get_ist_now().isoformat()
        }), 500

@agents_bp.route('/trainer/run', methods=['POST'])
def run_trainer_agent():
    """Run trainer agent evaluation and retraining"""
    try:
        data = request.get_json() or {}
        product = data.get('product', 'equities')
        timeframe = data.get('timeframe', '5D')
        force = data.get('force', False)

        from src.common_repository.scheduler.trainer_job import TrainerAgentJob
        trainer_job = TrainerAgentJob()

        result = trainer_job.run_manual_evaluation(product, timeframe, force=force)

        return jsonify({
            'status': 'success',
            'result': result,
            'timestamp': get_ist_now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error running trainer agent: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': get_ist_now().isoformat()
        }), 500

@agents_bp.route('/trainer/history', methods=['GET'])
def get_trainer_history():
    """Get trainer agent execution history"""
    try:
        limit = int(request.args.get('limit', 10))

        from src.agents.impl.trainer_agent_service import TrainerAgentService
        trainer_service = TrainerAgentService()

        history = trainer_service.get_retrain_history(limit=limit)

        return jsonify({
            'status': 'success',
            'history': history,
            'timestamp': get_ist_now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting trainer history: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': get_ist_now().isoformat()
        }), 500

@agents_bp.route('/trainer/status', methods=['GET'])
def get_trainer_status():
    """Get trainer agent status"""
    try:
        product = request.args.get('product')

        from src.agents.impl.trainer_agent_service import TrainerAgentService
        trainer_service = TrainerAgentService()

        status = trainer_service.get_trainer_status(product=product)

        return jsonify({
            'status': 'success',
            'trainer_status': status,
            'timestamp': get_ist_now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting trainer status: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': get_ist_now().isoformat()
        }), 500

@agents_bp.route('/metrics', methods=['GET'])
def get_metrics():
    """Get orchestrator and agent metrics"""
    try:
        orchestrator_metrics = agent_orchestrator.get_metrics()
        queue_status = agent_orchestrator.get_queue_status()

        return jsonify({
            'success': True,
            'data': {
                'orchestrator': orchestrator_metrics,
                'queue': queue_status,
                'framework_status': 'active' if feature_flags.is_enabled('enable_agents_framework') else 'disabled'
            }
        })

    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500