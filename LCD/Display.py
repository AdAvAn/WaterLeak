import gc
import uasyncio as asyncio
import Helpers.Helpers as Helpers
import Helpers.LcdCustomSymbols as CustomSymbols
import Helpers.DisplayNames as DisplayNames
import Resources.Settings as Settings
import LCD.Progress 
from machine import Pin,I2C
from State.States import States
from Buzzers.Buzzers import Buzzers
from Logging.AppLogger import AppLogger
from .Driver.WSLCD1602RGB import WSLCD1602RGB


# from LCD.Screens.ProgressScreen import ProgressScreen
from LCD.Screens.Screen import Screen
from LCD.Screens.HotWaterValveScreen import HotWaterValveScreen
from LCD.Screens.ColdWaterValveScreen import ColdWaterValveScreen
from LCD.Screens.LeakZone1Screen import LeakZone1Screen
from LCD.Screens.LeakZone2Screen import LeakZone2Screen
from LCD.Screens.HotWaterScreen import HotWaterScreen
from LCD.Screens.WaterHeaterScreen import WaterHeaterScreen
from LCD.Screens.HeaterPowerSwithScreen import HeaterPowerSwithScreen
from LCD.Screens.StartingScreen import StartingScreen
from LCD.Screens.AlarmScreen import AlarmScreen
from LCD.Screens.ProgressScreen import ProgressScreen
from LCD.Screens.ErrorScreen import ErrorScreen

class Display:

    _presented_screen:int = 0
    _presented_screen_time_sec:int = Settings.PRESENTED_SCREEN_TIME_SEC
    _task = None
    _can_turn_sleep_mode = False
    _presentation_mode_screens_timout = 0

    def __init__(self, states: States):
        self.states = states
        i2c = I2C(id=1, sda=Pin(Settings.SDA_PIN), scl=Pin(Settings.SCL_PIN), freq=400000)
        self.lcd = WSLCD1602RGB(i2c, CustomSymbols.CUSTOM_SYMBOLS, Settings.LCD_NORMAL_BRIGHTNESS)
        self.logger = AppLogger()
        self.buzzers = Buzzers()
        self.progress = LCD.Progress.Progress(self.lcd, self)
        self._screens: list[Screen] = list()
        self.show_starting_screen()
        

    def start(self):
        if self._task is None:
            self._task = asyncio.create_task(self._display_loop())
            self.logger.info("DISPLAY: Start screen presentation")

    def stop(self):
        if self._task:
            self._task.cancel() # type: ignore
            self._task = None
            self.logger.info("DISPLAY: Stop screen presentation")
    
    def restart(self):
        self.logger.info("DISPLAY: Restarting screen presentation")
        self.stop() 
        self.start()  

    def get_screen_at_device_name(self, device_name):
        for screen in self._screens:
            if screen.get_device_name() == device_name:
                return screen
        return None
    
    def remove_screen(self, r_screan:Screen) -> bool:
        for screen in self._screens:
            if screen == r_screan:
                self._screens.remove(screen)
                print("remove_screen, exist more: ", self.is_exist_screens())
                return True
        return False
    
    def is_exist_screens(self) -> bool:
        return True if self.gen_number_of_screens() > 0 else False
    
    def gen_number_of_screens(self) -> int:
        return len(self._screens)

    # Alarm screens
    def show_alarm(self, title:str, text = None):
        self.reset_brightness()
        self._can_turn_sleep_mode = False
        alarm_screen = AlarmScreen(self.lcd)
        alarm_screen.update_alarm(title, text)
        self._screens = []
        self._screens.append(alarm_screen)
        self.stop()
        self._presented_screen = len(self._screens)
        alarm_screen.present()
        gc.collect()
    
    def reset_alarm(self):
        self.show_default_screens()
        self.restart()
        gc.collect()

    #MARK: Progress screens
    def show_progress(self, title, device_name,  progress):
        self.progress.update_progress(title, device_name,  progress)

    def add_new_progress_screens(self, screen: Screen):
        self.reset_brightness()
        self._can_turn_sleep_mode = False
        self._presented_screen_time_sec = 1
        self._screens = [screen for screen in self._screens if screen.get_screen_name() is DisplayNames.PROGRESS_SCREEN_NAME]
        self._screens.append(screen)
        self._presented_screen = len(self._screens)-1
        self.restart()

    #MARK: Default screens
    def show_default_screens(self, device_name = None):
        self._screens.clear()
        self._presented_screen_time_sec = 3
        self._screens = [
            HotWaterValveScreen(self.lcd, self.states),
            ColdWaterValveScreen(self.lcd, self.states),
            LeakZone1Screen(self.lcd, self.states),
            LeakZone2Screen(self.lcd, self.states),
            HotWaterScreen(self.lcd, self.states),
            HeaterPowerSwithScreen(self.lcd, self.states),
            WaterHeaterScreen(self.lcd, self.states)
        ]
        if device_name: 
            for i, x in enumerate(self._screens):
                if x.get_device_name() == device_name:
                    self._presented_screen = i
                    return
        self._presented_screen = 0
        self._can_turn_sleep_mode = True
        self._presentation_mode_screens_timout = 0
        self.restart()
        gc.collect()
    
    #MARK: Starting screens        
    def show_starting_screen(self):
        loading = StartingScreen(self.lcd)
        self._screens = [screen for screen in self._screens if issubclass(type(screen), StartingScreen)]
        loading.present()

    async def _display_loop(self):
        if not self._screens:
            self.logger.error("DISPLAY: No screens to present.")
            return 

        while self._task is not None:
            screen = Helpers.get_element_by_index(self._screens, self._presented_screen) or self._screens[0]
            screen.present()
            self._presented_screen = (self._presented_screen + 1) % len(self._screens)
            self._incress_sleep_mode_timer()
            await asyncio.sleep(self._presented_screen_time_sec)

    def _incress_sleep_mode_timer(self):
        if self._can_turn_sleep_mode:
            self._presentation_mode_screens_timout += self._presented_screen_time_sec
            self._reduce_brightness()

    def _reduce_brightness(self):
        if self._can_turn_sleep_mode and self._presentation_mode_screens_timout >= Settings.SLEEP_MODE_MODE_TIMEOUNT :
            if self.lcd.get_brightness() != Settings.SLEEP_MODE_MODE_TIMEOUNT:
                self.lcd.set_brightness(Settings.SLEEP_MODE_MODE_TIMEOUNT)
            
    def reset_brightness(self):
        self._presentation_mode_screens_timout = 0
        self.lcd.reset_brightness_to_default()
       

    #MARK: Error screen
    def show_error_screen(self, error_code, error_text=None):
        from LCD.Screens.ErrorScreen import ErrorScreen
        self.reset_brightness()
        error_screen = ErrorScreen(self.lcd, error_code, error_text)
        self._screens = []
        self._screens.append(error_screen)
        self.stop()
        error_screen.present()
        gc.collect()