from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from core.database import DatabaseManager
from core.analytics import AnalyticsEngine
from enhancements.predictive_analytics import PredictiveAnalytics
import logging
import pandas as pd

performance_bp = Blueprint('performance', __name__)
db_manager = DatabaseManager()
analytics_engine = AnalyticsEngine(db_manager)
predictive_analytics = PredictiveAnalytics(db_manager)

@performance_bp.route('/api/performance', methods=['GET'])
@jwt_required()
def get_performance_data():
    """Get performance analytics data"""
    try:
        vendor_id = request.args.get('vendor_id')
        period = request.args.get('period', '30')
        detailed = request.args.get('detailed', 'false').lower() == 'true'
        
        if vendor_id:
            # Single vendor performance
            performance_data = db_manager.get_vendor_performance(int(vendor_id), int(period))
            
            if detailed:
                # Get predictive analytics
                predictions = predictive_analytics.predict_attrition_risk(int(vendor_id))
                forecast = predictive_analytics.forecast_performance(int(vendor_id))
                
                return jsonify({
                    'success': True,
                    'data': {
                        'performance_history': performance_data,
                        'predictions': predictions,
                        'forecast': forecast.to_dict('records') if not forecast.empty else []
                    }
                }), 200
            else:
                return jsonify({
                    'success': True,
                    'data': performance_data
                }), 200
        else:
            # Overall performance analytics
            avg_performance = analytics_engine.calculate_average_performance()
            trends = analytics_engine.get_performance_trends(int(period))
            distribution = analytics_engine.get_performance_distribution()
            segments = analytics_engine.calculate_vendor_segments()
            
            return jsonify({
                'success': True,
                'data': {
                    'average_performance': avg_performance,
                    'trends': trends.to_dict('records'),
                    'distribution': distribution.describe().to_dict(),
                    'segments': segments.to_dict('records')
                }
            }), 200
            
    except Exception as e:
        logging.error(f"Error fetching performance data: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch performance data'
        }), 500

@performance_bp.route('/api/performance/alerts', methods=['GET'])
@jwt_required()
def get_performance_alerts():
    """Get performance-based alerts"""
    try:
        alerts = analytics_engine.get_recent_alerts()
        
        return jsonify({
            'success': True,
            'data': alerts
        }), 200
        
    except Exception as e:
        logging.error(f"Error fetching performance alerts: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch performance alerts'
        }), 500

@performance_bp.route('/api/performance/benchmarks', methods=['GET'])
@jwt_required()
def get_performance_benchmarks():
    """Get performance benchmarks and comparisons"""
    try:
        from enhancements.benchmarking import Benchmarking
        
        benchmarking = Benchmarking(db_manager)
        industry_comparison = benchmarking.compare_with_industry()
        peer_comparison = benchmarking.compare_with_peers()
        
        return jsonify({
            'success': True,
            'data': {
                'industry_comparison': industry_comparison,
                'peer_comparison': peer_comparison,
                'improvement_opportunities': benchmarking.identify_improvement_opportunities()
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Error fetching performance benchmarks: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch performance benchmarks'
        }), 500

@performance_bp.route('/api/performance/predictions', methods=['GET'])
@jwt_required()
def get_performance_predictions():
    """Get performance predictions and forecasts"""
    try:
        vendor_id = request.args.get('vendor_id')
        
        if vendor_id:
            # Single vendor predictions
            attrition_risk = predictive_analytics.predict_attrition_risk(int(vendor_id))
            performance_forecast = predictive_analytics.forecast_performance(int(vendor_id))
            
            return jsonify({
                'success': True,
                'data': {
                    'attrition_risk': attrition_risk,
                    'performance_forecast': performance_forecast.to_dict('records') if not performance_forecast.empty else []
                }
            }), 200
        else:
            # All vendors risk predictions
            risk_predictions = predictive_analytics.predict_risk_scores()
            
            return jsonify({
                'success': True,
                'data': risk_predictions.to_dict('records') if not risk_predictions.empty else []
            }), 200
            
    except Exception as e:
        logging.error(f"Error fetching performance predictions: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch performance predictions'
        }), 500

