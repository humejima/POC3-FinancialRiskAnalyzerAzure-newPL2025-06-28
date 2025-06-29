/**
 * 財務指標再計算機能を提供するJavaScript
 */

/**
 * アラートメッセージを表示する
 * @param {string} message - 表示するメッセージ
 * @param {string} className - アラートのクラス（alert-success, alert-danger, alert-warning）
 */
function showAlert(message, className) {
    // 既存のアラートを削除
    const existingAlerts = document.querySelectorAll('.custom-alert');
    existingAlerts.forEach(alert => alert.remove());
    
    // アラート要素を作成
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert ${className} alert-dismissible fade show custom-alert`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.style.position = 'fixed';
    alertDiv.style.top = '20px';
    alertDiv.style.right = '20px';
    alertDiv.style.zIndex = '9999';
    alertDiv.style.maxWidth = '400px';
    
    // メッセージを設定
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // bodyに追加
    document.body.appendChild(alertDiv);
    
    // 5秒後に自動的に閉じる
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// 指標再計算ボタンのイベントリスナー設定
document.addEventListener('DOMContentLoaded', function() {
    const recalculateBtn = document.getElementById('recalculateIndicators');
    if (recalculateBtn) {
        recalculateBtn.addEventListener('click', function() {
            // ボタンを無効化して処理中表示
            this.disabled = true;
            const originalText = this.innerHTML;
            this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 計算中...';
            
            // JAコードと年度を取得
            const jaCode = this.getAttribute('data-ja');
            const year = this.getAttribute('data-year');
            
            // フォームデータを作成
            const formData = new FormData();
            formData.append('ja_code', jaCode);
            formData.append('year', year);
            
            console.log('指標再計算リクエスト開始:', jaCode, year);
            
            // APIリクエスト送信
            fetch('/api/recalculate_indicators', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                // JSONレスポンスを解析
                if (!response.ok) {
                    throw new Error('APIリクエストが失敗しました');
                }
                return response.json();
            })
            .then(data => {
                // 処理成功時
                console.log('指標再計算API結果:', data);
                
                // アラートでメッセージを表示
                const alertClass = data.status === 'success' ? 'alert-success' : 'alert-warning';
                showAlert(data.message, alertClass);
                
                // ページを再読み込み（キャッシュを無効化）
                setTimeout(() => {
                    const currentUrl = window.location.href;
                    const refreshUrl = currentUrl.includes('?') 
                        ? currentUrl + '&nocache=' + new Date().getTime()
                        : currentUrl + '?nocache=' + new Date().getTime();
                    window.location.href = refreshUrl;
                }, 1500);
            })
            .catch(error => {
                // エラー発生時
                console.error('指標再計算エラー:', error);
                showAlert('指標の再計算に失敗しました: ' + error.message, 'alert-danger');
                
                // ボタンを元に戻す
                this.disabled = false;
                this.innerHTML = originalText;
            });
        });
    }
});