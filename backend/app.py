#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CChanTrader-AI Web管理平台
Flask Web应用主程序
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import os
import json
import sqlite3
from datetime import datetime, timedelta
import threading
import time
from dotenv import load_dotenv

# 添加项目根目录到路径
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入我们的模块
from backend.services.email_config import EmailSender
from backend.daily_report_generator import DailyReportGenerator
from analysis.trading_day_scheduler import TradingDayScheduler

app = Flask(__name__, 
           template_folder='../frontend/templates',
           static_folder='../frontend/static')
app.secret_key = 'cchan_trader_ai_secret_key'

# 全局变量
scheduler_instance = None
scheduler_thread = None

class WebAppManager:
    """Web应用管理器"""
    
    def __init__(self):
        self.db_path = "data/cchan_web.db"
        self.init_database()
        
    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建股票推荐表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                symbol TEXT NOT NULL,
                stock_name TEXT,
                market TEXT,
                current_price REAL,
                total_score REAL,
                tech_score REAL,
                auction_score REAL,
                auction_ratio REAL,
                gap_type TEXT,
                confidence TEXT,
                strategy TEXT,
                entry_price REAL,
                stop_loss REAL,
                target_price REAL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建系统配置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_key TEXT UNIQUE NOT NULL,
                config_value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建系统日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_recommendations(self, recommendations: list, date: str):
        """保存股票推荐到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 先删除当日旧数据
        cursor.execute('DELETE FROM stock_recommendations WHERE date = ?', (date,))
        
        # 插入新数据
        for stock in recommendations:
            cursor.execute('''
                INSERT INTO stock_recommendations 
                (date, symbol, stock_name, market, current_price, total_score, 
                 tech_score, auction_score, auction_ratio, gap_type, confidence, 
                 strategy, entry_price, stop_loss, target_price)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                date, stock.get('symbol'), stock.get('stock_name'), 
                stock.get('market'), stock.get('current_price'), 
                stock.get('total_score'), stock.get('tech_score'),
                stock.get('auction_score'), stock.get('auction_ratio'),
                stock.get('gap_type'), stock.get('confidence'),
                stock.get('strategy'), stock.get('entry_price'),
                stock.get('stop_loss'), stock.get('target_price')
            ))
        
        conn.commit()
        conn.close()
    
    def get_recommendations(self, date: str = None, limit: int = 50):
        """获取股票推荐"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if date:
            cursor.execute('''
                SELECT * FROM stock_recommendations 
                WHERE date = ? 
                ORDER BY total_score DESC LIMIT ?
            ''', (date, limit))
        else:
            cursor.execute('''
                SELECT * FROM stock_recommendations 
                ORDER BY created_at DESC LIMIT ?
            ''', (limit,))
        
        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results
    
    def get_system_status(self):
        """获取系统状态"""
        global scheduler_instance
        
        # 检查是否应该自动启动调度器
        auto_start_enabled = os.getenv('AUTO_START_SCHEDULER', 'false').lower() == 'true'
        
        status = {
            'scheduler_running': scheduler_instance is not None and scheduler_instance.is_running,
            'auto_start_enabled': auto_start_enabled,
            'last_update': self.get_last_update_time(),
            'today_recommendations': len(self.get_recommendations(datetime.now().strftime('%Y-%m-%d'))),
            'email_configured': self.is_email_configured(),
            'system_health': 'good',  # 简化版
            'trading_mode': os.getenv('TRADING_MODE', 'short_term'),  # 新增交易模式
            'scheduler_recommended': self._should_recommend_scheduler_start()
        }
        
        return status
    
    def _should_recommend_scheduler_start(self):
        """判断是否建议启动调度器"""
        # 如果邮件已配置且当前是交易时间段，建议启动
        if self.is_email_configured():
            now = datetime.now()
            # 工作日的8:00-16:00建议启动
            if now.weekday() < 5 and 8 <= now.hour <= 16:
                return True
        return False
    
    def get_last_update_time(self):
        """获取最后更新时间"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT MAX(created_at) FROM stock_recommendations')
        result = cursor.fetchone()[0]
        conn.close()
        return result if result else "从未更新"
    
    def is_email_configured(self):
        """检查邮件是否已配置"""
        # 强制重新加载，避免缓存
        load_dotenv(override=True)
        sender_email = os.getenv('SENDER_EMAIL', '')
        sender_password = os.getenv('SENDER_PASSWORD', '')
        recipient_emails = os.getenv('RECIPIENT_EMAILS', '')
        
        configured = all([sender_email, sender_password, recipient_emails])
        print(f"邮件配置检查: {configured} (邮箱:{bool(sender_email)}, 密码:{bool(sender_password)}, 接收:{bool(recipient_emails)})")
        
        return configured
    
    def save_email_config(self, config: dict):
        """保存邮件配置"""
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
        
        # 创建新的环境变量内容
        env_content = f"""# CChanTrader-AI 邮件配置
