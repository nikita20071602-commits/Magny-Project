import time
import requests

from config import DATA_MODE, ROBOT_BASE_URL, ROBOT_GET_ENDPOINT, REQUEST_TIMEOUT


def to_number(value):
    try:
        if "." in str(value):
            return float(value)
        return int(value)
    except (ValueError, TypeError):
        return value


def get_robot_data(num: int):
    response = requests.get(
        f"{ROBOT_BASE_URL}{ROBOT_GET_ENDPOINT}",
        params={"num": num},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.text.strip()


def get_file_mode_telemetry():
    return {
        "enabled": False,
        "mode": "file",
        "source": "Delta2D_HEX_Data.txt",
        "connection": "file_mode",
        "message": "Телеметрия отключена. Сейчас используется файл Delta2D.",
        "speed": None,
        "battery": None,
        "robot_angle": None,
        "tilt_angle": None,
        "timestamp": round(time.time(), 2),
    }


def get_robot_telemetry():
    try:
        # Номера data условные.
        # На реальном роботе нужно проверить, что именно отдаёт data1-data4.
        speed = to_number(get_robot_data(1))
        robot_angle = to_number(get_robot_data(2))
        tilt_angle = to_number(get_robot_data(3))
        battery = to_number(get_robot_data(4))

        return {
            "enabled": True,
            "mode": "robot",
            "source": ROBOT_BASE_URL,
            "connection": "connected",
            "message": "Робот подключён",
            "speed": speed,
            "battery": battery,
            "robot_angle": robot_angle,
            "tilt_angle": tilt_angle,
            "timestamp": round(time.time(), 2),
        }

    except requests.RequestException as error:
        return {
            "enabled": False,
            "mode": "robot",
            "source": ROBOT_BASE_URL,
            "connection": "error",
            "message": "Робот не отвечает",
            "error": "Нет соединения с роботом. Проверь Wi-Fi и адрес 192.168.4.1.",
            "speed": None,
            "battery": None,
            "robot_angle": None,
            "tilt_angle": None,
            "timestamp": round(time.time(), 2),
        }


def get_telemetry():
    if DATA_MODE == "robot":
        return get_robot_telemetry()

    return get_file_mode_telemetry()