from Helpers.Singleton import Singleton
from Logging.Logger import *

class AppLogger(Singleton):
    
    def __init__(self):
        if hasattr(self, 'log'):
            return
        
        self.log = Logger("AppLogger")
        self.log.setLevel(DEBUG)
        formatter = Formatter("%(levelname)s:%(name)s: %(message)s")

        # Handler for console
        console_handler = StreamHandler()
        console_handler.setFormatter(formatter)
        self.log.addHandler(console_handler)


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
    