SENDER_EMAIL={config.get('sender_email', '')}
SENDER_PASSWORD={config.get('sender_password', '')}
RECIPIENT_EMAILS={config.get('recipient_emails', '')}
EMAIL_PROVIDER={config.get('email_provider', 'gmail')}
"""
        
        try:
            # 先备份现有文件
            import shutil
            backup_path = env_path + '.backup'
            if os.path.exists(env_path):
                shutil.copy2(env_path, backup_path)
            
            # 写入新配置
            with open(env_path, 'w', encoding='utf-8') as f:
                f.write(env_content)
            
            # 验证文件写入成功
            with open(env_path, 'r', encoding='utf-8') as f:
                written_content = f.read()
            
            print(f"配置已写入 {env_path}:")
            print(written_content)
            
            # 强制重新加载环境变量 - 多种方式确保加载成功
            import importlib
            import dotenv
            
            # 清除现有环境变量缓存
            for key in ['SENDER_EMAIL', 'SENDER_PASSWORD', 'RECIPIENT_EMAILS', 'EMAIL_PROVIDER']:
                if key in os.environ:
                    del os.environ[key]
            
            # 重新加载
            load_dotenv(env_path, override=True)
            
            # 验证加载成功
            print(f"验证环境变量加载:")
            print(f"SENDER_EMAIL: {os.getenv('SENDER_EMAIL', 'NOT_FOUND')}")
            print(f"EMAIL_PROVIDER: {os.getenv('EMAIL_PROVIDER', 'NOT_FOUND')}")
            print(f"RECIPIENT_EMAILS: {os.getenv('RECIPIENT_EMAILS', 'NOT_FOUND')}")
            
        except Exception as e:
            print(f"保存邮件配置失败: {e}")
            # 如果有备份，尝试恢复
            if 'backup_path' in locals() and os.path.exists(backup_path):
                try:
                    shutil.copy2(backup_path, env_path)
                    print("已恢复备份配置")
                except:
                    pass
            raise e
    
    def save_strategy_config(self, config: dict):
        """保存策略配置"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 更新或插入策略配置
            for key, value in config.items():
                cursor.execute('''
                    INSERT OR REPLACE INTO system_config (config_key, config_value, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (f'strategy_{key}', str(value)))
            
            conn.commit()
            conn.close()
            
            print(f"策略配置已保存: {config}")
            
        except Exception as e:
            print(f"保存策略配置失败: {e}")
            raise e
    
    def get_strategy_config(self):
        """获取策略配置"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT config_key, config_value FROM system_config 
                WHERE config_key LIKE 'strategy_%'
            ''')
            
            results = cursor.fetchall()
            conn.close()
            
            # 构建配置字典 (调整默认价格范围以包含低价股)
            config = {
                'tech_weight': 0.65,
                'auction_weight': 0.35,
                'score_threshold': 0.65,
                'max_recommendations': 15,
                'min_price': 2.0,  # 包含低价股
                'max_price': 300.0,
                'updated_at': '从未设置'
            }
            
            for key, value in results:
                config_name = key.replace('strategy_', '')
                if config_name in config:
                    try:
                        if config_name in ['tech_weight', 'auction_weight', 'score_threshold', 'min_price', 'max_price']:
                            config[config_name] = float(value)
                        elif config_name == 'max_recommendations':
                            config[config_name] = int(value)
                        else:
                            config[config_name] = value
                    except ValueError:
                        # 如果转换失败，保持默认值
                        pass
            
            return config
            
        except Exception as e:
            print(f"获取策略配置失败: {e}")
            # 返回默认配置
            return {
                'tech_weight': 0.65,
                'auction_weight': 0.35,
                'score_threshold': 0.65,
                'max_recommendations': 15,
                'min_price': 2.0,
                'max_price': 300.0,
                'updated_at': '从未设置'
            }

