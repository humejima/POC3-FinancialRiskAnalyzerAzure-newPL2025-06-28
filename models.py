from datetime import datetime
import logging
import json
from app import db
from utils import normalize_string

# ロガーの設定
logger = logging.getLogger(__name__)

class JA(db.Model):
    """JA (Agricultural Cooperative) basic information table"""
    __tablename__ = 'ja'
    
    ja_code = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    prefecture = db.Column(db.String(20), nullable=False)
    scale = db.Column(db.String(20), nullable=True)  # 規模: 大規模, 中規模, 小規模
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    year = db.Column(db.Integer, nullable=False)
    available_data = db.Column(db.String(10), nullable=False)  # Comma-separated: bs,pl,cf
    
    # Define relationships
    csv_data = db.relationship('CSVData', backref='ja', lazy=True)
    standard_balances = db.relationship('StandardAccountBalance', backref='ja', lazy=True)
    analysis_results = db.relationship('AnalysisResult', backref='ja', lazy=True)

class CSVData(db.Model):
    """Imported CSV data table"""
    __tablename__ = 'csv_data'
    
    id = db.Column(db.Integer, primary_key=True)
    ja_code = db.Column(db.String(10), db.ForeignKey('ja.ja_code'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    file_type = db.Column(db.String(2), nullable=False)  # bs, pl, cf
    row_number = db.Column(db.Integer, nullable=False)
    account_name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))
    current_value = db.Column(db.Float)
    previous_value = db.Column(db.Float)
    is_mapped = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<CSVData {self.account_name} - {self.file_type}>"
        
    def __setattr__(self, name, value):
        """文字列フィールドの値を設定する前に正規化する"""
        # 特定の文字列フィールドに対してのみ正規化を適用
        if name in ['account_name', 'category'] and value is not None:
            if isinstance(value, str):
                # 文字列の場合、正規化を適用
                normalized_value = normalize_string(value, for_db=True)
                logger.debug(f"CSVData 文字列正規化: {name}={value} -> {normalized_value}")
                super().__setattr__(name, normalized_value)
            else:
                super().__setattr__(name, value)
        else:
            super().__setattr__(name, value)

class StandardAccount(db.Model):
    """Standard account code master table"""
    __tablename__ = 'standard_account'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    financial_statement = db.Column(db.String(2), nullable=False)  # bs, pl, cf
    account_type = db.Column(db.String(20), nullable=False)
    display_order = db.Column(db.Integer, nullable=False)
    parent_code = db.Column(db.String(10), nullable=True)  # 上位科目コード
    description = db.Column(db.Text)
    
    def __repr__(self):
        return f"<StandardAccount {self.code} - {self.name}>"
        
    def __setattr__(self, name, value):
        """文字列フィールドの値を設定する前に正規化する"""
        # 特定の文字列フィールドに対してのみ正規化を適用
        if name in ['name', 'category', 'account_type', 'description'] and value is not None:
            if isinstance(value, str):
                # 文字列の場合、正規化を適用
                normalized_value = normalize_string(value, for_db=True)
                logger.debug(f"StandardAccount 文字列正規化: {name}={value} -> {normalized_value}")
                super().__setattr__(name, normalized_value)
            else:
                super().__setattr__(name, value)
        else:
            super().__setattr__(name, value)

