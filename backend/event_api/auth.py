from functools import wraps
from flask import request, jsonify, current_app

def require_api_key(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        if request.headers.get('x-api-key') and request.headers.get('x-api-key') == current_app.config['API_KEY']:
            return view_function(*args, **kwargs)
        else:
            return jsonify({"error": "Unauthorized. Invalid or missing API Key."}), 401
    return decorated_function
