import psutil
import os

from manager import log_manager

class ResourceMonitor:
    def __init__(self, logger: log_manager.Logger) -> None:
        self.logger = logger

    def print_current_resource_usage(self):
        log_msg = ""
        curr_pid = os.getpid()

        for process in psutil.process_iter():
            if curr_pid == process.pid:
                # log_msg = f"프로세스 정보 \n이름 : {process.name()} \nPID : {process.pid} \n현재 시스템 리소스 사용량 \nCPU : {process.cpu_percent(interval=0.1)}% \nRAM : {round(process.memory_percent(), 3)}%"
                log_msg = f"프로세스 정보 \n이름 : {process.name()} \nPID : {process.pid} \n현재 시스템 리소스 사용량 \nRAM : {round(process.memory_percent(), 3)}%"
                break
        self.logger.log_info(log_msg)