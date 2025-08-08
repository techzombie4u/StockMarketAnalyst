# Reporters Module for GoAhead++ Enhancement
"""
Reporters package - Contains reporting and analytics modules
"""

class InsightGenerator:
    """Generate insights from training results"""

    def __init__(self):
        pass

    def generate_training_insights(self, results):
        """Generate insights from training results"""
        insights = []

        if results.get('successful_count', 0) > 0:
            insights.append(f"✅ Successfully trained {results['successful_count']} models")

        if results.get('failed_count', 0) > 0:
            insights.append(f"⚠️ {results['failed_count']} stocks failed training")

        return insights

insights = InsightGenerator()