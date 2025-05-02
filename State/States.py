import gc
import ujson
from State.TemperatureSensorState import TemperatureSensorState
from State.ValveState import ValveState
from State.WaterLeakSensorState import WaterLeakSensorState
from State.HeaterSwithState import HeaterSwithState
from Resources.Errors import *
import Helpers.DeviceNames as DeviceNames
from Logging.AppLogger import AppLogger

class States:
   
    def __init__(self):
        self.state_file = "State/state.json"
        self.logger = AppLogger()
        self.states: dict = {}
        self._make_init_states()
        self._load_states_from_file()

    # MARK: Setters
    # MARK: SET States
    def update_valve_state(self, device_name:str, new_state) -> None:
        self._update_device_state(DeviceNames.VALVE_SECTION_KEY, device_name, new_state)

    def update_leak_sensor_state(self, device_name:str, new_state) -> None:
        self._update_device_state(DeviceNames.LEAK_SECTION_KEY, device_name, new_state)

    def update_temperature(self, device_name:str, new_state) -> None:
        self._update_device_state(DeviceNames.TEMP_SECTION_KEY, device_name, new_state)
    
    def update_heater_state(self, device_name:str, new_state) -> None:
        self._update_device_state(DeviceNames.HEATER_SECTION_KEY, device_name, new_state)

    # MARK: Getters
    # MARK: GET States
    def get_valve_state(self, device_name:str):
        return self._get_device_state(DeviceNames.VALVE_SECTION_KEY, device_name)

    def get_leak_sensor_state(self, device_name:str):
        return self._get_device_state(DeviceNames.LEAK_SECTION_KEY, device_name)
        
    def get_temperature(self, device_name:str):
        return self._get_device_state(DeviceNames.TEMP_SECTION_KEY, device_name)
    
    def get_heater_state(self, device_name:str):
        return self._get_device_state(DeviceNames.HEATER_SECTION_KEY, device_name)


    # MARK: GET Preview States
    def get_valve_preview_state(self, device_name:str):
        return self._get_preview_device_state(DeviceNames.VALVE_SECTION_KEY, device_name)
    
    def get_leak_sensor_preview_state(self, device_name:str):
        return self._get_preview_device_state(DeviceNames.LEAK_SECTION_KEY, device_name)
    
    def get_temperature_preview_state(self, device_name:str):
        return self._get_preview_device_state(DeviceNames.TEMP_SECTION_KEY, device_name)

    def get_heater_preview_state(self, device_name:str):
        return self._get_preview_device_state(DeviceNames.HEATER_SECTION_KEY, device_name)
    

    # MARK: Helpers

    def _update_device_state(self, device_type:str, device_name:str, new_state):
        device = self.states[device_type].get(device_name)
        if device is None:
            raise ValueError(f"STATES: {device_name} not found in section {device_type}")
        current_state = device.get_state()
        if current_state != new_state:
            device.set_state(new_value=new_state, can_notify=True)
            self.logger.debug(f"STATES: The state of {device_name} has changed, previous: {current_state}, new: {new_state}")
            self._update_state_changes_in_file(device_type, device_name)

    def _get_device_state(self, device_type, device_name):
        try:
            device = self.states[device_type].get(device_name)
            if device is None:
                raise ValueError(f"STATES: Device {device_type} by name {device_name} not found")
            return device.get_state()
        except Exception as e:
            self.logger.error(f"STATES: Failed to get device {device_type} state for {device_name}. Error: {e}")
            return None
        
    def _get_preview_device_state(self, device_type, device_name):
        try:
            device = self.states[device_type].get(device_name)
            if device is None:
                 raise ValueError(f"STATES: Device {device_type} by name {device_name} not found")
            return device.get_preview_state()
        except Exception as e:
            self.logger.error(f"STATES: Failed to get device {device_type} state for {device_name}. Error: {e}")
            return None


    def _load_states_from_file(self):
        try:
            with open(self.state_file, 'r') as file:
                data = ujson.load(file)
                self._apply_loaded_states(data)
        except OSError as e:
            if e.args[0] == 2:  
                self.logger.warning(f"STATES: State file {self.state_file} not found. Creating a new one with default states.")
                self._create_empty_states_file() 
            else:
                exception = AppException(Errors.FAILED_READ_STATES_FILE(), e)
                self.logger.critical(exception.get_error_message())
                raise exception
        except Exception as e:
            exception = AppException(Errors.FAILED_READ_STATES_FILE(), e)
            self.logger.critical(exception.get_error_message())
            raise exception


    def _apply_loaded_states(self, data):
        for device_type in self.states:
            for device_name, state_info in data.get(device_type, {}).items():
                if device_type != DeviceNames.LEAK_SECTION_KEY:
                    self.states[device_type][device_name].set_state(state_info[DeviceNames.STATE_KEY], can_notify = False)
                    self.states[device_type][device_name].set_preview_state(state_info[DeviceNames.PREVIEW_STATE_KEY])
                    self.states[device_type][device_name].set_last_changed(state_info[DeviceNames.LAST_CHANGED_KEY])
        self.logger.debug("STATES: Loaded status data from file")
        gc.collect()


    def _update_state_changes_in_file(self, device_type, device):
        try:
            with open(self.state_file, 'r') as file:
                data = ujson.load(file)
        except Exception as e:
            data = {}
            
        # Если данных по устройствам нет, создаем пустые записи
        if device_type not in data:
            data[device_type] = {}

        data[device_type][device] = self.states.get(device_type).get(device).get_data() # type: ignore
        self.logger.debug(f"STATES: Successfully saved state for {device_type}: {device}")
        self._write_file(data)
        gc.collect()
        
    def _write_file(self, data):
        try:
            with open(self.state_file, 'w') as file:
                ujson.dump(data, file)
                self.logger.debug(f"STATES: State file {self.state_file} successfully writted.")
        except Exception as e:
            exception = AppException(Errors.FAILED_WRITE_STATES_FILE(), e)
            self.logger.critical(exception.get_error_message())
            raise exception

    def _create_empty_states_file(self):
        data = {}
        for section_key, devices in self.states.items():
            data[section_key] = {}
            for device_key, device in devices.items():
                data[section_key][device_key] = device.get_data()
        self.logger.debug(f"STATES: Created new state file {self.state_file} with None states of all divice.")
        self._write_file(data)
        gc.collect()
        
    def _make_init_states(self):
        self.states = {
            DeviceNames.VALVE_SECTION_KEY: {
                DeviceNames.HOT_WATER_VALVE_KEY: ValveState(DeviceNames.HOT_WATER_VALVE_KEY),
                DeviceNames.COLD_WATER_VALVE_KEY: ValveState(DeviceNames.COLD_WATER_VALVE_KEY),
            },
            DeviceNames.LEAK_SECTION_KEY: {
                DeviceNames.ZONE_1_LEAK_SENSORS_KEY: WaterLeakSensorState(DeviceNames.ZONE_1_LEAK_SENSORS_KEY),
                DeviceNames.ZONE_2_LEAK_SENSORS_KEY: WaterLeakSensorState(DeviceNames.ZONE_2_LEAK_SENSORS_KEY)
            },
            DeviceNames.TEMP_SECTION_KEY: {
                DeviceNames.HOT_WATER_TEMP_SENSORS_KEY: TemperatureSensorState(DeviceNames.HOT_WATER_TEMP_SENSORS_KEY),
                DeviceNames.HEATER_TEMP_SENSORS_KEY: TemperatureSensorState(DeviceNames.HEATER_TEMP_SENSORS_KEY)
            },
            DeviceNames.HEATER_SECTION_KEY:{
                 DeviceNames.HEATER_POWER_SWITH_KEY: HeaterSwithState(DeviceNames.HEATER_POWER_SWITH_KEY),
            }
        }



