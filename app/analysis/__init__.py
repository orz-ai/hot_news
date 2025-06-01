"""
热点分析模块，包含热点聚合分析和热点趋势预测功能
"""

from app.analysis.trend_analyzer import TrendAnalyzer
from app.analysis.predictor import TrendPredictor

__all__ = ['TrendAnalyzer', 'TrendPredictor'] 