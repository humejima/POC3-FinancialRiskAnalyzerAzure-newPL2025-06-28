import os
import logging
import unicodedata
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from sqlalchemy import event
from sqlalchemy.engine import Engine

# Configure logging
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy with our base
db = SQLAlchemy(model_class=Base)

# Create the Flask application
app = Flask(__name__)

# Set the secret key from environment variable
app.secret_key = os.environ.get("SESSION_SECRET", "ja_financial_risk_analysis_secret_key")

# セッションとCookieのセキュリティ設定
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=3600,  # 1時間
    SESSION_COOKIE_DOMAIN=None  # 自動検出
)

# Configure the proxy fix middleware for correct URL generation
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database connection
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///ja_financial_risk.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# アップロードディレクトリの設定
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# データベース操作の前にすべての文字列データを正規化するための関数
def normalize_db_strings(attr, value, target, model):
    """SQLAlchemyイベントリスナー：文字列属性が設定される前に正規化を行う"""
    from utils import normalize_string
    
    if isinstance(value, str):
        return normalize_string(value, for_db=True)
    return value

# 文字列型の属性を持つすべてのクラスにリスナーを設定
@event.listens_for(Base, 'attribute_instrument')
def configure_listener(class_, key, inst):
    if not hasattr(inst.prop, 'columns'):
        return
    
    # 文字列型のカラムにのみリスナーを設定
    if any(isinstance(column.type, db.String) or isinstance(column.type, db.Text) 
           for column in inst.prop.columns):
        event.listen(getattr(class_, key), 'set', normalize_db_strings, retval=True)

# データベースコミット前のイベントリスナーを設定（エンティティ全体の正規化）
@event.listens_for(db.session, 'before_flush')
def normalize_before_flush(session, flush_context, instances):
    """フラッシュ前にセッション内のすべてのエンティティの文字列属性を確認して正規化"""
    import traceback
    from utils import normalize_string
    
    try:
        # 新規作成または変更されたエンティティを処理
        entities = session.new.union(session.dirty)
        logger.debug(f"フラッシュ前に正規化する対象: {len(entities)}エンティティ")
        
        for instance in entities:
            # エンティティのクラス名をログに記録
            entity_class = instance.__class__.__name__
            logger.debug(f"エンティティ正規化: {entity_class}")
            
            try:
                # 各インスタンスを個別に処理し、1つの失敗が全体を中断しないようにする
                for attr in instance.__dict__:
                    if attr.startswith('_'):
                        continue  # SQLAlchemyの内部属性をスキップ
                    
                    try:
                        # 各属性も個別に処理
                        value = getattr(instance, attr)
                        if isinstance(value, str):
                            # 既に安全に変換されている可能性があるため、try-except で囲む
                            try:
                                # 文字列の長さで問題を検出できるように記録
                                value_len = len(value)
                                # エンコーディングの問題があるかチェック
                                safe_value = value.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
                                
                                # 正規化処理を実行
                                normalized = normalize_string(safe_value, for_db=True)
                                # Noneチェックを追加
                                if normalized is not None:
                                    normalized_len = len(normalized)
                                    
                                    if normalized != value:
                                        logger.debug(f"属性正規化: {entity_class}.{attr} (長さ: {value_len} -> {normalized_len})")
                                        setattr(instance, attr, normalized)
                            except Exception as attr_e:
                                # 属性の処理中にエラーが発生した場合は、その属性をスキップしてログに記録
                                logger.error(f"属性正規化エラー: {entity_class}.{attr}: {str(attr_e)}")
                                logger.debug(traceback.format_exc())
                    except Exception as e:
                        # 特定の属性の取得または設定中にエラーが発生した場合は、次の属性に進む
                        logger.error(f"属性処理エラー: {entity_class}.{attr}: {str(e)}")
                        continue
            except Exception as instance_e:
                # インスタンス処理中にエラーが発生した場合は、次のインスタンスに進む
                logger.error(f"エンティティ処理エラー: {entity_class}: {str(instance_e)}")
                logger.debug(traceback.format_exc())
                continue
    except Exception as e:
        # 全体の処理中にエラーが発生した場合でも、フラッシュ操作を中断せずに続行
        logger.error(f"フラッシュ前正規化で予期しないエラー: {str(e)}")
        logger.error(traceback.format_exc())

# データベースコネクション確立後のイベントリスナー
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """データベース接続時に必要な設定を行う"""
    logger.info("データベース接続を確立しました")
    # SQLiteの場合はPRAGMA設定が可能
    # if isinstance(dbapi_connection, sqlite3.Connection):
    #     cursor = dbapi_connection.cursor()
    #     cursor.execute("PRAGMA foreign_keys=ON")
    #     cursor.close()

# Initialize the app with SQLAlchemy
db.init_app(app)

# Add custom template filter for safe integer formatting
@app.template_filter('safe_int')
def safe_int_filter(value):
    """
    Safely convert numeric values to integers, removing decimal points
    Handles both numeric and string values
    """
    if value is None or value == '':
        return value
    
    try:
        # Convert to string first
        str_value = str(value)
        # Remove .0 if present
        if str_value.endswith('.0'):
            return str_value[:-2]
        # Try to convert to int and back to string to remove unnecessary decimals
        float_value = float(str_value)
        if float_value.is_integer():
            return str(int(float_value))
        return str_value
    except (ValueError, TypeError):
        return value

# Create database tables within the application context
with app.app_context():
    # Import models to ensure they're registered with SQLAlchemy
    import models
    
    # Import utility functions
    from utils import normalize_string
    
    logger.info("Creating database tables...")
    db.create_all()
    logger.info("Database tables created successfully")
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
