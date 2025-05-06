from Sensors.TempPort import TempPort
import Resources.Settings as Settings
from State.States import States
import uasyncio as asyncio
from Logging.AppLogger import AppLogger
import Helpers.DeviceNames as DeviceNames

class TempSensors:

    _task = None

    def __init__(self, states:States):
        self.states = states
        self.logger = AppLogger()
        self.temp_senmsor_polling_time = Settings.TEMP_SENSOR_POLLING_TIME
        self.heater_temp_sensor = TempPort(DeviceNames.HEATER_TEMP_SENSORS_KEY, Settings.HEATER_TEMP_PIN)
        self.hot_water_line_sensor = TempPort(DeviceNames.HOT_WATER_TEMP_SENSORS_KEY, Settings.HWLT_SE1_PIN)
        
       
    def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._update_temperature())
            self.logger.info(f"TEMP SENSORS: Temperature sensor [{self.hot_water_line_sensor.name} and {self.heater_temp_sensor.name}] has start monitoring")

    def stop(self) -> None:
        if self._task:
            self._task.cancel() # type: ignore
            self._task = None
            self.logger.info("TEMP SENSORS: Temperature sensor monitoring has stoped")

    async def _update_temperature(self) -> None:
        while self._task is not None:
            await self._update_hot_water_line_temp_sensor()
            await self._update_heater_temp_sensor()
            await asyncio.sleep(self.temp_senmsor_polling_time)

    async def _update_hot_water_line_temp_sensor(self) -> None:
        try:
            sensor_name = self.hot_water_line_sensor.get_name()
            temp = await self.hot_water_line_sensor.read_temperature()
            self.states.update_temperature(sensor_name, round(temp, 1))
        except Exception as e:
            self.logger.error(f"TEMP SENSORS: Failed to upadte temperature for {self.hot_water_line_sensor.get_name()} sensor. Error: {e}")

    async def _update_heater_temp_sensor(self) -> None:
        try:
            sensor_name = self.heater_temp_sensor.get_name()
            temp = await self.heater_temp_sensor.read_temperature()
            self.states.update_temperature(sensor_name, round(temp, 1))
        except Exception as e:
            self.logger.error(f"TEMP SENSORS: Failed upadte temperature for {self.heater_temp_sensor.get_name()} sensor. Error: {e}")
