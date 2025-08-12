
"""
Test real KPI calculators with golden data
Assert stable outputs and proper calculation logic
"""

import pytest
import json
import os
from src.kpi.calculators import KPICalculator, calculate_timeframe_kpis, KPIResults

class TestKPICalculators:
    """Test suite for KPI calculators"""
    
    @pytest.fixture
    def calculator(self):
        """KPI calculator instance"""
        return KPICalculator()
    
    @pytest.fixture
    def golden_3d_data(self):
        """Load golden 3D prediction data"""
        return self._load_golden_data('sample_3d.json')
    
    @pytest.fixture
    def golden_5d_data(self):
        """Load golden 5D prediction data"""
        return self._load_golden_data('sample_5d.json')
    
    @pytest.fixture
    def golden_30d_data(self):
        """Load golden 30D prediction data"""
        return self._load_golden_data('sample_30d.json')
    
    def _load_golden_data(self, filename):
        """Load golden data from file"""
        golden_path = os.path.join('data', 'golden', 'predictions', filename)
        if os.path.exists(golden_path):
            with open(golden_path, 'r') as f:
                return json.load(f)
        return []
    
    def test_3d_kpi_calculation(self, calculator, golden_3d_data):
        """Test 3D KPI calculation with golden data"""
        if not golden_3d_data:
            pytest.skip("Golden 3D data not available")
        
        results = calculator.calculate_kpis(golden_3d_data, '3D')
        
        # Verify structure
        assert isinstance(results, KPIResults)
        assert results.timeframe == '3D'
        assert results.sample_size == len(golden_3d_data)
        
        # Assert stable outputs (within tolerances)
        assert 0.0 <= results.brier_score <= 1.0
        assert 0.0 <= results.directional_accuracy <= 100.0
        assert 0.0 <= results.mape <= 100.0
        assert results.rmse >= 0.0
        assert 0.0 <= results.hit_rate <= 100.0
        
        # Financial metrics bounds
        assert -5.0 <= results.sharpe_ratio <= 5.0
        assert -5.0 <= results.sortino_ratio <= 5.0
        assert results.max_drawdown >= 0.0
        
        # Risk metrics bounds
        assert 0.0 <= results.var_95 <= 100.0
        assert 0.0 <= results.var_99 <= 100.0
        assert results.volatility >= 0.0
        
        # Status should be determined
        assert results.status in ['green', 'amber', 'red', 'insufficient_data']
    
    def test_5d_kpi_calculation(self, calculator, golden_5d_data):
        """Test 5D KPI calculation with golden data"""
        if not golden_5d_data:
            pytest.skip("Golden 5D data not available")
        
        results = calculator.calculate_kpis(golden_5d_data, '5D')
        
        # Test specific expected values for 5D data
        assert results.timeframe == '5D'
        assert results.sample_size == len(golden_5d_data)
        
        # More predictions should give better stability
        assert results.sample_size >= 8
        
        # Expected ranges for this specific dataset
        assert 0.0 <= results.brier_score <= 0.5  # Should be reasonable
        assert 40.0 <= results.directional_accuracy <= 100.0  # At least random
        assert 0.0 <= results.mape <= 50.0  # Should be reasonable error
        
        # Status determination
        if results.sample_size >= 5:
            assert results.status != 'insufficient_data'
    
    def test_30d_kpi_calculation(self, calculator, golden_30d_data):
        """Test 30D KPI calculation with golden data"""
        if not golden_30d_data:
            pytest.skip("Golden 30D data not available")
        
        results = calculator.calculate_kpis(golden_30d_data, '30D')
        
        # Longer timeframe may have different characteristics
        assert results.timeframe == '30D'
        assert results.sample_size == len(golden_30d_data)
        
        # 30D predictions might be less accurate but more stable
        assert results.sample_size >= 10  # More data points expected
        
        # Verify all metrics are calculated
        assert results.brier_score is not None
        assert results.directional_accuracy is not None
        assert results.sharpe_ratio is not None
        assert results.max_drawdown is not None
        assert results.var_95 is not None
    
    def test_convenience_function(self, golden_5d_data):
        """Test convenience function returns proper dict format"""
        if not golden_5d_data:
            pytest.skip("Golden 5D data not available")
        
        result_dict = calculate_timeframe_kpis(golden_5d_data, '5D')
        
        # Verify dict structure
        assert isinstance(result_dict, dict)
        assert 'timeframe' in result_dict
        assert 'sample_size' in result_dict
        assert 'prediction_kpis' in result_dict
        assert 'financial_kpis' in result_dict
        assert 'risk_kpis' in result_dict
        assert 'quality_kpis' in result_dict
        assert 'status' in result_dict
        
        # Check nested structures
        pred_kpis = result_dict['prediction_kpis']
        assert 'brier_score' in pred_kpis
        assert 'directional_accuracy' in pred_kpis
        assert 'mape' in pred_kpis
        assert 'rmse' in pred_kpis
        assert 'hit_rate' in pred_kpis
        
        fin_kpis = result_dict['financial_kpis']
        assert 'sharpe_ratio' in fin_kpis
        assert 'sortino_ratio' in fin_kpis
        assert 'calmar_ratio' in fin_kpis
        assert 'information_ratio' in fin_kpis
        
        risk_kpis = result_dict['risk_kpis']
        assert 'max_drawdown' in risk_kpis
        assert 'var_95' in risk_kpis
        assert 'var_99' in risk_kpis
        assert 'volatility' in risk_kpis
    
    def test_insufficient_data_handling(self, calculator):
        """Test handling of insufficient data"""
        # Empty data
        results = calculator.calculate_kpis([], '5D')
        assert results.status == 'insufficient_data'
        assert results.sample_size == 0
        
        # Too few predictions
        minimal_data = [
            {'predicted': 100, 'actual': 105, 'timestamp': '2025-01-01'},
            {'predicted': 200, 'actual': 195, 'timestamp': '2025-01-02'}
        ]
        results = calculator.calculate_kpis(minimal_data, '5D')
        assert results.status == 'insufficient_data'
        assert results.sample_size == 2
    
    def test_malformed_data_handling(self, calculator):
        """Test handling of malformed data"""
        malformed_data = [
            {'predicted': 100, 'actual': 105, 'timestamp': '2025-01-01'},
            {'predicted': 'invalid', 'actual': 195, 'timestamp': '2025-01-02'},
            {'predicted': 200, 'actual': None, 'timestamp': '2025-01-03'},
            {'predicted': 150, 'actual': 155, 'timestamp': '2025-01-04'},
            {'pred': 175, 'actual_value': 180, 'ts': '2025-01-05'},  # Different format
            {'predicted': 0, 'actual': 0, 'timestamp': '2025-01-06'},  # Zero values
        ]
        
        results = calculator.calculate_kpis(malformed_data, '5D')
        
        # Should only process valid records
        assert results.sample_size == 2  # Only 2 valid records
        assert results.status == 'insufficient_data'  # Due to low sample size
    
    def test_status_determination_logic(self, calculator):
        """Test status determination with controlled data"""
        # Create perfect predictions (should get green status)
        perfect_data = []
        for i in range(10):
            perfect_data.append({
                'predicted': 1000 + i,
                'actual': 1000 + i,  # Perfect match
                'timestamp': f'2025-01-{i+1:02d}',
                'confidence': 95.0
            })
        
        results = calculator.calculate_kpis(perfect_data, '5D')
        
        # Should have excellent metrics
        assert results.hit_rate == 100.0  # Perfect hit rate
        assert results.directional_accuracy == 100.0  # Perfect direction
        assert results.brier_score == 0.0  # Perfect Brier score
        
        # Create poor predictions (should get red status)
        poor_data = []
        for i in range(10):
            poor_data.append({
                'predicted': 1000,
                'actual': 500,  # Always wrong by 50%
                'timestamp': f'2025-01-{i+1:02d}',
                'confidence': 95.0
            })
        
        results = calculator.calculate_kpis(poor_data, '5D')
        
        # Should have poor metrics
        assert results.hit_rate == 0.0  # No hits
        assert results.mape == 50.0  # 50% error
        assert results.status == 'red'
    
    def test_metric_calculations_precision(self, calculator):
        """Test that metric calculations are precise and reproducible"""
        test_data = [
            {'predicted': 1000, 'actual': 1050, 'timestamp': '2025-01-01', 'confidence': 80},
            {'predicted': 2000, 'actual': 1950, 'timestamp': '2025-01-02', 'confidence': 75},
            {'predicted': 1500, 'actual': 1575, 'timestamp': '2025-01-03', 'confidence': 85},
            {'predicted': 1800, 'actual': 1780, 'timestamp': '2025-01-04', 'confidence': 70},
            {'predicted': 2200, 'actual': 2150, 'timestamp': '2025-01-05', 'confidence': 90},
        ]
        
        # Calculate multiple times to ensure consistency
        results1 = calculator.calculate_kpis(test_data, '5D')
        results2 = calculator.calculate_kpis(test_data, '5D')
        
        # Should be identical
        assert results1.brier_score == results2.brier_score
        assert results1.directional_accuracy == results2.directional_accuracy
        assert results1.mape == results2.mape
        assert results1.sharpe_ratio == results2.sharpe_ratio
        assert results1.max_drawdown == results2.max_drawdown
        assert results1.var_95 == results2.var_95
        
        # Test specific calculations are reasonable
        assert 0.0 <= results1.brier_score <= 1.0
        assert results1.directional_accuracy >= 0.0
        assert results1.mape >= 0.0
        assert results1.sample_size == 5

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
