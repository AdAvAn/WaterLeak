# APPLICATION VERSION
APP_VERSION: str = '1.1'

# WIFI Connection credentials
WIFI_SSID: str = 'YOUR_WIFI_SSID'
WIFI_PASSWORD: str = 'YOUR_WIFI_PASSWORD'

# NTP server address
NTP_SERVER: str = 'ua.pool.ntp.org'

# Time zone offset in hours (e.g., UTC+3 for Ukraine)
TIME_ZONE_OFFSET: int = 3

# Default screen display duration in seconds
PRESENTED_SCREEN_TIME_SEC: int = 3

# Normal screen brightness in percentage
LCD_NORMAL_BRIGHTNESS: int = 100

# Screen brightness in sleep mode in percentage
LCD_SLEEP_MODE_BRIGHTNESS: int = 15

# Timeout in seconds before sleep mode activates
SLEEP_MODE_TIMEOUT: int = 100

# STATE MANAGEMENT I/O OPTIMIZATION SETTINGS
# Minimum interval between state file writes (seconds)
# This reduces wear on flash memory by batching writes
STATE_WRITE_INTERVAL: int = 30

# Maximum delay for critical state writes (seconds)
# Critical states (leaks, valve positions) will be written within this time
STATE_MAX_WRITE_DELAY: int = 300

# Temperature update frequency optimization
# How often to actually write temperature changes to disk (in update cycles)
# E.g., value of 3 means write every 3rd temperature update
TEMP_WRITE_FREQUENCY: int = 2

# WIFI MANAGEMENT SETTINGS
# Initial retry interval for WiFi connection attempts (seconds)
WIFI_INITIAL_RETRY_INTERVAL: int = 60
# Maximum retry interval for WiFi connection attempts (seconds)
WIFI_MAX_RETRY_INTERVAL: int = 120
# Multiplier for increasing retry interval after failed attempts
WIFI_RETRY_MULTIPLIER: float = 2
# Maximum number of connection attempts per session
WIFI_MAX_ATTEMPTS_PER_SESSION: int = 10
# Delay between individual attempts within a session (seconds)
WIFI_ATTEMPT_DELAY: int = 2
# Force retry interval - minimum time to wait before retry regardless of success/failure
WIFI_FORCE_RETRY_INTERVAL: int = 30

# BUZZERS
# Operational buzzer pin
BUZZ_CONTROL_PIN = 16
# Alarm buzzer pin
BUZZ_ALARM_PIN = 17

# BUTTONS
# Button to open hot water
VHOB_PIN = 27
# Button to close hot water
VHCB_PIN = 26
# Button to open cold water
VCOB_PIN = 22
# Button to close cold water
VCCB_PIN = 21
# Button to control the water heater valve
HOCB_PIN = 20

# I2C1 pins
SCL_PIN = 19
SDA_PIN = 18

# HEATER
# Pin to switch the water heater on/off
POWER_HEATER_PIN = 11

# VALVES
# Valve opening/closing duration in seconds
VALVES_OPERATION_TIME = 21
# Pin to open hot water valve
OPEN_HOT_W_PIN = 0
# Pin to close hot water valve
CLOSE_HOT_W_PIN = 1
# Pin indicating hot water valve error
ERROR_HOT_W_PIN = 2
# Pin to open cold water valve
OPEN_COLD_W_PIN = 3
# Pin to close cold water valve
CLOSE_COLD_W_PIN = 4
# Pin indicating cold water valve error
ERROR_COLD_W_PIN = 5
# Pin to open heater valve
OPEN_HEATER_W_PIN = 6
# Pin to close heater valve
CLOSE_HEATER_W_PIN = 7

# Pin for alarm signal from RTC
DSDTC_ALARM_PIN = 10

# SENSORS
# Polling interval for temperature sensors in seconds
TEMP_SENSOR_POLLING_TIME = 30
# Pin for hot water temperature sensor
HWLT_SE1_PIN = 12
# Pin for heater temperature sensor
HEATER_TEMP_PIN = 13

# Pin for water leak sensor in zone #1
LEAK_ZONE1_PIN = 14
# Pin for water leak sensor in zone #2
LEAK_ZONE2_PIN = 15