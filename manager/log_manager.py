from enum import IntEnum
from datetime import datetime

class LogLevel(IntEnum):
    TRACE = 1
    DEBUG = 2
    INFO = 3
    WARN = 4
    ERROR = 5
    FATAL = 6

class LogType(IntEnum):
    BUILD = 1
    DEBUG = 2

class Logger:
    def __init__(self, log_type: LogType):
        self.log_type = log_type
        self.log_stack = []
        
    def log_trace(self, log_msg):
        now = datetime.now()
        msg = f"[{now.strftime('%Y-%m-%d %H:%M:%S')}][{LogLevel.TRACE.name}]{log_msg}"
        self.log_stack.append(msg)
        if self.log_type.value >= 2:
            print(msg)
    
    def log_debug(self, log_msg):
        now = datetime.now()
        msg = f"[{now.strftime('%Y-%m-%d %H:%M:%S')}][{LogLevel.DEBUG.name}]{log_msg}"
        self.log_stack.append(msg)
        if self.log_type.value >= 2:
            print(msg)
            
    def log_info(self, log_msg):
        now = datetime.now()
        msg = f"[{now.strftime('%Y-%m-%d %H:%M:%S')}][{LogLevel.INFO.name}]{log_msg}"
        print(msg)
        self.log_stack.append(msg)
        
    def log_warn(self, log_msg):
        now = datetime.now()
        msg = f"[{now.strftime('%Y-%m-%d %H:%M:%S')}][{LogLevel.WARN.name}]{log_msg}"
        print(msg)
        self.log_stack.append(msg)
        
    def log_error(self, log_msg):
        now = datetime.now()
        msg = f"[{now.strftime('%Y-%m-%d %H:%M:%S')}][{LogLevel.ERROR.name}]{log_msg}"
        print(msg)
        self.log_stack.append(msg)
        self.save_log()
        
    def log_fatal(self, log_msg):
        now = datetime.now()
        msg = f"[{now.strftime('%Y-%m-%d %H:%M:%S')}][{LogLevel.FATAL.name}]{log_msg}"
        print(msg)
        self.log_stack.append(msg)
        self.save_log()
        
    def save_log(self):
        file_path = "log.txt"
        with open(file_path, "w", encoding='UTF-8') as file:
            for log in self.log_stack:
                file.write(log + "\n")
                
        self.log_stack.clear()
        del self.log_stack
        self.log_stack = []