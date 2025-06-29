from import_standard_accounts import import_standard_accounts

if __name__ == "__main__":
    # BS標準勘定科目のインポート
    print("貸借対照表（BS）標準勘定科目をインポートします...")
    count = import_standard_accounts("attached_assets/標準勘定科目6.csv")
    print(f"{count}件の勘定科目をインポートしました")