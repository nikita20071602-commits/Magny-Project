# Режим работы:
# "file"  — карта и данные лидара читаются из Delta2D_HEX_Data.txt
# "robot" — карта и телеметрия пробуют читаться с реального робота
DATA_MODE = "file"

# Адрес робота
ROBOT_BASE_URL = "http://192.168.4.1"

# Endpoint телеметрии:
# http://192.168.4.1/api/get?num=1
ROBOT_GET_ENDPOINT = "/api/get"

# Endpoint лидара.
# На защите надо проверить, как реально робот отдаёт лидар.
# Поддерживаемые варианты ответа:
# 1) JSON с points
# 2) JSON с hex/raw
# 3) просто HEX-текст
ROBOT_LIDAR_ENDPOINT = "/api/lidar"

# Файл с записанными данными Delta2D
LIDAR_FILE = "Delta2D_HEX_Data.txt"

# Таймаут запросов к роботу, секунд
REQUEST_TIMEOUT = 1