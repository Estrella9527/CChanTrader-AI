# >>> CChanTrader-AI Explain Patch
"""
股票推荐解释生成器
为选股结果生成自然语言说明，包含买卖点、止损止盈、选中原因、预期收益等
"""

from typing import List, Dict, Optional
import json

def generate_explain(selected: List[Dict], structure_dict: dict = None) -> List[Dict]:
    """
    根据选股结果生成自然语言解释
    
    Args:
        selected: 选股结果列表
        structure_dict: 结构分析数据字典（可选）
    
    Returns:
        包含详细解释的字典列表
    """
    results = []
    
    for stock in selected:
        try:
            # 提取基础数据
            symbol = stock.get('symbol', 'N/A')
            stock_name = stock.get('stock_name', '未知股票')
            entry_price = stock.get('entry_price', 0) or stock.get('current_price', 0)
            stop_loss = stock.get('stop_loss', 0)
            signal = stock.get('signal', 'unknown')
            confidence = stock.get('confidence', 'medium')
            total_score = stock.get('total_score', 0)
            tech_score = stock.get('tech_score', 0)
            auction_score = stock.get('auction_score', 0)
            auction_ratio = stock.get('auction_ratio', 0)
            market = stock.get('market', '未知市场')
            
            # 计算目标价格区间
            if entry_price > 0:
                if confidence == 'very_high':
                    target_low = round(entry_price * 1.15, 2)
                    target_high = round(entry_price * 1.25, 2)
                elif confidence == 'high':
                    target_low = round(entry_price * 1.10, 2)
                    target_high = round(entry_price * 1.18, 2)
                else:
                    target_low = round(entry_price * 1.06, 2)
                    target_high = round(entry_price * 1.12, 2)
            else:
                target_low = target_high = 0
            
            # 计算风险收益比
            if entry_price > 0 and stop_loss > 0 and entry_price > stop_loss:
                avg_target = (target_low + target_high) / 2
                expected_rr = round((avg_target - entry_price) / (entry_price - stop_loss), 2)
            else:
                expected_rr = '∞'
            
            # 生成信号解释
            signal_explanation = _generate_signal_explanation(signal, confidence, total_score)
            
            # 生成技术面解释
            tech_explanation = _generate_tech_explanation(tech_score, auction_score, auction_ratio)
            
            # 生成综合原因说明
            reason = _generate_comprehensive_reason(
                stock_name, market, signal, confidence, total_score, 
                auction_ratio, entry_price, stop_loss, target_low, target_high
            )
            
            # 生成买点说明
            buy_point_explanation = _generate_buy_point_explanation(
                signal, entry_price, auction_ratio, confidence
            )
            
            # 生成卖点逻辑
            sell_logic = _generate_sell_logic(signal, confidence, target_high, stop_loss)
            
            # 组装结果
            explanation_dict = {
                'symbol': symbol,
                'stock_name': stock_name,
                'reason': reason,
                'signal_explanation': signal_explanation,
                'tech_explanation': tech_explanation,
                'buy_point': entry_price,
                'buy_point_explanation': buy_point_explanation,
                'sell_logic': sell_logic,
                'stop_loss': stop_loss,
                'target_range': [target_low, target_high],
                'expected_rr': expected_rr,
                'confidence_level': confidence,
                'risk_reward_analysis': _generate_risk_reward_analysis(
                    entry_price, stop_loss, target_low, target_high, expected_rr
                )
            }
            
            results.append(explanation_dict)
            
        except Exception as e:
            # 异常处理，返回默认解释
            results.append(_generate_default_explanation(stock))
    
    return results

