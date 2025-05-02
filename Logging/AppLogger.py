from Helpers.Singleton import Singleton
from Logging.Logger import *
from Logging.RotatingFileHandler import RotatingFileHandler

class AppLogger(Singleton):
    
    def __init__(self):
        if hasattr(self, 'log'):
            return
        
        log_file_name = "app.log"
        self.log = Logger("AppLogger")
        self.log.setLevel(DEBUG)
        formatter = Formatter("%(levelname)s:%(name)s: %(message)s")

        # Handler для консоли
        console_handler = StreamHandler()
        console_handler.setFormatter(formatter)
        self.log.addHandler(console_handler)

        # Handler для записи в файл
        # file_handler = FileHandler("logfile.log")
        # file_handler.setFormatter(formatter)
        # self.log.addHandler(file_handler)

        # RotatingFileHandler для ротации логов
        rfh_handler = RotatingFileHandler(log_file_name, maxBytes=512, backupCount=1)
        rfh_handler.setFormatter(formatter)
        self.log.addHandler(rfh_handler)

    def debug(self, msg, *args):
        self.log.debug(msg, *args)
    
    def info(self, msg, *args):
        self.log.info(msg, *args)
    
    def warning(self, msg, *args):
        self.log.warning(msg, *args)
    
    def error(self, msg, *args):
        self.log.error(msg, *args)
    
    def critical(self, msg, *args):
        self.log.critical(msg, *args)
    

