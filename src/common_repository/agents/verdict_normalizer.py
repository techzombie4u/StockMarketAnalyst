
"""
Verdict Normalizer - Harmonize AI verdict labels across agents
"""

from typing import Dict, Optional

class VerdictNormalizer:
    """Normalizes AI verdicts to consistent 5-level scale"""
    
    # Master normalization mapping
    NORMALIZATION_MAP = {
        # Equity Agent verdicts
        'STRONG_BUY': 'STRONG_BUY',
        'BUY': 'BUY',
        'HOLD': 'HOLD', 
        'SELL': 'CAUTIOUS',
        'STRONG_SELL': 'AVOID',
        
        # Options Agent verdicts
        'EXECUTE': 'STRONG_BUY',
        'FAVORABLE': 'BUY',
        'NEUTRAL': 'HOLD',
        'CAUTION': 'CAUTIOUS',
        'AVOID': 'AVOID',
        
        # Sentiment Agent verdicts
        'VERY_BULLISH': 'STRONG_BUY',
        'BULLISH': 'BUY',
        'NEUTRAL': 'HOLD',
        'BEARISH': 'CAUTIOUS', 
        'VERY_BEARISH': 'AVOID',
        
        # Communication Agent verdicts
        'HIGH_CONFIDENCE': 'STRONG_BUY',
        'CONFIDENT': 'BUY',
        'MODERATE': 'HOLD',
        'LOW_CONFIDENCE': 'CAUTIOUS',
        'NO_CONFIDENCE': 'AVOID',
        
        # Trainer Agent verdicts
        'RETRAIN_SUCCESS': 'BUY',
        'RETRAIN_NEEDED': 'CAUTIOUS',
        'MODEL_STABLE': 'HOLD',
        'MODEL_DRIFT': 'CAUTIOUS',
        
        # Dev Agent verdicts  
        'APPROVED': 'BUY',
        'NEEDS_REVIEW': 'CAUTIOUS',
        'STABLE': 'HOLD',
        
        # New Agent verdicts
        'INNOVATIVE': 'STRONG_BUY',
        'PROMISING': 'BUY',
        'EXPERIMENTAL': 'CAUTIOUS',
        
        # Generic fallbacks
        'POSITIVE': 'BUY',
        'NEGATIVE': 'CAUTIOUS',
        'UNKNOWN': 'HOLD',
        'ERROR': 'HOLD'
    }
    
    # Agent-specific context for better normalization
    AGENT_CONTEXTS = {
        'equity_agent': {
            'UP_TREND': 'BUY',
            'DOWN_TREND': 'CAUTIOUS',
            'SIDEWAYS': 'HOLD'
        },
        'options_agent': {
            'PROFITABLE': 'STRONG_BUY',
            'BREAKEVEN': 'HOLD',
            'LOSS_RISK': 'AVOID'
        },
        'sentiment_agent': {
            'STRONG_POSITIVE': 'STRONG_BUY',
            'WEAK_POSITIVE': 'BUY',
            'MIXED': 'HOLD',
            'WEAK_NEGATIVE': 'CAUTIOUS',
            'STRONG_NEGATIVE': 'AVOID'
        }
    }
    
    @classmethod
    def normalize_verdict(cls, agent_name: str, raw_verdict: str) -> str:
        """Normalize a verdict from any agent to standard 5-level scale"""
        if not raw_verdict:
            return 'HOLD'
        
        # Clean input
        raw_verdict = str(raw_verdict).upper().strip()
        
        # Try agent-specific mapping first
        if agent_name in cls.AGENT_CONTEXTS:
            agent_map = cls.AGENT_CONTEXTS[agent_name]
            if raw_verdict in agent_map:
                return agent_map[raw_verdict]
        
        # Try global mapping
        if raw_verdict in cls.NORMALIZATION_MAP:
            return cls.NORMALIZATION_MAP[raw_verdict]
        
        # Fuzzy matching for common patterns
        if any(word in raw_verdict for word in ['STRONG', 'VERY', 'HIGH']):
            if any(word in raw_verdict for word in ['BUY', 'BULL', 'POS']):
                return 'STRONG_BUY'
            elif any(word in raw_verdict for word in ['SELL', 'BEAR', 'NEG']):
                return 'AVOID'
        
        if any(word in raw_verdict for word in ['BUY', 'BULL', 'POS']):
            return 'BUY'
        elif any(word in raw_verdict for word in ['SELL', 'BEAR', 'NEG']):
            return 'CAUTIOUS'
        elif any(word in raw_verdict for word in ['AVOID', 'DANGER', 'RISK']):
            return 'AVOID'
        
        # Default fallback
        return 'HOLD'
    
    @classmethod
    def get_verdict_color(cls, normalized_verdict: str) -> str:
        """Get UI color class for a normalized verdict"""
        color_map = {
            'STRONG_BUY': 'text-emerald-600',
            'BUY': 'text-green-600', 
            'HOLD': 'text-gray-600',
            'CAUTIOUS': 'text-amber-600',
            'AVOID': 'text-red-600'
        }
        return color_map.get(normalized_verdict, 'text-gray-600')
    
    @classmethod
    def get_verdict_badge_class(cls, normalized_verdict: str) -> str:
        """Get UI badge class for a normalized verdict"""
        badge_map = {
            'STRONG_BUY': 'bg-emerald-100 text-emerald-800',
            'BUY': 'bg-green-100 text-green-800',
            'HOLD': 'bg-gray-100 text-gray-800', 
            'CAUTIOUS': 'bg-amber-100 text-amber-800',
            'AVOID': 'bg-red-100 text-red-800'
        }
        return badge_map.get(normalized_verdict, 'bg-gray-100 text-gray-800')

# Global instance
verdict_normalizer = VerdictNormalizer()
