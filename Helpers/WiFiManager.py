import time
import uasyncio as asyncio
import network
import Resources.Settings as Settings
from Logging.AppLogger import AppLogger
from Helpers.Singleton import Singleton


class WiFiManager(Singleton):
    def __init__(self):
        if getattr(self, 'wlan', None):
            return

        self.logger = AppLogger()
        self.wlan = network.WLAN(network.STA_IF)
        self.is_connected = False
        self.ip_address = None
        self.last_connection_attempt = 0
        
        # Configurable WiFi settings from Settings
        self.initial_retry_interval = Settings.WIFI_INITIAL_RETRY_INTERVAL
        self.max_retry_interval = Settings.WIFI_MAX_RETRY_INTERVAL
        self.retry_multiplier = Settings.WIFI_RETRY_MULTIPLIER
        self.max_attempts_per_session = Settings.WIFI_MAX_ATTEMPTS_PER_SESSION
        self.attempt_delay = Settings.WIFI_ATTEMPT_DELAY
        self.force_retry_interval = Settings.WIFI_FORCE_RETRY_INTERVAL
        
        # Current retry interval (starts with initial value)
        self.retry_interval = self.initial_retry_interval
        
        self.connection_attempts = 0
        self.successful_connections = 0
        self.disconnection_count = 0
        self.last_disconnection_time = 0
        self.signal_strength_history = []
        self.connection_start_time = None

    def is_wifi_connected(self) -> bool:
        """Check if WiFi is connected."""
        try:
            if self.wlan.isconnected():
                if not self.is_connected:
                    self.is_connected = True
                    self.ip_address = self.wlan.ifconfig()[0]
                    self.connection_start_time = time.time()
                    self.successful_connections += 1
                    self.logger.info(f"WiFi reconnected: {self.ip_address}")
                
               # Checking the signal quality
                self._check_signal_strength()
                return True
            else:
                if self.is_connected:
                    self._handle_disconnection()
                return False
                
        except Exception as e:
            self.logger.error(f"WiFi status check failed: {e}")
            if self.is_connected:
                self._handle_disconnection()
            return False

    async def connect_wifi(self, retry_count = None, retry_delay = None) -> bool:
        """Connecting to WiFi"""
        if self.is_wifi_connected():
            return True

        # Use configured values if not provided
        if retry_count is None:
            retry_count = self.max_attempts_per_session
        if retry_delay is None:
            retry_delay = self.attempt_delay

        current_time = time.time()
        
        # Check if we need to wait before attempting connection
        time_since_last_attempt = current_time - self.last_connection_attempt
        if time_since_last_attempt < self.retry_interval:
            remaining_time = self.retry_interval - time_since_last_attempt
            self.logger.debug(f"WiFi retry interval not elapsed, waiting {remaining_time:.1f}s more")
            return False

        self.last_connection_attempt = current_time
        self.connection_attempts += 1
        
        self.logger.info(f"WiFi connection attempt #{self.connection_attempts} to: {Settings.WIFI_SSID}")
        self.logger.debug(f"WiFi settings: retry_interval={self.retry_interval}s, max_attempts={retry_count}, attempt_delay={retry_delay}s")

        try:
            # Reset WiFi adapter if many unsuccessful attempts
            if self.connection_attempts % 5 == 0:
                self.logger.info("Resetting WiFi adapter")
                self.wlan.active(False)
                await asyncio.sleep(2)
                
            self.wlan.active(True)
            
            await self._scan_networks()
            
            self.wlan.connect(Settings.WIFI_SSID, Settings.WIFI_PASSWORD)

            for attempt in range(retry_count):
                if self.wlan.isconnected():
                    self.is_connected = True
                    self.ip_address = self.wlan.ifconfig()[0]
                    self.connection_start_time = time.time()
                    self.successful_connections += 1
                    
                    self.logger.info(f"WiFi connected: {Settings.WIFI_SSID}, IP: {self.ip_address}")
                    self.logger.info(f"Connection stats: {self.successful_connections}/{self.connection_attempts} successful")
                    
                    # Reset retry interval on successful connection
                    self.retry_interval = self.initial_retry_interval
                    return True
                    
                self.logger.debug(f"Waiting for connection... ({attempt + 1}/{retry_count})")
                await asyncio.sleep(retry_delay)

            # Connection failed - increase retry interval
            self._increase_retry_interval()
            self.logger.error(f"WiFi connection failed after {retry_count} attempts, next attempt in {self.retry_interval}s")
            return False
            
        except Exception as e:
            self._increase_retry_interval()
            self.logger.error(f"WiFi connection exception: {e}, next attempt in {self.retry_interval}s")
            return False

    def _increase_retry_interval(self):
        """Increase retry interval for next attempt"""
        old_interval = self.retry_interval
        self.retry_interval = min(self.retry_interval * self.retry_multiplier, self.max_retry_interval)
        
        if self.retry_interval != old_interval:
            self.logger.warning(f"WiFi retry interval increased from {old_interval}s to {self.retry_interval}s")
        
    async def _scan_networks(self):
        """Scanning available WiFi networks for diagnostics"""
        try:
            networks = self.wlan.scan()
            target_found = False
            
            for net in networks:
                ssid = net[0].decode('utf-8')
                if ssid == Settings.WIFI_SSID:
                    target_found = True
                    rssi = net[3]
                    self.logger.debug(f"Target network found: {ssid}, RSSI: {rssi}")
                    break
            
            if not target_found:
                self.logger.warning(f"Target network '{Settings.WIFI_SSID}' not found in scan")
                
        except Exception as e:
            self.logger.debug(f"Network scan failed: {e}")

    async def monitor_connection(self):
        """Continuous WiFi connection monitoring"""
        while True:
            try:
                if not self.is_wifi_connected():
                    self.logger.info("WiFi disconnected, attempting reconnection...")
                    success = await self.connect_wifi()
                    
                    if not success:
                        self.logger.warning(f"WiFi reconnection failed, next attempt in {self.retry_interval}s")
                
                # Use force_retry_interval for monitoring checks
                await asyncio.sleep(self.force_retry_interval)
                
            except Exception as e:
                self.logger.error(f"WiFi monitor error: {e}")
                await asyncio.sleep(60)


    def get_ip_address(self):
        """Return the current IP address if connected."""
        return self.ip_address if self.is_wifi_connected() else None
    
    def _handle_disconnection(self):
        """WiFi Disconnect Handling"""
        self.is_connected = False
        self.ip_address = None
        self.disconnection_count += 1
        self.last_disconnection_time = time.time()
        
        connection_duration = 0
        if self.connection_start_time:
            connection_duration = time.time() - self.connection_start_time
            
        self.logger.warning(f"WiFi disconnected (was connected for {connection_duration:.1f}s)")

    def _check_signal_strength(self):
        """Signal Quality Monitoring"""
        try:
            rssi = self.wlan.status('rssi') if hasattr(self.wlan, 'status') else None
            
            if rssi is not None:
                self.signal_strength_history.append(rssi)
                
                # Save only the last 10 measurements
                if len(self.signal_strength_history) > 10:
                    self.signal_strength_history.pop(0)
                
                # Weak signal warning
                if rssi < -80:
                    self.logger.warning(f"Weak WiFi signal: {rssi} dBm")
                    
        except Exception as e:
            self.logger.debug(f"Failed to check signal strength: {e}")