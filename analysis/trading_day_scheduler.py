#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CChanTrader-AI 交易日定时调度器
在每个交易日9:25-9:29时间段自动执行分析并发送日报
"""

import schedule
import time
import threading
from datetime import datetime, timedelta
import logging
import os
from daily_report_generator import DailyReportGenerator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/yang/trading_scheduler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class TradingDayScheduler:
    """交易日调度器"""
    
    def __init__(self):
        self.report_generator = DailyReportGenerator()
        self.is_running = False
        self.report_sent_today = False
        self.last_report_date = None
        
        # 创建锁防止重复执行
        self.execution_lock = threading.Lock()
        
        logging.info("📅 CChanTrader-AI 交易日调度器已初始化")
    
    def is_trading_time(self) -> bool:
        """检查是否为交易时间"""
        now = datetime.now()
        current_time = now.time()
        
        # 检查是否为交易日
        if not self.report_generator.is_trading_day():
            return False
        
        # 检查时间窗口 (9:25-9:29)
        start_time = datetime.strptime("09:25", "%H:%M").time()
        end_time = datetime.strptime("09:29", "%H:%M").time()
        
        return start_time <= current_time <= end_time
    
    def should_send_report(self) -> bool:
        """判断是否应该发送报告"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 检查今天是否已发送
        if self.report_sent_today and self.last_report_date == today:
            return False
        
        # 如果是新的一天，重置状态
        if self.last_report_date != today:
            self.report_sent_today = False
            self.last_report_date = today
        
        return True
    
    def execute_daily_analysis(self):
        """执行每日分析"""
        with self.execution_lock:
            try:
                now = datetime.now()
                today = now.strftime('%Y-%m-%d')
                current_time = now.strftime('%H:%M:%S')
                
                logging.info(f"🚀 开始执行交易日分析 - {today} {current_time}")
                
                # 检查执行条件
                if not self.is_trading_time():
                    logging.warning(f"⏰ 当前不在交易时间窗口内: {current_time}")
                    return
                
                if not self.should_send_report():
                    logging.info(f"📭 今日报告已发送，跳过执行")
                    return
                
                # 执行分析并发送报告
                logging.info("📊 开始生成和发送交易日报...")
                success = self.report_generator.send_daily_report()
                
                if success:
                    self.report_sent_today = True
                    self.last_report_date = today
                    logging.info(f"✅ 交易日报发送成功! {today} {current_time}")
                else:
                    logging.error(f"❌ 交易日报发送失败! {today} {current_time}")
                
            except Exception as e:
                logging.error(f"❌ 执行每日分析时出错: {e}")
    
    def setup_schedule(self):
        """设置定时任务"""
        # 在9:25-9:29时间段每分钟检查一次
        schedule.every().day.at("09:25").do(self.execute_daily_analysis)
        schedule.every().day.at("09:26").do(self.execute_daily_analysis)
        schedule.every().day.at("09:27").do(self.execute_daily_analysis)
        schedule.every().day.at("09:28").do(self.execute_daily_analysis)
        
        # 添加备用时间点 (如果9:25-9:29失败)
        schedule.every().day.at("09:30").do(self.execute_daily_analysis)
        
        # 可选：添加盘后补发时间
        schedule.every().day.at("15:05").do(self.execute_fallback_report)
        
        logging.info("⏰ 定时任务已设置:")
        logging.info("   📊 主要执行时间: 9:25-9:29 (每分钟)")
        logging.info("   🔄 备用执行时间: 9:30")
        logging.info("   📋 盘后补发时间: 15:05")
    
    def execute_fallback_report(self):
        """盘后补发报告"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            # 如果今天还没发送报告，则补发
            if not self.report_sent_today or self.last_report_date != today:
                logging.info("📋 执行盘后补发报告...")
                self.execute_daily_analysis()
            else:
                logging.info("📭 今日报告已发送，无需补发")
                
        except Exception as e:
            logging.error(f"❌ 盘后补发时出错: {e}")
    
    def start_scheduler(self):
        """启动调度器"""
        if self.is_running:
            logging.warning("⚠️ 调度器已在运行中")
            return
        
        self.is_running = True
        self.setup_schedule()
        
        logging.info("🟢 交易日调度器已启动")
        logging.info("📅 等待交易日执行时间...")
        
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(30)  # 每30秒检查一次
                
        except KeyboardInterrupt:
            logging.info("🛑 收到停止信号")
        except Exception as e:
            logging.error(f"❌ 调度器运行错误: {e}")
        finally:
            self.stop_scheduler()
    
    def stop_scheduler(self):
        """停止调度器"""
        self.is_running = False
        schedule.clear()
        logging.info("🔴 交易日调度器已停止")
    
    def run_test_mode(self):
        """测试模式运行"""
        logging.info("🧪 启动测试模式...")
        
        # 忽略时间和交易日限制，直接执行
        try:
            logging.info("📊 执行测试分析...")
            success = self.report_generator.send_daily_report()
            
            if success:
                logging.info("✅ 测试模式执行成功!")
            else:
                logging.error("❌ 测试模式执行失败")
                
        except Exception as e:
            logging.error(f"❌ 测试模式错误: {e}")
    
    def get_status(self) -> dict:
        """获取调度器状态"""
        now = datetime.now()
        return {
            'is_running': self.is_running,
            'current_time': now.strftime('%Y-%m-%d %H:%M:%S'),
            'is_trading_day': self.report_generator.is_trading_day(),
            'is_trading_time': self.is_trading_time(),
            'report_sent_today': self.report_sent_today,
            'last_report_date': self.last_report_date,
            'next_execution': self._get_next_execution_time()
        }
    
    def _get_next_execution_time(self) -> str:
        """获取下次执行时间"""
        try:
            jobs = schedule.get_jobs()
            if jobs:
                next_run = min(job.next_run for job in jobs)
                return next_run.strftime('%Y-%m-%d %H:%M:%S')
            return "未设置"
        except Exception:
            return "未知"

class SchedulerDaemon:
    """调度器守护进程"""
    
    def __init__(self):
        self.scheduler = TradingDayScheduler()
        self.daemon_thread = None
    
    def start_daemon(self):
        """启动守护进程"""
        if self.daemon_thread and self.daemon_thread.is_alive():
            logging.warning("⚠️ 守护进程已在运行")
            return
        
        self.daemon_thread = threading.Thread(
            target=self.scheduler.start_scheduler,
            daemon=True
        )
        self.daemon_thread.start()
        
        logging.info("👻 守护进程已启动")
    
    def stop_daemon(self):
        """停止守护进程"""
        self.scheduler.stop_scheduler()
        if self.daemon_thread:
            self.daemon_thread.join(timeout=5)
        logging.info("👻 守护进程已停止")
    
    def get_status(self):
        """获取状态"""
        return self.scheduler.get_status()

def create_startup_script():
    """创建启动脚本"""
    script_content = f"""#!/bin/bash
