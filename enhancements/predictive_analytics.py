import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class PredictiveAnalytics:
    def __init__(self, db_manager):
        self.db = db_manager
    
    def get_risk_predictions(self):
        """Get risk predictions for vendors"""
        vendors_data = self.db.get_vendors_with_performance()
        
        if vendors_data.empty:
            return {
                'attrition_risk': [],
                'performance_forecast': []
            }
        
        # Simple prediction logic
        attrition_risk = []
        for _, vendor in vendors_data.iterrows():
            risk_score = self._calculate_attrition_risk(vendor)
            attrition_risk.append({
                'vendor_name': vendor['name'],
                'attrition_risk': risk_score,
                'risk_level': 'High' if risk_score > 70 else 'Medium' if risk_score > 40 else 'Low'
            })
        
        # Performance forecast
        performance_forecast = self._generate_performance_forecast()
        
        return {
            'attrition_risk': attrition_risk,
            'performance_forecast': performance_forecast
        }
    
    def _calculate_attrition_risk(self, vendor):
        """Calculate attrition risk for a vendor"""
        base_risk = 100 - vendor.get('performance_score', 0)
        
        # Adjust based on risk level
        risk_level_multiplier = {
            'High': 1.3,
            'Medium': 1.0,
            'Low': 0.7
        }
        
        multiplier = risk_level_multiplier.get(vendor.get('risk_level', 'Medium'), 1.0)
        return min(100, base_risk * multiplier)
    
    def _generate_performance_forecast(self):
        """Generate performance forecast"""
        dates = []
        scores = []
        
        for i in range(6):  # Next 6 months
            date = datetime.now() + timedelta(days=30*i)
            dates.append(date.strftime('%Y-%m-%d'))
            scores.append(np.random.normal(80, 5))
        
        return [{'date': date, 'predicted_score': score} for date, score in zip(dates, scores)]