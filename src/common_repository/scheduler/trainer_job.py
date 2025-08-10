
"""
Trainer Agent Scheduler Job
Runs daily evaluations and triggers retraining as needed
"""

import logging
from datetime import datetime
from typing import Dict, List

from src.agents.impl.trainer_agent_service import TrainerAgentService
from src.common_repository.utils.date_utils import get_ist_now
from src.common_repository.storage.json_store import json_store

logger = logging.getLogger(__name__)

class TrainerAgentJob:
    def __init__(self):
        self.trainer_service = TrainerAgentService()
        self.products = ['equities', 'options', 'comm']
        self.timeframes = ['5D', '30D']
    
    def run_daily_evaluation(self) -> Dict[str, any]:
        """Run daily trainer evaluation for all products and timeframes"""
        try:
            logger.info("Starting daily trainer evaluation")
            
            results = {
                'timestamp': get_ist_now().isoformat(),
                'evaluations': [],
                'retrainings': [],
                'errors': []
            }
            
            for product in self.products:
                for timeframe in self.timeframes:
                    try:
                        # Evaluate retrain need
                        decision = self.trainer_service.evaluate_retrain_need(product, timeframe)
                        
                        evaluation = {
                            'product': product,
                            'timeframe': timeframe,
                            'triggered': decision.triggered,
                            'reason': decision.reason,
                            'timestamp': decision.timestamp
                        }
                        results['evaluations'].append(evaluation)
                        
                        # Execute retraining if triggered
                        if decision.triggered:
                            logger.info(f"Triggering retrain for {product} {timeframe}: {decision.reason}")
                            
                            retrain_result = self.trainer_service.execute_retrain(decision)
                            
                            retrain_entry = {
                                'product': product,
                                'timeframe': timeframe,
                                'decision': decision.__dict__,
                                'result': retrain_result,
                                'timestamp': get_ist_now().isoformat()
                            }
                            results['retrainings'].append(retrain_entry)
                        
                    except Exception as e:
                        error_msg = f"Error evaluating {product} {timeframe}: {str(e)}"
                        logger.error(error_msg)
                        results['errors'].append(error_msg)
            
            # Save results
            self._save_job_results(results)
            
            logger.info(f"Daily evaluation completed: {len(results['retrainings'])} retrainings triggered")
            return results
            
        except Exception as e:
            logger.error(f"Error in daily trainer evaluation: {e}")
            return {
                'timestamp': get_ist_now().isoformat(),
                'error': str(e),
                'evaluations': [],
                'retrainings': [],
                'errors': [str(e)]
            }
    
    def run_manual_evaluation(self, product: str, timeframe: str, force: bool = False) -> Dict[str, any]:
        """Run manual trainer evaluation for specific product/timeframe"""
        try:
            logger.info(f"Running manual evaluation for {product} {timeframe} (force={force})")
            
            # Evaluate retrain need
            decision = self.trainer_service.evaluate_retrain_need(product, timeframe, force=force)
            
            result = {
                'timestamp': get_ist_now().isoformat(),
                'product': product,
                'timeframe': timeframe,
                'decision': decision.__dict__,
                'retrain_executed': False
            }
            
            # Execute retraining if triggered or forced
            if decision.triggered:
                logger.info(f"Executing retrain for {product} {timeframe}: {decision.reason}")
                
                retrain_result = self.trainer_service.execute_retrain(decision)
                result['retrain_result'] = retrain_result
                result['retrain_executed'] = retrain_result.get('success', False)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in manual trainer evaluation: {e}")
            return {
                'timestamp': get_ist_now().isoformat(),
                'product': product,
                'timeframe': timeframe,
                'error': str(e),
                'retrain_executed': False
            }
    
    def _save_job_results(self, results: Dict[str, any]):
        """Save job results to tracking file"""
        try:
            job_history = json_store.load('trainer_job_history', [])
            job_history.append(results)
            
            # Keep only last 30 job runs
            if len(job_history) > 30:
                job_history = job_history[-30:]
            
            json_store.save('trainer_job_history', job_history)
            
        except Exception as e:
            logger.error(f"Error saving job results: {e}")
    
    def get_job_history(self, limit: int = 10) -> List[Dict[str, any]]:
        """Get recent job execution history"""
        try:
            history = json_store.load('trainer_job_history', [])
            return history[-limit:] if history else []
        except Exception as e:
            logger.error(f"Error getting job history: {e}")
            return []
