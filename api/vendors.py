from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from core_modules.database import DatabaseManager
from core_modules.auth import Authentication
import logging

vendors_bp = Blueprint('vendors', __name__)
db_manager = DatabaseManager()
auth_manager = Authentication()

@vendors_bp.route('/api/vendors', methods=['GET'])
@jwt_required()
def get_vendors():
    """Get vendors with filtering and pagination"""
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        category = request.args.get('category')
        status = request.args.get('status')
        risk_level = request.args.get('risk_level')
        search = request.args.get('search')
        
        # Build filters
        filters = {}
        if category:
            filters['category'] = category.split(',')
        if status:
            filters['status'] = status
        if risk_level:
            filters['risk_level'] = risk_level
        
        # Get vendors
        vendors = db_manager.get_vendors(filters)
        
        # Apply search filter
        if search:
            vendors = [v for v in vendors if search.lower() in v['vendor_name'].lower()]
        
        # Pagination
        total_vendors = len(vendors)
        total_pages = (total_vendors + per_page - 1) // per_page
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_vendors = vendors[start_idx:end_idx]
        
        return jsonify({
            'success': True,
            'data': paginated_vendors,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_vendors,
                'total_pages': total_pages
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Error fetching vendors: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch vendors'
        }), 500

@vendors_bp.route('/api/vendors/<int:vendor_id>', methods=['GET'])
@jwt_required()
def get_vendor(vendor_id):
    """Get detailed vendor information"""
    try:
        vendors = db_manager.get_vendors()
        vendor = next((v for v in vendors if v['vendor_id'] == vendor_id), None)
        
        if not vendor:
            return jsonify({
                'success': False,
                'message': 'Vendor not found'
            }), 404
        
        # Get performance history
        performance_history = db_manager.get_vendor_performance(vendor_id, 365)
        
        # Get financial data
        financial_data = db_manager.execute_query('''
            SELECT * FROM financial_metrics 
            WHERE vendor_id = ? 
            ORDER BY period DESC 
            LIMIT 12
        ''', (vendor_id,))
        
        # Get risk assessments
        risk_assessments = db_manager.execute_query('''
            SELECT * FROM risk_assessments 
            WHERE vendor_id = ? 
            ORDER BY assessment_date DESC 
            LIMIT 5
        ''', (vendor_id,))
        
        return jsonify({
            'success': True,
            'data': {
                'vendor': vendor,
                'performance_history': performance_history,
                'financial_data': [dict(row) for row in financial_data],
                'risk_assessments': [dict(row) for row in risk_assessments]
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Error fetching vendor details: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch vendor details'
        }), 500

@vendors_bp.route('/api/vendors/<int:vendor_id>', methods=['PUT'])
@jwt_required()
def update_vendor(vendor_id):
    """Update vendor information"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        # Update vendor
        success = db_manager.update_vendor(vendor_id, data)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Vendor updated successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to update vendor'
            }), 400
            
    except Exception as e:
        logging.error(f"Error updating vendor: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to update vendor'
        }), 500

@vendors_bp.route('/api/vendors', methods=['POST'])
@jwt_required()
def create_vendor():
    """Create new vendor"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['vendor_name', 'category', 'contact_email', 'contract_value']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Insert new vendor
        conn = db_manager.execute_query('''
            INSERT INTO vendors (
                vendor_name, category, contact_email, contact_phone, address,
                contract_value, contract_start_date, contract_end_date, status, risk_level
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['vendor_name'],
            data['category'],
            data['contact_email'],
            data.get('contact_phone', ''),
            data.get('address', ''),
            data['contract_value'],
            data.get('contract_start_date', '2024-01-01'),
            data.get('contract_end_date', '2024-12-31'),
            data.get('status', 'Active'),
            data.get('risk_level', 'Medium')
        ))
        
        return jsonify({
            'success': True,
            'message': 'Vendor created successfully',
            'vendor_id': conn.lastrowid
        }), 201
        
    except Exception as e:
        logging.error(f"Error creating vendor: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to create vendor'
        }), 500

@vendors_bp.route('/api/vendors/<int:vendor_id>/performance', methods=['GET'])
@jwt_required()
def get_vendor_performance(vendor_id):
    """Get vendor performance metrics"""
    try:
        period = request.args.get('period', '365')
        
        performance_data = db_manager.get_vendor_performance(vendor_id, int(period))
        
        return jsonify({
            'success': True,
            'data': performance_data
        }), 200
        
    except Exception as e:
        logging.error(f"Error fetching vendor performance: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch vendor performance'
        }), 500

@vendors_bp.route('/api/vendors/<int:vendor_id>/performance', methods=['POST'])
@jwt_required()
def add_performance_metric(vendor_id):
    """Add performance metric for vendor"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['metric_date', 'quality_score', 'delivery_score', 'cost_score', 
                          'innovation_score', 'compliance_score']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Calculate overall score
        overall_score = (
            data['quality_score'] + data['delivery_score'] + data['cost_score'] +
            data['innovation_score'] + data['compliance_score']
        ) / 5
        
        # Insert performance metric
        db_manager.execute_query('''
            INSERT INTO performance_metrics (
                vendor_id, metric_date, quality_score, delivery_score, cost_score,
                innovation_score, compliance_score, overall_score, feedback
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            vendor_id,
            data['metric_date'],
            data['quality_score'],
            data['delivery_score'],
            data['cost_score'],
            data['innovation_score'],
            data['compliance_score'],
            overall_score,
            data.get('feedback', '')
        ))
        
        return jsonify({
            'success': True,
            'message': 'Performance metric added successfully'
        }), 201
        
    except Exception as e:
        logging.error(f"Error adding performance metric: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to add performance metric'
        }), 500

@vendors_bp.route('/api/vendors/export', methods=['GET'])
@jwt_required()
def export_vendors():
    """Export vendors data"""
    try:
        format_type = request.args.get('format', 'csv')
        vendors = db_manager.get_vendors()
        
        if format_type == 'csv':
            # Generate CSV
            import csv
            from io import StringIO
            
            output = StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'Vendor ID', 'Vendor Name', 'Category', 'Contact Email', 'Contact Phone',
                'Contract Value', 'Contract Start', 'Contract End', 'Status', 'Risk Level',
                'Performance Score', 'Risk Score'
            ])
            
            # Write data
            for vendor in vendors:
                writer.writerow([
                    vendor['vendor_id'],
                    vendor['vendor_name'],
                    vendor['category'],
                    vendor['contact_email'],
                    vendor['contact_phone'],
                    vendor['contract_value'],
                    vendor['contract_start_date'],
                    vendor['contract_end_date'],
                    vendor['status'],
                    vendor['risk_level'],
                    vendor.get('current_score', 0),
                    vendor.get('current_risk', 0)
                ])
            
            return output.getvalue(), 200, {
                'Content-Type': 'text/csv',
                'Content-Disposition': f'attachment; filename=vendors_export.csv'
            }
            
        else:
            return jsonify({
                'success': False,
                'message': 'Unsupported export format'
            }), 400
            
    except Exception as e:
        logging.error(f"Error exporting vendors: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to export vendors'
        }), 500