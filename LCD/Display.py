import gc
import uasyncio as asyncio

import Helpers.Helpers as Helpers
import Helpers.LcdCustomSymbols as CustomSymbols
import Helpers.DisplayNames as DisplayNames
import Resources.Settings as Settings

from State.States import States
from Logging.AppLogger import AppLogger

from LCD.Screens.Screen import Screen
from LCD.Screens.HotWaterValveScreen import HotWaterValveScreen
from LCD.Screens.ColdWaterValveScreen import ColdWaterValveScreen
from LCD.Screens.LeakZone1Screen import LeakZone1Screen
from LCD.Screens.LeakZone2Screen import LeakZone2Screen
from LCD.Screens.HotWaterScreen import HotWaterScreen
from LCD.Screens.WaterHeaterScreen import WaterHeaterScreen
from LCD.Screens.StartingScreen import StartingScreen
from LCD.Screens.AlarmScreen import AlarmScreen
from LCD.Progress import Progress
from LCD.Screens.NetworkScreen import NetworkScreen

class Display:
    def __init__(self, states: States):
        from machine import Pin, I2C
        from .Driver.WSLCD1602RGB import WSLCD1602RGB

        self.states = states
        i2c = I2C(1, sda=Pin(Settings.SDA_PIN), scl=Pin(Settings.SCL_PIN), freq=400_000)
        self.lcd = WSLCD1602RGB(i2c, CustomSymbols.CUSTOM_SYMBOLS, Settings.LCD_NORMAL_BRIGHTNESS)
        self.logger = AppLogger()
        self.progress = Progress(self.lcd, self)
        self._screens: list[Screen] = []
        self._presented_screen = 0
        self._presented_screen_time_sec = Settings.PRESENTED_SCREEN_TIME_SEC
        self._task = None
        self._can_turn_sleep_mode = False
        self._presentation_mode_screens_timeout = 0

        self.show_starting_screen()

    def start(self):
        if self._task is None:
            self._task = asyncio.create_task(self._display_loop())
            self.logger.info("DISPLAY: Start screen presentation")

    def stop(self):
        if self._task:
            self._task.cancel()
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
                self.logger.info(f"DISPLAY: Remove screen, exist more: {self.is_exist_screens()}")
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
        self._screens.clear()
        self._screens.append(alarm_screen)
        self.stop()
        self._presented_screen = len(self._screens)
        alarm_screen.present()
        gc.collect()

    def reset_alarm(self):
        self.reset_brightness()
        self.show_carusel()
        self.restart()
        gc.collect()

    def show_progress(self, title:str, device_name:str,  progress:float):
        self.progress.update_progress(title, device_name,  progress)

    def add_new_progress_screens(self, screen: Screen):
        self.reset_brightness()
        self._can_turn_sleep_mode = False
        self._presented_screen_time_sec = 1
        # Remove all not progress scren
        self._screens = [s for s in self._screens if s.get_screen_name() is DisplayNames.PROGRESS_SCREEN_NAME]
        # Remove current screrean
        self._screens = [s for s in self._screens if s.get_device_name() is screen.get_device_name()]
        # Add the new progress screen
        self._screens.append(screen)
        self._presented_screen = len(self._screens)-1
        self.restart()
        gc.collect()

    def show_carusel(self, device_name=None):
        self._screens.clear()
        self._presented_screen_time_sec = 3
        self._screens = [
            NetworkScreen(self.lcd),
            HotWaterValveScreen(self.lcd, self.states),
            ColdWaterValveScreen(self.lcd, self.states),
            LeakZone1Screen(self.lcd, self.states),
            LeakZone2Screen(self.lcd, self.states),
            HotWaterScreen(self.lcd, self.states),
            WaterHeaterScreen(self.lcd, self.states),
        ]
        if device_name: 
            for i, screen in enumerate(self._screens):
                if screen.get_device_name() == device_name:
                    self._presented_screen = i
                    return
        self._presented_screen = 0
        self._can_turn_sleep_mode = True
        self._presentation_mode_screens_timeout = 0  
        self.restart()
        gc.collect()

    #MARK: Starting screens             
    def show_starting_screen(self):
        self.starting_screen = StartingScreen(self.lcd)
        self._screens = [screen for screen in self._screens if issubclass(type(screen), StartingScreen)]
        self.starting_screen.present()
    
    def update_initialization_status(self, status: str):
        """Update initialization status on starting screen"""
        if hasattr(self, 'starting_screen') and self.starting_screen:
            self.starting_screen.update_status(status)

    async def _display_loop(self):
        if not self._screens:
            self.logger.error("DISPLAY: No screens to present.")
            return

        while self._task:
            screen = Helpers.get_element_by_index(self._screens, self._presented_screen) or self._screens[0]
            screen.present()
            self._presented_screen = (self._presented_screen + 1) % len(self._screens)
            self._increment_sleep_mode_timer()
            await asyncio.sleep(self._presented_screen_time_sec)

    def _increment_sleep_mode_timer(self):
        if self._can_turn_sleep_mode:
            self._presentation_mode_screens_timeout += self._presented_screen_time_sec
            self._maybe_reduce_brightness()

    def _maybe_reduce_brightness(self):
        if self._presentation_mode_screens_timeout >= Settings.SLEEP_MODE_TIMEOUT:
            if self.lcd.get_brightness() != Settings.LCD_SLEEP_MODE_BRIGHTNESS:
                self.lcd.set_brightness(Settings.LCD_SLEEP_MODE_BRIGHTNESS)
                self.logger.info(f"DISPLAY: Bghtness decrease from {self.lcd.get_brightness()} to {Settings.LCD_SLEEP_MODE_BRIGHTNESS}")

    def reset_brightness(self):
        self._presentation_mode_screens_timeout = 0
        self.lcd.reset_brightness_to_default()
        self.logger.info(f"DISPLAY: Bghtness reseted")

    def show_error_screen(self, error_code, error_text=None):
        from LCD.Screens.ErrorScreen import ErrorScreen
        error_screen = ErrorScreen(self.lcd, error_code, error_text)
        self._screens.clear()
        self._screens.append(error_screen)
        self.stop()
        error_screen.present()
        gc.collect()