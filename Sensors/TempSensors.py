from Sensors.TempPort import TempPort
from Sensors.TempPortStub import TempPortStub
import Resources.Settings as Settings
from State.States import States
import uasyncio as asyncio
from Logging.AppLogger import AppLogger
import Helpers.DeviceNames as DeviceNames

class TempSensors:

    _task = None

    def __init__(self, states: States):
        self.states = states
        self.logger = AppLogger()
        
        # Error counters for each sensor
        self.hot_water_error_count = 0
        self.heater_error_count = 0
        self.max_consecutive_errors = 5
        
        # Sensor failure flags
        self.hot_water_sensor_failed = False
        self.heater_sensor_failed = False
        
        # Optimization: Temperature write frequency control
        self.hot_water_write_counter = 0
        self.heater_write_counter = 0
        self.temp_write_frequency = getattr(Settings, 'TEMP_WRITE_FREQUENCY', 2)
        
        # Temperature change threshold to avoid writing minor fluctuations
        self.temp_change_threshold = 0.5  # Only write if temp changed by at least 0.5°C
        self.last_written_temps = {}
        
        # Try to initialize heater temperature sensor
        try:
            self.heater_temp_sensor = TempPort(DeviceNames.HEATER_TEMP_SENSORS_KEY, Settings.HEATER_TEMP_PIN)
            self.logger.info(f"Heater temperature sensor initialized successfully on pin {Settings.HEATER_TEMP_PIN}")
        except Exception as e:
            self.logger.warning(f"Failed to initialize heater temp sensor on pin {Settings.HEATER_TEMP_PIN}: {e}")
            self.heater_sensor_failed = True
            self.heater_temp_sensor = TempPortStub(
                DeviceNames.HEATER_TEMP_SENSORS_KEY, 
                Settings.HEATER_TEMP_PIN, 
                f"Init failed: {e}"
            )
            
        # Try to initialize hot water line sensor
        try:
            self.hot_water_line_sensor = TempPort(DeviceNames.HOT_WATER_TEMP_SENSORS_KEY, Settings.HWLT_SE1_PIN)
            self.logger.info(f"Hot water temperature sensor initialized successfully on pin {Settings.HWLT_SE1_PIN}")
        except Exception as e:
            self.logger.warning(f"Failed to initialize hot water temp sensor on pin {Settings.HWLT_SE1_PIN}: {e}")
            self.hot_water_sensor_failed = True
            self.hot_water_line_sensor = TempPortStub(
                DeviceNames.HOT_WATER_TEMP_SENSORS_KEY, 
                Settings.HWLT_SE1_PIN, 
                f"Init failed: {e}"
            )
       
    def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._update_temperature())
            
            # Count working sensors and stubs
            working_sensors = []
            stub_sensors = []
            
            if not self.hot_water_sensor_failed:
                working_sensors.append(f"{self.hot_water_line_sensor.name} (pin {Settings.HWLT_SE1_PIN})")
            else:
                stub_sensors.append(f"{self.hot_water_line_sensor.name} (pin {Settings.HWLT_SE1_PIN})")
                
            if not self.heater_sensor_failed:
                working_sensors.append(f"{self.heater_temp_sensor.name} (pin {Settings.HEATER_TEMP_PIN})")
            else:
                stub_sensors.append(f"{self.heater_temp_sensor.name} (pin {Settings.HEATER_TEMP_PIN})")
            
            if working_sensors:
                self.logger.info(f"TEMP SENSORS: Working temperature sensors: {working_sensors}")
            if stub_sensors:
                self.logger.warning(f"TEMP SENSORS: Using stubs for: {stub_sensors}")
            if not working_sensors:
                self.logger.warning("TEMP SENSORS: No working temperature sensors found, all using stubs")

    def stop(self) -> None:
        if self._task:
            self._task.cancel()
            self._task = None
            self.logger.info("TEMP SENSORS: Temperature sensor monitoring has stopped")

    async def _update_temperature(self) -> None:
        while self._task is not None:
            await self._update_hot_water_line_temp_sensor()
            await self._update_heater_temp_sensor()
            await asyncio.sleep(Settings.TEMP_SENSOR_POLLING_TIME)

    async def _update_hot_water_line_temp_sensor(self) -> None:
        sensor_name = self.hot_water_line_sensor.get_name()
        
        # If sensor initially failed (using stub), just update state
        if self.hot_water_sensor_failed:
            temp_value = await self.hot_water_line_sensor.read_temperature()
            self._update_temperature_with_optimization(sensor_name, temp_value, 'hot_water')
            return
            
        # Attempt to read from real sensor
        try:
            temp = await self.hot_water_line_sensor.read_temperature()
            
            # Check for reasonable temperature values
            if isinstance(temp, (int, float)) and -10 <= temp <= 100: 
                rounded_temp = round(temp, 1)
                self._update_temperature_with_optimization(sensor_name, rounded_temp, 'hot_water')
                self.hot_water_error_count = 0
            else:
                raise ValueError(f"Temperature out of range or invalid: {temp}")
                
        except Exception as e:
            self.hot_water_error_count += 1
            self.logger.error(f"Hot water temp sensor error #{self.hot_water_error_count}: {e}")
            
            if self.hot_water_error_count >= self.max_consecutive_errors:
                self.hot_water_sensor_failed = True
                self.logger.critical("Hot water temperature sensor marked as FAILED, switching to stub")
                self.states.update_temperature(sensor_name, "ERROR")
                # Replace with stub
                self.hot_water_line_sensor = TempPortStub(
                    sensor_name, 
                    Settings.HWLT_SE1_PIN, 
                    "Sensor failed during operation"
                )
            
            if self.hot_water_error_count == 10:
                await self._try_reinitialize_hot_water_sensor()

    async def _update_heater_temp_sensor(self) -> None:
        sensor_name = self.heater_temp_sensor.get_name()
        
        # If the sensor was not working initially (a stub is used), simply update the state
        if self.heater_sensor_failed:
            temp_value = await self.heater_temp_sensor.read_temperature()
            self._update_temperature_with_optimization(sensor_name, temp_value, 'heater')
            return
            
        try:
            temp = await self.heater_temp_sensor.read_temperature()
            
            # Check for reasonable temperature values
            if isinstance(temp, (int, float)) and -10 <= temp <= 100:
                rounded_temp = round(temp, 1)
                self._update_temperature_with_optimization(sensor_name, rounded_temp, 'heater')
                self.heater_error_count = 0
            else:
                raise ValueError(f"Temperature out of range or invalid: {temp}")
                
        except Exception as e:
            self.heater_error_count += 1
            self.logger.error(f"Heater temp sensor error #{self.heater_error_count}: {e}")
            
            if self.heater_error_count >= self.max_consecutive_errors:
                self.heater_sensor_failed = True
                self.logger.critical("Heater temperature sensor marked as FAILED, switching to stub")
                self.states.update_temperature(sensor_name, "ERROR")
               
                self.heater_temp_sensor = TempPortStub(
                    sensor_name, 
                    Settings.HEATER_TEMP_PIN, 
                    "Sensor failed during operation"
                )

    def _update_temperature_with_optimization(self, sensor_name: str, temp_value, sensor_type: str):
        """Update temperature with write frequency optimization and change threshold"""
        
        # Handle error states - always update immediately
        if temp_value in ["No temp sensor", "ERROR"]:
            self.states.update_temperature(sensor_name, temp_value)
            return
        
        # For numeric temperatures, apply optimization
        if isinstance(temp_value, (int, float)):
            # Check if temperature changed significantly
            last_temp = self.last_written_temps.get(sensor_name)
            temp_changed_significantly = (
                last_temp is None or 
                abs(temp_value - last_temp) >= self.temp_change_threshold
            )
            
            # Update write counter
            if sensor_type == 'hot_water':
                self.hot_water_write_counter += 1
                should_write_by_frequency = (self.hot_water_write_counter >= self.temp_write_frequency)
                if should_write_by_frequency:
                    self.hot_water_write_counter = 0
            else:  # heater
                self.heater_write_counter += 1
                should_write_by_frequency = (self.heater_write_counter >= self.temp_write_frequency)
                if should_write_by_frequency:
                    self.heater_write_counter = 0
            
            # Decide whether to write
            should_write = temp_changed_significantly or should_write_by_frequency
            
            if should_write:
                self.states.update_temperature(sensor_name, temp_value)
                self.last_written_temps[sensor_name] = temp_value
                self.logger.debug(f"TEMP SENSORS: Updated {sensor_name}: {temp_value}°C (significant change: {temp_changed_significantly})")
            else:
                # Update in-memory state without writing to disk
                # This requires a new method in states that updates without scheduling write
                self._update_memory_only(sensor_name, temp_value)
                self.logger.debug(f"TEMP SENSORS: Memory-only update {sensor_name}: {temp_value}°C")
        else:
            # For non-numeric values, update normally
            self.states.update_temperature(sensor_name, temp_value)

    def _update_memory_only(self, sensor_name: str, temp_value):
        """Update temperature in memory without scheduling disk write"""
        try:
            device = self.states.states[DeviceNames.TEMP_SECTION_KEY].get(sensor_name)
            if device:
                current_state = device.get_state()
                if current_state != temp_value:
                    # Update state without notifying (to avoid disk write scheduling)
                    device.set_state(new_value=temp_value, can_notify=False)
                    
        except Exception as e:
            self.logger.error(f"TEMP SENSORS: Failed to update memory-only for {sensor_name}: {e}")

    async def _try_reinitialize_hot_water_sensor(self):
        """Attempt to reinitialize hot water sensor"""
        try:
            self.logger.info("Attempting to reinitialize hot water temp sensor...")
            test_sensor = TempPort(DeviceNames.HOT_WATER_TEMP_SENSORS_KEY, Settings.HWLT_SE1_PIN)
            
            # Test reading
            test_temp = await test_sensor.read_temperature()
            if isinstance(test_temp, (int, float)) and -10 <= test_temp <= 100:
                self.hot_water_line_sensor = test_sensor
                self.hot_water_sensor_failed = False
                self.hot_water_error_count = 0
                self.logger.info("Hot water temp sensor successfully reinitialized")
            else:
                raise ValueError(f"Test reading failed: {test_temp}")
                
        except Exception as e:
            self.logger.error(f"Failed to reinitialize hot water temp sensor: {e}")
            
            self.hot_water_line_sensor = TempPortStub(
                DeviceNames.HOT_WATER_TEMP_SENSORS_KEY, 
                Settings.HWLT_SE1_PIN, 
                f"Reinit failed: {e}"
            )
    
    def has_working_sensors(self) -> bool:
        """Check if there is at least one working sensor"""
        return not self.heater_sensor_failed or not self.hot_water_sensor_failed