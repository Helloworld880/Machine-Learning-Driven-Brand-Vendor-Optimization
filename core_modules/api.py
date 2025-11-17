from flask import Flask, jsonify, request
import json
from datetime import datetime

class APIManager:
    def __init__(self):
        self.endpoints = {}
    
    def setup_api_routes(self, app):
        """Setup API routes for the Flask app"""
        
        @app.route('/api/vendors', methods=['GET'])
        def get_vendors():
            """Get all vendors"""
            sample_vendors = [
                {
                    "id": 1,
                    "name": "Tech Solutions Inc.",
                    "category": "Strategic",
                    "status": "Active",
                    "performance_score": 85.5
                },
                {
                    "id": 2, 
                    "name": "Global Logistics Ltd",
                    "category": "Tactical",
                    "status": "Active",
                    "performance_score": 78.2
                }
            ]
            return jsonify(sample_vendors)
        
        @app.route('/api/vendors/<int:vendor_id>', methods=['GET'])
        def get_vendor(vendor_id):
            """Get specific vendor details"""
            vendor = {
                "id": vendor_id,
                "name": f"Vendor {vendor_id}",
                "details": "Sample vendor details",
                "performance_history": [
                    {"date": "2024-01-01", "score": 85},
                    {"date": "2024-01-15", "score": 82}
                ]
            }
            return jsonify(vendor)
        
        return app