# CChanTrader-AI 交易日调度器启动脚本

cd /Users/yang
export PYTHONPATH=/Users/yang:$PYTHONPATH

# 启动调度器
python3 trading_day_scheduler.py --daemon

echo "📅 CChanTrader-AI 交易日调度器已启动"
echo "📝 日志文件: /Users/yang/trading_scheduler.log"
echo "🛑 停止命令: python3 trading_day_scheduler.py --stop"
"""
    
    script_path = '/Users/yang/start_scheduler.sh'
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    # 添加执行权限
    os.chmod(script_path, 0o755)
    
    logging.info(f"📝 启动脚本已创建: {script_path}")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='CChanTrader-AI 交易日调度器')
    parser.add_argument('--daemon', action='store_true', help='守护进程模式')
    parser.add_argument('--test', action='store_true', help='测试模式')
    parser.add_argument('--status', action='store_true', help='查看状态')
    parser.add_argument('--stop', action='store_true', help='停止调度器')
    
    args = parser.parse_args()
    
    if args.test:
        # 测试模式
        scheduler = TradingDayScheduler()
        scheduler.run_test_mode()
        
    elif args.status:
        # 查看状态
        scheduler = TradingDayScheduler()
        status = scheduler.get_status()
        print("📊 调度器状态:")
        for key, value in status.items():
            print(f"   {key}: {value}")
            
    elif args.daemon:
        # 守护进程模式
        daemon = SchedulerDaemon()
        try:
            daemon.start_daemon()
            print("📅 调度器守护进程已启动，按 Ctrl+C 停止...")
            # 保持主线程运行
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            print("\n🛑 正在停止调度器...")
            daemon.stop_daemon()
            
    elif args.stop:
        # 停止调度器 (简化版，实际需要进程管理)
        print("🛑 请使用 Ctrl+C 停止正在运行的调度器")
        
    else:
        # 直接运行模式
        scheduler = TradingDayScheduler()
        try:
            scheduler.start_scheduler()
        except KeyboardInterrupt:
            print("\n🛑 调度器已停止")

if __name__ == "__main__":
    # 创建启动脚本
    create_startup_script()
    
    # 运行主程序
    main()