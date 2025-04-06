import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
import inspect

class Logger:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        # 创建logs目录
        self.log_dir = "logs"
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            
        # 生成日志文件名，格式：logs/app_年月日.log
        self.log_file = os.path.join(
            self.log_dir,
            f"app_{datetime.now().strftime('%Y%m%d')}.log"
        )
        
        # 创建logger实例
        self.logger = logging.getLogger('app_logger')
        self.logger.setLevel(logging.DEBUG)
        
        # 日志格式
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(caller_file)s:%(caller_line)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        
        # 文件处理器（支持日志轮转）
        file_handler = RotatingFileHandler(
            self.log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        
        # 添加处理器
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        
        self._initialized = True
    
    def _get_caller_info(self):
        """获取调用者的信息"""
        frame = inspect.currentframe()
        # 跳过当前方法
        frame = frame.f_back
        # 跳过装饰器方法
        while frame.f_code.co_filename.endswith('logger.py'):
            frame = frame.f_back
        return frame
    
    def debug(self, message):
        frame = self._get_caller_info()
        self.logger.debug(message, extra={
            'caller_file': frame.f_code.co_filename,
            'caller_line': frame.f_lineno
        })
    
    def info(self, message):
        frame = self._get_caller_info()
        self.logger.info(message, extra={
            'caller_file': frame.f_code.co_filename,
            'caller_line': frame.f_lineno
        })
    
    def warning(self, message):
        frame = self._get_caller_info()
        self.logger.warning(message, extra={
            'caller_file': frame.f_code.co_filename,
            'caller_line': frame.f_lineno
        })
    
    def error(self, message):
        frame = self._get_caller_info()
        self.logger.error(message, extra={
            'caller_file': frame.f_code.co_filename,
            'caller_line': frame.f_lineno
        })
    
    def critical(self, message):
        frame = self._get_caller_info()
        self.logger.critical(message, extra={
            'caller_file': frame.f_code.co_filename,
            'caller_line': frame.f_lineno
        })
    
    def exception(self, message):
        frame = self._get_caller_info()
        self.logger.exception(message, extra={
            'caller_file': frame.f_code.co_filename,
            'caller_line': frame.f_lineno
        })

# 创建全局logger实例
logger = Logger()