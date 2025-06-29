import os
import logging
import json
from flask import Flask, request, jsonify

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/api_test', methods=['GET'])
def api_test():
    return jsonify({"message": "API test endpoint is working"})

@app.route('/ai_recommendation_test', methods=['POST', 'GET'])
def ai_recommendation_test():
    """A simplified test endpoint for AI recommendation"""
    try:
        # Log the request
        logger.info(f"Request method: {request.method}")
        logger.info(f"Request headers: {dict(request.headers)}")
        
        # Extract data based on request type
        if request.method == 'GET':
            account_name = request.args.get('account_name', 'Sample Account')
            file_type = request.args.get('file_type', 'bs')
            logger.info(f"GET parameters: account_name={account_name}, file_type={file_type}")
        else:  # POST
            logger.info(f"Content type: {request.content_type}")
            if request.is_json:
                data = request.json
                account_name = data.get('account_name', 'Sample Account')
                file_type = data.get('file_type', 'bs')
                logger.info(f"JSON data: {data}")
            elif request.form:
                account_name = request.form.get('account_name', 'Sample Account')
                file_type = request.form.get('file_type', 'bs')
                logger.info(f"Form data: {dict(request.form)}")
            else:
                # Try to parse raw data
                try:
                    raw_data = request.get_data(as_text=True)
                    logger.info(f"Raw data: {raw_data}")
                    data = json.loads(raw_data)
                    account_name = data.get('account_name', 'Sample Account')
                    file_type = data.get('file_type', 'bs')
                except:
                    logger.exception("Could not parse raw data")
                    account_name = 'Sample Account'
                    file_type = 'bs'
        
        # Return a mock response
        response = {
            'success': True,
            'recommendation': {
                'account_name': account_name,
                'standard_account_code': '1010',
                'standard_account_name': 'テスト勘定科目',
                'confidence': 0.85,
                'rationale': 'これはテスト用の説明です。',
                'account_type': 'テスト'
            }
        }
        
        logger.info(f"Sending response: {response}")
        return jsonify(response)
    
    except Exception as e:
        logger.exception(f"Error in test endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'エラーが発生しました: {str(e)}'
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)