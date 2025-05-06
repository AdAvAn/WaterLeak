# WIFI Connection credentials
WIFI_SSID: str = 'AP-5965'
WIFI_PASSWORD: str = 'Kustik2011'

# NTP server address
NTP_SERVER: str = 'ua.pool.ntp.org'

# Time zone offset in hours (e.g., UTC+3 for Ukraine)
TIME_ZONE_OFFSET: int = 3

# Default screen display duration in seconds
PRESENTED_SCREEN_TIME_SEC: int = 3

# Normal screen brightness in percentage
LCD_NORMAL_BRIGHTNESS: int = 100

# Screen brightness in sleep mode in percentage
LCD_SLEEP_MODE_BRIGHTNESS: int = 30

# Timeout in seconds before sleep mode activates
SLEEP_MODE_TIMEOUT: int = 100

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