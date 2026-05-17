import os
import sys
import time
import warnings
import logging
from datetime import datetime
from typing import Optional, Dict, Any

# 添加自定义库路径
sys.path.append('E:\pythonLib\site-packages')

# 禁用代理和 Gradio 网络检查
os.environ['NO_PROXY'] = 'localhost,127.0.0.1'
os.environ['GRADIO_ANALYTICS_ENABLED'] = 'False'

import gradio as gr
from rag_pipeline import RAGPipeline
from real_time_data import RealTimeDataService

warnings.filterwarnings("ignore")

# 配置日志
log_dir = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"gradio_app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)
logger.info(f"日志文件: {log_file}")

# 初始化服务
logger.info("=" * 80)
logger.info("初始化RAG系统...")
logger.info("=" * 80)
data_dir = os.path.join(os.path.dirname(__file__), "data")
rag_pipeline = RAGPipeline(data_dir)
real_time_data = RealTimeDataService()
logger.info("✅ RAG系统初始化完成")

# 全局变量
session_histories = {}

# 生成实时数据卡片HTML
def generate_real_time_cards():
    """生成实时数据卡片HTML"""
    # 获取最新的实时数据
    sh_index_data = real_time_data.get_sh_index_real_time()
    stock_data = real_time_data.get_stock_real_time("600855")
    # 获取上证指数 K 线数据
    sh_kline_data = real_time_data.get_sh_index_kline_data("1W")
    # 获取航天长峰 K 线数据
    stock_kline_data = real_time_data.get_stock_kline_data("600855", "1D")
    current_time = time.strftime("%H:%M:%S")
    
    # 生成专业风格的 K 线图（复刻 investing.com 风格）
    def generate_kline_svg(data, price_min, price_max, price_labels):
        """生成专业风格的 K 线图 SVG，复刻 investing.com 风格"""
        svg = f"""
        <svg width="300" height="200" style="background: #ffffff; border: 1px solid #e0e0e0; border-radius: 6px;">
            <!-- 定义样式 -->
            <defs>
                <!-- 上涨K线颜色 -->
                <rect id="kline-up" width="1" height="1" fill="#26a69a" />
                <!-- 下跌K线颜色 -->
                <rect id="kline-down" width="1" height="1" fill="#ef5350" />
                <!-- 成交量上涨颜色 -->
                <rect id="volume-up" width="1" height="1" fill="#b2dfdb" />
                <!-- 成交量下跌颜色 -->
                <rect id="volume-down" width="1" height="1" fill="#ffcdd2" />
                <!-- 网格线样式 -->
                <pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse">
                    <path d="M 10 0 L 0 0 0 10" fill="none" stroke="#f0f0f0" stroke-width="0.5"/>
                </pattern>
            </defs>
            
            <!-- 绘制背景网格 -->
            <rect width="300" height="200" fill="url(#grid)" />
            
            <!-- 绘制边框 -->
            <rect x="0" y="0" width="300" height="200" fill="none" stroke="#e0e0e0" stroke-width="1" rx="6" ry="6" />
            
            <!-- 绘制价格轴 -->
            <g>
                <line x1="50" y1="20" x2="290" y2="20" style="stroke: #e0e0e0; stroke-width: 1;" />
                <line x1="50" y1="60" x2="290" y2="60" style="stroke: #e0e0e0; stroke-width: 1;" />
                <line x1="50" y1="100" x2="290" y2="100" style="stroke: #e0e0e0; stroke-width: 1;" />
                <line x1="50" y1="140" x2="290" y2="140" style="stroke: #e0e0e0; stroke-width: 1;" />
                <line x1="50" y1="180" x2="290" y2="180" style="stroke: #e0e0e0; stroke-width: 1;" />
                <line x1="50" y1="20" x2="50" y2="180" style="stroke: #e0e0e0; stroke-width: 1;" />
            </g>
            
            <!-- 绘制价格轴标签 -->
            <g font-size="11" fill="#666666" text-anchor="end" font-family="Arial, sans-serif">
                <text x="48" y="24">{price_labels[0]}</text>
                <text x="48" y="64">{price_labels[1]}</text>
                <text x="48" y="104">{price_labels[2]}</text>
                <text x="48" y="144">{price_labels[3]}</text>
                <text x="48" y="184">{price_labels[4]}</text>
            </g>
            
            <!-- 绘制日期标签 -->
            <g font-size="11" fill="#666666" text-anchor="middle" font-family="Arial, sans-serif">
                <text x="70" y="195">周一</text>
                <text x="105" y="195">周二</text>
                <text x="140" y="195">周三</text>
                <text x="175" y="195">周四</text>
                <text x="210" y="195">周五</text>
                <text x="245" y="195">周六</text>
                <text x="280" y="195">周日</text>
            </g>
            
            <!-- 绘制K线数据 -->
            <g>
        """
        
        # 添加K线数据
        if data:
            for i in range(min(7, len(data['dates']))):
                date = data['dates'][i]
                open_price = data['opens'][i]
                high_price = data['highs'][i]
                low_price = data['lows'][i]
                close_price = data['closes'][i]
                volume = data['volumes'][i]
                x = 60 + i * 35
                is_up = close_price >= open_price
                kline_color = '#26a69a' if is_up else '#ef5350'
                volume_color = '#b2dfdb' if is_up else '#ffcdd2'
                
                # 计算Y轴坐标
                price_range = price_max - price_min
                y_high = 20 + (price_min + price_range - high_price) / price_range * 160
                y_low = 20 + (price_min + price_range - low_price) / price_range * 160
                y_open = 20 + (price_min + price_range - open_price) / price_range * 160
                y_close = 20 + (price_min + price_range - close_price) / price_range * 160
                kline_height = abs(y_close - y_open)
                kline_y = min(y_open, y_close)
                
                # 添加K线
                svg += f"""
                                <!-- 绘制影线 -->
                                <line x1="{x + 5}" y1="{y_high}" x2="{x + 5}" y2="{y_low}" stroke="{kline_color}" stroke-width="1.5" />
                                
                                <!-- 绘制实体 -->
                                <rect x="{x}" y="{kline_y}" width="10" height="{max(kline_height, 1)}" fill="{kline_color}" />
                                
                                <!-- 绘制成交量 -->
                                <rect x="{x}" y="{180 - min(volume / 50000000000 * 20, 20)}" width="10" height="{min(volume / 50000000000 * 20, 20)}" fill="{volume_color}" />
                """
        else:
            # 默认K线数据
            svg += f"""
                                <!-- 默认K线数据 -->
                                <line x1="65" y1="40" x2="65" y2="160" stroke="#26a69a" stroke-width="1.5" />
                                <rect x="60" y="80" width="10" height="80" fill="#26a69a" />
                                <line x1="95" y1="60" x2="95" y2="180" stroke="#ef5350" stroke-width="1.5" />
                                <rect x="90" y="80" width="10" height="100" fill="#ef5350" />
                                <line x1="130" y1="50" x2="130" y2="170" stroke="#26a69a" stroke-width="1.5" />
                                <rect x="125" y="100" width="10" height="70" fill="#26a69a" />
                                <line x1="165" y1="40" x2="165" y2="160" stroke="#26a69a" stroke-width="1.5" />
                                <rect x="160" y="90" width="10" height="70" fill="#26a69a" />
                                <line x1="200" y1="60" x2="200" y2="180" stroke="#ef5350" stroke-width="1.5" />
                                <rect x="195" y="110" width="10" height="70" fill="#ef5350" />
                                <line x1="235" y1="30" x2="235" y2="150" stroke="#26a69a" stroke-width="1.5" />
                                <rect x="230" y="80" width="10" height="70" fill="#26a69a" />
                                <line x1="270" y1="50" x2="270" y2="170" stroke="#26a69a" stroke-width="1.5" />
                                <rect x="265" y="100" width="10" height="70" fill="#26a69a" />
                                <!-- 成交量 -->
                                <rect x="60" y="160" width="10" height="20" fill="#b2dfdb" />
                                <rect x="90" y="165" width="10" height="15" fill="#ffcdd2" />
                                <rect x="125" y="162" width="10" height="18" fill="#b2dfdb" />
                                <rect x="160" y="160" width="10" height="20" fill="#b2dfdb" />
                                <rect x="195" y="163" width="10" height="17" fill="#ffcdd2" />
                                <rect x="230" y="158" width="10" height="22" fill="#b2dfdb" />
                                <rect x="265" y="161" width="10" height="19" fill="#b2dfdb" />
            """
        
        # 完成SVG
        svg += f"""
                            </g>
                            
                            <!-- 绘制5日均线 -->
                            <polyline points="65,100 95,110 130,106 165,100 200,102 235,96 270,92" 
                                      fill="none" stroke="#2196f3" stroke-width="2" opacity="0.8" />
                        </svg>
        """
        
        return svg
    
    # 处理上证指数数据
    if sh_index_data:
        sh_price = f"{sh_index_data['最新价']:.2f}"
        sh_change = f"{sh_index_data['涨跌幅']:.2f}"
        sh_change_class = "up" if sh_index_data['涨跌幅'] >= 0 else "down"
        sh_volume = f"{sh_index_data['成交量']:.0f}"
        sh_turnover = f"{sh_index_data['成交额']:.0f}"
        
        # 生成上证指数 K 线图
        sh_kline_svg = generate_kline_svg(
            sh_kline_data,
            price_min=3100,
            price_max=3300,
            price_labels=["3300", "3250", "3200", "3150", "3100"]
        )
        
        sh_index_card = f"""
        <div class="data-card">
            <div class="data-card-header">
                <h3>📈 上证指数</h3>
                <span style='font-size: 12px; color: #64748b; margin-left: 10px;'>更新: {current_time} (1分钟刷新一次)</span>
            </div>
            <div class="data-card-content-horizontal">
                <div class="data-info">
                    <div class="data-value">{sh_price}</div>
                    <div class="data-change {sh_change_class}">{sh_change}%</div>
                    <div class="data-detail">成交额: {sh_volume}</div>
                    <div class="data-detail">成交量: {sh_turnover}</div>
                </div>
                <!-- K线图 -->
                <div class="k-line-chart">
                    <div class="chart-title">📊 一周K线</div>
                    <div class="k-line-container">
                        {sh_kline_svg}
                    </div>
                </div>
            </div>
        </div>
        """
    else:
        sh_index_card = f"<div class='data-card error'>无法获取上证指数数据 (更新: {current_time})</div>"
    
    # 处理航天长峰数据（医疗板块）
    if stock_data:
        stock_price = f"{stock_data['最新价']:.2f}"
        stock_change = f"{stock_data['涨跌幅']:.2f}"
        stock_change_class = "up" if stock_data['涨跌幅'] >= 0 else "down"
        stock_high = f"{stock_data['最高价']:.2f}"
        stock_low = f"{stock_data['最低价']:.2f}"
        
        # 生成航天长峰 K 线图
        stock_kline_svg = generate_kline_svg(
            stock_kline_data,
            price_min=19,
            price_max=21,
            price_labels=["21", "20.5", "20", "19.5", "19"]
        )
        
        stock_card = f"""
        <div class="data-card">
            <div class="data-card-header">
                <h3>🏢 航天长峰 (600855)</h3>
                <span style='font-size: 12px; color: #64748b; margin-left: 10px;'>更新: {current_time} (1分钟刷新一次)</span>
            </div>
            <div class="data-card-content-horizontal">
                <div class="data-info">
                    <div class="data-value">{stock_price}</div>
                    <div class="data-change {stock_change_class}">{stock_change}%</div>
                    <div class="data-detail">最高价: {stock_high}</div>
                    <div class="data-detail">最低价: {stock_low}</div>
                </div>
                <!-- K线图 -->
                <div class="k-line-chart">
                    <div class="chart-title">📊 当日K线</div>
                    <div class="k-line-container">
                        {stock_kline_svg}
                    </div>
                </div>
            </div>
        </div>
        """
    else:
        stock_card = f"<div class='data-card error'>无法获取航天长峰数据 (更新: {current_time})</div>"
    
    return f"<div class='data-cards-container'>{sh_index_card}{stock_card}</div>"