def _generate_signal_explanation(signal: str, confidence: str, total_score: float) -> str:
    """生成信号解释"""
    signal_map = {
        '1_buy': '一类买点：趋势反转信号，前期下跌结束，开始新的上涨趋势',
        '2_buy': '二类买点：中枢突破信号，价格突破重要阻力位，上涨动能强劲', 
        '3_buy': '三类买点：回踩确认信号，价格回调至支撑位后反弹，风险相对较低',
        'breakout': '突破信号：价格突破关键技术位，伴随放量确认',
        'reversal': '反转信号：技术指标显示超跌反弹，具备修复空间'
    }
    
    base_explanation = signal_map.get(signal, f'{signal}信号：技术形态良好，具备上涨潜力')
    
    confidence_text = {
        'very_high': '信心度极高，多项指标共振确认',
        'high': '信心度较高，技术面表现强势',
        'medium': '信心度中等，需要密切关注后续表现'
    }
    
    score_text = f"综合评分{total_score:.3f}" if total_score > 0 else "技术面评估良好"
    
    return f"{base_explanation}。{confidence_text.get(confidence, '')}，{score_text}。"

def _generate_tech_explanation(tech_score: float, auction_score: float, auction_ratio: float) -> str:
    """生成技术面解释"""
    tech_parts = []
    
    if tech_score > 0.7:
        tech_parts.append("技术指标强势")
    elif tech_score > 0.5:
        tech_parts.append("技术指标良好")
    else:
        tech_parts.append("技术指标一般")
    
    if auction_score > 0.7:
        tech_parts.append("竞价表现活跃")
    elif auction_score > 0.5:
        tech_parts.append("竞价表现稳定")
    
    if auction_ratio > 2:
        tech_parts.append(f"高开{auction_ratio:.1f}%显示资金热情")
    elif auction_ratio > 0:
        tech_parts.append(f"温和高开{auction_ratio:.1f}%")
    elif auction_ratio < -2:
        tech_parts.append(f"低开{auction_ratio:.1f}%存在压力")
    
    return "，".join(tech_parts) + "。"

def _generate_comprehensive_reason(stock_name: str, market: str, signal: str, confidence: str, 
                                 total_score: float, auction_ratio: float, entry_price: float,
                                 stop_loss: float, target_low: float, target_high: float) -> str:
    """生成综合推荐原因"""
    
    # 主要推荐理由
    main_reasons = []
    
    # 信号类型理由
    if signal in ['2_buy', '3_buy']:
        main_reasons.append(f"出现{signal}买点信号")
    else:
        main_reasons.append("技术形态良好")
    
    # 市场表现理由
    if auction_ratio > 2:
        main_reasons.append(f"竞价高开{auction_ratio:.1f}%显示资金关注")
    elif auction_ratio > 0:
        main_reasons.append("竞价表现平稳")
    
    # 评分理由
    if total_score > 0.8:
        main_reasons.append("综合评分优秀")
    elif total_score > 0.6:
        main_reasons.append("综合评分良好")
    
    # 信心度理由
    confidence_map = {
        'very_high': '多项指标共振确认',
        'high': '技术面强势表现',
        'medium': '具备上涨潜力'
    }
    main_reasons.append(confidence_map.get(confidence, '技术面支撑'))
    
    reason_text = f"{stock_name}({market})：" + "，".join(main_reasons)
    
    # 添加操作建议
    if entry_price > 0 and stop_loss > 0:
        reason_text += f"。建议{entry_price}元附近买入，止损{stop_loss}元"
        if target_low > 0 and target_high > 0:
            reason_text += f"，目标{target_low}-{target_high}元"
    
    return reason_text + "。"

def _generate_buy_point_explanation(signal: str, entry_price: float, auction_ratio: float, confidence: str) -> str:
    """生成买点说明"""
    buy_explanations = []
    
    # 基于信号类型的买点说明
    if signal == '2_buy':
        buy_explanations.append("等待价格突破中枢上沿时买入")
    elif signal == '3_buy':
        buy_explanations.append("回踩确认后反弹时买入")
    elif signal == '1_buy':
        buy_explanations.append("趋势反转确认后买入")
    else:
        buy_explanations.append("技术信号确认后买入")
    
    # 基于竞价表现的买点说明
    if auction_ratio > 3:
        buy_explanations.append("开盘大幅高开可适当追涨")
    elif auction_ratio > 1:
        buy_explanations.append("开盘高开可跟进")
    elif auction_ratio > -1:
        buy_explanations.append("平开后观察量能")
    else:
        buy_explanations.append("低开后等待企稳")
    
    # 基于信心度的买点说明
    if confidence == 'very_high':
        buy_explanations.append("可积极建仓")
    elif confidence == 'high':
        buy_explanations.append("可适度建仓")
    else:
        buy_explanations.append("建议轻仓试探")
    
    return "，".join(buy_explanations) + f"，参考价位{entry_price}元。"

