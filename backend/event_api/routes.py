from flask import Blueprint, request, jsonify
from .auth import require_api_key
from .services.scraper import UnifiedEventService
from .limiter import limiter

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')
scraper = UnifiedEventService()

@api_bp.route('/events', methods=['GET'])
@require_api_key
@limiter.limit("10 per minute")
def get_events():
    location = request.args.get('location')
    category = request.args.get('category')
    
    if not location or not category:
        return jsonify({"error": "Missing required parameters: location, category"}), 400
        
    try:
        events = scraper.get_events(location, category)
        return jsonify({
            "status": "success",
            "count": len(events),
            "data": events
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
