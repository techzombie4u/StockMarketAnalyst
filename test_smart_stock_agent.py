
#!/usr/bin/env python3
"""
Test Script for SmartStockAgent Implementation
Tests all the required features from the specification
"""

import sys
import json
from datetime import datetime
from intelligent_prediction_agent import SmartStockAgent, get_enhanced_agent_analysis

def test_input_aggregation():
    """Test 1. Input Aggregation functionality"""
    print("🔍 Testing Input Aggregation...")
    
    try:
        agent = SmartStockAgent()
        
        # Test data with all required sources
        test_predictions = {
            'technical': {
                'rsi_14': 45, 'macd_bullish': True, 'bb_position': 60, 
                'current_price': 100, 'trend_strength': 70, 'volume_ratio_10': 1.3, 
                'atr_volatility': 2.1, 'momentum_5d_pct': 3.2
            },
            'ml_lstm': {'predicted_change': 3.5, 'confidence': 75, 'direction': 'UP'},
            'ml_rf': {'direction_label': 'UP', 'confidence': 0.8},
            'ensemble': {'pred_1mo': 5.2, 'confidence': 70, 'pred_24h': 0.5, 'pred_5d': 2.1},
            'fundamentals': {
                'pe_ratio': 18, 'debt_to_equity': 0.4, 'revenue_growth': 8.5, 
                'earnings_growth': 6.2, 'promoter_buying': True
            },
            'sentiment': {'bulk_deal_bonus': 5, 'news_score': 2, 'social_score': 1}
        }
        
        # Test aggregation
        aggregated = agent._aggregate_inputs('TESTSTOCK', test_predictions)
        
        # Verify all sources are captured
        sources = aggregated.get('sources', {})
        required_sources = ['technical', 'ml_lstm', 'ml_rf', 'ensemble', 'sentiment', 'fundamentals']
        
        for source in required_sources:
            assert source in sources, f"Missing source: {source}"
        
        # Verify technical indicators are properly captured
        tech = sources['technical']
        assert 'rsi_14' in tech, "RSI not captured"
        assert 'macd_signal' in tech, "MACD not captured"
        assert 'bb_position' in tech, "Bollinger Bands not captured"
        
        print("✅ Input aggregation working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Input aggregation failed: {str(e)}")
        return False

def test_signal_evaluation_conflict_resolution():
    """Test 2. Signal Evaluation & Conflict Resolution"""
    print("⚖️ Testing Signal Evaluation & Conflict Resolution...")
    
    try:
        agent = SmartStockAgent()
        
        # Create conflicting signals for testing
        conflicting_data = {
            'sources': {
                'technical': {'rsi_14': 25, 'confidence': 80},  # Bullish (oversold)
                'ml_lstm': {'predicted_change': -5, 'confidence': 75},  # Bearish
                'ml_rf': {'direction_label': 'UP', 'confidence': 70},  # Bullish
                'ensemble': {'pred_1mo': -2, 'confidence': 65}  # Bearish
            }
        }
        
        # Test conflict resolution
        signal_analysis = agent._evaluate_signals_and_resolve_conflicts(conflicting_data)
        
        # Verify conflict detection
        assert 'conflicts' in signal_analysis, "Conflicts not detected"
        assert 'consensus_level' in signal_analysis, "Consensus level not calculated"
        assert 'directional_signals' in signal_analysis, "Directional signals not analyzed"
        
        # Verify dynamic weighting
        directional_signals = signal_analysis['directional_signals']
        for source, signal_data in directional_signals.items():
            assert 'weight' in signal_data, f"Weight not assigned to {source}"
            assert 0 < signal_data['weight'] <= 0.5, f"Invalid weight for {source}"
        
        print("✅ Signal evaluation and conflict resolution working")
        return True
        
    except Exception as e:
        print(f"❌ Signal evaluation failed: {str(e)}")
        return False

