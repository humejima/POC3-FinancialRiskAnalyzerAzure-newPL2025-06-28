"""
PLデータの残高表示問題を修正する簡易的なスクリプト
"""
import logging
from app import app, db
from models import StandardAccountBalance, StandardAccount, CSVData, AccountMapping

# ロガーの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_pl_balance_entries(ja_code, year):
    """
    PLの標準残高データを直接作成する
    """
    with app.app_context():
        # 既存の標準残高データを確認
        existing_balances = StandardAccountBalance.query.filter_by(
            ja_code=ja_code,
            year=year,
            statement_type='pl'
        ).all()
        
        # 存在する場合は削除
        if existing_balances:
            logger.info(f"既存のPL残高データを削除: {len(existing_balances)}件")
            for balance in existing_balances:
                db.session.delete(balance)
            db.session.commit()
        
        # PLの標準勘定科目を取得
        standard_accounts = StandardAccount.query.filter_by(
            financial_statement='pl'
        ).all()
        
        # CSVデータを取得（主要な科目だけ）
        csv_data_dict = {}
        csv_records = CSVData.query.filter_by(
            ja_code=ja_code,
            year=year,
            file_type='pl'
        ).all()
        
        # 科目名と値のマッピングを作成
        for record in csv_records:
            csv_data_dict[record.account_name] = {
                'current_value': record.current_value,
                'previous_value': record.previous_value,
                'category': record.category
            }
        
        # 主要な科目の静的マッピング
        key_mappings = {
            '40000': {'name': '経常収益', 'subtype': 'PL収益'},
            '41000': {'name': '資金運用収益', 'subtype': 'PL収益'},
            '41100': {'name': '貸出金利息', 'subtype': 'PL収益'},
            '41200': {'name': '預け金利息', 'subtype': 'PL収益'},
            '41300': {'name': '有価証券利息配当金', 'subtype': 'PL収益'},
            '41400': {'name': 'その他の資金運用収益', 'subtype': 'PL収益'},
            '41500': {'name': '役務取引等収益', 'subtype': 'PL収益'},
            '41700': {'name': 'その他経常収益', 'subtype': 'PL収益'},
            '50000': {'name': '経常費用', 'subtype': 'PL費用'},
            '51000': {'name': '資金調達費用', 'subtype': 'PL費用'},
            '51100': {'name': '預金利息', 'subtype': 'PL費用'},
            '51500': {'name': '役務取引等費用', 'subtype': 'PL費用'},
            '60000': {'name': '経常利益', 'subtype': 'PL収益'},
            '70000': {'name': '特別利益', 'subtype': 'PL収益'},
            '75000': {'name': '特別損失', 'subtype': 'PL費用'},
            '80000': {'name': '税引前当期利益', 'subtype': 'PL収益'},
            '85000': {'name': '法人税等', 'subtype': 'PL費用'},
            '90000': {'name': '当期純利益', 'subtype': 'PL収益'},
            '91000': {'name': '当期首繰越剰余金', 'subtype': 'PL収益'},
            '93000': {'name': '当期未処分剰余金', 'subtype': 'PL収益'}
        }
        
        # CSVデータからの値の抽出
        pl_values = {
            '40000': csv_data_dict.get('経常収益', {}).get('current_value', 0),
            '41000': csv_data_dict.get('資金運用収益', {}).get('current_value', 0),
            '41100': csv_data_dict.get('貸出金利息', {}).get('current_value', 0),
            '41200': csv_data_dict.get('預け金利息', {}).get('current_value', 0),
            '41300': csv_data_dict.get('有価証券利息配当金', {}).get('current_value', 0),
            '41400': csv_data_dict.get('その他の資金運用収益', {}).get('current_value', 0),
            '41500': csv_data_dict.get('役務取引等収益', {}).get('current_value', 0),
            '41700': csv_data_dict.get('その他経常収益', {}).get('current_value', 0),
            '50000': csv_data_dict.get('経常費用', {}).get('current_value', 0),
            '51000': csv_data_dict.get('資金調達費用', {}).get('current_value', 0),
            '51100': csv_data_dict.get('預金利息', {}).get('current_value', 0),
            '51500': csv_data_dict.get('役務取引等費用', {}).get('current_value', 0),
            '60000': csv_data_dict.get('経常利益', {}).get('current_value', 0),
            '70000': csv_data_dict.get('特別利益', {}).get('current_value', 0),
            '75000': csv_data_dict.get('特別損失', {}).get('current_value', 0),
            '80000': csv_data_dict.get('税引前当期利益', {}).get('current_value', 0),
            '85000': csv_data_dict.get('法人税・住民税及び事業税', {}).get('current_value', 0),
            '90000': csv_data_dict.get('当期純利益', {}).get('current_value', 0),
            '91000': csv_data_dict.get('当期首繰越利益剰余金', {}).get('current_value', 0),
            '93000': csv_data_dict.get('当期末剰余金', {}).get('current_value', 0)
        }
        
        # 前年度の値
        pl_previous_values = {
            '40000': csv_data_dict.get('経常収益', {}).get('previous_value', 0),
            '41000': csv_data_dict.get('資金運用収益', {}).get('previous_value', 0),
            '41100': csv_data_dict.get('貸出金利息', {}).get('previous_value', 0),
            '41200': csv_data_dict.get('預け金利息', {}).get('previous_value', 0),
            '41300': csv_data_dict.get('有価証券利息配当金', {}).get('previous_value', 0),
            '41400': csv_data_dict.get('その他の資金運用収益', {}).get('previous_value', 0),
            '41500': csv_data_dict.get('役務取引等収益', {}).get('previous_value', 0),
            '41700': csv_data_dict.get('その他経常収益', {}).get('previous_value', 0),
            '50000': csv_data_dict.get('経常費用', {}).get('previous_value', 0),
            '51000': csv_data_dict.get('資金調達費用', {}).get('previous_value', 0),
            '51100': csv_data_dict.get('預金利息', {}).get('previous_value', 0),
            '51500': csv_data_dict.get('役務取引等費用', {}).get('previous_value', 0),
            '60000': csv_data_dict.get('経常利益', {}).get('previous_value', 0),
            '70000': csv_data_dict.get('特別利益', {}).get('previous_value', 0),
            '75000': csv_data_dict.get('特別損失', {}).get('previous_value', 0),
            '80000': csv_data_dict.get('税引前当期利益', {}).get('previous_value', 0),
            '85000': csv_data_dict.get('法人税・住民税及び事業税', {}).get('previous_value', 0),
            '90000': csv_data_dict.get('当期純利益', {}).get('previous_value', 0),
            '91000': csv_data_dict.get('当期首繰越利益剰余金', {}).get('previous_value', 0),
            '93000': csv_data_dict.get('当期末剰余金', {}).get('previous_value', 0)
        }
        
        # 残高データの作成
        created_count = 0
        balances_to_add = []
        
        for code, info in key_mappings.items():
            try:
                # 標準勘定科目を取得
                std_account = StandardAccount.query.filter_by(code=code).first()
                
                if std_account:
                    account_name = std_account.name
                else:
                    account_name = info['name']
                
                # 現在値と前年度値
                current_value = float(pl_values.get(code, 0)) if pl_values.get(code) is not None else 0
                previous_value = float(pl_previous_values.get(code, 0)) if pl_previous_values.get(code) is not None else 0
                
                # 新しい残高エントリを作成
                new_balance = StandardAccountBalance(
                    ja_code=ja_code,
                    year=year,
                    statement_type='pl',
                    statement_subtype=info['subtype'],
                    standard_account_code=code,
                    standard_account_name=account_name,
                    current_value=current_value,
                    previous_value=previous_value
                )
                
                balances_to_add.append(new_balance)
                created_count += 1
                logger.info(f"残高データを作成: {account_name} ({code}), 値: {current_value}")
                
                # 対応するCSVデータをマッピング済みとしてマーク
                csv_data = CSVData.query.filter_by(
                    ja_code=ja_code,
                    year=year,
                    file_type='pl',
                    account_name=info['name']
                ).first()
                
                if csv_data:
                    csv_data.is_mapped = True
                
            except Exception as e:
                logger.error(f"残高データ作成エラー（コード {code}）: {str(e)}")
        
        # データベースに保存
        if balances_to_add:
            db.session.add_all(balances_to_add)
            db.session.commit()
            logger.info(f"{created_count}件のPL残高データを作成しました")
        
        return created_count

if __name__ == "__main__":
    ja_code = "JA001"
    year = 2021
    
    logger.info(f"PLデータの残高作成を開始: JA={ja_code}, 年度={year}")
    count = create_pl_balance_entries(ja_code, year)
    logger.info(f"PLデータの残高作成完了: {count}件")