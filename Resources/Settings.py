
# WIFI Connection cred.
WIFI_SSID:str = 'AP-5965'
WIFI_PASSWORD:str = 'Kustik2011'  

# NTP Сервер
NTP_SERVER:str = 'ua.pool.ntp.org'

# Смещение часового пояса в часах (например, UTC+3 для Украины)
TIME_ZONE_OFFSET:int = 3

#Промежуток времени смены стандартых экарнов по умолчанию
PRESENTED_SCREEN_TIME_SEC:int = 3 

#Пнормальная яркость экрана в процентах
LCD_NORMAL_BRIGHTNESS:int = 100

#Яркость экрана в режими сна в процентах
LCD_SLEEP_MODE_BRIGHTNESS:int = 1

#Врем в секунад после которго вклчиться режим сна
SLEEP_MODE_MODE_TIMEOUNT:int = 100


# BUZZERS
# Операционный buzzer 
BUZZ_CONTROL_PIN = 16
# Buzzer сиглализации
BUZZ_ALARM_PIN = 17

# BUTTONS
# Кнопка откытия горячей воды 
VHOB_PIN = 27
# Кнопка закрытия горячей воды 
VHCB_PIN = 26
# Кнопка откытия холодной воды 
VCOB_PIN = 22
# Кнопка закрытия холодной воды 
VCCB_PIN = 21
# Кнопка управления клпапаном нагревателя воды 
HOCB_PIN = 20

# I2C1
SCL_PIN = 19
SDA_PIN = 18

# HEATER
# Порт включения / выключения водонагревателя
POWER_HEATER_PIN = 11

# VALVES
# Время закрытия / открытия клапана в секундах
VALVES_OPERAION_TIME = 21
# Порт открытия клапана горячей воды 
OPEN_HOT_W_PIN = 0
# Порт закрытия клапана горячей воды 
CLOSE_HOT_W_PIN = 1
# Порт ошибки клапана горячей воды 
ERROR_HOT_W_PIN = 2
# Порт открытия клапана холодной воды
OPEN_COLD_W_PIN = 3
# Порт закрытия клапана холодной воды 
CLOSE_COLD_W_PIN = 4
# Порт ошибки клапана холодной воды 
ERROR_COLD_W_PIN = 5

# Порт открытия клапана водонагревателя воды 
OPEN_HEATER_W_PIN = 6
# Порт закрытия клапана водонагревателя воды 
CLOSE_HEATER_W_PIN = 7

# Порт получения сигнала от будильника
DSDTC_ALARM_PIN = 10

# SENSORS  
TEMP_SENMSOR_POLLING_TIME = 30
# Датчик темепратуры горячей воды
HWLT_SE1_PIN = 12
# Датчик темепратуры вотонагревателя
HEATER_TEMP_PIN = 13

# Датчик утечки воды в зоне №1
LEAK_ZONE1_PIN = 14
# Датчик утечки воды в зоне №2
LEAK_ZONE2_PIN = 15

