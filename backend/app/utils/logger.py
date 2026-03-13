# app/utils/logger.py
import logging
from datetime import datetime, timedelta, timezone
import os
import sys
import io

# 配置标准输出为 UTF-8 编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class BeijingLogger:
    def __init__(self, log_dir=None, log_level=logging.INFO):
        # 使用绝对路径
        if log_dir is None:
            # 当前目录的父目录下的logs目录
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.log_dir = os.path.join(base_dir, "logs")
        else:
            self.log_dir = log_dir
            
        print(f"Log directory set to: {self.log_dir}")  # 调试输出，确认日志目录
        self.log_level = log_level
        self.logger = None
        self.current_date = None
        self.update_logger()  # 初始化并配置 logger

    def update_logger(self):
        # 获取当前北京时间
        now = datetime.now(timezone.utc) + timedelta(hours=8)
        current_date = now.strftime('%Y-%m-%d')

        # 如果日期发生变化，更新日志文件
        if self.current_date != current_date:
            self.current_date = current_date
            log_file = os.path.join(self.log_dir, current_date + ".log")
            os.makedirs(self.log_dir, exist_ok=True)

            # 如果 logger 已经存在，移除旧的 handler
            if self.logger and self.logger.hasHandlers():
                self.logger.handlers.clear()

            # 创建新的 logger 和 handler
            self.logger = logging.getLogger("BeijingLogger")  # 确保获取的 logger 实例唯一
            self.logger.setLevel(self.log_level)
            self.logger.propagate = False  # 防止日志被传递到根logger

            # 避免重复添加 handler
            if not self.logger.hasHandlers():
                # 添加文件处理器
                try:
                    file_handler = logging.FileHandler(log_file, encoding="utf-8")
                    formatter = BeijingFormatter('%(asctime)s - %(levelname)s - %(message)s',
                                                datefmt='%Y-%m-%d %H:%M:%S')
                    file_handler.setFormatter(formatter)
                    self.logger.addHandler(file_handler)
                    
                    # 添加控制台处理器
                    console_handler = logging.StreamHandler()
                    console_handler.setFormatter(formatter)
                    self.logger.addHandler(console_handler)
                    
                    # 输出日志路径信息
                    self.logger.info(f"Logger initialized. Logging to: {log_file}")
                except Exception as e:
                    print(f"Error setting up logger: {str(e)}")
                    # 如果无法创建文件处理器，至少添加一个控制台处理器
                    console_handler = logging.StreamHandler()
                    formatter = BeijingFormatter('%(asctime)s - %(levelname)s - %(message)s',
                                                datefmt='%Y-%m-%d %H:%M:%S')
                    console_handler.setFormatter(formatter)
                    self.logger.addHandler(console_handler)

    def get_logger(self):
        return self.LoggerWrapper(self)  # 使用包装类以实现自动更新日志文件

    class LoggerWrapper:
        def __init__(self, parent_logger):
            self.parent_logger = parent_logger

        def __getattr__(self, attr):
            """
            使用此方法来动态代理 logger 的方法，确保每次调用时检查日期
            """
            # 每次调用 logger 的方法前，更新日志文件
            self.parent_logger.update_logger()
            return getattr(self.parent_logger.logger, attr)

class BeijingFormatter(logging.Formatter):
    def converter(self, timestamp):
        # 使用北京时间
        dt = datetime.fromtimestamp(timestamp, timezone.utc) + timedelta(hours=8)
        return dt

    def formatTime(self, record, datefmt=None):
        dt = self.converter(record.created)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.strftime('%Y-%m-%d %H:%M:%S')

    def format(self, record):
        # 将日志消息强制转换为 UTF-8 编码
        record.msg = self.ensure_utf8(record.msg)
        return super().format(record)

    def ensure_utf8(self, message):
        if isinstance(message, bytes):
            return message.decode('utf-8', errors='replace')
        elif isinstance(message, str):
            try:
                return message.encode('utf-8', errors='replace').decode('utf-8')
            except UnicodeEncodeError:
                return message.encode('utf-8', errors='replace').decode('utf-8')
        else:
            return str(message)
