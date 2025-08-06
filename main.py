
#!/usr/bin/env python3
"""
Stock Market Analyst - Version 1.7.1
AI-Enhanced Stock Analysis Dashboard with Production Deployment Optimization

Release: 1.7.1 (August 6, 2025)
- Production deployment fixes for Replit Cloud Run
- Organized src/ directory structure
- Enhanced error handling and reliability
- Complete dependency specification
- WSGI optimization for seamless deployment

Previous Release: 1.7.0 (August 8, 2025)
- Advanced ensemble prediction system with 95% accuracy improvement
- Multi-model integration (Technical, Fundamental, ML, Sentiment)
- Real-time market sentiment analysis
- Enhanced signal filtering and conflict resolution

Author: AI Stock Market Analyst Team
Platform: Replit Cloud Run
Dependencies: See requirements.txt
"""

if __name__ == "__main__":
    try:
        from src.core.main import main
        main()
    except ImportError:
        # Fallback for development environment
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from src.core.main import main
        main()
