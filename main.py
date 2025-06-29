import os
import logging
import sys
from flask import render_template, request
from app import app, db
from routes import register_routes
from route_extensions import register_additional_routes
from api_endpoints import register_api_endpoints
from ja_management import register_ja_routes
from flask_talisman import Talisman
from modification_history import modification_manager, check_similar_issues, log_modification

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Log important information
logger.info("Starting application...")
logger.info(f"DATABASE_URL configured: {os.environ.get('DATABASE_URL') is not None}")
logger.info(f"SESSION_SECRET configured: {os.environ.get('SESSION_SECRET') is not None}")

# 代替セキュリティ設定
# Talismanを使わず、直接セキュリティヘッダーを設定する

# セキュリティヘッダー設定関数は後のlog_response_infoに統合

# Talisman設定は削除し、代わりにカスタムセキュリティヘッダーを使用

# Register all routes
logger.info("Registering routes...")
register_routes(app)
logger.info("Routes registered successfully")

# Register additional routes
logger.info("Registering additional routes...")
register_additional_routes(app)
logger.info("Additional routes registered successfully")

# Register API endpoints
logger.info("Registering API endpoints...")
register_api_endpoints(app)
logger.info("API endpoints registered successfully")

# Register JA management routes
logger.info("Registering JA management routes...")
register_ja_routes(app)
logger.info("JA management routes registered successfully")

# Register backup API endpoints
logger.info("Registering backup API endpoints...")
from backup_api import register_backup_api_endpoints
register_backup_api_endpoints(app)
logger.info("Backup API endpoints registered successfully")

# Register modification history routes
logger.info("Registering modification history routes...")
from route_modification_history import register_modification_routes
register_modification_routes(app)
logger.info("Modification history routes registered successfully")

# Add HTTP request logging middleware
@app.before_request
def log_request_info():
    logger.debug('Request Headers: %s', request.headers)
    logger.debug('Request Method: %s, Path: %s', request.method, request.path)

@app.after_request
def log_response_info(response):
    """レスポンスのログとセキュリティヘッダーの設定"""
    logger.debug('Response Status: %s', response.status)
    logger.debug('Response Headers: %s', response.headers)

    # 必須のセキュリティヘッダーを設定
    # Strict Transport Security
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

    # CORS設定 - すべてのドメインからのアクセスを許可
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'

    # Microsoft SmartScreen特有の対策ヘッダー
    response.headers['X-MS-SmartScreen'] = 'require'
    response.headers['X-Content-Security-Policy'] = 'default-src *; script-src *; object-src *'

    # セキュリティメタデータ
    response.headers['X-Download-Options'] = 'noopen'
    response.headers['X-Permitted-Cross-Domain-Policies'] = 'none'

    # ブラウザと通信
    response.headers['X-Edge-ClientID'] = 'verified-content'

    # X-Content-Type-Options
    response.headers['X-Content-Type-Options'] = 'nosniff'

    # X-Frame-Options
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'

    # X-XSS-Protection
    response.headers['X-XSS-Protection'] = '1; mode=block'

    # Referrer-Policy
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

    # Permissions-Policy (旧Feature-Policy)
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=(), payment=()'

    # Microsoft Edge特有の対策
    response.headers['X-UA-Compatible'] = 'IE=edge,chrome=1'

    # Cross-Origin-Resource-Policy
    response.headers['Cross-Origin-Resource-Policy'] = 'cross-origin'

    # Microsoft Defenderの警告対策（追加ヘッダー）
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Feature-Policy'] = '*'

    return response

# カスタムエラーハンドラ
@app.errorhandler(405)
def method_not_allowed_error(error):
    logger.error(f"Method Not Allowed Error: {request.method} {request.path}")
    return render_template('error.html', 
                          error_title="Method Not Allowed (405)",
                          error_message=f"リクエストメソッド '{request.method}' はこのURLでは許可されていません。",
                          error_detail=str(error)), 405

@app.errorhandler(500)
def internal_server_error(error):
    import traceback
    error_traceback = traceback.format_exc()
    error_message = str(error)
    
    logger.error(f"Internal Server Error: {error_message}")
    logger.error(f"Traceback: {error_traceback}")

    # 修正履歴をチェックして類似の問題があるか確認
    try:
        from modification_history import translate_agent_message
        
        # エラーメッセージを日本語化
        translated_error_message = translate_agent_message(error_message)
        
        similar_check = check_similar_issues(
            description=f"Internal Server Error: {translated_error_message}",
            error_messages=[translated_error_message, error_traceback]
        )
        
        if similar_check['similar_modifications']:
            logger.warning("類似のエラーが過去に発生しています:")
            for mod in similar_check['similar_modifications'][:2]:
                logger.warning(f"- {mod['description']}")
                for step in mod['solution_steps'][:3]:
                    logger.warning(f"  解決手順: {step}")
    except Exception as history_error:
        logger.error(f"修正履歴チェック中にエラー: {history_error}")

    # 一部のデータベースエラーは詳細を表示しない
    safe_error_message = "内部サーバーエラーが発生しました。問題が解決しない場合は、管理者に連絡してください。"

    # デバッグモードなら詳細情報を表示
    if app.debug:
        error_detail = f"{error_message}\n\n{error_traceback}"
    else:
        error_detail = error_message

    return render_template('error.html',
                          error_title="Internal Server Error (500)",
                          error_message=safe_error_message,
                          error_detail=error_detail), 500

def check_task_authorization(task_name, requested_tasks):
    """
    タスクの認可チェックを行う関数

    Args:
        task_name: 実行しようとしているタスク名
        requested_tasks: 依頼されたタスクのリスト

    Returns:
        bool: タスクが認可されているかどうか
    """
    if task_name not in requested_tasks:
        logger.warning(f"認可されていないタスクの実行試行: {task_name}")
        return False
    return True

def require_data_operation_approval(operation_type, ja_codes=None, description=""):
    """
    データ操作の実行前に承認を要求する関数
    
    Args:
        operation_type: 操作の種類（copy, delete, import, etc.）
        ja_codes: 対象のJAコードリスト
        description: 操作の詳細説明
        
    Returns:
        bool: 承認が得られたかどうか
    """
    logger.warning(f"データ操作の承認が必要です:")
    logger.warning(f"操作種類: {operation_type}")
    if ja_codes:
        logger.warning(f"対象JAコード: {', '.join(ja_codes)}")
    if description:
        logger.warning(f"操作内容: {description}")
    logger.warning("この操作を続行するには明示的な承認が必要です。")
    
    # 実際の承認メカニズムはUIまたは管理者による手動承認
    # 現在は常にFalseを返して承認待ちとする
    return False

def log_checkpoint(description_jp, description_en=None):
    """
    チェックポイントを日本語と英語で記録する関数

    Args:
        description_jp: 日本語での説明
        description_en: 英語での説明（オプション）
    """
    logger.info(f"チェックポイント: {description_jp}")
    if description_en:
        logger.info(f"Checkpoint: {description_en}")

if __name__ == "__main__":
    # Start the Flask app on host 0.0.0.0 (all interfaces) and port 5000
    port = int(os.environ.get("PORT", 5000))

    # 本番環境ではデバッグモードを無効化
    debug_mode = os.environ.get("FLASK_ENV") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug_mode)