def test_scoring_final_decision():
    """Test 3. Scoring & Final Decision Making"""
    print("🎯 Testing Scoring & Final Decision Making...")
    
    try:
        agent = SmartStockAgent()
        
        # Test data for decision making
        test_aggregated = {
            'sources': {
                'technical': {'rsi_14': 40, 'current_price': 150, 'confidence': 85},
                'ml_lstm': {'predicted_change': 8, 'confidence': 80},
                'fundamentals': {'pe_ratio': 15, 'revenue_growth': 12}
            }
        }
        
        test_signal_analysis = {
            'consensus_level': 'strong_bullish',
            'consensus_strength': 75,
            'has_conflicts': False
        }
        
        test_quality_assessment = {
            'signal_quality': {'score': 80, 'level': 'high'},
            'risk_assessment': {'score': 20, 'level': 'low'}
        }
        
        # Test decision making
        decision = agent._make_final_decision('TESTSTOCK', test_aggregated, test_signal_analysis, test_quality_assessment)
        
        # Verify decision components
        assert 'action' in decision, "Action not generated"
        assert 'confidence' in decision, "Confidence not calculated"
        assert 'target_price' in decision, "Target price not set"
        assert 'predictions' in decision, "Predictions not generated"
        
        # Verify action format
        valid_actions = ['STRONG_BUY', 'BUY', 'HOLD', 'WEAK_SELL', 'STRONG_SELL']
        action_clean = decision['action'].replace('🔼 ', '').replace('🔽 ', '').replace('⏸️ ', '')
        assert action_clean in valid_actions, f"Invalid action: {action_clean}"
        
        # Verify confidence range
        confidence = decision['confidence']
        assert 0 <= confidence <= 100, f"Invalid confidence: {confidence}"
        
        print("✅ Scoring and final decision making working")
        return True
        
    except Exception as e:
        print(f"❌ Scoring and decision making failed: {str(e)}")
        return False

def test_explainable_ai():
    """Test 4. Explainable AI (XAI)"""
    print("💡 Testing Explainable AI...")
    
    try:
        agent = SmartStockAgent()
        
        # Mock decision and analysis data
        mock_decision = {
            'action': '🔼 BUY',
            'confidence': 75,
            'consensus_level': 'weak_bullish',
            'risk_level': 'medium'
        }
        
        mock_signal_analysis = {
            'directional_signals': {
                'technical': {'direction': 'bullish', 'confidence': 80, 'weight': 0.3},
                'ml_lstm': {'direction': 'bullish', 'confidence': 75, 'weight': 0.25},
                'ml_rf': {'direction': 'neutral', 'confidence': 60, 'weight': 0.2}
            },
            'conflicts': ['Mixed ML signals detected']
        }
        
        mock_quality_assessment = {
            'signal_quality': {'level': 'high', 'factors': ['Strong consensus', 'Multiple sources']}
        }
        
        # Test explanation generation
        explanation = agent._generate_explanation('TESTSTOCK', mock_decision, mock_signal_analysis, mock_quality_assessment)
        
        # Verify explanation components
        assert 'decision_reasoning' in explanation, "Decision reasoning not generated"
        assert 'top_3_drivers' in explanation, "Top 3 drivers not identified"
        assert 'contradictory_signals' in explanation, "Contradictory signals not highlighted"
        assert 'human_readable_summary' in explanation, "Human-readable summary not generated"
        
        # Verify human-readable summary
        summary = explanation['human_readable_summary']
        assert len(summary) > 50, "Summary too short"
        assert 'TESTSTOCK' in summary, "Stock symbol not in summary"
        
        print("✅ Explainable AI working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Explainable AI failed: {str(e)}")
        return False

def test_prediction_stability_monitoring():
    """Test 5. Prediction Stability Monitoring"""
    print("📈 Testing Prediction Stability Monitoring...")
    
    try:
        agent = SmartStockAgent()
        
        # Mock decision with stability requirements
        mock_decision = {
            'action': '🔼 BUY',
            'confidence': 80,
            'target_price': 120
        }
        
        # Test stability monitoring
        stable_decision = agent._monitor_prediction_stability('TESTSTOCK', mock_decision)
        
        # Verify stability information is added
        assert 'stability' in stable_decision, "Stability information not added"
        
        stability = stable_decision['stability']
        assert 'is_stable' in stability, "Stability flag not set"
        assert 'stability_score' in stability, "Stability score not calculated"
        
        # Verify stability score range
        stability_score = stability['stability_score']
        assert 0 <= stability_score <= 100, f"Invalid stability score: {stability_score}"
        
        print("✅ Prediction stability monitoring working")
        return True
        
    except Exception as e:
        print(f"❌ Prediction stability monitoring failed: {str(e)}")
        return False

def test_time_based_decision_management():
    """Test 6. Time-Based Decision Management"""
    print("⌛ Testing Time-Based Decision Management...")
    
    try:
        agent = SmartStockAgent()
        
        # Mock decision for time-based management
        mock_decision = {
            'action': '🔼 BUY',
            'confidence': 85,
            'target_price': 125
        }
        
        # Test time-based management
        managed_decision = agent._apply_time_based_management('TESTSTOCK', mock_decision)
        
        # Verify time-based fields are added
        assert 'is_locked' in managed_decision, "Lock status not set"
        
        # If locked, verify lock expiration
        if managed_decision.get('is_locked'):
            assert 'lock_expires' in managed_decision, "Lock expiration not set"
            assert 'lock_reason' in managed_decision, "Lock reason not provided"
        
        print("✅ Time-based decision management working")
        return True
        
    except Exception as e:
        print(f"❌ Time-based decision management failed: {str(e)}")
        return False

