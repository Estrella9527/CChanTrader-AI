/**
 * CChanTrader-AI 优化版股票推荐模态框脚本
 * 处理JSON API响应、骨架屏和Chart.js K线图渲染
 */

// 全局变量
let currentChart = null;

/**
 * 打开股票详情模态框
 * @param {string} symbol - 股票代码
 */
function openStockModal(symbol) {
    const modal = document.getElementById("pickModal");
    const modalBody = document.getElementById("pickModalBody");
    const skeleton = document.getElementById("modalSkeleton");
    
    // 显示模态框和骨架屏
    modal.classList.remove("hidden");
    if (skeleton) {
        skeleton.style.display = "block";
    }
    
    // 获取股票详情数据
    fetch(`/api/stocks/${symbol}/analysis`)
        .then(response => response.json())
        .then(data => {
            // 隐藏骨架屏
            if (skeleton) {
                skeleton.style.display = "none";
            }
            
            // 更新HTML内容
            modalBody.innerHTML = data.html;
            
            // 渲染图表
            setTimeout(() => {
                renderChart(data.prices);
            }, 100);
            
        })
        .catch(error => {
            console.error("Failed to load stock analysis:", error);
            
            // 隐藏骨架屏并显示错误信息
            if (skeleton) {
                skeleton.style.display = "none";
            }
            
            modalBody.innerHTML = `
                <div class="text-center py-8">
                    <div class="text-red-400 mb-4">
                        <svg class="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                    </div>
                    <p class="text-red-500 mb-2">加载失败</p>
                    <p class="text-gray-500 text-sm">股票代码: ${symbol}</p>
                    <p class="text-gray-400 text-sm">请稍后重试</p>
                </div>
            `;
        });
}

/**
 * 关闭股票详情模态框
 */
function closeStockModal() {
    const modal = document.getElementById("pickModal");
    modal.classList.add("hidden");
    
    // 销毁现有图表
    if (currentChart) {
        currentChart.destroy();
        currentChart = null;
    }
}

/**
 * 渲染Chart.js迷你图表
 * @param {Array} prices - 价格数据数组
 */
function renderChart(prices) {
    const canvas = document.getElementById("miniChart");
    
    if (!canvas || !prices || !prices.length) {
        console.warn("Chart canvas not found or no price data available");
        return;
    }
    
    // 销毁现有图表
    if (currentChart) {
        currentChart.destroy();
    }
    
    try {
        // 生成时间标签（简化为索引）
        const labels = prices.map((_, index) => index + 1);
        
        // 创建新的Chart.js迷你K线图
        currentChart = new Chart(canvas, {
            type: "line",
            data: {
                labels: labels,
                datasets: [{
                    data: prices,
                    borderColor: "#4F46E5",
                    backgroundColor: "rgba(79, 70, 229, 0.1)",
                    tension: 0.3,
                    borderWidth: 2,
                    fill: true,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    pointHoverBackgroundColor: "#4F46E5"
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                return `价格: ¥${context.parsed.y.toFixed(2)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: false,
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        display: false,
                        grid: {
                            display: false
                        }
                    }
                },
                elements: {
                    point: {
                        radius: 0,
                        hoverRadius: 4
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
        
        console.log("Chart.js miniChart created successfully");
        
    } catch (error) {
        console.error("Error creating chart:", error);
    }
}

// 处理模态框键盘事件（ESC键关闭）
document.addEventListener("keydown", function(e) {
    if (e.key === "Escape") {
        const modal = document.getElementById("pickModal");
        if (modal && !modal.classList.contains("hidden")) {
            closeStockModal();
        }
    }
});

// 辅助函数：生成模拟价格数据（用于测试）
function generateMockPriceData(basePrice = 10, days = 30) {
    const prices = [];
    let currentPrice = basePrice;
    
    for (let i = 0; i < days; i++) {
        // 模拟价格波动（-3% 到 +3%）
        const change = (Math.random() - 0.5) * 0.06;
        currentPrice = Math.max(0.01, currentPrice * (1 + change));
        prices.push(parseFloat(currentPrice.toFixed(2)));
    }
    
    return prices;
}

// 全局可用的模态框控制函数（向后兼容）
window.PickModal = {
    open: openStockModal,
    close: closeStockModal,
    toggle: function() {
        const modal = document.getElementById("pickModal");
        if (modal) {
            if (modal.classList.contains("hidden")) {
                // 需要股票代码，这里无法调用openStockModal
                console.warn("Use openStockModal(symbol) instead");
            } else {
                closeStockModal();
            }
        }
    }
};

// 暴露全局函数
window.openStockModal = openStockModal;
window.closeStockModal = closeStockModal;
window.renderChart = renderChart;

console.log("✅ Optimized pick_modal.js loaded successfully");