class StandardAccountBalance(db.Model):
    """Mapped account balance table"""
    __tablename__ = 'standard_account_balance'
    
    id = db.Column(db.Integer, primary_key=True)
    ja_code = db.Column(db.String(10), db.ForeignKey('ja.ja_code'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    statement_type = db.Column(db.String(2), nullable=False)  # bs, pl, cf
    statement_subtype = db.Column(db.String(20), nullable=False)  # BS資産, BS負債, PL収益, etc.
    standard_account_code = db.Column(db.String(10), nullable=False)
    standard_account_name = db.Column(db.String(100), nullable=False)
    current_value = db.Column(db.Float)
    previous_value = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<StandardAccountBalance {self.standard_account_code} - {self.current_value}>"
        
    def __setattr__(self, name, value):
        """文字列フィールドの値を設定する前に正規化する"""
        # 特定の文字列フィールドに対してのみ正規化を適用
        if name in ['statement_subtype', 'standard_account_name'] and value is not None:
            if isinstance(value, str):
                # 文字列の場合、正規化を適用
                normalized_value = normalize_string(value, for_db=True)
                logger.debug(f"StandardAccountBalance 文字列正規化: {name}={value} -> {normalized_value}")
                super().__setattr__(name, normalized_value)
            else:
                super().__setattr__(name, value)
        else:
            super().__setattr__(name, value)

class AccountMapping(db.Model):
    """Account mapping information table"""
    __tablename__ = 'account_mapping'
    
    id = db.Column(db.Integer, primary_key=True)
    ja_code = db.Column(db.String(10), nullable=False)
    original_account_name = db.Column(db.String(100), nullable=False)
    standard_account_code = db.Column(db.String(10), nullable=False)
    standard_account_name = db.Column(db.String(100), nullable=False)
    financial_statement = db.Column(db.String(2), nullable=False)  # bs, pl, cf
    confidence = db.Column(db.Float)
    rationale = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<AccountMapping {self.original_account_name} -> {self.standard_account_name}>"
        
    def __setattr__(self, name, value):
        """文字列フィールドの値を設定する前に正規化する"""
        # 特定の文字列フィールドに対してのみ正規化を適用
        if name in ['original_account_name', 'standard_account_name', 'rationale'] and value is not None:
            if isinstance(value, str):
                # 文字列の場合、正規化を適用
                normalized_value = normalize_string(value, for_db=True)
                logger.debug(f"AccountMapping 文字列正規化: {name}={value} -> {normalized_value}")
                super().__setattr__(name, normalized_value)
            else:
                super().__setattr__(name, value)
        else:
            super().__setattr__(name, value)

class AnalysisResult(db.Model):
    """Financial analysis and risk assessment results table"""
    __tablename__ = 'analysis_result'
    
    id = db.Column(db.Integer, primary_key=True)
    ja_code = db.Column(db.String(10), db.ForeignKey('ja.ja_code'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    analysis_type = db.Column(db.String(20), nullable=False)  # liquidity, safety, profitability, etc.
    indicator_name = db.Column(db.String(50), nullable=False)
    indicator_value = db.Column(db.Float)
    benchmark = db.Column(db.Float)
    risk_score = db.Column(db.Integer)  # 1-5
    risk_level = db.Column(db.String(10))  # low, medium, high
    analysis_result = db.Column(db.Text)
    formula = db.Column(db.String(500))  # 計算式の説明
    calculation = db.Column(db.Text)  # 実際の計算過程を示す文字列
    accounts_used = db.Column(db.Text)  # 計算に使用した勘定科目と値のJSON文字列
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<AnalysisResult {self.indicator_name} - {self.risk_level}>"

class AccountFormula(db.Model):
    """勘定科目の計算式を定義するテーブル"""
    __tablename__ = 'account_formula'
    
    id = db.Column(db.Integer, primary_key=True)
    target_code = db.Column(db.String(10), nullable=False)  # 計算結果の科目コード
    target_name = db.Column(db.String(100), nullable=False)  # 計算結果の科目名
    financial_statement = db.Column(db.String(2), nullable=False)  # bs, pl, cf
    formula_type = db.Column(db.String(20), nullable=False)  # sum, diff, product, ratio
    components = db.Column(db.Text, nullable=False)  # 計算に使用する科目コードのJSON配列
    operator = db.Column(db.String(5), nullable=False, default='+')  # 演算子（+, -, *, /）
    description = db.Column(db.Text)  # 計算式の説明
    priority = db.Column(db.Integer, default=0)  # 計算優先順位（高いほど先に計算）
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<AccountFormula {self.target_code} = f({self.components})>"
    
    @property
    def component_codes(self):
        """コンポーネント科目コードのリストを返す"""
        if self.components:
            try:
                return json.loads(self.components)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON in components field: {self.components}")
                return []
        return []
        
    def __setattr__(self, name, value):
        """文字列フィールドの値を設定する前に正規化する"""
        # 特定の文字列フィールドに対してのみ正規化を適用
        if name in ['target_name', 'description'] and value is not None:
            if isinstance(value, str):
                # 文字列の場合、正規化を適用
                normalized_value = normalize_string(value, for_db=True)
                logger.debug(f"AccountFormula 文字列正規化: {name}={value} -> {normalized_value}")
                super().__setattr__(name, normalized_value)
            else:
                super().__setattr__(name, value)
        else:
            super().__setattr__(name, value)

class User(db.Model):
    """User information table for authentication"""
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, analyst, viewer
    
    def __repr__(self):
        return f"<User {self.username}>"
