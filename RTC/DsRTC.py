import network
import ntptime
import time
import uasyncio as asyncio
import Resources.Settings as Settings
from machine import Pin, I2C, RTC
from Helpers.Singleton import Singleton
from Logging.AppLogger import AppLogger
from .Driver.DS3231 import DS3231
from Buzzers.Buzzers import Buzzers
from Helpers.WiFiManager import WiFiManager

class DsRTC(Singleton):

    def __init__(self):
        if not hasattr(self, '_ds'): 
            self._logger = AppLogger()
            self._buzzer = Buzzers()
            self._action_handler = None
            self._ds = DS3231(I2C(1, sda=Pin(Settings.SDA_PIN), scl=Pin(Settings.SCL_PIN), freq=400000))
            self._alarm_pin = Pin(Settings.DSDTC_ALARM_PIN, Pin.IN)
            self._alarm_pin.irq(trigger=Pin.IRQ_FALLING, handler=self.alarm_triggered)
            self._set_time_from_ds()
    
    # MARK: Public
    def get_ds_rtc_datetime(self) -> tuple:
        return self._ds.datetime() # type: ignore
    
    def set_every_day_alarm(self, hour: int, minute: int, second: int, action_handler):
        if not (0 <= hour <= 23):
            raise ValueError("The clock must be between 0 and 23")
        if not (0 <= minute <= 59):
            raise ValueError("Minutes must be between 0 and 59")
        if not (0 <= second <= 59):
            raise ValueError("Seconds must be between 0 and 59")

        self._action_handler = action_handler
        adjusted_hour = (hour - Settings.TIME_ZONE_OFFSET) % 24
        alarm_time = (second, minute, adjusted_hour)
        self._ds.alarm1(alarm_time, match=self._ds.AL1_MATCH_HMS, int_en=True, weekday=False)
        self._logger.info(f'DSRTC: Set every day alarm to LOCAL:{hour}:{minute}:{second} (GMT:{adjusted_hour}:{minute}:{second}). Current: {self._ds.datetime()}')


    async def update_time(self):
        if self._ds.OSF():
            await self._set_time_from_ntp()
        else:
            self._set_time_from_ds()
            
    def get_datetime_iso8601(self)->str:
        dt:tuple = time.localtime(time.time() + Settings.TIME_ZONE_OFFSET * 60 * 60) # type: ignore
        # ISO 8601 format: YYYY-MM-DDTHH:MM:SS
        return "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}".format(dt[0], dt[1], dt[2], dt[3], dt[4], dt[5])

    def get_datetime_ddmmyy(self)->str:
        dt:tuple = time.localtime(time.time() + Settings.TIME_ZONE_OFFSET * 60 * 60) # type: ignore
        # Format: dd.mm.yy HH:mm
        return "{:02d}.{:02d}.{:02d} {:02d}:{:02d}".format(dt[2], dt[1], dt[0] % 100, dt[3], dt[4])

    # MARK: HELPERS
    def _set_time_from_ds(self) -> None:
        tm:tuple = self._ds.datetime()  # type: ignore #
        RTC().datetime(tm)
        self._logger.info(f'DSRTC: DsRTC time updated from DS3231: {self.get_datetime_iso8601()}')

    async def _set_time_from_ntp(self) -> None:
        try:
            wifiManager = WiFiManager()
            if await wifiManager.connect_wifi():
                tmn = await self._get_time_from_ntp()
                self._ds.datetime(tmn)
                self._set_time_from_ds() 
                self._logger.info(f'DSRTC: Time updated from NTP: {self.get_datetime_iso8601()}')
            else:
                self._logger.error('DSRTC: Failed to connect to WiFi for NTP sync')
        except Exception as e:
            self._logger.error(f'DSRTC: Failed to set time from NTP. EXCEPTION: {e}')
            return None
       
    # Get NTP time and adjust for time zone
    async def _get_time_from_ntp(self) ->tuple:
        try:
            ntptime.settime()
            return time.localtime(ntptime.time())
        except Exception as e:
            raise ValueError(f"DSRTC: Failed to get time from NTP: {Settings.NTP_SERVER}. EXCEPTION: {e}")
        
                
    def alarm_triggered(self, pin):
        self._logger.info(f'DSRTC: Timer ALARM tgriggered')
        if self._action_handler:
            self._action_handler()
