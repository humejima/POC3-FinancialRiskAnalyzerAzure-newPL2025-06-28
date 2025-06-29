// 預金残高修正用スクリプト
document.addEventListener('DOMContentLoaded', function() {
    // 預金残高のみ再計算ボタンのイベントハンドラ
    const fixDepositBtn = document.getElementById('fix-deposit-btn');
    if (fixDepositBtn) {
        fixDepositBtn.addEventListener('click', function() {
            // フォームの値を取得
            const jaCode = document.getElementById('ja_code').value;
            const year = document.getElementById('year').value;
            
            // 入力チェック
            if (!jaCode) {
                alert('JAを選択してください');
                return;
            }
            
            if (!year || isNaN(parseInt(year))) {
                alert('有効な年度を入力してください');
                return;
            }
            
            // 確認ダイアログを表示
            if (confirm('預金残高のみを再計算します。よろしいですか？\n\n※この操作は既存の預金残高データを削除します。')) {
                // POSTリクエストを作成
                const formData = new FormData();
                formData.append('ja_code', jaCode);
                formData.append('year', year);
                
                // 処理中メッセージ
                const btn = this;
                const originalText = btn.innerHTML;
                btn.disabled = true;
                btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 処理中...';
                
                // APIリクエスト
                fetch('/api/fix_deposit_balances', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        // 成功時の処理
                        alert('預金残高の再計算が完了しました。\n\n' + 
                            '削除: ' + data.details.deleted + '件\n' +
                            '作成: ' + data.details.created + '件');
                        
                        // 残高一覧ページにリダイレクト
                        window.location.href = '/account_balances?ja_code=' + jaCode + '&year=' + year + '&financial_statement=bs';
                    } else {
                        // エラー時の処理
                        alert('エラーが発生しました: ' + data.message);
                        btn.disabled = false;
                        btn.innerHTML = originalText;
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('処理中にエラーが発生しました。');
                    btn.disabled = false;
                    btn.innerHTML = originalText;
                });
            }
        });
    }
});