# 浅蓝科技风主题 CSS
custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700;900&family=Orbitron:wght@700&display=swap');

/* ========== 整体布局 - 浅蓝科技风 ========== */
body, .gradio-container {
    font-family: 'Noto Sans SC', 'Microsoft YaHei', sans-serif !important;
    background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 50%, #e0f2fe 100%) !important;
}

.gradio-container { max-width: 100% !important; }

/* ========== 左侧边栏 - 白色玻璃 ========== */
#sidebar { 
    background: rgba(255, 255, 255, 0.85) !important;
    backdrop-filter: blur(20px) !important;
    border-right: 1px solid rgba(59, 130, 246, 0.2) !important;
    padding: 30px 20px !important; 
    min-height: 100vh;
    box-shadow: 4px 0 30px rgba(59, 130, 246, 0.1) !important;
}

/* Logo区域 */
.logo-container {
    text-align: center;
    padding: 20px 0 30px 0;
    border-bottom: 1px solid rgba(59, 130, 246, 0.15);
    margin-bottom: 25px;
}

.logo-icon {
    width: 55px;
    height: 55px;
    background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
    border-radius: 14px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 12px;
    box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4);
}

.logo-icon svg {
    width: 30px;
    height: 30px;
    fill: white;
}

.logo-title {
    font-size: 26px;
    font-weight: 700;
    background: linear-gradient(135deg, #1e40af 0%, #0891b2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: 3px;
}

.logo-subtitle {
    font-size: 10px;
    color: #64748b;
    letter-spacing: 4px;
    margin-top: 6px;
}

/* 侧边栏按钮 */
.sidebar-btn { 
    display: block !important; 
    width: 100% !important; 
    text-align: left !important; 
    padding: 14px 18px !important; 
    border: 1px solid transparent !important; 
    background: transparent !important; 
    font-size: 15px !important; 
    margin-bottom: 6px !important;
    border-radius: 12px !important; 
    color: #475569 !important;
    transition: all 0.3s ease !important;
}

.sidebar-btn:hover { 
    background: rgba(59, 130, 246, 0.08) !important;
    border-color: rgba(59, 130, 246, 0.2) !important;
    color: #2563eb !important;
    transform: translateX(5px) !important;
}

.sidebar-btn.active { 
    background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%) !important;
    color: #ffffff !important;
    box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4) !important;
    border-color: transparent !important;
}

