#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CChanTrader-AI 邮件配置系统
支持多种邮件服务商的自动发送
"""

import smtplib
import ssl
import email.mime.text
import email.mime.multipart
import email.mime.base
import email.encoders
import os
from datetime import datetime
from dotenv import load_dotenv

class EmailSender:
    """邮件发送器"""
    
    def __init__(self):
        # 强制重新加载环境变量，避免缓存问题
        load_dotenv(override=True)
        self.smtp_configs = {
            'qq': {
                'server': 'smtp.qq.com',
                'port': 587,
                'use_tls': True
            },
            '163': {
                'server': 'smtp.163.com', 
                'port': 587,
                'use_tls': True
            },
            'gmail': {
                'server': 'smtp.gmail.com',
                'port': 587,
                'use_tls': True
            },
            'outlook': {
                'server': 'smtp-mail.outlook.com',
                'port': 587,
                'use_tls': True
            },
            'sina': {
                'server': 'smtp.sina.com',
                'port': 587,
                'use_tls': True
            }
        }
        
        # 从环境变量获取配置
        self.sender_email = os.getenv('SENDER_EMAIL', '')
        self.sender_password = os.getenv('SENDER_PASSWORD', '')
        self.recipient_emails = self._parse_recipient_emails(os.getenv('RECIPIENT_EMAILS', ''))
        self.email_provider = os.getenv('EMAIL_PROVIDER', 'qq').lower()
        
        if not all([self.sender_email, self.sender_password, self.recipient_emails]):
            print("⚠️ 请在.env文件中配置邮件参数:")
            print("SENDER_EMAIL=your_email@qq.com")
            print("SENDER_PASSWORD=your_password_or_app_token")
            print("RECIPIENT_EMAILS=email1@qq.com,email2@163.com,email3@gmail.com")
            print("EMAIL_PROVIDER=qq  # 可选: qq, 163, gmail, outlook, sina")
    
    def _parse_recipient_emails(self, email_string: str) -> list:
        """解析收件人邮箱列表"""
        if not email_string:
            return []
        
        # 支持逗号、分号、空格分隔
        emails = []
        for separator in [',', ';', ' ']:
            email_string = email_string.replace(separator, ',')
        
        for email in email_string.split(','):
            email = email.strip()
            if email and '@' in email:
                emails.append(email)
        
        return emails
    
    def send_email(self, subject: str, html_content: str, attachments: list = None) -> bool:
        """发送邮件到多个收件人"""
        try:
            if not all([self.sender_email, self.sender_password, self.recipient_emails]):
                print("❌ 邮件配置不完整，无法发送邮件")
                return False
            
            success_count = 0
            total_count = len(self.recipient_emails)
            
            # 获取SMTP配置
            config = self.smtp_configs.get(self.email_provider, self.smtp_configs['qq'])
            
            # 建立SMTP连接
            context = ssl.create_default_context()
            with smtplib.SMTP(config['server'], config['port']) as server:
                if config['use_tls']:
                    server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
                
                # 逐个发送邮件
                for recipient_email in self.recipient_emails:
                    try:
                        # 创建邮件对象
                        msg = email.mime.multipart.MIMEMultipart('alternative')
                        msg['From'] = self.sender_email
                        msg['To'] = recipient_email
                        msg['Subject'] = subject
                        
                        # 添加HTML内容
                        html_part = email.mime.text.MIMEText(html_content, 'html', 'utf-8')
                        msg.attach(html_part)
                        
                        # 添加附件
                        if attachments:
                            for file_path in attachments:
                                if os.path.exists(file_path):
                                    with open(file_path, 'rb') as attachment:
                                        part = email.mime.base.MIMEBase('application', 'octet-stream')
                                        part.set_payload(attachment.read())
                                    
                                    email.encoders.encode_base64(part)
                                    part.add_header(
                                        'Content-Disposition',
                                        f'attachment; filename= {os.path.basename(file_path)}'
                                    )
                                    msg.attach(part)
                        
                        # 发送邮件
                        server.send_message(msg)
                        success_count += 1
                        print(f"✅ 邮件发送成功: {recipient_email}")
                        
                    except Exception as e:
                        print(f"❌ 发送到 {recipient_email} 失败: {e}")
                        continue
            
            if success_count > 0:
                print(f"📧 邮件发送完成: {success_count}/{total_count} 成功")
                return True
            else:
                print("❌ 所有邮件发送失败")
                return False
            
        except Exception as e:
            print(f"❌ 邮件发送失败: {e}")
            return False
    
    def send_daily_report(self, report_data: dict) -> bool:
        """发送交易日报"""
        subject = f"📊 CChanTrader-AI 交易日报 - {report_data.get('date', datetime.now().strftime('%Y-%m-%d'))}"
        
        html_content = self._generate_report_html(report_data)
        
        # 添加JSON附件
        attachments = []
        if 'json_file' in report_data:
            attachments.append(report_data['json_file'])
        
        return self.send_email(subject, html_content, attachments)
    
    def _generate_report_html(self, data: dict) -> str:
        """生成HTML邮件内容 - 使用专业金融模板"""
        
        # 获取推荐股票列表
        recommendations = data.get('recommendations', [])
        market_summary = data.get('market_summary', {})
        auction_analysis = data.get('auction_analysis', {})
        
        # 计算统计数据
        high_confidence_count = len([r for r in recommendations if r.get('confidence') == 'very_high'])
        breakout_signals_count = len([r for r in recommendations if r.get('breakout_signal', False)])
        strong_auction_count = len([r for r in recommendations if r.get('auction_ratio', 0) >= 2])
        volume_surge_count = len([r for r in recommendations if r.get('volume_surge', False)])
        market_cap_fit_count = len([r for r in recommendations if 40 <= r.get('market_cap_billion', 0) <= 200])
        
        # 读取专业模板文件
        template_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'email_template.html')
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
        except FileNotFoundError:
            # 如果模板文件不存在，使用简化版本
            return self._generate_fallback_html(data)
        
        # 使用Jinja2风格的模板替换
        template_vars = {
            'date': data.get('date', datetime.now().strftime('%Y-%m-%d')),
            'analysis_time': data.get('analysis_time', datetime.now().strftime('%H:%M:%S')),
            'market_summary': market_summary,
            'recommendations': recommendations,
            'high_confidence_count': high_confidence_count,
            'breakout_signals_count': breakout_signals_count,
            'strong_auction_count': strong_auction_count,
            'volume_surge_count': volume_surge_count,
            'market_cap_fit_count': market_cap_fit_count,
        }
        
        # 手动替换模板变量
        html = template_content
        html = html.replace('{{date}}', template_vars['date'])
        html = html.replace('{{analysis_time}}', template_vars['analysis_time'])
        html = html.replace('{{market_summary.total_analyzed}}', str(market_summary.get('total_analyzed', 0)))
        html = html.replace('{{recommendations|length}}', str(len(recommendations)))
        html = html.replace('{{high_confidence_count}}', str(high_confidence_count))
        html = html.replace('{{market_summary.avg_score|round(3)}}', str(round(market_summary.get('avg_score', 0), 3)))
        html = html.replace('{{breakout_signals_count}}', str(breakout_signals_count))
        html = html.replace('{{strong_auction_count}}', str(strong_auction_count))
        html = html.replace('{{volume_surge_count}}', str(volume_surge_count))
        html = html.replace('{{market_cap_fit_count}}', str(market_cap_fit_count))
        
        # 生成股票推荐内容
        stock_cards_html = ""
        for stock in recommendations:
            confidence_class = {
                'very_high': 'high-confidence',
                'high': 'medium-confidence',
                'medium': ''
            }.get(stock.get('confidence', 'medium'), '')
            
            confidence_text = {
                'very_high': '强烈推荐',
                'high': '值得关注',
                'medium': '谨慎观察'
            }.get(stock.get('confidence', 'medium'), '谨慎观察')
            
            auction_ratio_class = 'positive' if stock.get('auction_ratio', 0) > 0 else 'negative' if stock.get('auction_ratio', 0) < 0 else 'neutral'
            
            # 生成信号标签
            signals_html = ""
            if stock.get('total_score', 0) >= 0.8:
                signals_html += '<div class="signal-item"><span>🚀</span><span>强势信号</span></div>'
            if stock.get('auction_ratio', 0) >= 2:
                signals_html += '<div class="signal-item"><span>📊</span><span>竞价活跃</span></div>'
            if stock.get('current_price', 999) <= 10:
                signals_html += '<div class="signal-item"><span>💰</span><span>低价机会</span></div>'
            if stock.get('market_cap_billion', 0) <= 200:
                signals_html += '<div class="signal-item"><span>🎯</span><span>中小盘股</span></div>'
            
            stock_card_html = f"""
                    <div class="stock-card {confidence_class}">
                        <div class="stock-header">
                            <div class="stock-info">
                                <div class="stock-symbol">{stock.get('symbol', 'N/A')}</div>
                                <div class="stock-name">{stock.get('stock_name', '未知股票')}</div>
                                <div class="stock-price">¥{stock.get('current_price', 0):.2f}</div>
                            </div>
                            <div class="confidence-badge confidence-{stock.get('confidence', 'medium').replace('_', '-')}">
                                {confidence_text}
                            </div>
                        </div>
                        
                        <div class="stock-metrics">
                            <div class="metric">
                                <div class="metric-label-small">竞价表现</div>
                                <div class="metric-value-small {auction_ratio_class}">
                                    {stock.get('auction_ratio', 0):+.1f}%
                                </div>
                            </div>
                            <div class="metric">
                                <div class="metric-label-small">目标价</div>
                                <div class="metric-value-small positive">¥{stock.get('target_price', 0):.2f}</div>
                            </div>
                            <div class="metric">
                                <div class="metric-label-small">止损价</div>
                                <div class="metric-value-small negative">¥{stock.get('stop_loss', 0):.2f}</div>
                            </div>
                        </div>
                        
                        <div class="stock-strategy">
                            <div class="strategy-text">{stock.get('strategy', '暂无策略分析')}</div>
                        </div>
                        
                        <div class="investment-details">
                            <div class="detail-row">
                                <span class="detail-label">买入时机:</span>
                                <span class="detail-value">{stock.get('buy_point', '等待信号')}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">卖出策略:</span>
                                <span class="detail-value">{stock.get('sell_point', '目标价位')}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">预期收益:</span>
                                <span class="detail-value positive">{stock.get('expected_return_pct', 10):.1f}%</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">持股周期:</span>
                                <span class="detail-value">{stock.get('holding_period_days', 30)}天</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">建议仓位:</span>
                                <span class="detail-value">{stock.get('position_suggestion', 10):.1f}%</span>
                            </div>
                        </div>
                        
                        <div class="signals-grid">
                            {signals_html}
                        </div>
                    </div>"""
            
            stock_cards_html += stock_card_html
        
        # 替换股票卡片内容
        html = html.replace('{% for stock in recommendations %}', '')
        html = html.replace('{% endfor %}', '')
        html = html.replace('{% if stock.confidence == \'very_high\' %}high-confidence{% elif stock.confidence == \'high\' %}medium-confidence{% endif %}', '')
        
        # 找到股票推荐部分并替换
        start_marker = '<div class="stock-grid">'
        end_marker = '</div>\n                </div>\n            \n            <!-- Risk Warning -->'
        
        start_idx = html.find(start_marker)
        end_idx = html.find(end_marker)
        
        if start_idx != -1 and end_idx != -1:
            html = html[:start_idx + len(start_marker)] + stock_cards_html + html[end_idx:]
        else:
            # 如果找不到标记，返回简化版本
            return self._generate_fallback_html(data)
        
        return html
    
    def _generate_fallback_html(self, data: dict) -> str:
        """生成简化版HTML邮件内容 - 作为模板文件不存在时的后备方案"""
        
        recommendations = data.get('recommendations', [])
        market_summary = data.get('market_summary', {})
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>CChanTrader-AI 交易日报</title>
    <style>
        body {{ font-family: Inter, -apple-system, sans-serif; background: #FAFAFA; margin: 0; padding: 20px; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #1E3A8A, #3B82F6); color: white; padding: 32px; text-align: center; }}
        .header h1 {{ font-size: 28px; font-weight: 700; margin-bottom: 8px; }}
        .content {{ padding: 32px; }}
        .section {{ margin-bottom: 32px; }}
        .section h2 {{ font-size: 20px; font-weight: 600; color: #111827; margin-bottom: 16px; }}
        .stock-card {{ background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 16px; padding: 24px; margin-bottom: 20px; }}
        .footer {{ background: #F8FAFC; padding: 24px; text-align: center; font-size: 12px; color: #64748B; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 CChanTrader-AI 智能交易日报</h1>
            <p>{data.get('date', datetime.now().strftime('%Y-%m-%d'))}</p>
        </div>
        <div class="content">
            <div class="section">
                <h2>今日推荐股票</h2>
                {'<p>今日暂无符合条件的推荐股票</p>' if not recommendations else ''.join([
                    f'<div class="stock-card"><strong>{stock.get("symbol", "N/A")} {stock.get("stock_name", "未知")}</strong><br>价格: ¥{stock.get("current_price", 0):.2f}<br>评分: {stock.get("total_score", 0):.3f}</div>' 
                    for stock in recommendations[:5]
                ])}
            </div>
        </div>
        <div class="footer">
            <p>CChanTrader-AI • 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""
        
        return html
    
    def _get_position_suggestion(self, confidence: str) -> str:
        """获取仓位建议"""
        position_map = {
            'very_high': '15-20% (重仓)',
            'high': '10-15% (中仓)', 
            'medium': '5-10% (轻仓)'
        }
        return position_map.get(confidence, '5-10% (轻仓)')
    
    def test_email_connection(self) -> bool:
        """测试邮件连接 - 仅发送给测试邮箱"""
        test_subject = "📧 CChanTrader-AI 邮件测试"
        
        # 生成完整的测试报告
        test_report_data = self._generate_test_report_data()
        test_content = self._generate_report_html(test_report_data)
        
        # 临时保存原有接收邮箱
        original_recipients = self.recipient_emails.copy()
        
        # 设置测试邮箱（仅发送给指定邮箱）
        test_email = "azhizhengzhuan@gmail.com"
        self.recipient_emails = [test_email] if test_email in original_recipients else [original_recipients[0]]
        
        print(f"🧪 测试模式：仅发送邮件给 {self.recipient_emails[0]}")
        
        try:
            result = self.send_email(test_subject, test_content)
        finally:
            # 恢复原有接收邮箱列表
            self.recipient_emails = original_recipients
        
        return result
    
    def _generate_test_report_data(self):
        """生成测试报告数据"""
        from datetime import datetime
        current_date = datetime.now().strftime('%Y-%m-%d')
        current_time = datetime.now().strftime('%H:%M:%S')
        
        # 使用固定的测试数据，确保邮件内容完整
        test_recommendations = [
            {
                'symbol': '000606',
                'stock_name': '顺利办',
                'market': '深圳主板',
                'current_price': 3.85,
                'total_score': 0.823,
                'tech_score': 0.798,
                'auction_score': 0.862,
                'auction_ratio': 2.9,
                'gap_type': 'gap_up',
                'confidence': 'very_high',
                'strategy': '信息服务+低价弹性+市值48亿+短线爆发力强',
                'entry_price': 3.90,
                'stop_loss': 3.65,
                'target_price': 4.35,
                'rsi': 61.8,
                'market_cap_billion': 48.2,
                'breakout_signal': True,
                'volume_surge': True
            },
            {
                'symbol': '002139',
                'stock_name': '拓邦股份',
                'market': '深圳主板',
                'current_price': 6.12,
                'total_score': 0.789,
                'tech_score': 0.765,
                'auction_score': 0.834,
                'auction_ratio': 2.4,
                'gap_type': 'gap_up',
                'confidence': 'high',
                'strategy': '智能控制器+IoT概念+市值72亿+低价成长',
                'entry_price': 6.20,
                'stop_loss': 5.85,
                'target_price': 6.85,
                'rsi': 58.3,
                'market_cap_billion': 72.1,
                'breakout_signal': False,
                'volume_surge': True
            },
            {
                'symbol': '002812',
                'stock_name': '恩捷股份',
                'market': '深圳主板',
                'current_price': 89.50,
                'total_score': 0.887,
                'tech_score': 0.845,
                'auction_score': 0.907,
                'auction_ratio': 3.2,
                'gap_type': 'gap_up',
                'confidence': 'very_high',
                'strategy': '锂电材料+隔膜龙头+市值95亿适中+短线2-3天',
                'entry_price': 90.50,
                'stop_loss': 84.00,
                'target_price': 98.00,
                'rsi': 58.6,
                'market_cap_billion': 95.2,
                'breakout_signal': True,
                'volume_surge': False
            }
        ]
        
        market_summary = {
            'total_analyzed': 4532,
            'avg_score': sum(stock['total_score'] for stock in test_recommendations) / len(test_recommendations)
        }
        
        auction_analysis = {
            'avg_auction_ratio': sum(stock['auction_ratio'] for stock in test_recommendations) / len(test_recommendations),
            'gap_up_count': len([s for s in test_recommendations if s['gap_type'] == 'gap_up']),
            'flat_count': 0,
            'gap_down_count': 0
        }
        
        return {
            'date': current_date,
            'analysis_time': current_time,
            'recommendations': test_recommendations,
            'market_summary': market_summary,
            'auction_analysis': auction_analysis
        }

# 环境变量配置示例
def create_email_env_example():
    """创建环境变量配置示例"""
    env_example = """
