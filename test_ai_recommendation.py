"""
AI推薦機能のAPIエンドポイントをテストするスクリプト
"""
import requests
import json
import logging

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ai_recommendation_api():
    """AI推薦APIエンドポイントをテスト"""
    try:
        # 実際のサーバーURLを使用
        # Replitのデプロイメントに対応
        import os
        server_url = os.environ.get("REPLIT_URL", "https://cab8882f-b03a-4857-a5fa-23701902e586-00-3i28ryiq808gz.pike.replit.dev")
        base_url = server_url
        endpoint = "/ai_recommendation"
        
        # テスト用のパラメータ - AIアシストが必要な複雑な科目名
        params = {
            "account_name": "定期性貯金積金",
            "file_type": "bs"
        }
        
        # API呼び出し
        logger.info(f"Calling API at {base_url}{endpoint}")
        logger.info(f"Parameters: {params}")
        
        # POSTリクエスト
        response = requests.post(f"{base_url}{endpoint}", json=params)
        
        # レスポンスの確認
        logger.info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            # JSONレスポンスの解析
            data = response.json()
            logger.info("API Response:")
            logger.info(json.dumps(data, indent=2, ensure_ascii=False))
            
            # 成功判定
            if data.get("success"):
                # 推薦内容の表示
                recommendation = data.get("recommendation", {})
                logger.info("Recommendation Details:")
                logger.info(f"  Account Name: {recommendation.get('account_name')}")
                logger.info(f"  Standard Account: {recommendation.get('standard_account_code')} - {recommendation.get('standard_account_name')}")
                logger.info(f"  Confidence: {recommendation.get('confidence')}")
                logger.info(f"  Rationale: {recommendation.get('rationale')}")
                
                return True
            else:
                logger.error(f"API Error: {data.get('error')}")
                return False
        else:
            logger.error(f"API request failed with status code {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Testing AI Recommendation API...")
    success = test_ai_recommendation_api()
    
    if success:
        logger.info("Test completed successfully")
    else:
        logger.error("Test failed")