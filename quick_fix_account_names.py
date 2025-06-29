"""
CSVデータの勘定科目名を迅速に修正
"""
import logging
from app import db
from models import CSVData

logger = logging.getLogger(__name__)

def quick_fix_account_names():
    """問題のある勘定科目名を修正"""
    
    # 正しい科目名のマッピング（行番号順）
    correct_names = {
        0: "現金",
        1: "現金及び預金",
        2: "普通預金", 
        3: "定期預金",
        4: "譲渡性預金",
        5: "系統預金",
        6: "有価証券",
        7: "国債",
        8: "地方債",
        9: "社債",
        10: "株式",
        11: "投資信託",
        12: "その他有価証券",
        13: "貸出金",
        14: "短期貸付金",
        15: "長期貸付金",
        16: "その他貸出金",
        17: "その他資産",
        18: "未収金",
        19: "前払費用"
    }
    
    try:
        # JA005の2021年度BSデータを修正
        problem_records = CSVData.query.filter(
            CSVData.ja_code == 'JA005',
            CSVData.year == 2021,
            CSVData.file_type == 'bs',
            CSVData.account_name == '資産'
        ).all()
        
        logger.info(f"修正対象レコード数: {len(problem_records)}")
        
        fixed_count = 0
        for record in problem_records:
            row_num = record.row_number
            if row_num in correct_names:
                record.account_name = correct_names[row_num]
                fixed_count += 1
                logger.info(f"行{row_num}: 「{correct_names[row_num]}」に修正")
        
        db.session.commit()
        logger.info(f"修正完了: {fixed_count}件")
        
        return fixed_count
        
    except Exception as e:
        logger.error(f"修正エラー: {str(e)}")
        db.session.rollback()
        return 0

if __name__ == "__main__":
    from app import app
    with app.app_context():
        result = quick_fix_account_names()
        print(f"修正件数: {result}")