/* ========== 右侧主区域 - 浅蓝条纹科技风 ========== */
#main-content { 
    padding: 40px 50px !important; 
    background: 
        repeating-linear-gradient(
            90deg,
            transparent,
            transparent 60px,
            rgba(59, 130, 246, 0.12) 60px,
            rgba(59, 130, 246, 0.12) 61px
        ),
        repeating-linear-gradient(
            0deg,
            transparent,
            transparent 60px,
            rgba(59, 130, 246, 0.12) 60px,
            rgba(59, 130, 246, 0.12) 61px
        ),
        linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 50%, #cffafe 100%) !important;
    min-height: 100vh;
    position: relative;
}

/* 装饰性圆圈 */
#main-content::before {
    content: '';
    position: absolute;
    top: 10%;
    right: 5%;
    width: 300px;
    height: 300px;
    background: radial-gradient(circle, rgba(59, 130, 246, 0.08) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
}

#main-content::after {
    content: '';
    position: absolute;
    bottom: 15%;
    left: 10%;
    width: 200px;
    height: 200px;
    background: radial-gradient(circle, rgba(6, 182, 212, 0.08) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
}

/* 标题区域 */
#app-header { 
    text-align: center; 
    margin-bottom: 35px;
    position: relative;
    z-index: 1;
}

