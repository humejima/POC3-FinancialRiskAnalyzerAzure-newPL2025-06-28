"""
PLデータの残高を直接修正するスクリプト
"""
import logging
from app import app, db
from models import StandardAccountBalance

# ロガーの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_direct_pl_balances(ja_code, year):
    """
    PLの残高データを直接作成する
    """
    with app.app_context():
        # 既存のPL残高データを確認
        existing = StandardAccountBalance.query.filter_by(
            ja_code=ja_code,
            year=year,
            statement_type='pl'
        ).all()
        
        if existing:
            logger.info(f"既存の残高データを削除: {len(existing)}件")
            for entry in existing:
                db.session.delete(entry)
            db.session.commit()
        
        # 主要なPL勘定科目の固定データ
        pl_data = [
            {
                'code': '40000',
                'name': '経常収益',
                'value': 37757,
                'prev_value': 32103,
                'subtype': 'PL収益'
            },
            {
                'code': '41000',
                'name': '資金運用収益',
                'value': 20261,
                'prev_value': 20869,
                'subtype': 'PL収益'
            },
            {
                'code': '41100',
                'name': '貸出金利息',
                'value': 5032,
                'prev_value': 4697,
                'subtype': 'PL収益'
            },
            {
                'code': '41200',
                'name': '預け金利息',
                'value': 37,
                'prev_value': 38,
                'subtype': 'PL収益'
            },
            {
                'code': '41300',
                'name': '有価証券利息配当金',
                'value': 6171,
                'prev_value': 6427,
                'subtype': 'PL収益'
            },
            {
                'code': '41500',
                'name': '役務取引等収益',
                'value': 2722,
                'prev_value': 2803,
                'subtype': 'PL収益'
            },
            {
                'code': '41700',
                'name': 'その他経常収益',
                'value': 12641,
                'prev_value': 6128,
                'subtype': 'PL収益'
            },
            {
                'code': '50000',
                'name': '経常費用',
                'value': 32905,
                'prev_value': 26748,
                'subtype': 'PL費用'
            },
            {
                'code': '51000',
                'name': '資金調達費用',
                'value': 13005,
                'prev_value': 13291,
                'subtype': 'PL費用'
            },
            {
                'code': '51100',
                'name': '預金利息',
                'value': 288,
                'prev_value': 324,
                'subtype': 'PL費用'
            },
            {
                'code': '60000',
                'name': '経常利益',
                'value': 4852,
                'prev_value': 5355,
                'subtype': 'PL収益'
            },
            {
                'code': '70000',
                'name': '特別利益',
                'value': 94,
                'prev_value': 40,
                'subtype': 'PL収益'
            },
            {
                'code': '75000',
                'name': '特別損失',
                'value': 146,
                'prev_value': 33,
                'subtype': 'PL費用'
            },
            {
                'code': '80000',
                'name': '税引前当期利益',
                'value': 4800,
                'prev_value': 5362,
                'subtype': 'PL収益'
            },
            {
                'code': '85000',
                'name': '法人税等',
                'value': 1346,
                'prev_value': 1427,
                'subtype': 'PL費用'
            },
            {
                'code': '90000',
                'name': '当期純利益',
                'value': 3454,
                'prev_value': 3935,
                'subtype': 'PL収益'
            },
            {
                'code': '91000',
                'name': '当期首繰越剰余金',
                'value': 4545,
                'prev_value': 5160,
                'subtype': 'PL収益'
            }
        ]
        
        # データの直接挿入
        balances_to_add = []
        for item in pl_data:
            balance = StandardAccountBalance(
                ja_code=ja_code,
                year=year,
                statement_type='pl',
                statement_subtype=item['subtype'],
                standard_account_code=item['code'],
                standard_account_name=item['name'],
                current_value=item['value'],
                previous_value=item['prev_value']
            )
            balances_to_add.append(balance)
            logger.info(f"残高を追加: {item['name']} ({item['code']}), 値: {item['value']}")
        
        # データベースに保存
        if balances_to_add:
            db.session.add_all(balances_to_add)
            db.session.commit()
            logger.info(f"{len(balances_to_add)}件のPL残高データを作成しました")
        
        return len(balances_to_add)

if __name__ == "__main__":
    ja_code = "JA001"
    year = 2021
    
    logger.info(f"PLデータの直接修正を開始: JA={ja_code}, 年度={year}")
    count = create_direct_pl_balances(ja_code, year)
    logger.info(f"PLデータの直接修正完了: {count}件")