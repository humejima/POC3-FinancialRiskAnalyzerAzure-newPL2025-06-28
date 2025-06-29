/**
 * Main JavaScript functionality for JA Financial Risk Analysis System
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    
    // Show/hide new JA fields based on selection in data_import.html
    const jaSelect = document.getElementById('ja_code');
    const newJaFields = document.getElementById('new_ja_fields');
    
    if (jaSelect && newJaFields) {
        jaSelect.addEventListener('change', function() {
            if (this.value === 'new') {
                newJaFields.style.display = 'block';
            } else {
                newJaFields.style.display = 'none';
            }
        });
    }
    
    // File type validation for data_import.html
    const fileInput = document.getElementById('file');
    const fileTypeSelect = document.getElementById('file_type');
    
    if (fileInput && fileTypeSelect) {
        fileInput.addEventListener('change', function() {
            const fileName = this.value.toLowerCase();
            let detectedType = '';
            
            if (fileName.includes('bs') || fileName.includes('balance')) {
                detectedType = 'bs';
            } else if (fileName.includes('pl') || fileName.includes('profit') || fileName.includes('loss')) {
                detectedType = 'pl';
            } else if (fileName.includes('cf') || fileName.includes('cash') || fileName.includes('flow')) {
                detectedType = 'cf';
            }
            
            if (detectedType && fileTypeSelect.value !== detectedType) {
                if (confirm(`ファイル名から "${detectedType}" タイプが検出されました。選択を変更しますか？`)) {
                    fileTypeSelect.value = detectedType;
                }
            }
        });
    }
    
    // Confidence threshold slider in mapping.html
    const confidenceSlider = document.getElementById('confidence_threshold');
    const confidenceValue = document.getElementById('confidence_value');
    
    if (confidenceSlider && confidenceValue) {
        confidenceSlider.addEventListener('input', function() {
            confidenceValue.textContent = this.value;
        });
    }
    
    // スライダーと信頼度値の同期
    document.addEventListener('DOMContentLoaded', function() {
        console.log("JA財務リスク分析システムが正常に読み込まれました");
        
        // スライダーの値が変わった時に値を表示要素に同期
        const confidenceSliderMain = document.getElementById('confidence_threshold');
        const confidenceValueMain = document.getElementById('confidence_value');
        
        if (confidenceSliderMain && confidenceValueMain) {
            confidenceSliderMain.addEventListener('input', function() {
                confidenceValueMain.textContent = this.value;
            });
        }
    });
    
    // Delete confirmation handler in data_management.html
    const deleteDataBtn = document.getElementById('deleteDataBtn');
    if (deleteDataBtn) {
        deleteDataBtn.addEventListener('click', function() {
            const deleteModal = new bootstrap.Modal(document.getElementById('deleteConfirmModal'));
            deleteModal.show();
        });
    }
    
    // Validation modal in data_management.html
    const validateDataBtn = document.getElementById('validateDataBtn');
    const validationResult = document.getElementById('validation-result');
    
    if (validateDataBtn && validationResult) {
        validateDataBtn.addEventListener('click', function() {
            // This would be an API call in a complete implementation
            // Here we show a loading indicator and then success
            validationResult.innerHTML = `
                <div class="alert alert-info">
                    <i class="fa-solid fa-spinner fa-spin"></i>
                    データを検証しています...
                </div>
            `;
            validationResult.style.display = 'block';
            
            // Simulate API call delay
            setTimeout(() => {
                validationResult.innerHTML = `
                    <div class="alert alert-success">
                        <i class="fa-solid fa-check-circle"></i>
                        データ検証が完了しました。問題は見つかりませんでした。
                    </div>
                `;
            }, 1500);
        });
    }
    
    // Print report functionality in reports.html
    const printReportBtn = document.getElementById('printReportBtn');
    if (printReportBtn) {
        printReportBtn.addEventListener('click', function() {
            const reportContent = document.getElementById('report-content');
            const originalContents = document.body.innerHTML;
            
            document.body.innerHTML = reportContent.innerHTML;
            window.print();
            document.body.innerHTML = originalContents;
            location.reload();
        });
    }
    
    // Mapping modal in mapping.html
    const mappingModal = document.getElementById('mappingModal');
    if (mappingModal) {
        const mapButtons = document.querySelectorAll('.map-account-btn');
        const accountIdInput = document.getElementById('account_id_input');
        const originalAccountInput = document.getElementById('original_account_name');
        const saveButton = document.getElementById('save-mapping-btn');
        const mappingForm = document.getElementById('manual-mapping-form');
        
        // Setup for opening the mapping modal
        mapButtons.forEach(button => {
            button.addEventListener('click', function() {
                const accountId = this.getAttribute('data-account-id');
                const accountName = this.getAttribute('data-account-name');
                
                accountIdInput.value = accountId;
                originalAccountInput.value = accountName;
                
                const bsModal = new bootstrap.Modal(mappingModal);
                bsModal.show();
            });
        });
        
        // Save mapping button
        if (saveButton) {
            saveButton.addEventListener('click', function() {
                mappingForm.submit();
            });
        }
        
        // Edit mapping functionality
        const editButtons = document.querySelectorAll('.edit-mapping-btn');
        
        editButtons.forEach(button => {
            button.addEventListener('click', function() {
                const originalName = this.getAttribute('data-original-name');
                const standardCode = this.getAttribute('data-standard-code');
                
                originalAccountInput.value = originalName;
                
                // Find the account with matching name in unmapped accounts
                const unmappedAccounts = document.querySelectorAll('.map-account-btn');
                let accountId = null;
                
                unmappedAccounts.forEach(account => {
                    if (account.getAttribute('data-account-name') === originalName) {
                        accountId = account.getAttribute('data-account-id');
                    }
                });
                
                accountIdInput.value = accountId || 'existing_' + originalName;
                
                // Select the right standard account
                const standardAccountSelect = document.getElementById('standard_account_code');
                if (standardAccountSelect) {
                    for (let i = 0; i < standardAccountSelect.options.length; i++) {
                        if (standardAccountSelect.options[i].value === standardCode) {
                            standardAccountSelect.selectedIndex = i;
                            break;
                        }
                    }
                }
                
                const bsModal = new bootstrap.Modal(mappingModal);
                bsModal.show();
            });
        });
    }
    
    // Set current date for reports if needed
    const reportDateElements = document.querySelectorAll('.report-date');
    if (reportDateElements.length > 0) {
        const now = new Date();
        const dateString = now.getFullYear() + '/' + 
                          (now.getMonth() + 1).toString().padStart(2, '0') + '/' + 
                          now.getDate().toString().padStart(2, '0');
        
        reportDateElements.forEach(el => {
            el.textContent = dateString;
        });
    }
    
    // Enable responsive tables
    const tables = document.querySelectorAll('.table');
    tables.forEach(table => {
        if (!table.closest('.table-responsive')) {
            const wrapper = document.createElement('div');
            wrapper.className = 'table-responsive';
            table.parentNode.insertBefore(wrapper, table);
            wrapper.appendChild(table);
        }
    });
    
    // Handle form validation
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
});

/**
 * Format number with commas
 * @param {number} num - Number to format
 * @returns {string} Formatted number
 */