# 初始化管理器
web_manager = WebAppManager()

def generate_test_report_data():
    """生成测试日报数据"""
    current_date = datetime.now().strftime('%Y-%m-%d')
    current_time = datetime.now().strftime('%H:%M:%S')
    
    # 模拟短线交易优化的股票推荐数据（包含低价股，价格范围2-90元）
    test_recommendations = [
        # 低价股推荐 (2-10元区间)
        {
            'symbol': '000606',
            'stock_name': '顺利办',
            'market': '深圳主板',
            'current_price': 3.85,
            'total_score': 0.823,
            'tech_score': 0.798,
            'auction_score': 0.862,
            'mktcap_score': 0.089,
            'auction_ratio': 2.9,
            'gap_type': 'gap_up',
            'confidence': 'very_high',
            'strategy': '信息服务+低价弹性+市值48亿+短线爆发力强',
            'entry_price': 3.90,
            'stop_loss': 3.65,
            'target_price': 4.35,
            'capital_bias': 0.756,
            'rsi': 61.8,
            'market_cap_billion': 48.2
        },
        {
            'symbol': '002139',
            'stock_name': '拓邦股份',
            'market': '深圳主板',
            'current_price': 6.12,
            'total_score': 0.789,
            'tech_score': 0.765,
            'auction_score': 0.834,
            'mktcap_score': 0.095,
            'auction_ratio': 2.4,
            'gap_type': 'gap_up',
            'confidence': 'high',
            'strategy': '智能控制器+IoT概念+市值72亿+低价成长',
            'entry_price': 6.20,
            'stop_loss': 5.85,
            'target_price': 6.85,
            'capital_bias': 0.689,
            'rsi': 58.3,
            'market_cap_billion': 72.1
        },
        {
            'symbol': '300365',
            'stock_name': '恒华科技',
            'market': '创业板',
            'current_price': 8.43,
            'total_score': 0.756,
            'tech_score': 0.723,
            'auction_score': 0.798,
            'mktcap_score': 0.087,
            'auction_ratio': 2.1,
            'gap_type': 'gap_up',
            'confidence': 'high',
            'strategy': '电力信息化+数字化转型+市值58亿+低估值',
            'entry_price': 8.50,
            'stop_loss': 8.05,
            'target_price': 9.25,
            'capital_bias': 0.634,
            'rsi': 55.7,
            'market_cap_billion': 58.4
        },
        # 中价股推荐 (10-50元区间)
        {
            'symbol': '002475',
            'stock_name': '立讯精密',
            'market': '深圳主板',
            'current_price': 32.45,
            'total_score': 0.756,
            'tech_score': 0.734,
            'auction_score': 0.778,
            'mktcap_score': 0.096,
            'auction_ratio': 2.1,
            'gap_type': 'gap_up',
            'confidence': 'high',
            'strategy': '消费电子+市值156亿+产业链复苏，短线2-4天',
            'entry_price': 32.80,
            'stop_loss': 31.00,
            'target_price': 36.00,
            'capital_bias': 0.645,
            'rsi': 57.8,
            'market_cap_billion': 156.3
        },
        {
            'symbol': '300496',
            'stock_name': '中科创达',
            'market': '创业板',
            'current_price': 52.30,
            'total_score': 0.698,
            'tech_score': 0.712,
            'auction_score': 0.684,
            'mktcap_score': 0.078,
            'auction_ratio': 1.4,
            'gap_type': 'flat',
            'confidence': 'medium',
            'strategy': '智能汽车OS+市值112亿+技术整理，3-5天',
            'entry_price': 52.80,
            'stop_loss': 50.50,
            'target_price': 57.00,
            'capital_bias': 0.534,
            'rsi': 48.9,
            'market_cap_billion': 112.8
        },
        # 高价股推荐 (50元以上)
        {
            'symbol': '002812',
            'stock_name': '恩捷股份',
            'market': '深圳主板',
            'current_price': 89.50,
            'total_score': 0.887,
            'tech_score': 0.845,
            'auction_score': 0.907,
            'mktcap_score': 0.126,
            'auction_ratio': 3.2,
            'gap_type': 'gap_up',
            'confidence': 'very_high',
            'strategy': '锂电材料+隔膜龙头+市值95亿适中+短线2-3天',
            'entry_price': 90.50,
            'stop_loss': 84.00,
            'target_price': 98.00,
            'capital_bias': 0.823,
            'rsi': 58.6,
            'market_cap_billion': 95.2
        }
    ]
    
    # 模拟市场概况数据
    market_summary = {
        'total_analyzed': 4532,
        'avg_score': sum(stock['total_score'] for stock in test_recommendations) / len(test_recommendations)
    }
    
    # 模拟竞价分析数据
    auction_analysis = {
        'avg_auction_ratio': sum(stock['auction_ratio'] for stock in test_recommendations) / len(test_recommendations),
        'gap_up_count': len([s for s in test_recommendations if s['gap_type'] == 'gap_up']),
        'flat_count': len([s for s in test_recommendations if s['gap_type'] == 'flat']),
        'gap_down_count': len([s for s in test_recommendations if s['gap_type'] == 'gap_down'])
    }
    
    return {
        'date': current_date,
        'analysis_time': current_time,
        'recommendations': test_recommendations,
        'market_summary': market_summary,
        'auction_analysis': auction_analysis
    }