def _generate_sell_logic(signal: str, confidence: str, target_price: float, stop_loss: float) -> str:
    """生成卖点逻辑"""
    sell_parts = []
    
    # 止盈逻辑
    if target_price > 0:
        sell_parts.append(f"价格达到{target_price}元附近时分批止盈")
    
    # 技术卖点
    if signal in ['2_buy', '3_buy']:
        sell_parts.append("出现技术破位或二卖信号时止损")
    else:
        sell_parts.append("技术形态恶化时及时止损")
    
    # 止损逻辑
    if stop_loss > 0:
        sell_parts.append(f"跌破{stop_loss}元坚决止损")
    
    # 基于信心度的卖点调整
    if confidence == 'very_high':
        sell_parts.append("可适当放宽止盈目标")
    elif confidence == 'medium':
        sell_parts.append("建议快进快出")
    
    return "；".join(sell_parts) + "。"

def _generate_risk_reward_analysis(entry_price: float, stop_loss: float, 
                                 target_low: float, target_high: float, expected_rr) -> str:
    """生成风险收益分析"""
    if entry_price <= 0 or stop_loss <= 0:
        return "风险收益比待确定，请谨慎操作。"
    
    risk_amount = entry_price - stop_loss
    risk_pct = round(risk_amount / entry_price * 100, 1)
    
    if target_low > 0 and target_high > 0:
        profit_low = target_low - entry_price
        profit_high = target_high - entry_price
        profit_pct_low = round(profit_low / entry_price * 100, 1)
        profit_pct_high = round(profit_high / entry_price * 100, 1)
        
        analysis = f"预期收益{profit_pct_low}-{profit_pct_high}%，"
        analysis += f"潜在风险{risk_pct}%，"
        analysis += f"风险收益比1:{expected_rr}。"
        
        if expected_rr != '∞' and float(expected_rr) >= 2:
            analysis += "风险收益比良好，值得关注。"
        elif expected_rr != '∞' and float(expected_rr) >= 1.5:
            analysis += "风险收益比一般，注意控制仓位。"
        else:
            analysis += "风险收益比偏低，建议谨慎参与。"
    else:
        analysis = f"潜在风险{risk_pct}%，建议严格执行止损策略。"
    
    return analysis

def _generate_default_explanation(stock: Dict) -> Dict:
    """生成默认解释（异常情况下使用）"""
    symbol = stock.get('symbol', 'N/A')
    entry_price = stock.get('entry_price', 0) or stock.get('current_price', 0)
    
    return {
        'symbol': symbol,
        'stock_name': stock.get('stock_name', '未知股票'),
        'reason': f"{symbol}技术面表现良好，具备投资价值，建议关注后续走势。",
        'signal_explanation': "技术信号良好，适合关注。",
        'tech_explanation': "基础技术指标支撑。",
        'buy_point': entry_price,
        'buy_point_explanation': f"参考价位{entry_price}元附近。",
        'sell_logic': "根据技术形态变化及时调整策略。",
        'stop_loss': entry_price * 0.92 if entry_price > 0 else 0,
        'target_range': [entry_price * 1.08, entry_price * 1.15] if entry_price > 0 else [0, 0],
        'expected_rr': '1.5',
        'confidence_level': 'medium',
        'risk_reward_analysis': "请根据个人风险偏好谨慎操作。"
    }

# 导出主要函数
__all__ = ['generate_explain']