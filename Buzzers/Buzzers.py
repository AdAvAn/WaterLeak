from Helpers.Singleton import Singleton
from Buzzers.AlarmBuzzer import AlarmBuzzer
from Buzzers.ControlBuzzer import ControlBuzzer

class Buzzers(Singleton):
    def __init__(self):
        if not hasattr(self, 'alarm'): 
            self.alarm = AlarmBuzzer()
            self.control = ControlBuzzer()