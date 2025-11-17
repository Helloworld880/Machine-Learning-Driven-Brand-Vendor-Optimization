#!/usr/bin/env python3
"""
Vendor Dashboard API Server
"""

from api import app
import os

if __name__ == '__main__':
    print("🚀 Starting Vendor Dashboard API Server...")
    print("🌐 API URL: http://localhost:5000")
    print("📚 API Documentation:")
    print("   GET  /api/v1/health")
    print("   GET  /api/v1/vendors")
    print("   GET  /api/v1/vendors/<vendor_id>")
    print("   GET  /api/v1/performance/metrics")
    print("   GET  /api/v1/alerts")
    print("   POST /api/v1/vendors")
    print("   POST /api/v1/performance")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)