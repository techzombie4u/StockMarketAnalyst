
"""
Agent Orchestrator - Manages agent execution, scheduling, and event handling
"""

import logging
import threading
import time
from typing import Dict, Any, List, Optional
from queue import Queue, Empty
from datetime import datetime, timedelta

from .core.runner import agent_runner
from .core.registry import agent_registry
from .core.contracts import AgentInput, AgentOutput, AgentError
from .store.agent_outputs_repo import agent_outputs_repo
from ..common_repository.config.feature_flags import feature_flags

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    """Orchestrates agent execution with scheduling and event handling"""
    
    def __init__(self):
        self.execution_queue = Queue()
        self.is_running = False
        self.worker_thread = None
        self.metrics = {
            'total_runs': 0,
            'successful_runs': 0,
            'failed_runs': 0,
            'last_activity': None
        }
        self.last_agent_activity = {}
        
    def start(self):
        """Start the orchestrator worker thread"""
        if not self.is_running:
            self.is_running = True
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
            logger.info("Agent orchestrator started")
    
    def stop(self):
        """Stop the orchestrator"""
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        logger.info("Agent orchestrator stopped")
    
    def _worker_loop(self):
        """Main worker loop for processing agent execution queue"""
        logger.info("Agent orchestrator worker loop started")
        
        while self.is_running:
            try:
                # Process queued executions
                try:
                    job = self.execution_queue.get(timeout=1)
                    self._execute_agent_job(job)
                    self.execution_queue.task_done()
                except Empty:
                    continue
                    
            except Exception as e:
                logger.error(f"Error in orchestrator worker loop: {e}")
                time.sleep(1)
    
    def _execute_agent_job(self, job: Dict[str, Any]):
        """Execute a single agent job"""
        try:
            agent_name = job['agent']
            scope = job.get('scope', 'default')
            agent_input = job['input']
            
            logger.info(f"Executing agent job: {agent_name}/{scope}")
            
            # Run the agent
            start_time = time.time()
            output = agent_runner.run_agent(agent_name, agent_input)
            execution_time = time.time() - start_time
            
            # Save output
            agent_outputs_repo.save_output(agent_name, scope, output.to_dict())
            
            # Update metrics
            self.metrics['total_runs'] += 1
            if output.verdict != 'ERROR':
                self.metrics['successful_runs'] += 1
            else:
                self.metrics['failed_runs'] += 1
                
            self.metrics['last_activity'] = datetime.now().isoformat()
            self.last_agent_activity[agent_name] = datetime.now().isoformat()
            
            logger.info(f"Completed agent job: {agent_name}/{scope} in {execution_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Error executing agent job: {e}")
            self.metrics['failed_runs'] += 1
    
    def enqueue_agent_run(self, agent: str, context: Dict[str, Any], scope: str = 'default') -> str:
        """Enqueue an agent run"""
        try:
            if not feature_flags.is_enabled('enable_agents_framework'):
                raise AgentError("Agents framework is disabled")
                
            if not agent_registry.is_agent_enabled(agent):
                raise AgentError(f"Agent {agent} is not enabled")
            
            # Create agent input
            agent_input = AgentInput(context=context)
            
            # Create job
            job_id = f"{agent}_{scope}_{int(time.time())}"
            job = {
                'id': job_id,
                'agent': agent,
                'scope': scope,
                'input': agent_input,
                'queued_at': datetime.now().isoformat()
            }
            
            # Add to queue
            self.execution_queue.put(job)
            logger.info(f"Enqueued agent job: {job_id}")
            
            return job_id
            
        except Exception as e:
            logger.error(f"Error enqueuing agent run: {e}")
            raise
    
    def on_kpi_change(self, kpi_data: Dict[str, Any]):
        """Handle KPI change events"""
        try:
            logger.info("Processing KPI change event")
            
            # Enqueue trainer agent
            trainer_context = {
                'kpi_changes': kpi_data,
                'event_type': 'kpi_change',
                'timestamp': datetime.now().isoformat()
            }
            
            self.enqueue_agent_run('trainer', trainer_context, 'kpi_change')
            
            # Enqueue relevant product agents based on KPI data
            affected_products = kpi_data.get('affected_products', ['equity'])
            for product in affected_products:
                if product in ['equity', 'options'] and agent_registry.is_agent_enabled(product):
                    product_context = {
                        'kpi_snapshot': kpi_data,
                        'event_type': 'kpi_change',
                        'product': product
                    }
                    self.enqueue_agent_run(product, product_context, f'kpi_change_{product}')
                    
        except Exception as e:
            logger.error(f"Error handling KPI change event: {e}")
    
    def on_prediction_close(self, prediction_data: Dict[str, Any]):
        """Handle prediction close events"""
        try:
            logger.info("Processing prediction close event")
            
            product = prediction_data.get('product', 'equity')
            timeframe = prediction_data.get('timeframe', '5D')
            
            context = {
                'closed_prediction': prediction_data,
                'event_type': 'prediction_close',
                'timestamp': datetime.now().isoformat()
            }
            
            scope = f'prediction_close_{product}_{timeframe}'
            
            if agent_registry.is_agent_enabled(product):
                self.enqueue_agent_run(product, context, scope)
                
        except Exception as e:
            logger.error(f"Error handling prediction close event: {e}")
    
    def schedule_periodic_runs(self):
        """Schedule periodic agent runs (simplified scheduling)"""
        try:
            now = datetime.now()
            
            # Daily trainer run at 18:00 IST (simplified check)
            if now.hour == 18 and now.minute == 0:
                context = {
                    'event_type': 'scheduled_daily',
                    'timestamp': now.isoformat()
                }
                self.enqueue_agent_run('trainer', context, 'daily_scheduled')
            
            # Hourly sentiment during market hours (9-15:30 IST)
            if 9 <= now.hour <= 15 and now.minute == 0:
                context = {
                    'event_type': 'scheduled_hourly',
                    'timestamp': now.isoformat()
                }
                self.enqueue_agent_run('sentiment', context, 'hourly_scheduled')
                
        except Exception as e:
            logger.error(f"Error in periodic scheduling: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get orchestrator metrics"""
        return {
            **self.metrics,
            'queue_size': self.execution_queue.qsize(),
            'is_running': self.is_running,
            'last_agent_activity': self.last_agent_activity
        }
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        return {
            'size': self.execution_queue.qsize(),
            'is_running': self.is_running,
            'worker_active': self.worker_thread.is_alive() if self.worker_thread else False
        }

# Global orchestrator instance
agent_orchestrator = AgentOrchestrator()