@app.route('/')
def index():
    """首页 - 监控面板"""
    system_status = web_manager.get_system_status()
    today_recommendations = web_manager.get_recommendations(
        datetime.now().strftime('%Y-%m-%d'), 6
    )
    
    return render_template('index.html', 
                         system_status=system_status,
                         recommendations=today_recommendations)

@app.route('/recommendations')
def recommendations():
    """推荐页面"""
    date_filter = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    recommendations = web_manager.get_recommendations(date_filter)
    
    return render_template('recommendations.html', 
                         recommendations=recommendations,
                         current_date=date_filter)

@app.route('/stock/<symbol>')
def stock_detail(symbol):
    """股票详情页面"""
    try:
        # 使用深度分析器生成详细报告
        from analysis.deep_stock_analyzer import DeepStockAnalyzer
        analyzer = DeepStockAnalyzer()
        
        # 生成深度分析报告
        analysis_report = analyzer.generate_deep_analysis_report(symbol)
        
        if not analysis_report:
            flash('股票分析失败，请稍后重试', 'error')
            return redirect(url_for('recommendations'))
        
        return render_template('stock_detail.html', stock=analysis_report)
        
    except Exception as e:
        print(f"❌ 股票详情页面错误: {e}")
        import traceback
        traceback.print_exc()
        flash(f'加载股票详情失败: {str(e)}', 'error')
        return redirect(url_for('recommendations'))