@performance_bp.route('/api/performance/outliers', methods=['GET'])
@jwt_required()
def get_performance_outliers():
    """Identify performance outliers"""
    try:
        metric = request.args.get('metric', 'overall_score')
        threshold = float(request.args.get('threshold', 2.0))
        
        outliers = analytics_engine.identify_outliers(metric)
        
        # Filter by threshold if provided
        if threshold:
            outliers = [o for o in outliers if o['z_score'] > threshold]
        
        return jsonify({
            'success': True,
            'data': outliers
        }), 200
        
    except Exception as e:
        logging.error(f"Error identifying outliers: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to identify outliers'
        }), 500

@performance_bp.route('/api/performance/correlations', methods=['GET'])
@jwt_required()
def get_performance_correlations():
    """Get correlation analysis between performance metrics"""
    try:
        correlation_matrix = analytics_engine.calculate_correlation_matrix()
        
        return jsonify({
            'success': True,
            'data': correlation_matrix.to_dict()
        }), 200
        
    except Exception as e:
        logging.error(f"Error calculating correlations: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to calculate correlations'
        }), 500

@performance_bp.route('/api/performance/trends', methods=['GET'])
@jwt_required()
def get_performance_trends():
    """Get performance trends analysis"""
    try:
        period = request.args.get('period', '90')
        trend_type = request.args.get('type', 'overall')
        
        trends_data = analytics_engine.get_performance_trends(int(period))
        
        if trend_type == 'category':
            # Get trends by category (simplified implementation)
            vendors = db_manager.get_vendors()
            category_trends = {}
            
            for vendor in vendors:
                category = vendor['category']
                if category not in category_trends:
                    category_trends[category] = []
                category_trends[category].append(vendor.get('current_score', 0))
            
            # Calculate average by category
            category_avgs = {}
            for category, scores in category_trends.items():
                if scores:
                    category_avgs[category] = sum(scores) / len(scores)
            
            trends_data = pd.DataFrame({
                'category': list(category_avgs.keys()),
                'average_score': list(category_avgs.values())
            })
        
        return jsonify({
            'success': True,
            'data': trends_data.to_dict('records')
        }), 200
        
    except Exception as e:
        logging.error(f"Error fetching performance trends: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch performance trends'
        }), 500

@performance_bp.route('/api/performance/segments', methods=['GET'])
@jwt_required()
def get_performance_segments():
    """Get vendor segmentation analysis"""
    try:
        segments = analytics_engine.calculate_vendor_segments()
        
        # Calculate segment statistics
        segment_stats = segments.groupby('segment').agg({
            'performance_score': ['count', 'mean', 'std'],
            'risk_score': 'mean'
        }).round(2)
        
        return jsonify({
            'success': True,
            'data': {
                'segments': segments.to_dict('records'),
                'statistics': segment_stats.to_dict()
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Error calculating segments: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to calculate segments'
        }), 500

@performance_bp.route('/api/performance/reports', methods=['POST'])
@jwt_required()
def generate_performance_report():
    """Generate performance report"""
    try:
        from enhancements.report_generator import ReportGenerator
        
        data = request.get_json()
        vendor_ids = data.get('vendor_ids')
        report_format = data.get('format', 'pdf')
        report_type = data.get('type', 'performance')
        
        report_generator = ReportGenerator(db_manager)
        
        if report_type == 'performance':
            report_path = report_generator.generate_performance_report(vendor_ids, report_format)
        elif report_type == 'risk':
            report_path = report_generator.generate_risk_report(vendor_ids, report_format)
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid report type'
            }), 400
        
        if report_path:
            return jsonify({
                'success': True,
                'message': 'Report generated successfully',
                'report_path': report_path
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to generate report'
            }), 500
            
    except Exception as e:
        logging.error(f"Error generating performance report: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to generate performance report'
        }), 500