#app-title {
    font-size: 52px;
    font-weight: 900;
    letter-spacing: 6px;
    margin-bottom: 8px;
    display: inline-block;
    text-shadow: 2px 2px 4px rgba(59, 130, 246, 0.2);
}

.title-char {
    display: inline-block;
    transition: all 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

.title-char:nth-child(1) { color: #2563eb; }
.title-char:nth-child(2) { color: #059669; }
.title-char:nth-child(3) { color: #1e40af; }
.title-char:nth-child(4) { color: #0891b2; }
.title-char:nth-child(5) { color: #3b82f6; }
.title-char:nth-child(6) { color: #06b6d4; }
.title-char:nth-child(7) { color: #1d4ed8; }

.title-char:hover {
    transform: translateY(-12px) scale(1.2) rotate(0deg) !important;
    text-shadow: 0 20px 40px currentColor;
}

#app-subtitle { 
    font-size: 16px !important; 
    color: #475569 !important; 
    margin-top: 15px !important; 
    letter-spacing: 2px;
}

/* 实时数据卡片 */
.data-cards-container {
    display: flex;
    gap: 20px;
    margin-bottom: 30px;
    flex-wrap: wrap;
    position: relative;
    z-index: 1;
}

.data-card {
    background: rgba(255, 255, 255, 0.85);
    border: 1px solid rgba(59, 130, 246, 0.2);
    border-radius: 16px;
    padding: 20px;
    flex: 1;
    min-width: 300px;
    box-shadow: 0 0 30px rgba(59, 130, 246, 0.15);
    backdrop-filter: blur(10px);
    transition: all 0.3s ease;
}

.data-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 0 40px rgba(59, 130, 246, 0.25);
}

.data-card-header h3 {
    color: #3b82f6;
    margin: 0;
    font-size: 18px;
    font-weight: 600;
}

.data-card-content {
    margin-top: 15px;
}

/* 水平布局的数据卡片内容 */
.data-card-content-horizontal {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 20px;
    margin-top: 15px;
}

.data-info {
    flex: 1;
}

/* K线图样式 */
.k-line-chart {
    flex: 1;
    min-width: 300px;
}

.chart-title {
    font-size: 12px;
    font-weight: 600;
    color: #3b82f6;
    margin-bottom: 8px;
    text-align: center;
}

.k-line-container {
    background: linear-gradient(to top, #e0f2fe 0%, #bae6fd 100%);
    border-radius: 6px;
    padding: 10px;
    display: flex;
    justify-content: center;
    align-items: center;
}

.data-value {
    font-size: 32px;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 10px;
}

.data-change {
    font-size: 24px;
    font-weight: 600;
    margin-bottom: 15px;
}

.data-change.up {
    color: #10b981;
}

.data-change.down {
    color: #ef4444;
}

.data-detail {
    font-size: 14px;
    color: #64748b;
    margin-bottom: 5px;
}

/* 聊天框容器 */
#chatbot {
    background: rgba(255, 255, 255, 0.75) !important;
    border: 1px solid rgba(59, 130, 246, 0.15) !important;
    border-radius: 24px !important;
    padding: 25px !important;
    backdrop-filter: blur(15px) !important;
    box-shadow: 0 10px 40px rgba(59, 130, 246, 0.1) !important;
    position: relative;
    z-index: 1;
}

/* 用户消息气泡 */
#chatbot .user {
    background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%) !important;
    border: none !important;
    border-radius: 20px 20px 4px 20px !important;
    color: #ffffff !important;
    padding: 16px 22px !important;
    box-shadow: 0 6px 20px rgba(59, 130, 246, 0.35) !important;
}

/* AI回答气泡 */
#chatbot .bot {
    background: linear-gradient(135deg, #ffffff 0%, #f0f9ff 100%) !important;
    border: 1px solid rgba(59, 130, 246, 0.12) !important;
    border-radius: 20px 20px 20px 4px !important;
    color: #1e293b !important;
    padding: 18px 22px !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.06) !important;
}

/* 建议按钮 */
.suggestion-btn { 
    background: rgba(255, 255, 255, 0.8) !important;
    border: 1px solid rgba(59, 130, 246, 0.2) !important;
    padding: 12px 24px !important;
    border-radius: 25px !important;
    color: #3b82f6 !important;
    font-size: 14px !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 2px 10px rgba(59, 130, 246, 0.1) !important;
}

.suggestion-btn:hover { 
    background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%) !important;
    border-color: transparent !important;
    color: #ffffff !important;
    transform: translateY(-3px) !important;
    box-shadow: 0 8px 25px rgba(59, 130, 246, 0.35) !important;
}

/* 输入框区域 */
#input-container { 
    background: rgba(255, 255, 255, 0.9) !important;
    border: 2px solid rgba(59, 130, 246, 0.2) !important;
    border-radius: 30px !important;
    padding: 10px 10px 10px 25px !important;
    display: flex !important;
    align-items: center !important;
    backdrop-filter: blur(10px);
    box-shadow: 0 4px 20px rgba(59, 130, 246, 0.1) !important;
    transition: all 0.3s ease;
    position: relative;
    z-index: 1;
}

#input-container:focus-within {
    border-color: #3b82f6 !important;
    box-shadow: 
        0 0 0 4px rgba(59, 130, 246, 0.15),
        0 4px 20px rgba(59, 130, 246, 0.2) !important;
}