@app.route('/config')
def config():
    """配置页面"""
    # 强制重新加载环境变量，避免缓存问题
    load_dotenv(override=True)
    
    email_config = {
        'sender_email': os.getenv('SENDER_EMAIL', ''),
        'sender_password': os.getenv('SENDER_PASSWORD', ''),
        'recipient_emails': os.getenv('RECIPIENT_EMAILS', ''),
        'email_provider': os.getenv('EMAIL_PROVIDER', 'gmail')
    }
    
    # 获取策略配置
    strategy_config = web_manager.get_strategy_config()
    
    # 调试信息
    print(f"配置页面加载 - 当前环境变量:")
    print(f"SENDER_EMAIL: {email_config['sender_email']}")
    print(f"EMAIL_PROVIDER: {email_config['email_provider']}")
    print(f"密码长度: {len(email_config['sender_password']) if email_config['sender_password'] else 0}")
    print(f"策略配置: {strategy_config}")
    
    return render_template('config.html', 
                         email_config=email_config,
                         strategy_config=strategy_config)

@app.route('/api/save_email_config', methods=['POST'])
def save_email_config():
    """保存邮件配置API"""
    try:
        config = request.json
        
        # 验证必要字段
        if not config.get('sender_email'):
            return jsonify({'success': False, 'message': '请填写发送邮箱'})
        if not config.get('sender_password'):
            return jsonify({'success': False, 'message': '请填写邮箱密码'})
        if not config.get('recipient_emails'):
            return jsonify({'success': False, 'message': '请填写接收邮箱'})
        
        # 验证邮箱格式
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, config.get('sender_email')):
            return jsonify({'success': False, 'message': '发送邮箱格式不正确'})
        
        # 验证接收邮箱列表
        recipient_emails = config.get('recipient_emails', '').split(',')
        for email in recipient_emails:
            email = email.strip()
            if email and not re.match(email_pattern, email):
                return jsonify({'success': False, 'message': f'接收邮箱格式不正确: {email}'})
        
        # 保存配置并强制重新加载
        web_manager.save_email_config(config)
        
        # 双重确保环境变量重新加载
        load_dotenv(override=True)
        
        # 验证保存成功
        saved_email = os.getenv('SENDER_EMAIL', '')
        saved_password = os.getenv('SENDER_PASSWORD', '')
        saved_recipients = os.getenv('RECIPIENT_EMAILS', '')
        
        print(f"保存后验证 - 发送邮箱: {saved_email}")
        print(f"保存后验证 - 密码长度: {len(saved_password) if saved_password else 0}")
        print(f"保存后验证 - 接收邮箱: {saved_recipients}")
        
        email_count = len([e for e in recipient_emails if e.strip()])
        
        if saved_email and saved_password and saved_recipients:
            return jsonify({
                'success': True, 
                'message': f'邮件配置已成功保存，共配置 {email_count} 个接收邮箱。新密码已生效！',
                'debug_info': {
                    'sender': saved_email,
                    'provider': os.getenv('EMAIL_PROVIDER', 'unknown'),
                    'recipient_count': email_count
                }
            })
        else:
            return jsonify({
                'success': False, 
                'message': '配置保存可能失败，请检查输入信息',
                'debug_info': {
                    'saved_email': bool(saved_email),
                    'saved_password': bool(saved_password),
                    'saved_recipients': bool(saved_recipients)
                }
            })
    except Exception as e:
        import traceback
        print(f"保存邮件配置异常: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'保存失败: {str(e)}'})

@app.route('/api/test_email', methods=['POST'])
def test_email():
    """测试邮件发送API"""
    try:
        # 强制重新加载环境变量，确保获取最新配置
        load_dotenv(override=True)
        
        # 创建新的EmailSender实例，确保使用最新配置
        email_sender = EmailSender()
        
        print(f"测试邮件 - 当前配置:")
        print(f"发送邮箱: {email_sender.sender_email}")
        print(f"邮箱密码长度: {len(email_sender.sender_password) if email_sender.sender_password else 0}")
        print(f"接收邮箱: {email_sender.recipient_emails}")
        print(f"邮件服务商: {email_sender.email_provider}")
        
        # 添加详细的配置检查
        if not email_sender.sender_email:
            return jsonify({'success': False, 'message': '发送邮箱未配置，请先保存邮件配置'})
        if not email_sender.sender_password:
            return jsonify({'success': False, 'message': '邮箱授权码未配置，请填写正确的授权码'})
        if not email_sender.recipient_emails:
            return jsonify({'success': False, 'message': '接收邮箱未配置，请添加接收邮箱'})
        
        # 生成测试日报数据
        test_report_data = generate_test_report_data()
        
        print(f"开始发送测试邮件...")
        
        # 发送正式格式的测试邮件
        success = email_sender.send_daily_report(test_report_data)
        
        if success:
            return jsonify({
                'success': True, 
                'message': f'✅ 测试邮件发送成功！已发送到 {len(email_sender.recipient_emails)} 个邮箱，请检查收件箱。新授权码已生效！'
            })
        else:
            return jsonify({
                'success': False, 
                'message': '❌ 邮件发送失败，请检查：1) 授权码是否正确 2) 网络连接是否正常 3) 邮箱SMTP是否开启'
            })
    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"邮件测试异常: {e}")
        traceback.print_exc()
        
        # 根据错误类型提供具体的解决建议
        if '535' in error_msg or 'Authentication failed' in error_msg:
            error_msg = '❌ 邮箱认证失败：授权码可能已过期或不正确，请重新生成授权码'
        elif 'Connection' in error_msg or 'timeout' in error_msg:
            error_msg = '❌ 网络连接失败：请检查网络连接或邮件服务器设置'
        elif 'SSL' in error_msg or 'TLS' in error_msg:
            error_msg = '❌ 安全连接失败：请检查邮箱SMTP/SSL设置'
        
        return jsonify({'success': False, 'message': f'测试失败: {error_msg}'})

