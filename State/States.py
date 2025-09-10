import gc
import os
import ujson
import time
import uasyncio as asyncio
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
        self.backup_file = "State/state_backup.json"
        self.temp_file = "State/state_temp.json"
        self.logger = AppLogger()
        self.states: dict = {}
        self.write_failures = 0
        self.max_write_failures = 5
        
        # Optimization: Write batching and scheduling
        self._pending_writes = set()  # Track devices that need writing
        self._last_write_time = 0
        self._write_interval = 30  # Minimum seconds between writes
        self._max_write_delay = 300  # Maximum seconds to delay critical writes
        self._write_task = None
        self._critical_write_pending = False
        
        # Optimization: Change tracking to avoid unnecessary writes
        self._last_written_states = {}
        
        self._make_init_states()
        self._load_states_from_file()
        self._start_write_scheduler()

    def _start_write_scheduler(self):
        """Start the background write scheduler task"""
        if self._write_task is None:
            self._write_task = asyncio.create_task(self._write_scheduler_loop())

    async def _write_scheduler_loop(self):
        """Background task that handles batched writes"""
        while True:
            try:
                current_time = time.time()
                time_since_last_write = current_time - self._last_write_time
                
                # Check if we should write
                should_write = (
                    self._pending_writes and  # Have pending changes
                    (time_since_last_write >= self._write_interval or  # Enough time passed
                     self._critical_write_pending)  # Or critical write needed
                )
                
                if should_write:
                    await self._flush_pending_writes()
                
                # Sleep for a short interval
                await asyncio.sleep(5)
                
            except Exception as e:
                self.logger.error(f"STATES: Write scheduler error: {e}")
                await asyncio.sleep(10)

    async def _flush_pending_writes(self):
        """Flush all pending writes to disk"""
        if not self._pending_writes:
            return
            
        try:
            # Read current file state
            try:
                with open(self.state_file, 'r') as file:
                    data = ujson.load(file)
            except Exception:
                data = {}
            
            # Update only changed devices
            changes_made = False
            for device_key in list(self._pending_writes):
                device_type, device_name = device_key.split(':', 1)
                
                if device_type not in data:
                    data[device_type] = {}
                
                device_state = self.states.get(device_type, {}).get(device_name)
                if device_state:
                    new_data = device_state.get_data()
                    
                    # Check if data actually changed since last write
                    last_written = self._last_written_states.get(device_key)
                    if last_written != new_data:
                        data[device_type][device_name] = new_data
                        self._last_written_states[device_key] = new_data.copy()
                        changes_made = True
                        self.logger.debug(f"STATES: Batched write for {device_type}:{device_name}")
            
            # Only write if there were actual changes
            if changes_made:
                self._write_file(data)
                self.logger.info(f"STATES: Batched write completed for {len(self._pending_writes)} devices")
            
            # Clear pending writes
            self._pending_writes.clear()
            self._critical_write_pending = False
            self._last_write_time = time.time()
            
        except Exception as e:
            self.logger.error(f"STATES: Flush pending writes failed: {e}")

    # MARK: Setters
    # MARK: SET States
    def update_valve_state(self, device_name: str, new_state) -> None:
        self._update_device_state(DeviceNames.VALVE_SECTION_KEY, device_name, new_state, is_critical=True)

    def update_leak_sensor_state(self, device_name: str, new_state) -> None:
        self._update_device_state(DeviceNames.LEAK_SECTION_KEY, device_name, new_state, is_critical=True)

    def update_temperature(self, device_name: str, new_state) -> None:
        # Temperature changes are less critical and can be batched
        self._update_device_state(DeviceNames.TEMP_SECTION_KEY, device_name, new_state, is_critical=False)
    
    def update_heater_state(self, device_name: str, new_state) -> None:
        self._update_device_state(DeviceNames.HEATER_SECTION_KEY, device_name, new_state, is_critical=True)

    # MARK: Getters (unchanged)
    def get_valve_state(self, device_name: str):
        return self._get_device_state(DeviceNames.VALVE_SECTION_KEY, device_name)

    def get_leak_sensor_state(self, device_name: str):
        return self._get_device_state(DeviceNames.LEAK_SECTION_KEY, device_name)
        
    def get_temperature(self, device_name: str):
        return self._get_device_state(DeviceNames.TEMP_SECTION_KEY, device_name)
    
    def get_heater_state(self, device_name: str):
        return self._get_device_state(DeviceNames.HEATER_SECTION_KEY, device_name)

    def get_valve_preview_state(self, device_name: str):
        return self._get_preview_device_state(DeviceNames.VALVE_SECTION_KEY, device_name)
    
    def get_leak_sensor_preview_state(self, device_name: str):
        return self._get_preview_device_state(DeviceNames.LEAK_SECTION_KEY, device_name)
    
    def get_temperature_preview_state(self, device_name: str):
        return self._get_preview_device_state(DeviceNames.TEMP_SECTION_KEY, device_name)

    def get_heater_preview_state(self, device_name: str):
        return self._get_preview_device_state(DeviceNames.HEATER_SECTION_KEY, device_name)
    
    def get_valve_action_time(self, device_name: str) -> str:
        return self._get_device_action_time(DeviceNames.VALVE_SECTION_KEY, device_name)

    def get_leak_sensor_action_time(self, device_name: str) -> str:
        return self._get_device_action_time(DeviceNames.LEAK_SECTION_KEY, device_name)

    def get_temperature_action_time(self, device_name: str) -> str:
        return self._get_device_action_time(DeviceNames.TEMP_SECTION_KEY, device_name)

    def get_heater_action_time(self, device_name: str) -> str:
        return self._get_device_action_time(DeviceNames.HEATER_SECTION_KEY, device_name)

    # MARK: Optimized Helper Methods

    def _update_device_state(self, device_type: str, device_name: str, new_state, is_critical: bool = False):
        """Update device state with optimized write scheduling"""
        device = self.states[device_type].get(device_name)
        if device is None:
            raise ValueError(f"STATES: {device_name} not found in section {device_type}")
            
        current_state = device.get_state()
        if current_state != new_state:
            device.set_state(new_value=new_state, can_notify=True)
            self.logger.debug(f"STATES: State changed {device_name}: {current_state} -> {new_state}")
            
            # Schedule write instead of immediate write
            self._schedule_write(device_type, device_name, is_critical)

    def _schedule_write(self, device_type: str, device_name: str, is_critical: bool = False):
        """Schedule a device for writing instead of immediate write"""
        device_key = f"{device_type}:{device_name}"
        self._pending_writes.add(device_key)
        
        if is_critical:
            self._critical_write_pending = True
            
        self.logger.debug(f"STATES: Scheduled write for {device_key} (critical: {is_critical})")

    async def force_write(self):
        """Force immediate write of all pending changes - useful for shutdown"""
        if self._pending_writes:
            self.logger.info("STATES: Force writing all pending changes")
            await self._flush_pending_writes()

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
        
    def _get_device_action_time(self, device_type: str, device_name: str) -> str:
        """Get the timestamp of the last state change for the specified device, formatted as dd.mm.yy HH:mm."""
        try:
            device = self.states.get(device_type, {}).get(device_name)
            if device is None:
                self.logger.error(f"STATES: Device {device_name} not found in section {device_type} when getting action time")
                return "Unknown"    

            iso = device.get_data().get(DeviceNames.LAST_CHANGED_KEY)
            if not iso:
                return "Unknown"    

            # Parse ISO datetime string "YYYY-MM-DDTHH:MM:SS" and reformat to "dd.mm.yy HH:mm"
            day   = iso[8:10]
            month = iso[5:7]
            year  = iso[2:4]
            time_ = iso[11:16]  # "HH:MM"

            return f"{day}.{month}.{year} {time_}"
        except Exception as e:
            self.logger.error(f"STATES: Failed to get action time for {device_name} in {device_type}. Error: {e}")
            return "Unknown"    

    def _load_states_from_file(self):
        """Load states from file with recovery from backup"""
        files_to_try = [self.state_file, self.backup_file]
        
        for file_path in files_to_try:
            try:
                if self._file_exists(file_path):
                    with open(file_path, 'r') as file:
                        data = ujson.load(file)
                        if self._validate_state_data(data):
                            self._apply_loaded_states(data)
                            # Initialize last written states tracking
                            self._initialize_last_written_states(data)
                            self.logger.info(f"States loaded from: {file_path}")
                            return
                        else:
                            self.logger.warning(f"Invalid state data in: {file_path}")
            except Exception as e:
                self.logger.warning(f"Failed to load from {file_path}: {e}")
        
        # If all files are corrupted - create new
        self.logger.warning("All state files corrupted, creating new state file")
        self._create_empty_states_file()

    def _initialize_last_written_states(self, data):
        """Initialize tracking of last written states to avoid unnecessary writes"""
        for device_type in data:
            for device_name, state_info in data[device_type].items():
                device_key = f"{device_type}:{device_name}"
                self._last_written_states[device_key] = state_info.copy()

    def _apply_loaded_states(self, data):
        """Apply loaded state data to state objects"""
        for device_type in self.states:
            for device_name, state_info in data.get(device_type, {}).items():
                if device_type != DeviceNames.LEAK_SECTION_KEY:
                    self.states[device_type][device_name].set_state(state_info[DeviceNames.STATE_KEY], can_notify=False)
                    self.states[device_type][device_name].set_preview_state(state_info[DeviceNames.PREVIEW_STATE_KEY])
                    self.states[device_type][device_name].set_last_changed(state_info[DeviceNames.LAST_CHANGED_KEY])
        self.logger.debug("STATES: Loaded status data from file")
        gc.collect()

    def _write_file(self, data):
        """Atomic write with backup - only used by scheduler now"""
        try:
            # Check available space
            if not self._check_disk_space():
                raise OSError("Insufficient disk space")
            
            # Create backup of existing file
            if self._file_exists(self.state_file):
                self._copy_file(self.state_file, self.backup_file)
            
            # Atomic write through temp file
            with open(self.temp_file, 'w') as file:
                ujson.dump(data, file)
            
            # Rename temp file to main file
            self._rename_file(self.temp_file, self.state_file)
            
            self.write_failures = 0
            self.logger.debug(f"State file successfully written: {self.state_file}")
            
        except Exception as e:
            self.write_failures += 1
            self.logger.error(f"Write failure #{self.write_failures}: {e}")
            
            # Clean up temp file on error
            self._safe_remove(self.temp_file)
            
            if self.write_failures >= self.max_write_failures:
                self.logger.critical("Too many write failures, filesystem may be corrupted")
                self._emergency_backup(data)
            
            raise AppException(Errors.FAILED_WRITE_STATES_FILE(), e)

    def _create_empty_states_file(self):
        """Create empty state file with default values"""
        data = {}
        for section_key, devices in self.states.items():
            data[section_key] = {}
            for device_key, device in devices.items():
                data[section_key][device_key] = device.get_data()
        self.logger.debug(f"STATES: Created new state file {self.state_file} with None states of all devices.")
        self._write_file(data)
        gc.collect()
        
    def _make_init_states(self):
        """Initialize state objects"""
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

    def _validate_state_data(self, data):
        """Validate structure of state data"""
        if not isinstance(data, dict):
            return False
        
        required_sections = [
            DeviceNames.VALVE_SECTION_KEY,
            DeviceNames.LEAK_SECTION_KEY,
            DeviceNames.TEMP_SECTION_KEY,
            DeviceNames.HEATER_SECTION_KEY
        ]
        
        for section in required_sections:
            if section not in data:
                self.logger.warning(f"Missing section in state data: {section}")
                return False
        
        return True        

    def _check_disk_space(self, min_free_bytes=8192):
        """Check available disk space"""
        try:
            stat = os.statvfs('/')
            free_bytes = stat[0] * stat[3]  # block_size * free_blocks
            return free_bytes >= min_free_bytes
        except:
            return True 

    def _file_exists(self, filepath):
        """Check if file exists"""
        try:
            os.stat(filepath)
            return True
        except OSError:
            return False
        
    def _copy_file(self, src, dst):
        """Copy file"""
        try:
            with open(src, 'r') as src_file:
                with open(dst, 'w') as dst_file:
                    dst_file.write(src_file.read())
        except Exception as e:
            self.logger.warning(f"Failed to copy {src} to {dst}: {e}")        

    def _rename_file(self, src, dst):
        """Rename file"""
        try:
            os.rename(src, dst)
        except Exception as e:
            self.logger.error(f"Failed to rename {src} to {dst}: {e}")
            raise

    def _safe_remove(self, filepath):
        """Safely remove file"""
        try:
            if self._file_exists(filepath):
                os.remove(filepath)
        except Exception as e:
            self.logger.warning(f"Failed to remove {filepath}: {e}")

    def _emergency_backup(self, data):
        """Emergency save to memory"""
        try:
            # Save critical data to class variables
            self.emergency_backup_data = data
            self.emergency_backup_time = time.time()
            self.logger.info("Emergency backup created in memory")
        except Exception as e:
            self.logger.error(f"Emergency backup failed: {e}")

    async def cleanup(self):
        """Cleanup method for graceful shutdown"""
        if self._write_task:
            # Force write any pending changes before shutdown
            await self.force_write()
            self._write_task.cancel()
            self._write_task = None
            self.logger.info("STATES: Write scheduler stopped and pending writes flushed")