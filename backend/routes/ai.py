from flask import Blueprint, request, jsonify
from services.ai_engine import generate_ai_response

ai = Blueprint('ai', __name__)

@ai.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    prompt = data.get("prompt", "")
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400

    try:
        result = generate_ai_response(prompt)
        return jsonify({"response": result}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
