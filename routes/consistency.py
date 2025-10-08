#!/usr/bin/env python3
"""
Quote consistency management routes.
"""

from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from models import db, Quote, AdminSetting
from utils.quote_consistency import QuoteConsistencyManager
import json

consistency_bp = Blueprint('consistency', __name__)

@consistency_bp.route('/admin/consistency')
@login_required
def consistency_dashboard():
    """Quote consistency dashboard"""
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    return render_template('admin/consistency_dashboard.html')

@consistency_bp.route('/api/consistency/analyze/<int:quote_id>', methods=['GET'])
@login_required
def analyze_quote_consistency(quote_id):
    """Analyze quote consistency against historical data"""
    try:
        consistency_manager = QuoteConsistencyManager()
        analysis = consistency_manager.analyze_quote_consistency(quote_id)
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@consistency_bp.route('/api/consistency/templates', methods=['GET'])
@login_required
def get_pricing_templates():
    """Get standard pricing templates"""
    try:
        consistency_manager = QuoteConsistencyManager()
        templates = consistency_manager.get_standard_pricing_templates()
        
        return jsonify({
            'success': True,
            'templates': templates
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@consistency_bp.route('/api/consistency/apply-template/<int:quote_id>', methods=['POST'])
@login_required
def apply_pricing_template(quote_id):
    """Apply standard pricing template to a quote"""
    try:
        data = request.get_json()
        template_name = data.get('template_name')
        
        if not template_name:
            return jsonify({
                'success': False,
                'error': 'Template name required'
            }), 400
        
        quote = Quote.query.get(quote_id)
        if not quote:
            return jsonify({
                'success': False,
                'error': 'Quote not found'
            }), 404
        
        consistency_manager = QuoteConsistencyManager()
        result = consistency_manager.apply_standard_template(quote, template_name)
        
        if 'error' in result:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
        
        return jsonify({
            'success': True,
            'template_result': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@consistency_bp.route('/api/consistency/comparison-report', methods=['GET'])
@login_required
def generate_comparison_report():
    """Generate comparison report for recent quotes"""
    try:
        # Get recent quotes for comparison
        recent_quotes = Quote.query.filter(
            Quote.created_at >= datetime.utcnow() - timedelta(days=30),
            Quote.status.in_(['sent', 'accepted'])
        ).order_by(Quote.created_at.desc()).limit(20).all()
        
        consistency_manager = QuoteConsistencyManager()
        
        report_data = []
        for quote in recent_quotes:
            analysis = consistency_manager.analyze_quote_consistency(quote.id)
            if analysis and 'error' not in analysis:
                report_data.append({
                    'quote_id': quote.id,
                    'quote_number': quote.quote_number,
                    'client_name': quote.client_name,
                    'project_title': quote.project_title,
                    'building_size': quote.building_size,
                    'total_cost': quote.estimated_cost,
                    'consistency_score': analysis.get('consistency_score', 0),
                    'similar_quotes_count': analysis.get('similar_quotes_count', 0),
                    'flags': analysis.get('flags', [])
                })
        
        return jsonify({
            'success': True,
            'report_data': report_data,
            'summary': {
                'total_quotes': len(report_data),
                'avg_consistency_score': sum(q['consistency_score'] for q in report_data) / len(report_data) if report_data else 0,
                'quotes_with_flags': len([q for q in report_data if q['flags']])
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