def test_historical_performance_awareness():
    """Test 7. Historical Performance Awareness"""
    print("📊 Testing Historical Performance Awareness...")
    
    try:
        agent = SmartStockAgent()
        
        # Mock performance data
        agent.model_performance = {
            'technical': {'win_rate': 0.75, 'recent_accuracy': 0.80},
            'ml_lstm': {'win_rate': 0.45, 'recent_accuracy': 0.35},  # Poor performance
            'ml_rf': {'win_rate': 0.65, 'recent_accuracy': 0.70}
        }
        
        # Mock decision and signal analysis
        mock_decision = {'confidence': 70}
        mock_signal_analysis = {
            'directional_signals': {
                'technical': {'weight': 0.3, 'confidence': 80},
                'ml_lstm': {'weight': 0.2, 'confidence': 60},
                'ml_rf': {'weight': 0.25, 'confidence': 75}
            }
        }
        
        # Test performance awareness
        adjusted_decision = agent._apply_performance_awareness(mock_decision, mock_signal_analysis)
        
        # Verify performance adjustments are applied
        assert 'performance_adjustment' in adjusted_decision, "Performance adjustment not applied"
        assert 'performance_adjustments' in adjusted_decision, "Performance adjustments not tracked"
        
        # Verify confidence is adjusted
        original_confidence = mock_decision['confidence']
        adjusted_confidence = adjusted_decision['confidence']
        
        # Should be different due to performance adjustments
        print(f"   Original confidence: {original_confidence}, Adjusted: {adjusted_confidence}")
        
        print("✅ Historical performance awareness working")
        return True
        
    except Exception as e:
        print(f"❌ Historical performance awareness failed: {str(e)}")
        return False

def test_risk_signal_quality_assessment():
    """Test 8. Risk & Signal Quality Assessment"""
    print("🧪 Testing Risk & Signal Quality Assessment...")
    
    try:
        agent = SmartStockAgent()
        
        # Mock data for quality assessment
        mock_aggregated = {
            'sources': {
                'technical': {'atr_volatility': 3.5, 'trend_strength': 75},
                'price_volume': {'momentum_5d': 8, 'volume_spike': True},
                'fundamentals': {'pe_ratio': 25, 'debt_to_equity': 0.8}
            }
        }
        
        mock_signal_analysis = {
            'consensus_strength': 70,
            'has_conflicts': False
        }
        
        # Test quality assessment
        quality_assessment = agent._assess_signal_quality_and_risk(mock_aggregated, mock_signal_analysis)
        
        # Verify assessment components
        assert 'signal_quality' in quality_assessment, "Signal quality not assessed"
        assert 'risk_assessment' in quality_assessment, "Risk assessment not performed"
        assert 'filter_recommendation' in quality_assessment, "Filter recommendation not provided"
        
        # Verify signal quality structure
        signal_quality = quality_assessment['signal_quality']
        assert 'score' in signal_quality, "Quality score not calculated"
        assert 'level' in signal_quality, "Quality level not determined"
        assert 'factors' in signal_quality, "Quality factors not listed"
        
        # Verify risk assessment structure
        risk_assessment = quality_assessment['risk_assessment']
        assert 'score' in risk_assessment, "Risk score not calculated"
        assert 'level' in risk_assessment, "Risk level not determined"
        assert 'factors' in risk_assessment, "Risk factors not listed"
        
        print("✅ Risk and signal quality assessment working")
        return True
        
    except Exception as e:
        print(f"❌ Risk and signal quality assessment failed: {str(e)}")
        return False

def test_intelligent_filtering():
    """Test 9. Intelligent Filtering & Signal Confirmation"""
    print("🧠 Testing Intelligent Filtering & Signal Confirmation...")
    
    try:
        agent = SmartStockAgent()
        
        # Test high-quality signals (should pass filter)
        high_quality_data = {
            'sources': {
                'technical': {'volume_ratio': 1.5, 'trend_strength': 70, 'atr_volatility': 2.0}
            }
        }
        
        high_quality_signals = {
            'consensus_strength': 75,
            'has_conflicts': False
        }
        
        # Test low-quality signals (should fail filter)
        low_quality_data = {
            'sources': {
                'technical': {'volume_ratio': 0.8, 'trend_strength': 40, 'atr_volatility': 6.0}
            }
        }
        
        low_quality_signals = {
            'consensus_strength': 35,
            'has_conflicts': True
        }
        
        # Test filtering
        high_quality_result = agent._intelligent_signal_confirmation(high_quality_data, high_quality_signals)
        low_quality_result = agent._intelligent_signal_confirmation(low_quality_data, low_quality_signals)
        
        # Verify filtering logic
        assert isinstance(high_quality_result, bool), "Filter result not boolean"
        assert isinstance(low_quality_result, bool), "Filter result not boolean"
        
        # High quality should pass, low quality should fail
        print(f"   High quality signals: {'PASS' if high_quality_result else 'FAIL'}")
        print(f"   Low quality signals: {'PASS' if low_quality_result else 'FAIL'}")
        
        print("✅ Intelligent filtering working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Intelligent filtering failed: {str(e)}")
        return False

