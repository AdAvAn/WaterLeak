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
        self.retry_interval = 10  # seconds between attempts

    def is_wifi_connected(self) -> bool:
        """Check if WiFi is connected."""
        if self.wlan.isconnected():
            if not self.is_connected:
                self.is_connected = True
                self.ip_address = self.wlan.ifconfig()[0]
            return True
        else:
            if self.is_connected:
                self.is_connected = False
                self.ip_address = None
                self.logger.warning("WIFI: Connection lost")
            return False

    async def connect_wifi(self, retry_count: int = 10, retry_delay: int = 1) -> bool:
        """Connect to WiFi with retry mechanism."""
        if self.is_wifi_connected():
            return True

        current_time = time.time()
        if current_time - self.last_connection_attempt < self.retry_interval:
            return False

        self.last_connection_attempt = current_time
        self.logger.info(f"WIFI: Connecting to network: {Settings.WIFI_SSID}")

        self.wlan.active(True)
        self.wlan.connect(Settings.WIFI_SSID, Settings.WIFI_PASSWORD)

        for attempt in range(retry_count):
            if self.wlan.isconnected():
                self.is_connected = True
                self.ip_address = self.wlan.ifconfig()[0]
                self.logger.info(f"WIFI: Connected: {Settings.WIFI_SSID}, IP: {self.ip_address}")
                return True
            self.logger.debug(f"WIFI: Waiting for connection to... ({attempt + 1}/{retry_count})")
            await asyncio.sleep(retry_delay)

        self.logger.error(f"WIFI: Failed to connect after retries. SSID: {Settings.WIFI_SSID}")
        return False

    def disconnect_wifi(self) -> bool:
        """Disconnect from WiFi."""
        if self.wlan.isconnected():
            self.wlan.disconnect()
            self.wlan.active(False)
            self.is_connected = False
            self.ip_address = None
            self.logger.info(f"WIFI: Disconnected from network. SSID: {Settings.WIFI_SSID}")
            return True
        return False

    def get_ip_address(self):
        """Return the current IP address if connected."""
        return self.ip_address if self.is_wifi_connected() else None