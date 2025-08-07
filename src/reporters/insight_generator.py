
#!/usr/bin/env python3
"""
Autonomous Insight Reporter

This module generates weekly .md or .html reports covering:
1. What changed in signals/models/thresholds?
2. Which strategies were evolved and why?
3. What's improving, what's degrading?
4. Suggested manual actions (e.g., "Watch NTPC for volatility breakout")
5. Log under: logs/goahead/reports/YYYY-WW-summary.md
"""

import os
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
import calendar

logger = logging.getLogger(__name__)

class InsightGenerator:
    def __init__(self):
        self.reports_path = "logs/goahead/reports"
        self.data_sources = {
            'meta_config': "data/orchestration/meta_config.json",
            'personal_signals': "data/personal_signals",
            'evolution_data': "data/strategies/evolution_data.json",
            'predictions_history': "data/tracking/predictions_history.json",
            'optimization_logs': "logs/goahead/orchestration"
        }
        
        # Ensure reports directory exists
        os.makedirs(self.reports_path, exist_ok=True)
        
        # Report configuration
        self.report_config = {
            'include_charts': True,
            'include_recommendations': True,
            'include_code_snippets': False,
            'detail_level': 'comprehensive',  # basic, standard, comprehensive
            'output_formats': ['md', 'html'],
            'retention_weeks': 12  # Keep reports for 12 weeks
        }

    def generate_weekly_report(self, week_offset: int = 0) -> Dict[str, Any]:
        """Generate comprehensive weekly insight report"""
        try:
            # Calculate target week
            target_date = datetime.now() - timedelta(weeks=week_offset)
            year, week_num, _ = target_date.isocalendar()
            
            report_data = {
                'report_metadata': {
                    'report_id': f"weekly_{year}W{week_num:02d}",
                    'generation_time': datetime.now().isoformat(),
                    'target_week': f"{year}-W{week_num:02d}",
                    'target_date_range': self._get_week_date_range(target_date),
                    'report_version': '1.0'
                },
                'executive_summary': {},
                'system_changes': {},
                'strategy_evolution': {},
                'performance_analysis': {},
                'recommendations': {},
                'manual_actions': {},
                'appendices': {}
            }
            
            # Generate each section
            report_data['executive_summary'] = self._generate_executive_summary(target_date)
            report_data['system_changes'] = self._analyze_system_changes(target_date)
            report_data['strategy_evolution'] = self._analyze_strategy_evolution(target_date)
            report_data['performance_analysis'] = self._analyze_performance_trends(target_date)
            report_data['recommendations'] = self._generate_recommendations(target_date)
            report_data['manual_actions'] = self._generate_manual_actions(target_date)
            report_data['appendices'] = self._generate_appendices(target_date)
            
            # Save reports in different formats
            report_files = self._save_reports(report_data)
            
            return {
                'status': 'success',
                'report_data': report_data,
                'report_files': report_files
            }
            
        except Exception as e:
            logger.error(f"Error generating weekly report: {str(e)}")
            return {'status': 'error', 'error': str(e)}

    def _generate_executive_summary(self, target_date: datetime) -> Dict[str, Any]:
        """Generate executive summary for the week"""
        try:
            # Load recent data
            meta_config = self._load_json(self.data_sources['meta_config'])
            predictions = self._load_recent_predictions(target_date)
            
            summary = {
                'key_metrics': {},
                'major_changes': [],
                'performance_highlights': [],
                'areas_of_concern': [],
                'week_overview': ''
            }
            
            # Calculate key metrics
            if predictions:
                total_predictions = len(predictions)
                successful_predictions = len([p for p in predictions if p.get('success', False)])
                avg_accuracy = np.mean([self._calculate_accuracy(p) for p in predictions])
                
                summary['key_metrics'] = {
                    'total_predictions': total_predictions,
                    'success_rate': successful_predictions / total_predictions if total_predictions > 0 else 0,
                    'average_accuracy': avg_accuracy,
                    'active_stocks': len(set(p.get('symbol', '') for p in predictions)),
                    'model_usage': self._analyze_model_usage(predictions)
                }
            
            # Identify major changes
            auto_adjustments = meta_config.get('auto_adjustments_history', [])
            recent_adjustments = [
                adj for adj in auto_adjustments 
                if self._is_in_week(adj.get('timestamp', ''), target_date)
            ]
            
            for adjustment in recent_adjustments:
                summary['major_changes'].append({
                    'type': 'automatic_adjustment',
                    'description': f"Adjusted {adjustment.get('parameter', 'unknown')} from {adjustment.get('old_value', 'N/A')} to {adjustment.get('new_value', 'N/A')}",
                    'reason': adjustment.get('reason', 'No reason provided'),
                    'impact': adjustment.get('expected_impact', 'Unknown impact')
                })
            
            # Performance highlights
            if summary['key_metrics'].get('success_rate', 0) > 0.75:
                summary['performance_highlights'].append("Strong prediction success rate above 75%")
            
            if summary['key_metrics'].get('average_accuracy', 0) > 0.80:
                summary['performance_highlights'].append("High prediction accuracy maintained")
            
            # Areas of concern
            if summary['key_metrics'].get('success_rate', 0) < 0.60:
                summary['areas_of_concern'].append("Prediction success rate below acceptable threshold")
            
            if len(recent_adjustments) > 3:
                summary['areas_of_concern'].append("High frequency of automatic adjustments may indicate instability")
            
            # Week overview
            year, week_num, _ = target_date.isocalendar()
            summary['week_overview'] = f"Week {week_num} of {year} showed {'stable' if len(summary['areas_of_concern']) == 0 else 'mixed'} performance with {summary['key_metrics'].get('total_predictions', 0)} predictions across {summary['key_metrics'].get('active_stocks', 0)} stocks."
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating executive summary: {str(e)}")
            return {'error': str(e)}

    def _analyze_system_changes(self, target_date: datetime) -> Dict[str, Any]:
        """Analyze system changes during the week"""
        try:
            meta_config = self._load_json(self.data_sources['meta_config'])
            
            changes = {
                'threshold_changes': [],
                'model_updates': [],
                'configuration_changes': [],
                'optimization_jobs': [],
                'summary': {}
            }
            
            # Analyze threshold changes
            auto_adjustments = meta_config.get('auto_adjustments_history', [])
            week_adjustments = [
                adj for adj in auto_adjustments 
                if self._is_in_week(adj.get('timestamp', ''), target_date)
            ]
            
            for adjustment in week_adjustments:
                changes['threshold_changes'].append({
                    'parameter': adjustment.get('parameter', 'unknown'),
                    'old_value': adjustment.get('old_value', 'N/A'),
                    'new_value': adjustment.get('new_value', 'N/A'),
                    'reason': adjustment.get('reason', 'No reason provided'),
                    'timestamp': adjustment.get('timestamp', ''),
                    'adjustment_type': adjustment.get('adjustment_type', 'unknown')
                })
            
            # Analyze optimization jobs (from orchestration logs)
            optimization_jobs = self._load_optimization_jobs(target_date)
            changes['optimization_jobs'] = optimization_jobs
            
            # Generate summary
            changes['summary'] = {
                'total_threshold_changes': len(changes['threshold_changes']),
                'total_model_updates': len(changes['model_updates']),
                'total_optimization_jobs': len(changes['optimization_jobs']),
                'change_frequency': 'high' if len(week_adjustments) > 2 else 'normal' if len(week_adjustments) > 0 else 'low'
            }
            
            return changes
            
        except Exception as e:
            logger.error(f"Error analyzing system changes: {str(e)}")
            return {'error': str(e)}

    def _analyze_strategy_evolution(self, target_date: datetime) -> Dict[str, Any]:
        """Analyze strategy evolution during the week"""
        try:
            evolution_data = self._load_json(self.data_sources['evolution_data'])
            
            evolution = {
                'evolved_strategies': [],
                'performance_improvements': [],
                'recommended_changes': [],
                'evolution_summary': {}
            }
            
            # Analyze evolution history
            evolution_history = evolution_data.get('evolution_history', [])
            week_evolutions = [
                ev for ev in evolution_history 
                if self._is_in_week(ev.get('timestamp', ''), target_date)
            ]
            
            for evolution_event in week_evolutions:
                evolution['evolved_strategies'].append({
                    'strategy_type': evolution_event.get('strategy_type', 'unknown'),
                    'changes_made': evolution_event.get('changes_made', []),
                    'reason': evolution_event.get('reason', 'No reason provided'),
                    'expected_improvement': evolution_event.get('expected_improvement', 0),
                    'confidence': evolution_event.get('confidence', 0),
                    'timestamp': evolution_event.get('timestamp', '')
                })
            
            # Analyze performance segments
            performance_segments = evolution_data.get('performance_segments', {})
            if 'combined_segments' in performance_segments:
                for segment_key, segment_data in performance_segments['combined_segments'].items():
                    if isinstance(segment_data, dict) and segment_data.get('sample_count', 0) > 10:
                        if segment_data.get('avg_accuracy', 0) > 0.80:
                            evolution['performance_improvements'].append({
                                'segment': segment_key,
                                'accuracy': segment_data.get('avg_accuracy', 0),
                                'sample_count': segment_data.get('sample_count', 0),
                                'improvement_type': 'high_accuracy'
                            })
            
            # Generate summary
            evolution['evolution_summary'] = {
                'total_strategy_changes': len(evolution['evolved_strategies']),
                'performance_improvements_count': len(evolution['performance_improvements']),
                'evolution_activity': 'high' if len(week_evolutions) > 1 else 'moderate' if len(week_evolutions) == 1 else 'low'
            }
            
            return evolution
            
        except Exception as e:
            logger.error(f"Error analyzing strategy evolution: {str(e)}")
            return {'error': str(e)}

    def _analyze_performance_trends(self, target_date: datetime) -> Dict[str, Any]:
        """Analyze performance trends during the week"""
        try:
            predictions = self._load_recent_predictions(target_date)
            
            trends = {
                'improving_stocks': [],
                'degrading_stocks': [],
                'stable_stocks': [],
                'model_performance': {},
                'timeframe_performance': {},
                'trend_summary': {}
            }
            
            if not predictions:
                return trends
            
            # Group predictions by stock
            stock_predictions = defaultdict(list)
            for pred in predictions:
                stock_predictions[pred.get('symbol', 'unknown')].append(pred)
            
            # Analyze each stock's trend
            for stock, stock_preds in stock_predictions.items():
                if len(stock_preds) >= 3:  # Need minimum predictions for trend analysis
                    accuracies = [self._calculate_accuracy(p) for p in stock_preds]
                    trend_slope = np.polyfit(range(len(accuracies)), accuracies, 1)[0] if len(accuracies) > 1 else 0
                    avg_accuracy = np.mean(accuracies)
                    
                    stock_trend = {
                        'stock': stock,
                        'average_accuracy': avg_accuracy,
                        'trend_slope': trend_slope,
                        'prediction_count': len(stock_preds),
                        'latest_accuracy': accuracies[-1] if accuracies else 0
                    }
                    
                    if trend_slope > 0.02:  # Improving
                        trends['improving_stocks'].append(stock_trend)
                    elif trend_slope < -0.02:  # Degrading
                        trends['degrading_stocks'].append(stock_trend)
                    else:  # Stable
                        trends['stable_stocks'].append(stock_trend)
            
            # Analyze model performance
            model_predictions = defaultdict(list)
            for pred in predictions:
                model_predictions[pred.get('model', 'unknown')].append(pred)
            
            for model, model_preds in model_predictions.items():
                accuracies = [self._calculate_accuracy(p) for p in model_preds]
                trends['model_performance'][model] = {
                    'average_accuracy': np.mean(accuracies),
                    'prediction_count': len(model_preds),
                    'success_rate': len([p for p in model_preds if p.get('success', False)]) / len(model_preds)
                }
            
            # Generate summary
            trends['trend_summary'] = {
                'improving_stocks_count': len(trends['improving_stocks']),
                'degrading_stocks_count': len(trends['degrading_stocks']),
                'stable_stocks_count': len(trends['stable_stocks']),
                'overall_trend': self._determine_overall_trend(trends)
            }
            
            return trends
            
        except Exception as e:
            logger.error(f"Error analyzing performance trends: {str(e)}")
            return {'error': str(e)}

    def _generate_recommendations(self, target_date: datetime) -> Dict[str, Any]:
        """Generate actionable recommendations"""
        try:
            # Load optimization logs to find recent recommendations
            optimization_files = self._get_optimization_log_files(target_date)
            
            recommendations = {
                'high_priority': [],
                'medium_priority': [],
                'low_priority': [],
                'strategic_recommendations': [],
                'recommendation_summary': {}
            }
            
            # Process optimization logs
            for log_file in optimization_files:
                log_data = self._load_json(log_file)
                if 'recommendations' in log_data:
                    for rec in log_data['recommendations']:
                        priority = rec.get('priority', 'medium')
                        if priority == 'high':
                            recommendations['high_priority'].append(rec)
                        elif priority == 'medium':
                            recommendations['medium_priority'].append(rec)
                        else:
                            recommendations['low_priority'].append(rec)
            
            # Generate strategic recommendations based on trends
            performance_analysis = self._analyze_performance_trends(target_date)
            
            if performance_analysis['trend_summary']['degrading_stocks_count'] > 2:
                recommendations['strategic_recommendations'].append({
                    'type': 'performance_investigation',
                    'title': 'Investigate Multiple Stock Degradation',
                    'description': f"{performance_analysis['trend_summary']['degrading_stocks_count']} stocks showing performance degradation",
                    'suggested_action': 'Review market regime detection and data quality for affected stocks',
                    'expected_impact': 'Prevent further performance decline'
                })
            
            if len(performance_analysis['model_performance']) > 0:
                best_model = max(performance_analysis['model_performance'].items(), 
                               key=lambda x: x[1]['average_accuracy'])[0]
                recommendations['strategic_recommendations'].append({
                    'type': 'model_optimization',
                    'title': f'Consider Expanding {best_model} Usage',
                    'description': f'{best_model} showing best performance this week',
                    'suggested_action': f'Evaluate expanding {best_model} usage to more stocks',
                    'expected_impact': 'Improved overall prediction accuracy'
                })
            
            # Generate summary
            total_recommendations = (len(recommendations['high_priority']) + 
                                   len(recommendations['medium_priority']) + 
                                   len(recommendations['low_priority']) + 
                                   len(recommendations['strategic_recommendations']))
            
            recommendations['recommendation_summary'] = {
                'total_recommendations': total_recommendations,
                'high_priority_count': len(recommendations['high_priority']),
                'action_required': len(recommendations['high_priority']) > 0
            }
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return {'error': str(e)}

    def _generate_manual_actions(self, target_date: datetime) -> Dict[str, Any]:
        """Generate specific manual actions needed"""
        try:
            actions = {
                'immediate_actions': [],
                'weekly_actions': [],
                'monitoring_actions': [],
                'investigation_actions': [],
                'action_summary': {}
            }
            
            # Analyze recent performance for specific actions
            performance_analysis = self._analyze_performance_trends(target_date)
            
            # Immediate actions for degrading stocks
            for stock_data in performance_analysis['degrading_stocks']:
                if stock_data['average_accuracy'] < 0.60:
                    actions['immediate_actions'].append({
                        'action_type': 'stock_investigation',
                        'title': f"Investigate {stock_data['stock']} Performance",
                        'description': f"Accuracy dropped to {stock_data['average_accuracy']:.2%}",
                        'specific_action': f"Review {stock_data['stock']} data quality and market conditions",
                        'urgency': 'high',
                        'estimated_time': '30 minutes'
                    })
            
            # Monitoring actions for volatile stocks
            for stock_data in performance_analysis['improving_stocks']:
                if stock_data['trend_slope'] > 0.05:  # Rapidly improving
                    actions['monitoring_actions'].append({
                        'action_type': 'volatility_monitoring',
                        'title': f"Monitor {stock_data['stock']} Volatility",
                        'description': f"Stock showing rapid improvement - watch for volatility breakout",
                        'specific_action': f"Set up enhanced monitoring for {stock_data['stock']} volatility patterns",
                        'frequency': 'daily',
                        'duration': '1 week'
                    })
            
            # Weekly maintenance actions
            actions['weekly_actions'].append({
                'action_type': 'system_maintenance',
                'title': 'Review Auto-Adjustment History',
                'description': 'Check if automatic adjustments are working as expected',
                'specific_action': 'Review meta_config.json auto_adjustments_history for patterns',
                'frequency': 'weekly',
                'estimated_time': '15 minutes'
            })
            
            # Investigation actions based on system changes
            system_changes = self._analyze_system_changes(target_date)
            if system_changes['summary']['change_frequency'] == 'high':
                actions['investigation_actions'].append({
                    'action_type': 'system_stability',
                    'title': 'Investigate High Change Frequency',
                    'description': f"System made {system_changes['summary']['total_threshold_changes']} threshold changes this week",
                    'specific_action': 'Review optimization triggers and thresholds for stability',
                    'priority': 'medium',
                    'estimated_time': '45 minutes'
                })
            
            # Generate summary
            total_actions = (len(actions['immediate_actions']) + 
                           len(actions['weekly_actions']) + 
                           len(actions['monitoring_actions']) + 
                           len(actions['investigation_actions']))
            
            actions['action_summary'] = {
                'total_actions': total_actions,
                'immediate_actions_count': len(actions['immediate_actions']),
                'urgent_attention_needed': len(actions['immediate_actions']) > 0
            }
            
            return actions
            
        except Exception as e:
            logger.error(f"Error generating manual actions: {str(e)}")
            return {'error': str(e)}

    def _generate_appendices(self, target_date: datetime) -> Dict[str, Any]:
        """Generate appendices with detailed data"""
        try:
            appendices = {
                'data_quality_report': {},
                'model_statistics': {},
                'configuration_snapshot': {},
                'raw_metrics': {}
            }
            
            # Data quality report
            predictions = self._load_recent_predictions(target_date)
            if predictions:
                appendices['data_quality_report'] = {
                    'total_predictions': len(predictions),
                    'data_completeness': len([p for p in predictions if p.get('predicted_price') and p.get('actual_price')]) / len(predictions),
                    'confidence_distribution': self._calculate_confidence_distribution(predictions),
                    'prediction_frequency_by_day': self._calculate_daily_frequency(predictions, target_date)
                }
            
            # Model statistics
            meta_config = self._load_json(self.data_sources['meta_config'])
            appendices['model_statistics'] = {
                'current_versions': meta_config.get('current_model_versions', {}),
                'performance_baselines': meta_config.get('performance_baselines', {}),
                'optimization_settings': meta_config.get('optimization_settings', {})
            }
            
            # Configuration snapshot
            appendices['configuration_snapshot'] = {
                'current_thresholds': meta_config.get('current_strategy_thresholds', {}),
                'active_experiments': meta_config.get('active_experiments', []),
                'last_updated': meta_config.get('last_updated', '')
            }
            
            return appendices
            
        except Exception as e:
            logger.error(f"Error generating appendices: {str(e)}")
            return {'error': str(e)}

    def _save_reports(self, report_data: Dict) -> Dict[str, str]:
        """Save reports in different formats"""
        try:
            report_id = report_data['report_metadata']['report_id']
            report_files = {}
            
            # Save Markdown report
            if 'md' in self.report_config['output_formats']:
                md_content = self._generate_markdown_report(report_data)
                md_file = os.path.join(self.reports_path, f"{report_id}-summary.md")
                with open(md_file, 'w', encoding='utf-8') as f:
                    f.write(md_content)
                report_files['markdown'] = md_file
            
            # Save HTML report
            if 'html' in self.report_config['output_formats']:
                html_content = self._generate_html_report(report_data)
                html_file = os.path.join(self.reports_path, f"{report_id}-summary.html")
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                report_files['html'] = html_file
            
            # Save raw JSON data
            json_file = os.path.join(self.reports_path, f"{report_id}-data.json")
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            report_files['json'] = json_file
            
            return report_files
            
        except Exception as e:
            logger.error(f"Error saving reports: {str(e)}")
            return {}

    def _generate_markdown_report(self, report_data: Dict) -> str:
        """Generate Markdown format report"""
        try:
            metadata = report_data['report_metadata']
            executive_summary = report_data.get('executive_summary', {})
            system_changes = report_data.get('system_changes', {})
            performance_analysis = report_data.get('performance_analysis', {})
            recommendations = report_data.get('recommendations', {})
            manual_actions = report_data.get('manual_actions', {})
            
            md_content = f"""# GoAhead AI Weekly Insight Report
## {metadata['target_week']}

**Generated:** {metadata['generation_time']}  
**Report ID:** {metadata['report_id']}  
**Coverage:** {metadata['target_date_range']['start']} to {metadata['target_date_range']['end']}

---

## 📊 Executive Summary

{executive_summary.get('week_overview', 'No overview available')}

### Key Metrics
- **Total Predictions:** {executive_summary.get('key_metrics', {}).get('total_predictions', 'N/A')}
- **Success Rate:** {executive_summary.get('key_metrics', {}).get('success_rate', 0):.2%}
- **Average Accuracy:** {executive_summary.get('key_metrics', {}).get('average_accuracy', 0):.2%}
- **Active Stocks:** {executive_summary.get('key_metrics', {}).get('active_stocks', 'N/A')}

### Performance Highlights
"""
            
            for highlight in executive_summary.get('performance_highlights', []):
                md_content += f"- ✅ {highlight}\n"
            
            if executive_summary.get('areas_of_concern'):
                md_content += "\n### Areas of Concern\n"
                for concern in executive_summary.get('areas_of_concern', []):
                    md_content += f"- ⚠️ {concern}\n"
            
            md_content += f"""

---

## 🔧 System Changes

### Threshold Adjustments ({system_changes.get('summary', {}).get('total_threshold_changes', 0)} changes)
"""
            
            for change in system_changes.get('threshold_changes', [])[:5]:  # Show top 5
                md_content += f"""
**{change['parameter']}**
- Changed from `{change['old_value']}` to `{change['new_value']}`
- Reason: {change['reason']}
- Time: {change['timestamp']}
"""
            
            md_content += f"""

### Optimization Jobs ({system_changes.get('summary', {}).get('total_optimization_jobs', 0)} jobs)
"""
            
            for job in system_changes.get('optimization_jobs', [])[:3]:  # Show top 3
                md_content += f"- {job.get('job_type', 'Unknown')}: {job.get('reason', 'No reason')}\n"
            
            md_content += f"""

---

## 📈 Performance Analysis

### Improving Stocks ({performance_analysis.get('trend_summary', {}).get('improving_stocks_count', 0)})
"""
            
            for stock in performance_analysis.get('improving_stocks', [])[:5]:  # Top 5
                md_content += f"- **{stock['stock']}**: {stock['average_accuracy']:.2%} accuracy (↗️ {stock['trend_slope']:+.3f})\n"
            
            if performance_analysis.get('degrading_stocks'):
                md_content += f"""
### Degrading Stocks ({performance_analysis.get('trend_summary', {}).get('degrading_stocks_count', 0)})
"""
                for stock in performance_analysis.get('degrading_stocks', [])[:5]:  # Top 5
                    md_content += f"- **{stock['stock']}**: {stock['average_accuracy']:.2%} accuracy (↘️ {stock['trend_slope']:+.3f})\n"
            
            md_content += """

---

## 🎯 Recommendations

### High Priority Actions
"""
            
            for rec in recommendations.get('high_priority', []):
                md_content += f"""
**{rec.get('title', 'No title')}**
- {rec.get('description', 'No description')}
- Action: {rec.get('suggested_action', 'No action specified')}
"""
            
            md_content += """

### Strategic Recommendations
"""
            
            for rec in recommendations.get('strategic_recommendations', []):
                md_content += f"""
**{rec.get('title', 'No title')}**
- {rec.get('description', 'No description')}
- Action: {rec.get('suggested_action', 'No action specified')}
- Expected Impact: {rec.get('expected_impact', 'Unknown')}
"""
            
            md_content += """

---

## 📋 Manual Actions Required

### Immediate Actions
"""
            
            for action in manual_actions.get('immediate_actions', []):
                md_content += f"""
**{action.get('title', 'No title')}** (🔥 {action.get('urgency', 'medium')} urgency)
- {action.get('description', 'No description')}
- Action: {action.get('specific_action', 'No action specified')}
- Time: {action.get('estimated_time', 'Unknown')}
"""
            
            if manual_actions.get('monitoring_actions'):
                md_content += """

### Monitoring Actions
"""
                for action in manual_actions.get('monitoring_actions', []):
                    md_content += f"""
**{action.get('title', 'No title')}**
- {action.get('description', 'No description')}
- Action: {action.get('specific_action', 'No action specified')}
- Frequency: {action.get('frequency', 'Unknown')}
"""
            
            md_content += f"""

---

## 📅 Next Week Focus

Based on this week's analysis, focus areas for next week:

1. **Monitor** {len(performance_analysis.get('degrading_stocks', []))} degrading stocks
2. **Investigate** {len(manual_actions.get('immediate_actions', []))} immediate actions
3. **Review** {system_changes.get('summary', {}).get('total_threshold_changes', 0)} system changes
4. **Implement** {len(recommendations.get('high_priority', []))} high-priority recommendations

---

*Report generated by GoAhead AI Autonomous Insight Reporter v1.0*  
*For questions or detailed analysis, review the JSON data file: `{metadata['report_id']}-data.json`*
"""
            
            return md_content
            
        except Exception as e:
            logger.error(f"Error generating markdown report: {str(e)}")
            return f"# Report Generation Error\n\nError: {str(e)}"

    def _generate_html_report(self, report_data: Dict) -> str:
        """Generate HTML format report"""
        try:
            metadata = report_data['report_metadata']
            executive_summary = report_data.get('executive_summary', {})
            
            html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GoAhead AI Weekly Report - {metadata['target_week']}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.6; margin: 40px; background: #f8fafc; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 12px 12px 0 0; }}
        .content {{ padding: 30px; }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .metric-card {{ background: #f1f5f9; padding: 20px; border-radius: 8px; text-align: center; }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #1e293b; }}
        .metric-label {{ color: #64748b; font-size: 0.9em; }}
        .section {{ margin: 30px 0; }}
        .section h2 {{ color: #1e293b; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; }}
        .highlight {{ background: #10b981; color: white; padding: 2px 8px; border-radius: 4px; }}
        .concern {{ background: #ef4444; color: white; padding: 2px 8px; border-radius: 4px; }}
        .recommendation {{ background: #f8fafc; border-left: 4px solid #3b82f6; padding: 15px; margin: 10px 0; border-radius: 4px; }}
        .urgent {{ border-left-color: #ef4444; background: #fef2f2; }}
        .footer {{ background: #f1f5f9; padding: 20px; border-radius: 0 0 12px 12px; text-align: center; color: #64748b; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>GoAhead AI Weekly Insight Report</h1>
            <h2>{metadata['target_week']}</h2>
            <p>Generated: {metadata['generation_time']}</p>
        </div>
        
        <div class="content">
            <div class="section">
                <h2>📊 Executive Summary</h2>
                <p>{executive_summary.get('week_overview', 'No overview available')}</p>
                
                <div class="metric-grid">
                    <div class="metric-card">
                        <div class="metric-value">{executive_summary.get('key_metrics', {}).get('total_predictions', 'N/A')}</div>
                        <div class="metric-label">Total Predictions</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{executive_summary.get('key_metrics', {}).get('success_rate', 0):.1%}</div>
                        <div class="metric-label">Success Rate</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{executive_summary.get('key_metrics', {}).get('average_accuracy', 0):.1%}</div>
                        <div class="metric-label">Average Accuracy</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{executive_summary.get('key_metrics', {}).get('active_stocks', 'N/A')}</div>
                        <div class="metric-label">Active Stocks</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>🎯 Key Highlights</h2>
"""
            
            for highlight in executive_summary.get('performance_highlights', []):
                html_content += f'<p><span class="highlight">✅ HIGHLIGHT</span> {highlight}</p>\n'
            
            for concern in executive_summary.get('areas_of_concern', []):
                html_content += f'<p><span class="concern">⚠️ CONCERN</span> {concern}</p>\n'
            
            html_content += """
            </div>
        </div>
        
        <div class="footer">
            <p>Report generated by GoAhead AI Autonomous Insight Reporter v1.0</p>
            <p>For detailed analysis, review the corresponding JSON data file</p>
        </div>
    </div>
</body>
</html>"""
            
            return html_content
            
        except Exception as e:
            logger.error(f"Error generating HTML report: {str(e)}")
            return f"<html><body><h1>Report Generation Error</h1><p>Error: {str(e)}</p></body></html>"

    # Helper methods
    def _get_week_date_range(self, target_date: datetime) -> Dict[str, str]:
        """Get start and end dates for the target week"""
        try:
            start_of_week = target_date - timedelta(days=target_date.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            
            return {
                'start': start_of_week.strftime('%Y-%m-%d'),
                'end': end_of_week.strftime('%Y-%m-%d')
            }
        except Exception:
            return {'start': 'Unknown', 'end': 'Unknown'}

    def _is_in_week(self, timestamp_str: str, target_date: datetime) -> bool:
        """Check if timestamp is in the target week"""
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            week_range = self._get_week_date_range(target_date)
            start_date = datetime.fromisoformat(week_range['start'])
            end_date = datetime.fromisoformat(week_range['end']) + timedelta(days=1)
            
            return start_date <= timestamp < end_date
        except Exception:
            return False

    def _load_recent_predictions(self, target_date: datetime, days: int = 7) -> List[Dict]:
        """Load predictions from target week"""
        try:
            predictions_path = self.data_sources['predictions_history']
            if os.path.exists(predictions_path):
                with open(predictions_path, 'r') as f:
                    data = json.load(f)
                    all_predictions = data.get('predictions', [])
                    
                    # Filter to target week
                    week_predictions = []
                    for pred in all_predictions:
                        if self._is_in_week(pred.get('timestamp', ''), target_date):
                            week_predictions.append(pred)
                    
                    return week_predictions
            return []
        except Exception as e:
            logger.error(f"Error loading recent predictions: {str(e)}")
            return []

    def _calculate_accuracy(self, prediction: Dict) -> float:
        """Calculate accuracy for a prediction"""
        try:
            predicted = prediction.get('predicted_price', 0)
            actual = prediction.get('actual_price', predicted)
            
            if actual == 0:
                return 0.0
            
            accuracy = 1.0 - abs(predicted - actual) / actual
            return max(0.0, min(1.0, accuracy))
        except Exception:
            return 0.0

    def _analyze_model_usage(self, predictions: List[Dict]) -> Dict[str, int]:
        """Analyze model usage distribution"""
        try:
            model_usage = defaultdict(int)
            for pred in predictions:
                model = pred.get('model', 'unknown')
                model_usage[model] += 1
            return dict(model_usage)
        except Exception:
            return {}

    def _load_optimization_jobs(self, target_date: datetime) -> List[Dict]:
        """Load optimization jobs from target week"""
        try:
            optimization_logs_path = self.data_sources['optimization_logs']
            jobs = []
            
            if os.path.exists(optimization_logs_path):
                for filename in os.listdir(optimization_logs_path):
                    if filename.startswith('optimization_cycle_'):
                        file_path = os.path.join(optimization_logs_path, filename)
                        log_data = self._load_json(file_path)
                        
                        if self._is_in_week(log_data.get('start_time', ''), target_date):
                            jobs.extend(log_data.get('optimization_jobs_created', []))
            
            return jobs
        except Exception as e:
            logger.error(f"Error loading optimization jobs: {str(e)}")
            return []

    def _get_optimization_log_files(self, target_date: datetime) -> List[str]:
        """Get optimization log files for target week"""
        try:
            optimization_logs_path = self.data_sources['optimization_logs']
            log_files = []
            
            if os.path.exists(optimization_logs_path):
                for filename in os.listdir(optimization_logs_path):
                    file_path = os.path.join(optimization_logs_path, filename)
                    if os.path.isfile(file_path) and filename.endswith('.json'):
                        log_files.append(file_path)
            
            return log_files
        except Exception:
            return []

    def _determine_overall_trend(self, trends: Dict) -> str:
        """Determine overall performance trend"""
        try:
            improving = len(trends.get('improving_stocks', []))
            degrading = len(trends.get('degrading_stocks', []))
            
            if improving > degrading * 1.5:
                return 'improving'
            elif degrading > improving * 1.5:
                return 'degrading'
            else:
                return 'stable'
        except Exception:
            return 'unknown'

    def _calculate_confidence_distribution(self, predictions: List[Dict]) -> Dict[str, int]:
        """Calculate confidence level distribution"""
        try:
            distribution = {'high': 0, 'medium': 0, 'low': 0}
            
            for pred in predictions:
                confidence = pred.get('confidence', 0) / 100.0
                if confidence >= 0.80:
                    distribution['high'] += 1
                elif confidence >= 0.60:
                    distribution['medium'] += 1
                else:
                    distribution['low'] += 1
            
            return distribution
        except Exception:
            return {'high': 0, 'medium': 0, 'low': 0}

    def _calculate_daily_frequency(self, predictions: List[Dict], target_date: datetime) -> Dict[str, int]:
        """Calculate prediction frequency by day"""
        try:
            daily_freq = defaultdict(int)
            
            for pred in predictions:
                timestamp = pred.get('timestamp', '')
                try:
                    pred_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    day_name = pred_date.strftime('%A')
                    daily_freq[day_name] += 1
                except Exception:
                    continue
            
            return dict(daily_freq)
        except Exception:
            return {}

    def _load_json(self, file_path: str) -> Dict:
        """Load JSON data from file"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading JSON from {file_path}: {str(e)}")
            return {}

    def get_available_reports(self) -> List[Dict[str, Any]]:
        """Get list of available reports"""
        try:
            reports = []
            
            if os.path.exists(self.reports_path):
                for filename in os.listdir(self.reports_path):
                    if filename.endswith('-summary.md') or filename.endswith('-summary.html'):
                        file_path = os.path.join(self.reports_path, filename)
                        file_stat = os.stat(file_path)
                        
                        reports.append({
                            'filename': filename,
                            'file_path': file_path,
                            'size': file_stat.st_size,
                            'created': datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                            'format': 'html' if filename.endswith('.html') else 'markdown'
                        })
            
            return sorted(reports, key=lambda x: x['created'], reverse=True)
        except Exception as e:
            logger.error(f"Error getting available reports: {str(e)}")
            return []

def main():
    """Test Insight Generator functionality"""
    generator = InsightGenerator()
    
    print("=== Testing Insight Generator ===")
    
    # Generate current week report
    result = generator.generate_weekly_report()
    
    if result['status'] == 'success':
        print("✅ Weekly report generated successfully")
        print(f"Report ID: {result['report_data']['report_metadata']['report_id']}")
        print(f"Files created: {list(result['report_files'].keys())}")
        
        # Display executive summary
        exec_summary = result['report_data']['executive_summary']
        print(f"Key metrics: {exec_summary.get('key_metrics', {})}")
        print(f"Performance highlights: {len(exec_summary.get('performance_highlights', []))}")
        print(f"Areas of concern: {len(exec_summary.get('areas_of_concern', []))}")
        
    else:
        print(f"❌ Error generating report: {result.get('error')}")
    
    # Test available reports
    available_reports = generator.get_available_reports()
    print(f"✅ Found {len(available_reports)} existing reports")
    
    print("\n✅ Insight Generator testing completed!")

if __name__ == "__main__":
    main()
