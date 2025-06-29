"""
BSデータを直接インポートするスクリプト
Webインターフェイスを使用せず、直接データベースにインポートする
"""
import os
import pandas as pd
import logging
from app import app, db
from models import JA, CSVData
from datetime import datetime

# ロギング設定
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def direct_import_bs(ja_code="JA001", year=2021, filepath="uploads/BS.csv"):
    """
    BSデータを直接インポートする
    
    Args:
        ja_code: JAコード (デフォルト: JA001)
        year: 会計年度 (デフォルト: 2021)
        filepath: BSファイルのパス (デフォルト: uploads/BS.csv)
    """
    if not os.path.exists(filepath):
        logger.error(f"ファイル {filepath} が存在しません")
        return False
    
    with app.app_context():
        # JAが存在するか確認
        ja = JA.query.filter_by(ja_code=ja_code).first()
        if not ja:
            logger.error(f"JAコード {ja_code} が存在しません")
            return False
        
        # 既存のデータをクリーンアップ
        existing_data = CSVData.query.filter_by(
            ja_code=ja_code, 
            year=year,
            file_type='bs'
        ).all()
        
        if existing_data:
            logger.info(f"既存のBSデータ {len(existing_data)}件 を削除します")
            for item in existing_data:
                db.session.delete(item)
            db.session.commit()
        
        # CSVファイルを読み込む
        try:
            # 様々なエンコーディングを試す
            for encoding in ['utf-8-sig', 'utf-8', 'shift-jis', 'cp932']:
                try:
                    df = pd.read_csv(filepath, encoding=encoding)
                    logger.info(f"ファイル {filepath} を {encoding} エンコーディングで読み込みました")
                    break
                except UnicodeDecodeError:
                    continue
            else:
                logger.error("サポートされているエンコーディングでファイルを読み込めませんでした")
                return False
            
            # データフレームのカラム名と型を確認
            logger.info(f"データフレームの列: {', '.join(df.columns)}")
            logger.info(f"データの行数: {len(df)}")
            
            # データの例を表示
            for idx, row in df.head(2).iterrows():
                logger.info(f"行 {idx}: {dict(row)}")
            
            # カラム名の確認と正規化
            required_columns = ['科目名', '当年度', '前年度']
            if not all(col in df.columns for col in required_columns):
                logger.error(f"必要なカラムがありません。必要なカラム: {', '.join(required_columns)}")
                logger.error(f"ファイルのカラム: {', '.join(df.columns)}")
                return False
            
            # データを保存
            imported_count = 0
            for idx, row in df.iterrows():
                try:
                    # 必要なデータを抽出
                    account_name = str(row.get('科目名', '')).strip()
                    current_value = float(row.get('当年度', 0)) if pd.notna(row.get('当年度', 0)) else 0
                    previous_value = float(row.get('前年度', 0)) if pd.notna(row.get('前年度', 0)) else 0
                    category = 'Assets' if '資産' in account_name else 'Liabilities' if '負債' in account_name else 'Equity' if '純資産' in account_name else 'Unknown'
                    
                    # 空の科目名はスキップ
                    if not account_name or account_name == 'nan':
                        continue
                        
                    # CSVDataレコードを作成
                    csv_data = CSVData(
                        ja_code=ja_code,
                        year=year,
                        file_type='bs',
                        row_number=idx + 1,
                        account_name=account_name,
                        category=category,
                        current_value=current_value,
                        previous_value=previous_value,
                        is_mapped=False,
                        created_at=datetime.now()
                    )
                    
                    db.session.add(csv_data)
                    imported_count += 1
                    
                    # 100件ごとにコミット
                    if imported_count % 100 == 0:
                        db.session.commit()
                        logger.info(f"{imported_count}件のレコードを保存しました")
                
                except Exception as e:
                    logger.error(f"行 {idx} の処理中にエラーが発生しました: {str(e)}")
                    continue
            
            # 残りのレコードをコミット
            db.session.commit()
            logger.info(f"合計 {imported_count} 件のBSデータを {ja_code} の {year} 年度にインポートしました")
            
            # JAのavailable_dataを更新
            if not ja.available_data:
                ja.available_data = 'bs'
            elif 'bs' not in ja.available_data.split(','):
                ja.available_data = ja.available_data + ',bs'
            db.session.commit()
            
            return True
            
        except Exception as e:
            import traceback
            logger.error(f"BSデータのインポート中にエラーが発生しました: {str(e)}")
            logger.error(traceback.format_exc())
            db.session.rollback()
            return False

if __name__ == "__main__":
    # BS（貸借対照表）のデータをインポート
    result = direct_import_bs("JA001", 2021, "uploads/BS.csv")
    print(f"インポート結果: {'成功' if result else '失敗'}")