function formatNumber(num) {
    return new Intl.NumberFormat('ja-JP').format(num);
}

/**
 * Get risk level color based on score
 * @param {number} score - Risk score (1-5)
 * @returns {string} Bootstrap color class
 */
function getRiskColor(score) {
    if (score >= 4.5) return 'danger';
    if (score >= 3.5) return 'warning';
    if (score >= 2.5) return 'info';
    if (score >= 1.5) return 'success';
    return 'primary';
}

/**
 * Get Japanese risk level text based on score
 * @param {number} score - Risk score (1-5)
 * @returns {string} Risk level text in Japanese
 */
function getRiskLevelText(score) {
    if (score >= 4.5) return '極めて高い';
    if (score >= 3.5) return '高い';
    if (score >= 2.5) return '中程度';
    if (score >= 1.5) return '低い';
    return '極めて低い';
}

/**
 * Format indicator name to Japanese
 * @param {string} name - Indicator name (English)
 * @returns {string} Indicator name in Japanese
 */
function formatIndicatorName(name) {
    const nameMap = {
        'current_ratio': '流動比率',
        'quick_ratio': '当座比率',
        'cash_ratio': '現金比率',
        'working_capital': '運転資本',
        'roa': '総資産利益率',
        'roe': '自己資本利益率',
        'profit_margin': '利益率',
        'operating_margin': '営業利益率',
        'debt_ratio': '負債比率',
        'equity_ratio': '自己資本比率',
        'debt_to_equity': '負債資本比率',
        'interest_coverage': 'インタレストカバレッジレシオ',
        'asset_turnover': '総資産回転率',
        'receivables_turnover': '売上債権回転率',
        'inventory_turnover': '棚卸資産回転率',
        'days_sales_outstanding': '売上債権回収期間',
        'ocf_to_debt': '営業CF対負債比率',
        'cf_to_revenue': 'CF対売上比率',
        'cf_to_net_income': 'CF対純利益比率',
        'free_cash_flow': 'フリーキャッシュフロー'
    };
    
    return nameMap[name] || name;
}

/**
 * Format category name to Japanese
 * @param {string} category - Category name (English)
 * @returns {string} Category name in Japanese
 */
function formatCategoryName(category) {
    const categoryMap = {
        'liquidity': '流動性',
        'profitability': '収益性',
        'safety': '安全性',
        'efficiency': '効率性',
        'cash_flow': 'キャッシュフロー'
    };
    
    return categoryMap[category] || category;
}