@app.route('/api/save_strategy_config', methods=['POST'])
def save_strategy_config():
    """保存策略参数配置API"""
    try:
        config = request.json
        
        # 验证必要字段和范围
        tech_weight = float(config.get('tech_weight', 0.65))
        auction_weight = float(config.get('auction_weight', 0.35))
        score_threshold = float(config.get('score_threshold', 0.65))
        max_recommendations = int(config.get('max_recommendations', 15))
        min_price = float(config.get('min_price', 2))
        max_price = float(config.get('max_price', 300))
        
        # 参数验证
        if not (0.4 <= tech_weight <= 0.8):
            return jsonify({'success': False, 'message': '技术分析权重必须在40%-80%之间'})
        
        if not (0.2 <= auction_weight <= 0.6):
            return jsonify({'success': False, 'message': '竞价分析权重必须在20%-60%之间'})
        
        if abs(tech_weight + auction_weight - 1.0) > 0.01:
            return jsonify({'success': False, 'message': '权重总和必须等于100%'})
        
        if not (0.5 <= score_threshold <= 0.9):
            return jsonify({'success': False, 'message': '评分阈值必须在0.5-0.9之间'})
        
        if not (5 <= max_recommendations <= 50):
            return jsonify({'success': False, 'message': '推荐数量必须在5-50之间'})
        
        if not (1 <= min_price <= max_price <= 1000):
            return jsonify({'success': False, 'message': '价格范围设置不合理'})
        
        # 保存策略配置
        strategy_config = {
            'tech_weight': tech_weight,
            'auction_weight': auction_weight,
            'score_threshold': score_threshold,
            'max_recommendations': max_recommendations,
            'min_price': min_price,
            'max_price': max_price,
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        web_manager.save_strategy_config(strategy_config)
        
        return jsonify({
            'success': True, 
            'message': f'策略参数已保存 - 技术权重{tech_weight*100:.0f}%, 竞价权重{auction_weight*100:.0f}%, 阈值{score_threshold:.2f}',
            'config': strategy_config
        })
        
    except ValueError as e:
        return jsonify({'success': False, 'message': f'参数格式错误: {str(e)}'})
    except Exception as e:
        import traceback
        print(f"保存策略配置异常: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'保存失败: {str(e)}'})

@app.route('/api/get_strategy_config', methods=['GET'])
def get_strategy_config():
    """获取策略参数配置API"""
    try:
        config = web_manager.get_strategy_config()
        return jsonify({'success': True, 'config': config})
    except Exception as e:
        print(f"获取策略配置异常: {e}")
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'})

@app.route('/api/start_scheduler', methods=['POST'])
def start_scheduler():
    """启动调度器API"""
    global scheduler_instance, scheduler_thread
    
    try:
        if scheduler_instance and scheduler_instance.is_running:
            return jsonify({'success': False, 'message': '调度器已在运行中'})
        
        scheduler_instance = TradingDayScheduler()
        scheduler_thread = threading.Thread(target=scheduler_instance.start_scheduler, daemon=True)
        scheduler_thread.start()
        
        return jsonify({'success': True, 'message': '调度器已启动'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'启动失败: {str(e)}'})

@app.route('/api/stop_scheduler', methods=['POST'])
def stop_scheduler():
    """停止调度器API"""
    global scheduler_instance
    
    try:
        if scheduler_instance:
            scheduler_instance.stop_scheduler()
            scheduler_instance = None
        
        return jsonify({'success': True, 'message': '调度器已停止'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'停止失败: {str(e)}'})

@app.route('/api/run_analysis', methods=['POST'])
def run_analysis():
    """立即执行分析API - 使用优化版分析器"""
    try:
        print(f"🔄 开始生成交易日报...")
        
        # 使用优化版分析器
        from analysis.optimized_stock_analyzer import OptimizedStockAnalyzer
        analyzer = OptimizedStockAnalyzer()
        report_data = analyzer.generate_optimized_recommendations()
        
        if report_data and 'recommendations' in report_data:
            recommendations = report_data['recommendations']
            
            # 保存到数据库
            web_manager.save_recommendations(
                recommendations,
                report_data['date']
            )
            
            # 统计分析结果
            high_confidence_count = len([r for r in recommendations if r.get('confidence') == 'very_high'])
            low_price_count = len([r for r in recommendations if r.get('current_price', 999) <= 10])
            avg_score = sum(r.get('total_score', 0) for r in recommendations) / len(recommendations) if recommendations else 0
            
            print(f"📊 分析完成: {len(recommendations)}只股票, 强烈推荐{high_confidence_count}只, 低价股{low_price_count}只")
            
            return jsonify({
                'success': True, 
                'message': f'分析完成！共筛选出 {len(recommendations)} 只推荐股票，其中强烈推荐 {high_confidence_count} 只，低价机会 {low_price_count} 只',
                'data': {
                    'total_count': len(recommendations),
                    'high_confidence_count': high_confidence_count,
                    'low_price_count': low_price_count,
                    'average_score': round(avg_score, 3),
                    'analysis_date': report_data['date'],
                    'analysis_time': report_data.get('analysis_time', 'Unknown')
                }
            })
        else:
            print("❌ 分析失败或无推荐股票")
            return jsonify({
                'success': False, 
                'message': '分析完成但未找到符合条件的股票，可能是市场条件不佳或筛选条件过于严格'
            })
            
    except Exception as e:
        import traceback
        print(f"❌ 分析异常: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False, 
            'message': f'分析过程中出现错误: {str(e)}，请检查系统配置或稍后重试'
        })

@app.route('/api/system_status')
def system_status():
    """获取系统状态API"""
    try:
        status = web_manager.get_system_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/update_stock_status', methods=['POST'])
def update_stock_status():
    """更新股票状态API"""
    try:
        data = request.json
        stock_id = data.get('id')
        new_status = data.get('status')
        
        conn = sqlite3.connect(web_manager.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE stock_recommendations SET status = ? WHERE id = ?',
            (new_status, stock_id)
        )
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '状态已更新'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'})

# >>> CChanTrader-AI Explain Patch : picks endpoint
@app.route('/api/picks', methods=['GET'])
def api_get_picks():
    """获取带解释的推荐股票列表API"""
    try:
        from analysis.optimized_stock_analyzer import OptimizedStockAnalyzer
        
        # 获取查询参数
        limit = request.args.get('limit', 10, type=int)
        confidence = request.args.get('confidence', '')
        
        analyzer = OptimizedStockAnalyzer()
        data = analyzer.generate_optimized_recommendations()
        recommendations = data.get('recommendations', [])
        
        # 应用过滤器
        if confidence:
            recommendations = [r for r in recommendations if r.get('confidence') == confidence]
        
        # 限制返回数量
        recommendations = recommendations[:limit]
        
        # 保存到数据库
        try:
            conn = sqlite3.connect(web_manager.db_path)
            cursor = conn.cursor()
            
            for stock in recommendations:
                cursor.execute('''
                    INSERT OR REPLACE INTO stock_analysis 
                    (symbol, stock_name, analysis_date, total_score, tech_score, 
                     auction_score, confidence, entry_price, stop_loss, target_price, explanation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    stock.get('symbol', ''),
                    stock.get('stock_name', ''),
                    datetime.now().strftime('%Y-%m-%d'),
                    stock.get('total_score', 0),
                    stock.get('tech_score', 0),
                    stock.get('auction_score', 0),
                    stock.get('confidence', 'medium'),
                    stock.get('entry_price', 0),
                    stock.get('stop_loss', 0),
                    stock.get('target_price', 0),
                    stock.get('explanation', '')
                ))
            
            conn.commit()
            conn.close()
            print(f"✅ 已保存 {len(recommendations)} 条推荐记录到数据库")
            
        except Exception as db_error:
            print(f"⚠️ 保存到数据库失败: {db_error}")
        
        return jsonify({
            'success': True,
            'data': recommendations,
            'total': len(recommendations),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': f'获取推荐失败: {str(e)}',
            'data': []
        })

# HTMX股票分析详情API端点
@app.route('/api/stocks/<symbol>/analysis', methods=['GET'])
def get_stock_analysis_detail(symbol):
    """获取股票分析详情（优化版 - 直接从数据库读取）"""
    try:
        import sqlite3
        import os
        import json
        
        # 从数据库读取预生成的解释HTML和价格数据
        conn = sqlite3.connect(os.path.join('.', "data/cchan_web.db"))
        cur = conn.cursor()
        
        row = cur.execute(
            "SELECT explain_html, mini_prices FROM stock_analysis WHERE symbol = ? ORDER BY created_at DESC LIMIT 1",
            (symbol,)
        ).fetchone()
        
        conn.close()
        
        if not row or not row[0]:
            # 如果数据库中没有数据，返回默认提示
            return jsonify({
                "html": f"""
                <div class="text-center py-8">
                    <div class="text-gray-400 mb-4">
                        <svg class="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293L16 6h2a2 2 0 012 2v11a2 2 0 01-2 2z"></path>
                        </svg>
                    </div>
                    <p class="text-gray-500 mb-2">暂无详细分析数据</p>
                    <p class="text-gray-400 text-sm">股票代码: {symbol}</p>
                    <p class="text-gray-400 text-sm">请运行分析后重试</p>
                </div>
                """,
                "prices": []
            })
        
        # 解析价格数据
        try:
            prices = json.loads(row[1] or "[]")
        except:
            prices = []
        
        return jsonify({
            "html": row[0],
            "prices": prices
        })
        
    except Exception as e:
        # 发生错误时返回JSON格式的错误信息
        return jsonify({
            "html": f"""
            <div class="text-center py-8">
                <div class="text-red-400 mb-4">
                    <svg class="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
                    </svg>
                </div>
                <p class="text-red-500 mb-2">数据加载失败</p>
                <p class="text-gray-500 text-sm">股票代码: {symbol}</p>
                <p class="text-gray-400 text-sm">错误信息: {str(e)}</p>
            </div>
            """,
            "prices": []
        })

@app.route("/health")
def health():
    """健康检查端点"""
    return "ok", 200

if __name__ == "__main__":
    # 确保数据目录存在
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    print("🚀 启动 CChanTrader-AI Web管理平台...")
    print("🌐 访问地址: http://localhost:8080")
    print("🛑 停止服务: Ctrl+C")
    
    # Railway 部署时使用环境变量中的端口
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)