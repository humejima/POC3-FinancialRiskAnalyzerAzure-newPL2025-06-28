import os
from sqlalchemy import create_engine, text

# データベース接続設定
db_url = os.environ.get("DATABASE_URL")
engine = create_engine(db_url)

# 新しいカラムを追加するSQLコマンド
sql_commands = [
    "ALTER TABLE analysis_result ADD COLUMN IF NOT EXISTS formula VARCHAR(500)",
    "ALTER TABLE analysis_result ADD COLUMN IF NOT EXISTS calculation TEXT",
    "ALTER TABLE analysis_result ADD COLUMN IF NOT EXISTS accounts_used TEXT"
]

def update_analysis_table():
    """analysis_resultテーブルを更新して新しいカラムを追加する"""
    with engine.connect() as conn:
        for sql in sql_commands:
            print(f"実行: {sql}")
            conn.execute(text(sql))
        conn.commit()
        print("完了: analysis_resultテーブルが更新されました")

if __name__ == "__main__":
    update_analysis_table()