# CChanTrader-AI 邮件配置
# 请根据您的邮箱服务商配置以下参数

# 发送邮箱 (您的邮箱地址)
SENDER_EMAIL=your_email@qq.com

# 邮箱密码或应用专用密码
# QQ邮箱: 需要开启SMTP服务并生成授权码
# 163邮箱: 需要开启SMTP服务并生成授权码  
# Gmail: 需要使用应用专用密码
SENDER_PASSWORD=your_password_or_app_token

# 接收邮箱 (多个邮箱用逗号分隔)
RECIPIENT_EMAILS=email1@qq.com,email2@163.com,email3@gmail.com

# 邮件服务商 (qq, 163, gmail, outlook, sina)
EMAIL_PROVIDER=qq

# 其他配置
AIHUBMIX_API_KEY=your_api_key
"""
    
    with open('/Users/yang/.env.example', 'w', encoding='utf-8') as f:
        f.write(env_example)
    
    print("📧 邮件配置示例已创建: .env.example")
    print("请复制为 .env 文件并修改配置")

if __name__ == "__main__":
    # 创建配置示例
    create_email_env_example()
    
    # 测试邮件发送
    email_sender = EmailSender()
    
    # 测试连接
    print("📧 测试邮件系统...")
    if email_sender.test_email_connection():
        print("✅ 邮件系统测试成功!")
    else:
        print("❌ 邮件系统测试失败，请检查配置")