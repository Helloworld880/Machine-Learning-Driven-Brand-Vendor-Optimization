import pandas as pd
import streamlit as st

class ComplianceManager:
    def __init__(self, db_manager):
        self.db = db_manager
    
    def get_compliance_status(self):
        """Get compliance status for all vendors"""
        vendors_data = self.db.get_vendors_with_performance()
        
        if vendors_data.empty:
            return pd.DataFrame()
        
        # Simple compliance check based on performance and risk
        compliance_data = []
        for _, vendor in vendors_data.iterrows():
            status = self._check_compliance(vendor)
            compliance_data.append({
                'vendor_name': vendor['name'],
                'performance_score': vendor.get('performance_score', 0),
                'risk_level': vendor.get('risk_level', 'Medium'),
                'compliance_status': status,
                'last_audit': '2024-01-15'
            })
        
        return pd.DataFrame(compliance_data)
    
    def _check_compliance(self, vendor):
        """Check if vendor is compliant"""
        performance = vendor.get('performance_score', 0)
        risk_level = vendor.get('risk_level', 'Medium')
        
        if performance >= 80 and risk_level != 'High':
            return 'Compliant'
        elif performance >= 60:
            return 'Needs Review'
        else:
            return 'Non-Compliant'