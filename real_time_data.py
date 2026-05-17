import sys
import os
import time
# 添加自定义库路径
sys.path.append('E:\pythonLib\site-packages')

import easyquotation
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# 导入 InvestingKlineSpider
from investing_kline_spider import InvestingKlineSpider
import akshare as ak  # 保留akshare，用于历史数据和其他功能

class RealTimeDataService:
    def __init__(self):
        """初始化实时数据服务"""
        print("✅ 初始化RealTimeDataService")
        # 初始化easyquotation客户端
        self.quotation = easyquotation.use('sina')  # 使用新浪数据源
        print("✅ 初始化easyquotation客户端")
        # 初始化InvestingKlineSpider
        self.kline_spider = InvestingKlineSpider()
        print("✅ 初始化InvestingKlineSpider")
        
    def get_sh_index_real_time(self) -> Optional[Dict[str, Any]]:
        """获取上证指数实时行情
        
        Returns:
            上证指数实时数据字典
        """
        try:
            # 优先使用easyquotation获取上证指数实时数据
            result = self.quotation.stocks(['sh000001'])
            
            # 检查返回结果中是否包含 '000001' 或 'sh000001'
            if '000001' in result:
                sh_data = result['000001']
            elif 'sh000001' in result:
                sh_data = result['sh000001']
            else:
                # easyquotation获取失败，尝试使用akshare作为备用
                print("⚠️  easyquotation获取上证指数失败，尝试使用akshare")
                return self._get_sh_index_real_time_akshare()
            
            # 计算涨跌幅和涨跌额
            change_amount = sh_data['now'] - sh_data['close']
            change_percent = (change_amount / sh_data['close']) * 100
            
            return {
                "代码": 'sh000001',
                "名称": sh_data['name'],
                "最新价": float(sh_data['now']),
                "涨跌幅": float(change_percent),
                "涨跌额": float(change_amount),
                "成交量": float(sh_data['volume']),
                "成交额": float(sh_data['turnover']),
                "最高价": float(sh_data['high']),
                "最低价": float(sh_data['low']),
                "今开": float(sh_data['open']),
                "昨收": float(sh_data['close']),
                "更新时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            print(f"❌ 使用easyquotation获取上证指数实时数据失败: {str(e)}")
            # 尝试使用akshare作为备用
            return self._get_sh_index_real_time_akshare()
    
    def _get_sh_index_real_time_akshare(self) -> Optional[Dict[str, Any]]:
        """使用akshare获取上证指数实时数据（备用方法）"""
        try:
            # 使用akshare获取上证指数实时数据
            stock_data = ak.stock_zh_index_spot_em()
            sh_info = stock_data[stock_data['代码'] == 'sh000001']
            
            if not sh_info.empty:
                sh_info = sh_info.iloc[0]
                return {
                    "代码": sh_info['代码'],
                    "名称": sh_info['名称'],
                    "最新价": float(sh_info['最新价']),
                    "涨跌幅": float(sh_info['涨跌幅']),
                    "涨跌额": float(sh_info['涨跌额']),
                    "成交量": float(sh_info['成交量']),
                    "成交额": float(sh_info['成交额']),
                    "最高价": float(sh_info['最高价']),
                    "最低价": float(sh_info['最低价']),
                    "今开": float(sh_info['今开']),
                    "昨收": float(sh_info['昨收']),
                    "更新时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            return None
        except Exception as e:
            print(f"❌ 使用akshare获取上证指数实时数据失败: {str(e)}")
            return None
    
    def get_stock_real_time(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """获取个股实时行情
        
        Args:
            stock_code: 股票代码，如 "600855"
            
        Returns:
            个股实时数据字典
        """
        try:
            # 为股票代码添加市场前缀
            if stock_code.startswith('60'):
                full_code = f'sh{stock_code}'
            elif stock_code.startswith('00') or stock_code.startswith('30'):
                full_code = f'sz{stock_code}'
            else:
                full_code = stock_code
            
            # 优先使用easyquotation获取个股实时数据
            result = self.quotation.stocks([full_code])
            
            # 检查返回结果中是否包含股票代码（带前缀或不带前缀）
            if stock_code in result:
                stock_data = result[stock_code]
            elif full_code in result:
                stock_data = result[full_code]
            else:
                # easyquotation获取失败，尝试使用akshare作为备用
                print(f"⚠️  easyquotation获取股票 {stock_code} 失败，尝试使用akshare")
                return self._get_stock_real_time_akshare(stock_code)
            
            # 计算涨跌幅和涨跌额
            change_amount = stock_data['now'] - stock_data['close']
            change_percent = (change_amount / stock_data['close']) * 100
            
            return {
                "代码": stock_code,
                "名称": stock_data['name'],
                "最新价": float(stock_data['now']),
                "涨跌幅": float(change_percent),
                "涨跌额": float(change_amount),
                "成交量": float(stock_data['volume']),
                "成交额": float(stock_data['turnover']),
                "最高价": float(stock_data['high']),
                "最低价": float(stock_data['low']),
                "今开": float(stock_data['open']),
                "昨收": float(stock_data['close']),
                "更新时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            print(f"❌ 使用easyquotation获取股票 {stock_code} 实时数据失败: {str(e)}")
            # 尝试使用akshare作为备用
            return self._get_stock_real_time_akshare(stock_code)
    
    def _get_stock_real_time_akshare(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """使用akshare获取个股实时数据（备用方法）"""
        try:
            # 使用akshare的个股实时行情接口
            stock_data = ak.stock_zh_a_spot_em()
            stock_info = stock_data[stock_data['代码'] == stock_code]
            
            if not stock_info.empty:
                stock_info = stock_info.iloc[0]
                return {
                    "代码": stock_info['代码'],
                    "名称": stock_info['名称'],
                    "最新价": float(stock_info['最新价']),
                    "涨跌幅": float(stock_info['涨跌幅']),
                    "涨跌额": float(stock_info['涨跌额']),
                    "成交量": float(stock_info['成交量']),
                    "成交额": float(stock_info['成交额']),
                    "最高价": float(stock_info['最高价']),
                    "最低价": float(stock_info['最低价']),
                    "今开": float(stock_info['今开']),
                    "昨收": float(stock_info['昨收']),
                    "涨停价": float(stock_info['涨停价']),
                    "跌停价": float(stock_info['跌停价']),
                    "更新时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            return None
        except Exception as e:
            print(f"❌ 使用akshare获取股票 {stock_code} 实时数据失败: {str(e)}")
            return None
    
    def get_historical_data(self, stock_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """获取股票历史K线数据
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期，格式 "YYYYMMDD"
            end_date: 结束日期，格式 "YYYYMMDD"
            
        Returns:
            历史K线数据DataFrame
        """
        try:
            # 获取历史K线数据
            historical_data = ak.stock_zh_a_daily_k(stock_code, adjust="qfq")
            
            # 转换日期格式
            historical_data['date'] = pd.to_datetime(historical_data['date'])
            historical_data['date_str'] = historical_data['date'].dt.strftime("%Y%m%d")
            
            # 筛选日期范围
            filtered_data = historical_data[(historical_data['date_str'] >= start_date) & 
                                           (historical_data['date_str'] <= end_date)]
            
            if not filtered_data.empty:
                return filtered_data
            return None
        except Exception as e:
            print(f"❌ 获取股票 {stock_code} 历史数据失败: {str(e)}")
            return None
    
    def calculate_dividend_yield(self, stock_code: str, dividend_per_share: float, date: str = None) -> Optional[Dict[str, Any]]:
        """计算股息率
        
        Args:
            stock_code: 股票代码
            dividend_per_share: 每股分红金额
            date: 计算日期，格式 "YYYYMMDD"，默认最近一个交易日
            
        Returns:
            股息率计算结果字典
        """
        try:
            if not date:
                # 获取最近一个交易日的收盘价
                real_time_data = self.get_stock_real_time(stock_code)
                if not real_time_data:
                    return None
                closing_price = real_time_data['最新价']
            else:
                # 获取指定日期的收盘价
                historical_data = self.get_historical_data(stock_code, date, date)
                if not historical_data or historical_data.empty:
                    return None
                closing_price = historical_data.iloc[0]['close']
            
            # 计算股息率
            dividend_yield = (dividend_per_share / closing_price) * 100
            
            return {
                "股票代码": stock_code,
                "每股分红": dividend_per_share,
                "收盘价": closing_price,
                "股息率": round(dividend_yield, 2),
                "计算日期": datetime.now().strftime("%Y-%m-%d") if not date else date
            }
        except Exception as e:
            print(f"❌ 计算股息率失败: {str(e)}")
            return None
    
    def get_industry_average(self, industry_name: str, indicator: str) -> Optional[float]:
        """获取行业平均水平
        
        Args:
            industry_name: 行业名称
            indicator: 指标名称，如 "市盈率", "市净率", "股息率"
            
        Returns:
            行业平均水平值
        """
        try:
            # 获取行业指数列表
            industry_index = ak.stock_board_industry_name_em()
            
            # 查找指定行业
            industry_data = industry_index[industry_index['板块名称'].str.contains(industry_name)]
            
            if not industry_data.empty:
                # 这里简化处理，实际应该获取行业内所有股票的指标并计算平均值
                print(f"⚠️  行业平均水平功能待完善，当前返回模拟数据")
                # 模拟返回行业平均数据
                mock_data = {
                    "市盈率": 25.5,
                    "市净率": 3.2,
                    "股息率": 2.8
                }
                return mock_data.get(indicator, 0.0)
            return None
        except Exception as e:
            print(f"❌ 获取行业平均水平失败: {str(e)}")
            return None
    
    def get_sector_index_real_time(self, sector_name: str) -> Optional[Dict[str, Any]]:
        """获取板块指数实时行情
        
        Args:
            sector_name: 板块名称，如 "军工", "电子"
            
        Returns:
            板块指数实时数据字典
        """
        try:
            # 获取板块指数列表
            sector_index = ak.stock_board_industry_name_em()
            
            # 查找指定板块
            sector_data = sector_index[sector_index['板块名称'].str.contains(sector_name)]
            
            if not sector_data.empty:
                sector_code = sector_data.iloc[0]['板块代码']
                # 获取板块指数实时行情
                sector_spot = ak.stock_zh_a_spot_em()
                sector_real_time = sector_spot[sector_spot['代码'] == sector_code]
                
                if not sector_real_time.empty:
                    sector_info = sector_real_time.iloc[0]
                    return {
                        "代码": sector_info['代码'],
                        "名称": sector_info['名称'],
                        "最新价": float(sector_info['最新价']),
                        "涨跌幅": float(sector_info['涨跌幅']),
                        "涨跌额": float(sector_info['涨跌额']),
                        "成交量": float(sector_info['成交量']),
                        "成交额": float(sector_info['成交额']),
                        "更新时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
            return None
        except Exception as e:
            print(f"❌ 获取板块指数实时数据失败: {str(e)}")
            return None
    
    def analyze_performance_market_correlation(self, stock_code: str, report_year: str, net_profit_change: float) -> Optional[Dict[str, Any]]:
        """业绩-行情联动分析
        
        Args:
            stock_code: 股票代码
            report_year: 报告年份，如 "2024"
            net_profit_change: 净利润变动百分比，如 -15.94
            
        Returns:
            业绩-行情联动分析结果字典
        """
        try:
            # 计算报告发布日期前后的股价走势
            # 简化处理：假设报告发布日期为次年3月31日
            report_date = f"{int(report_year) + 1}0331"
            # 获取报告发布前30天和后30天的日期
            report_date_dt = datetime.strptime(report_date, "%Y%m%d")
            start_date_dt = report_date_dt - timedelta(days=30)
            end_date_dt = report_date_dt + timedelta(days=30)
            start_date = start_date_dt.strftime("%Y%m%d")
            end_date = end_date_dt.strftime("%Y%m%d")
            
            # 获取股价走势数据
            stock_data = self.get_historical_data(stock_code, start_date, end_date)
            if not stock_data:
                return None
            
            # 计算报告发布前后的股价变动
            # 找到报告发布日的索引
            report_idx = stock_data[stock_data['date_str'] == report_date].index
            if not report_idx.empty:
                report_idx = report_idx[0]
                pre_report_close = stock_data.iloc[report_idx]['close']
                post_report_close = stock_data.iloc[-1]['close']
                price_change = ((post_report_close - pre_report_close) / pre_report_close) * 100
                
                return {
                    "股票代码": stock_code,
                    "报告年份": report_year,
                    "净利润变动": net_profit_change,
                    "报告发布日期": report_date,
                    "分析期间": f"{start_date} 至 {end_date}",
                    "报告前收盘价": round(pre_report_close, 2),
                    "报告后收盘价": round(post_report_close, 2),
                    "股价变动百分比": round(price_change, 2),
                    "联动分析": self._generate_correlation_analysis(net_profit_change, price_change),
                    "数据来源": "akshare"
                }
            return None
        except Exception as e:
            print(f"❌ 业绩-行情联动分析失败: {str(e)}")
            return None
    
    def _generate_correlation_analysis(self, profit_change: float, price_change: float) -> str:
        """生成联动分析文本
        
        Args:
            profit_change: 净利润变动百分比
            price_change: 股价变动百分比
            
        Returns:
            联动分析文本
        """
        if profit_change < 0 and price_change < 0:
            return "净利润下滑，股价同步下跌，市场反应符合预期。"
        elif profit_change < 0 and price_change > 0:
            return "净利润下滑，但股价上涨，市场可能预期公司未来业绩改善。"
        elif profit_change > 0 and price_change > 0:
            return "净利润增长，股价同步上涨，市场反应积极。"
        elif profit_change > 0 and price_change < 0:
            return "净利润增长，但股价下跌，市场可能对公司未来前景存在疑虑。"
        else:
            return "净利润和股价变动不明显，市场反应平稳。"
    
    def get_sh_index_kline_data(self, period: str = '1W') -> Optional[Dict[str, Any]]:
        """获取上证指数 K 线图数据（从 investing.com）
        
        Args:
            period: 时间周期，支持 '1D', '1W', '1M', '3M', '6M', '1Y', '5Y'
            
        Returns:
            K 线数据字典，包含日期、开盘价、最高价、最低价、收盘价、成交量
        """
        try:
            return self.kline_spider.get_sh_index_kline_data(period)
        except Exception as e:
            print(f"❌ 获取上证指数 K 线数据失败: {str(e)}")
            # 返回模拟数据作为备用
            return self._generate_mock_kline_data(period)
    
    def get_stock_kline_data(self, stock_code: str = '600855', period: str = '1D') -> Optional[Dict[str, Any]]:
        """获取股票 K 线图数据（从东方财富网）
        
        Args:
            stock_code: 股票代码
            period: 时间周期，支持 '1D', '1W', '1M', '3M', '6M', '1Y', '5Y'
            
        Returns:
            K 线数据字典，包含日期、开盘价、最高价、最低价、收盘价、成交量
        """
        try:
            return self.kline_spider.get_stock_kline_data(stock_code, period)
        except Exception as e:
            print(f"❌ 获取股票 {stock_code} K 线数据失败: {str(e)}")
            # 返回模拟数据作为备用
            return self._generate_mock_stock_kline_data(period)
    
    def _generate_mock_kline_data(self, period: str) -> Dict[str, Any]:
        """生成模拟 K 线数据（当无法从页面提取时使用）
        
        Args:
            period: 时间周期
            
        Returns:
            模拟 K 线数据字典
        """
        dates = []
        opens = []
        highs = []
        lows = []
        closes = []
        volumes = []
        
        # 生成过去 7 天的模拟数据
        base_price = 3200.0
        base_volume = 20000000000
        
        for i in range(7):
            date = (datetime.now() - timedelta(days=6-i)).strftime('%Y-%m-%d')
            dates.append(date)
            
            # 生成随机波动
            change = (i % 2 - 0.5) * 50 + i * 5
            open_price = base_price + change
            high_price = open_price + 20
            low_price = open_price - 20
            close_price = open_price + (i % 3 - 1) * 10
            volume = base_volume + i * 1000000000
            
            opens.append(round(open_price, 2))
            highs.append(round(high_price, 2))
            lows.append(round(low_price, 2))
            closes.append(round(close_price, 2))
            volumes.append(int(volume))
        
        return {
            'dates': dates,
            'opens': opens,
            'highs': highs,
            'lows': lows,
            'closes': closes,
            'volumes': volumes
        }
    
    def _generate_mock_stock_kline_data(self, period: str) -> Dict[str, Any]:
        """生成模拟股票 K 线数据（当无法从页面提取时使用）
        
        Args:
            period: 时间周期
            
        Returns:
            模拟 K 线数据字典
        """
        dates = []
        opens = []
        highs = []
        lows = []
        closes = []
        volumes = []
        
        # 生成当日分时模拟数据
        base_price = 20.03
        base_volume = 2096
        
        # 生成一天的分时数据（9:30 - 15:00）
        times = ['09:30', '10:00', '10:30', '11:00', '11:30', '13:30', '14:00', '14:30', '15:00']
        for i, time_str in enumerate(times):
            dates.append(time_str)
            
            # 生成随机波动
            change = (i % 3 - 1) * 0.1 + i * 0.01
            open_price = base_price + change
            high_price = open_price + 0.05
            low_price = open_price - 0.05
            close_price = open_price + (i % 2 - 0.5) * 0.05
            volume = base_volume + i * 100
            
            opens.append(round(open_price, 2))
            highs.append(round(high_price, 2))
            lows.append(round(low_price, 2))
            closes.append(round(close_price, 2))
            volumes.append(int(volume))
        
        return {
            'dates': dates,
            'opens': opens,
            'highs': highs,
            'lows': lows,
            'closes': closes,
            'volumes': volumes
        }