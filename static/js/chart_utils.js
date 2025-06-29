/**
 * チャート関連のユーティリティ関数
 */

// ラベルオーバーレイ処理を追加する関数
function addChartLabels(chartContainer, labels) {
  console.log('ラベル追加処理を開始します', chartContainer, labels);
  
  // 既存のラベルを削除
  const existingLabels = chartContainer.querySelectorAll('.chart-labels');
  console.log('既存ラベル数:', existingLabels.length);
  existingLabels.forEach(el => el.remove());
  
  // 新しいラベル要素作成
  const labelsContainer = document.createElement('div');
  labelsContainer.className = 'chart-labels';
  
  // 各ラベルの位置とテキスト
  const labelPositions = [
    {class: 'top', text: '収益性'},
    {class: 'right', text: '効率性'},
    {class: 'bottom-right', text: '安全性'},
    {class: 'left', text: 'キャッシュフロー'},
    {class: 'bottom-left', text: '流動性'}
  ];
  
  // カスタムテキストがある場合それを優先
  if (labels && labels.length > 0) {
    console.log('カスタムラベルを使用:', labels);
    for (let i = 0; i < Math.min(labelPositions.length, labels.length); i++) {
      labelPositions[i].text = labels[i];
    }
  }
  
  // ラベル要素をDOMに追加
  labelPositions.forEach(pos => {
    const label = document.createElement('span');
    label.className = `chart-label ${pos.class}`;
    label.innerText = pos.text;
    labelsContainer.appendChild(label);
  });
  
  // コンテナに追加
  chartContainer.appendChild(labelsContainer);
  console.log('ラベル追加完了');
}

// ダッシュボードのレーダーチャート描画
function drawRiskRadarChart(elementId, labels, scores, previousScores) {
  try {
    const ctx = document.getElementById(elementId).getContext('2d');
    if (!ctx) {
      console.error('チャートコンテキストが見つかりません');
      return null;
    }
    
    // Chart.jsのグローバル変数が利用可能か確認
    if (typeof Chart === 'undefined') {
      console.error('Chart.jsが読み込まれていません');
      return null;
    }
    
    // 既存のチャートをクリーンアップ
    const existingChart = Chart.getChart(ctx.canvas);
    if (existingChart) {
      existingChart.destroy();
    }
    
    // チャートコンテナのサイズを拡大
    const chartContainer = ctx.canvas.parentElement;
    chartContainer.style.height = '450px'; // 高さを1.5倍に拡大（300px→450px）
    
    // データセット配列を準備
    const datasets = [{
      label: '現在のリスク耐性',
      data: scores,
      backgroundColor: 'rgba(54, 162, 235, 0.3)',
      borderColor: 'rgba(54, 162, 235, 1)',
      borderWidth: 2.5,
      pointBackgroundColor: 'rgba(54, 162, 235, 1)',
      pointRadius: 5,
      pointHoverRadius: 7,
      pointBorderWidth: 2,
      pointBorderColor: '#fff',
      pointHoverBackgroundColor: '#fff',
      pointHoverBorderColor: 'rgba(54, 162, 235, 1)'
    }];
    
    // 前年度データがある場合は追加
    if (previousScores && previousScores.length > 0) {
      datasets.push({
        label: '前年度リスク耐性',
        data: previousScores,
        backgroundColor: 'rgba(255, 159, 64, 0.2)',
        borderColor: 'rgba(255, 159, 64, 1)',
        borderWidth: 2,
        pointBackgroundColor: 'rgba(255, 159, 64, 1)',
        pointRadius: 4,
        pointHoverRadius: 6,
        pointBorderWidth: 1.5,
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: 'rgba(255, 159, 64, 1)',
        borderDash: [5, 5] // 点線にして区別をつける
      });
    }
    
    // チャート設定
    const config = {
      type: 'radar',
      data: {
        labels: labels,
        datasets: datasets
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        elements: {
          line: {
            borderWidth: 2
          }
        },
        scales: {
          r: {
            min: 0,
            max: 5,
            beginAtZero: true,
            ticks: {
              stepSize: 1,
              showLabelBackdrop: true,
              backdropColor: 'rgba(40, 40, 40, 0.8)',
              backdropPadding: 5,
              font: {
                size: 14, // テキストサイズを大きく
                weight: 'bold'
              },
              color: '#ffffff',
              z: 1
            },
            grid: {
              display: true,
              color: '#ffffff',
              lineWidth: 0.5
            },
            angleLines: {
              display: true,
              color: '#ffffff',
              lineWidth: 0.5
            },
            pointLabels: {
              font: {
                size: 18, // ラベルサイズを大きく
                weight: 'bold'
              },
              color: '#ffffff',
              padding: 12, // パディングを増やす
              // ラベルの背景を追加して見やすくする
              callback: function(value) {
                return value;
              },
              // 文字の縁取りを追加
              textStrokeColor: '#000000',
              textStrokeWidth: 3
            }
          }
        },
        plugins: {
          tooltip: {
            backgroundColor: 'rgba(0, 0, 0, 0.7)',
            titleFont: {
              size: 14
            },
            bodyFont: {
              size: 13
            },
            padding: 10
          },
          legend: {
            position: 'bottom',
            labels: {
              font: {
                size: 13
              }
            }
          },
          tooltip: {
            backgroundColor: 'rgba(0, 0, 0, 0.7)',
            titleFont: {
              size: 14
            },
            bodyFont: {
              size: 13
            },
            padding: 10
          }
        }
      }
    };
    
    // チャートを作成して返す
    const chart = new Chart(ctx, config);
    console.log('レーダーチャートが正常に描画されました');
    return chart;
  } catch (error) {
    console.error('レーダーチャート描画エラー:', error);
    return null;
  }
}