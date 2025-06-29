"""
PLデータの問題を修正するスクリプト
特に93000(当期純利益)がCSVには存在するがDBには含まれていない問題を解決する
"""
from app import app, db
from models import CSVData, StandardAccountBalance
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_pl_net_income(ja_code='JA001', year=2021):
    """
    PLデータで93000(当期純利益)が欠落している問題を修正
    CSVデータから当期純利益を抽出し、StandardAccountBalanceに追加する
    
    Args:
        ja_code: JA code
        year: Financial year
    """
    with app.app_context():
        try:
            # 既存の当期純利益があるか確認
            existing = StandardAccountBalance.query.filter_by(
                ja_code=ja_code,
                year=year,
                statement_type='pl',
                standard_account_code='93000'
            ).first()
            
            if existing:
                logger.info(f"当期純利益(93000)の項目は既に存在します: {existing.current_value}")
                return True
            
            # CSVデータから当期純利益を検索（account_codeフィールドはないため、名前で検索）
            csv_data = CSVData.query.filter_by(
                ja_code=ja_code,
                year=year,
                file_type='pl'
            ).filter(CSVData.account_name.like('%当期純利益%')).first()
            
            if csv_data:
                logger.info(f"CSVデータから当期純利益を取得: {csv_data.account_name}, 値={csv_data.current_value}")
                
                # 新しいStandardAccountBalanceレコードを作成
                new_balance = StandardAccountBalance(
                    ja_code=ja_code,
                    year=year,
                    statement_type='pl',
                    standard_account_code='93000',
                    standard_account_name=csv_data.account_name,
                    current_value=csv_data.current_value,
                    previous_value=csv_data.previous_value,
                    is_manual=False
                )
                
                # 親コード設定（例: 90000）
                new_balance.parent_code = '90000'
                
                # データベースに追加して保存
                db.session.add(new_balance)
                db.session.commit()
                
                logger.info(f"当期純利益(93000)の項目を追加しました: {new_balance.current_value}")
                return True
            else:
                logger.warning(f"CSVデータに当期純利益(93000)が見つかりません: JA={ja_code}, 年度={year}")
                return False
                
        except Exception as e:
            logger.error(f"当期純利益の修正中にエラーが発生しました: {str(e)}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    fix_pl_net_income('JA001', 2021)