/* 输入框文本 */
#input-container input, #input-container textarea {
    background: transparent !important;
    border: none !important;
    color: #1e293b !important;
    font-size: 16px !important;
}

#input-container input::placeholder, #input-container textarea::placeholder {
    color: #94a3b8 !important;
}

/* 发送按钮 */
.gradio-button-primary { 
    background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 50% !important;
    width: 48px !important;
    height: 48px !important;
    font-size: 20px !important;
    box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4) !important;
    transition: all 0.3s ease !important;
}

.gradio-button-primary:hover { 
    transform: scale(1.1) rotate(15deg) !important;
    box-shadow: 0 8px 30px rgba(59, 130, 246, 0.5) !important;
}

/* 清除按钮 */
.gradio-button {
    background: rgba(255, 255, 255, 0.8) !important;
    border: 1px solid rgba(239, 68, 68, 0.3) !important;
    color: #ef4444 !important;
    transition: all 0.3s ease !important;
}

.gradio-button:hover {
    background: #ef4444 !important;
    color: white !important;
    transform: scale(1.05) !important;
}

/* 滚动条美化 */
::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.5);
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, #3b82f6, #06b6d4);
    border-radius: 4px;
}

/* 可滚动的折叠面板容器 */
.scrollable-accordion {
    /* 创建一个新的滚动容器，确保滚动条可见 */
    position: relative;
    max-height: 220px;
    overflow: hidden;
    border: 1px solid rgba(59, 130, 246, 0.2);
    border-radius: 8px;
}

/* 直接在折叠面板内部创建滚动容器 */
.scrollable-accordion .gradio-accordion-content {
    /* 关键修复：使用固定高度，确保一次只显示4个按钮 */
    height: 140px !important;
    /* 强制显示滚动条 */
    overflow-y: scroll !important;
    /* 确保滚动条始终可见，无论内容是否溢出 */
    overflow-x: hidden !important;
    /* 添加内边距，避免内容与滚动条重叠 */
    padding: 8px 12px 8px 8px !important;
    /* 重要：使用flex布局，确保按钮垂直排列 */
    display: flex !important;
    flex-direction: column !important;
    gap: 4px !important;
}

/* 重置Gradio默认样式 */
.scrollable-accordion .gradio-accordion-content > .w-full {
    /* 确保所有按钮都占满宽度 */
    width: 100% !important;
    margin: 0 !important;
}

/* 强制显示滚动条 - Webkit浏览器 */
.scrollable-accordion .gradio-accordion-content::-webkit-scrollbar {
    /* 设置滚动条宽度 */
    width: 12px !important;
    /* 确保滚动条始终可见 */
    -webkit-appearance: scrollbar !important;
}

/* 滚动条轨道样式 */
.scrollable-accordion .gradio-accordion-content::-webkit-scrollbar-track {
    /* 浅色背景，增加对比度 */
    background: linear-gradient(to right, rgba(255, 255, 255, 0.8), rgba(255, 255, 255, 0.8)) !important;
    /* 圆形轨道 */
    border-radius: 10px !important;
    /* 轻微阴影 */
    box-shadow: inset 0 0 5px rgba(0, 0, 0, 0.1) !important;
}