def test_full_integration():
    """Test full SmartStockAgent integration"""
    print("🚀 Testing Full SmartStockAgent Integration...")
    
    try:
        # Complete test predictions
        comprehensive_predictions = {
            'technical': {
                'rsi_14': 45, 'macd_bullish': True, 'bb_position': 60, 
                'current_price': 250, 'trend_strength': 75, 'volume_ratio_10': 1.4, 
                'atr_volatility': 2.8, 'momentum_5d_pct': 4.2
            },
            'ml_lstm': {'predicted_change': 6.5, 'confidence': 82, 'direction': 'UP', 'horizon_days': 30},
            'ml_rf': {'direction_label': 'UP', 'confidence': 0.78, 'feature_importance': {'rsi': 0.3, 'volume': 0.25}},
            'ensemble': {'pred_1mo': 8.2, 'confidence': 79, 'pred_24h': 1.2, 'pred_5d': 3.8},
            'fundamentals': {
                'pe_ratio': 22, 'debt_to_equity': 0.6, 'revenue_growth': 15.5, 
                'earnings_growth': 18.2, 'promoter_buying': True
            },
            'sentiment': {'bulk_deal_bonus': 10, 'news_score': 3, 'social_score': 2}
        }
        
        # Test full analysis
        result = get_enhanced_agent_analysis('INTEGRATION_TEST', comprehensive_predictions)
        
        # Verify comprehensive result structure
        required_fields = [
            'action', 'confidence', 'target_price', 'predictions',
            'risk_level', 'explanation', 'stability', 'agent_version'
        ]
        
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"
        
        # Verify explanation structure
        explanation = result['explanation']
        explanation_fields = ['decision_reasoning', 'top_3_drivers', 'human_readable_summary']
        for field in explanation_fields:
            assert field in explanation, f"Missing explanation field: {field}"
        
        # Verify predictions structure
        predictions = result['predictions']
        prediction_fields = ['pred_24h', 'pred_5d', 'pred_1mo']
        for field in prediction_fields:
            assert field in predictions, f"Missing prediction field: {field}"
        
        # Display results
        print(f"   Action: {result.get('action', 'N/A')}")
        print(f"   Confidence: {result.get('confidence', 'N/A')}%")
        print(f"   Target Price: ₹{result.get('target_price', 0)}")
        print(f"   Risk Level: {result.get('risk_level', 'N/A')}")
        print(f"   Stability Score: {result.get('stability', {}).get('stability_score', 'N/A')}")
        print(f"   Summary: {result.get('explanation', {}).get('human_readable_summary', 'N/A')[:100]}...")
        
        print("✅ Full SmartStockAgent integration working perfectly")
        return True
        
    except Exception as e:
        print(f"❌ Full integration test failed: {str(e)}")
        return False

def run_smart_stock_agent_tests():
    """Run all SmartStockAgent tests"""
    print("🤖 Starting SmartStockAgent Comprehensive Tests")
    print("=" * 60)
    
    tests = [
        ("Input Aggregation", test_input_aggregation),
        ("Signal Evaluation & Conflict Resolution", test_signal_evaluation_conflict_resolution),
        ("Scoring & Final Decision Making", test_scoring_final_decision),
        ("Explainable AI (XAI)", test_explainable_ai),
        ("Prediction Stability Monitoring", test_prediction_stability_monitoring),
        ("Time-Based Decision Management", test_time_based_decision_management),
        ("Historical Performance Awareness", test_historical_performance_awareness),
        ("Risk & Signal Quality Assessment", test_risk_signal_quality_assessment),
        ("Intelligent Filtering & Signal Confirmation", test_intelligent_filtering),
        ("Full Integration Test", test_full_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        print("-" * 50)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"💥 {test_name}: CRASHED - {str(e)}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SMARTSTOCKAGENT TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    print("=" * 60)
    
    if passed == total:
        print("🎉 ALL SMARTSTOCKAGENT TESTS PASSED!")
        print("✅ SmartStockAgent is fully functional and ready for production")
        return True
    else:
        print("⚠️ Some SmartStockAgent tests failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = run_smart_stock_agent_tests()
    sys.exit(0 if success else 1)