/* 滚动条滑块样式 */
.scrollable-accordion .gradio-accordion-content::-webkit-scrollbar-thumb {
    /* 渐变颜色，增加可见度 */
    background: linear-gradient(to bottom, #3b82f6, #06b6d4) !important;
    /* 圆形滑块 */
    border-radius: 10px !important;
    /* 阴影效果 */
    box-shadow: 0 2px 10px rgba(59, 130, 246, 0.5) !important;
    /* 边框 */
    border: 2px solid rgba(255, 255, 255, 0.9) !important;
}

/* 滚动条悬停效果 */
.scrollable-accordion .gradio-accordion-content::-webkit-scrollbar-thumb:hover {
    /* 深色渐变 */
    background: linear-gradient(to bottom, #2563eb, #0891b2) !important;
    /* 放大效果 */
    transform: scale(1.1) !important;
    /* 更强阴影 */
    box-shadow: 0 4px 15px rgba(59, 130, 246, 0.6) !important;
}

/* 强制显示滚动条 - Firefox */
.scrollable-accordion .gradio-accordion-content {
    /* Firefox滚动条宽度 */
    scrollbar-width: 12px !important;
    /* Firefox滚动条颜色 */
    scrollbar-color: #3b82f6 rgba(255, 255, 255, 0.8) !important;
}

/* 确保按钮样式不会影响滚动区域 */
.scrollable-accordion .sidebar-btn {
    margin: 0 !important; /* 重置margin */
    padding: 6px 10px !important; /* 调整按钮内边距，确保合适的高度 */
    font-size: 11px !important; /* 调整字体大小 */
    line-height: 1.2 !important; /* 调整行高 */
    min-height: 30px !important; /* 确保按钮有足够的高度 */
    width: 100% !important; /* 确保按钮占满宽度 */
    box-sizing: border-box !important; /* 确保内边距不影响总宽度 */
}

/* 图表样式 */
.chart-placeholder {
    margin-top: 15px;
    background: rgba(255, 255, 255, 0.7);
    border-radius: 8px;
    padding: 10px;
    border: 1px solid rgba(59, 130, 246, 0.2);
}

.chart-title {
    font-size: 12px;
    font-weight: 600;
    color: #3b82f6;
    margin-bottom: 8px;
    text-align: center;
}

.chart-bar-container {
    display: flex;
    align-items: flex-end;
    justify-content: space-around;
    height: 80px;
    background: linear-gradient(to top, #e0f2fe 0%, #bae6fd 100%);
    border-radius: 6px;
    padding: 5px;
    margin-bottom: 5px;
}

.chart-bar {
    flex: 1;
    margin: 0 2px;
    background: linear-gradient(to top, #3b82f6 0%, #06b6d4 100%);
    border-radius: 4px 4px 0 0;
    transition: height 0.5s ease;
    max-width: 20px;
}

.chart-labels {
    display: flex;
    justify-content: space-around;
    font-size: 10px;
    color: #64748b;
}
"""

# 预测函数
def predict(query, history, session_id):
    """Gradio 的核心预测函数"""
    if session_id not in session_histories:
        session_histories[session_id] = []
    
    messages = session_histories[session_id]
    messages.append({'role': 'user', 'content': query})
    
    try:
        logger.info(f"\n{'='*80}")
        logger.info(f"📝 收到用户查询: {query}")
        logger.info(f"{'='*80}")
        
        # 生成回答
        # 尝试多种企业名称匹配
        enterprise_names = [
            "北京航天长峰股份有限公司2025 年半年度报告",
            "北京航天长峰2025年半年度报告",
            "beijing_hangtian_2025",
            "航天长峰"
        ]
        
        answer = None
        reranked_results = []
        last_error = None
        
        # 尝试不同的企业名称，直到找到可用的知识库
        for enterprise_name in enterprise_names:
            try:
                logger.info(f"🔍 尝试企业名称: {enterprise_name}")
                answer, reranked_results = rag_pipeline.generate_answer(query, enterprise_name)
                
                # 检查是否获取到了有效回答
                if answer:
                    # 检查是否是错误消息
                    if "未找到该企业的知识库" not in answer and "抱歉" not in answer and "出错" not in answer:
                        logger.info(f"✅ 成功获取回答（使用企业名称: {enterprise_name}）")
                        break
                    else:
                        logger.warning(f"⚠️  回答包含错误信息: {answer[:100]}...")
                        last_error = answer
                else:
                    logger.warning(f"⚠️  未获取到回答")
            except Exception as e:
                error_msg = f"使用企业名称 {enterprise_name} 生成回答失败: {str(e)}"
                logger.error(f"❌ {error_msg}")
                last_error = error_msg
                import traceback
                logger.error(traceback.format_exc())
                continue
        
        # 如果没有获取到有效回答
        if not answer or "未找到该企业的知识库" in answer or ("抱歉" in answer and "暂时无法生成回答" in answer):
            if last_error:
                answer = f"抱歉，暂时无法生成回答。\n错误信息: {last_error}"
            else:
                answer = "抱歉，暂时无法生成回答，请稍后重试。"
        
        logger.info(f"✅ 最终回答长度: {len(answer)} 字符")
        logger.info(f"✅ 参考来源数量: {len(reranked_results)} 个")
        # 构建回答内容，只包含答案和来源信息
        full_answer = f"{answer}\n\n" + \
                      f"📎 参考来源:\n" + \
                      f"- 企业年报知识库\n" + \
                      f"- 实时网络搜索（Tavily）\n" + \
                      f"- 实时行情数据"

        messages.append({'role': 'assistant', 'content': full_answer})
        session_histories[session_id] = messages
        # 确保history格式正确
        if not history or len(history) == 0:
            history = [[query, full_answer]]
        else:
            # 确保最后一个元素是列表
            if not isinstance(history[-1], list) or len(history[-1]) < 2:
                history.append([query, full_answer])
            else:
                history[-1][1] = full_answer
        logger.info(f"✅ 回答已返回给用户")
        return history
    except Exception as e:
        error_msg = f"生成回答失败: {str(e)}"
        logger.error(f"❌ {error_msg}")
        import traceback
        logger.error(traceback.format_exc())
        # 安全地设置错误消息
        error_answer = f"抱歉，生成回答时出错: {str(e)}"
        if not history or len(history) == 0:
            history = [[query, error_answer]]
        else:
            if not isinstance(history[-1], list) or len(history[-1]) < 2:
                history.append([query, error_answer])
            else:
                history[-1][1] = error_answer
        return history

# 清除历史
def clear_history():
    """清除聊天历史"""
    return []
# 响应函数- 移除不必要的theme参数
with gr.Blocks(css=custom_css) as demo:
    session_id = gr.State(str(time.time()))
    with gr.Row():
        # 左侧导航栏
        with gr.Column(scale=2, elem_id="sidebar"):
            gr.HTML('''
                <div class="logo-container">
                    <div class="logo-icon">
                        <svg viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
                    </div>
                    <div class="logo-title">企业投资</div>
                    <div class="logo-subtitle">ENTERPRISE INVESTMENT SYSTEM</div>
                </div>
            ''')

            with gr.Accordion("📎 年报知识库(共8份)", open=True, elem_classes="scrollable-accordion"):
                gr.Button(" 北京航天长峰股份有限公司2025 年半年度报告", elem_classes=["sidebar-btn", "active"])
                gr.Button(" 北京航天长峰2025年半年度报告", elem_classes="sidebar-btn")
                gr.Button(" 北京航天长峰2024年年度报告", elem_classes="sidebar-btn")
                gr.Button(" 北京航天长峰2023年年度报告", elem_classes="sidebar-btn")
                gr.Button(" 北京航天长峰2022年年度报告", elem_classes="sidebar-btn")
                gr.Button(" 北京航天长峰2021年年度报告", elem_classes="sidebar-btn")
            with gr.Accordion("📝 专利知识库(共14份PDF)", open=True, elem_classes="scrollable-accordion"):
                gr.Button(" 一种车载综合器组件和体外诊断综合联线", elem_classes="sidebar-btn")
                gr.Button(" 一种综合器及体外诊断综合装置", elem_classes="sidebar-btn")
                gr.Button(" 一种气体混合装置", elem_classes="sidebar-btn")
                gr.Button(" 一种高效型体外循环系统", elem_classes="sidebar-btn")
                gr.Button(" 一种防护型体外循环系统", elem_classes="sidebar-btn")
                gr.Button(" 一种防反流血泵及其控制系统和应用", elem_classes="sidebar-btn")
                gr.Button(" 一种电子式体外膜肺氧合器组件及其二氧化碳清除率的检测方法", elem_classes="sidebar-btn")
                gr.Button(" 一种箱式综合器排水装置及安装方法", elem_classes="sidebar-btn")
            with gr.Accordion("🔍 快速查询", open=True):
                dividend_btn = gr.Button("股息情况", elem_classes="sidebar-btn")
                profit_btn = gr.Button("盈亏情况", elem_classes="sidebar-btn")
                inventor_btn = gr.Button("专利发明人", elem_classes="sidebar-btn")
                patent_date_btn = gr.Button("专利授权时间", elem_classes="sidebar-btn")
            setting_btn = gr.Button("⚙️ 设置", elem_classes="sidebar-btn")
        # 右侧主内容区
        with gr.Column(scale=8, elem_id="main-content"):
            gr.HTML('''
                <div id="app-header">
                    <h1 id="app-title">
                        <span class="title-char">企</span>
                        <span class="title-char">业</span>
                        <span class="title-char">投</span>
                        <span class="title-char">资</span>
                        <span class="title-char">分</span>
                        <span class="title-char">析</span>
                        <span class="title-char">系</span>
                        <span class="title-char">统</span>
                    </h1>
                    <p id="app-subtitle">融合本地知识仓库 + 实时网络搜索 + 实时行情数据</p>
                </div>
            ''')

            # 实时数据卡片 - 添加数据名称以便后续更新
            real_time_html = gr.HTML(generate_real_time_cards(), elem_id="real-time-data")
            # 聊天区域
            chatbot = gr.Chatbot(elem_id="chatbot", bubble_full_width=False, height=500)
            # 建议问题
            with gr.Row(elem_id="suggestion-row") as suggestion_row:
                suggestions = [
                    '📈 北京航天长峰2025年上半年的营业收入是多少？',
                    '📊 北京航天长峰2025年上半年净利润同比变化情况？',
                    '🔬 一种防护型体外循环系统专利的具体内容是什么？'
                ]
                suggestion_btns = []
                for s in suggestions:
                    btn = gr.Button(s, elem_classes="suggestion-btn")
                    suggestion_btns.append(btn)
            # 输入区域
            with gr.Row(elem_id="input-container-wrapper"):
                with gr.Row(elem_id="input-container"):
                    textbox = gr.Textbox(
                        container=False,
                        show_label=False,
                        placeholder="💡 输入你的问题，让 AI 为你解答...",
                        scale=10
                    )
                    submit_btn = gr.Button("🚀", scale=1, min_width=0, variant="primary")
                    clear_btn = gr.Button("🧹", scale=1, min_width=0)
    # 事件处理
    def on_submit(query, history):
        history.append([query, None])
        return "", history

    def on_suggestion_click(suggestion, history):
        history.append([suggestion, None])
        return "", history, gr.update(visible=False)

    # 侧边栏按钮点击处理函数
    def on_sidebar_button_click(button_text, history):
        """处理侧边栏按钮点击事件，确保完整触发预测流程"""
        # 根据按钮文本生成对应的查询
        query_map = {
            "股息情况": "北京航天长峰2024年的股息情况如何？",
            "盈亏情况": "北京航天长峰2024年的盈亏情况是多少？",
            "专利发明人": "北京航天长峰专利的发明人是谁？",
            "专利授权时间": "北京航天长峰专利的授权时间是什么时候？"
        }

        query = query_map.get(button_text, f"{button_text} 的相关信息")
        history.append([query, None])
        return "", history

    submit_event = textbox.submit(on_submit, [textbox, chatbot], [textbox, chatbot], queue=False)
    submit_event.then(lambda: gr.update(visible=False), None, suggestion_row)
    submit_event.then(predict, [textbox, chatbot, session_id], chatbot)
    click_event = submit_btn.click(on_submit, [textbox, chatbot], [textbox, chatbot], queue=False)
    click_event.then(lambda: gr.update(visible=False), None, suggestion_row)
    click_event.then(predict, [textbox, chatbot, session_id], chatbot)
    clear_btn.click(clear_history, [], chatbot)
    # 侧边栏按钮事件绑定
    def bind_sidebar_button(btn):
        """绑定侧边栏按钮点击事件，确保完整触发预测流程"""
        # 绑定点击事件，先添加问题到历史
        btn_click_event = btn.click(on_sidebar_button_click, [btn, chatbot], [textbox, chatbot], queue=False)
        # 然后隐藏建议栏
        btn_click_event.then(lambda: gr.update(visible=False), None, suggestion_row)
        # 最后调用预测函数生成回答
        btn_click_event.then(predict, [textbox, chatbot, session_id], chatbot)
    # 绑定快速查询按钮
    bind_sidebar_button(dividend_btn)
    bind_sidebar_button(profit_btn)
    bind_sidebar_button(inventor_btn)
    bind_sidebar_button(patent_date_btn)
    for btn in suggestion_btns:
        s_click_event = btn.click(on_suggestion_click, [btn, chatbot], [textbox, chatbot, suggestion_row], queue=False)
        s_click_event.then(predict, [btn, chatbot, session_id], chatbot)
    # 添加定时更新事件 - 每分钟更新一次实时数据
    def update_data():
        """更新实时数据"""
        return generate_real_time_cards()
    # 使用Gradio的API实现定时更新
    # 每60秒更新一次
    demo.load(update_data, None, real_time_html)
    # 添加一个隐藏的按钮来触发更新
    update_btn = gr.Button(visible=False)
    # 点击事件触发更新
    update_btn.click(update_data, None, real_time_html)
    # 使用JavaScript实现自动点击
    demo.load(None, None, None, js="""
        function autoUpdate() {
            setInterval(() => {
                const updateBtn = document.querySelector('.gradio-button:contains("Update")');
                if (updateBtn) {
                    updateBtn.click();
                }
            }, 60000);
        }
        autoUpdate();
    """)

# 启动应用
logger.info("=" * 80)
logger.info("🚀 启动Gradio应用...")
logger.info(f"📝 日志文件保存于: {log_file}")
logger.info("🔧 测试使用端口7863启动应用")
logger.info("=" * 80)

# 配置Gradio启动设置，并使用默认端口
demo.launch(
    share=False,
    server_name="127.0.0.1",
    quiet=False
)