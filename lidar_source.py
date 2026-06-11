import re
import requests

from config import (
    DATA_MODE,
    LIDAR_FILE,
    ROBOT_BASE_URL,
    ROBOT_LIDAR_ENDPOINT,
    REQUEST_TIMEOUT,
)

from lidar_delta2d_parser import (
    read_hex_file,
    parse_delta2d_packets,
    split_into_scans,
    scan_to_points,
)


def hex_text_to_bytes(text: str) -> list[int]:
    """
    Превращает HEX-текст в список байтов.
    """
    hex_values = re.findall(r"\b[0-9A-Fa-f]{2}\b", text)
    return [int(value, 16) for value in hex_values]


def normalize_point(point: dict) -> dict:
    """
    Приводит точку к единому формату.
    """
    return {
        "angle": float(point.get("angle", 0)),
        "distance": float(point.get("distance", 0)),
        "x": float(point.get("x", 0)),
        "y": float(point.get("y", 0)),
    }


def load_file_lidar_data():
    """
    Загружает записанные HEX-данные Delta2D из файла.
    """
    raw = read_hex_file(LIDAR_FILE)
    packets = parse_delta2d_packets(raw)
    scans = split_into_scans(packets)

    return raw, packets, scans


file_raw_data, file_packets, file_scans = load_file_lidar_data()


def get_file_lidar_info():
    return {
        "mode": DATA_MODE,
        "source": LIDAR_FILE,
        "lidar_source_mode": "file",
        "bytes": len(file_raw_data),
        "packets": len(file_packets),
        "scans": len(file_scans),
        "status": "ok",
    }


def normalize_scan_index(scan_index: int) -> int:
    if len(file_scans) == 0:
        return 0

    if scan_index < 0:
        return 0

    if scan_index >= len(file_scans):
        return len(file_scans) - 1

    return scan_index


def get_file_scan(scan_index: int):
    scan_index = normalize_scan_index(scan_index)

    points = scan_to_points(file_scans[scan_index])

    valid_points = [
        {
            "angle": point["angle"],
            "distance": point["distance"],
            "x": point["x"],
            "y": point["y"],
        }
        for point in points
        if point["distance"] > 0
    ]

    return {
        "mode": "file_scan",
        "data_mode": DATA_MODE,
        "source": LIDAR_FILE,
        "scan_index": scan_index,
        "packets_in_scan": len(file_scans[scan_index]),
        "points": valid_points,
        "status": "ok",
    }


def get_robot_lidar_response(scan_index: int = 0):
    """
    Пробует получить данные лидара с робота.
    """
    return requests.get(
        f"{ROBOT_BASE_URL}{ROBOT_LIDAR_ENDPOINT}",
        params={"index": scan_index},
        timeout=REQUEST_TIMEOUT,
    )


def parse_robot_lidar_payload(response):
    """
    Поддерживаем несколько возможных форматов от робота:

    1. JSON:
       {"points": [...]}

    2. JSON:
       {"hex": "AA 55 1E ..."}
       {"raw": "AA 55 1E ..."}

    3. Просто текст:
       AA 55 1E ...
    """
    content_type = response.headers.get("content-type", "").lower()

    if "application/json" in content_type:
        data = response.json()

        if isinstance(data, list):
            points = [normalize_point(point) for point in data]

            return {
                "points": points,
                "raw_bytes": [],
                "packets": [],
                "scans": [],
                "format": "json_points_list",
            }

        if "points" in data:
            points = [normalize_point(point) for point in data["points"]]

            return {
                "points": points,
                "raw_bytes": [],
                "packets": [],
                "scans": [],
                "format": "json_points",
            }

        if "hex" in data:
            raw_bytes = hex_text_to_bytes(data["hex"])
        elif "raw" in data:
            raw_bytes = hex_text_to_bytes(data["raw"])
        else:
            raise ValueError("JSON от робота не содержит points, hex или raw")

    else:
        raw_bytes = hex_text_to_bytes(response.text)

    packets = parse_delta2d_packets(raw_bytes)
    scans = split_into_scans(packets)

    if not scans:
        raise ValueError("Не удалось собрать скан Delta2D из данных робота")

    points = scan_to_points(scans[0])

    valid_points = [
        {
            "angle": point["angle"],
            "distance": point["distance"],
            "x": point["x"],
            "y": point["y"],
        }
        for point in points
        if point["distance"] > 0
    ]

    return {
        "points": valid_points,
        "raw_bytes": raw_bytes,
        "packets": packets,
        "scans": scans,
        "format": "hex_delta2d",
    }


def get_robot_scan(scan_index: int = 0):
    """
    Возвращает один скан с реального робота.
    Если робот не отвечает или формат неизвестен — возвращает ошибку,
    но сайт не падает.
    """
    try:
        response = get_robot_lidar_response(scan_index)
        response.raise_for_status()

        parsed = parse_robot_lidar_payload(response)

        return {
            "mode": "robot_scan",
            "data_mode": DATA_MODE,
            "source": f"{ROBOT_BASE_URL}{ROBOT_LIDAR_ENDPOINT}",
            "scan_index": scan_index,
            "packets_in_scan": len(parsed["packets"][0:24]) if parsed["packets"] else 0,
            "points": parsed["points"],
            "format": parsed["format"],
            "status": "ok",
        }

    except Exception as error:
        return {
            "mode": "robot_scan",
            "data_mode": DATA_MODE,
            "source": f"{ROBOT_BASE_URL}{ROBOT_LIDAR_ENDPOINT}",
            "scan_index": scan_index,
            "packets_in_scan": 0,
            "points": [],
            "status": "error",
            "error": "Нет соединения с роботом или endpoint лидара недоступен.",
        }


def get_robot_lidar_info():
    """
    Информация по лидару в robot-режиме.
    Реальное количество сканов заранее неизвестно.
    """
    return {
        "mode": DATA_MODE,
        "source": f"{ROBOT_BASE_URL}{ROBOT_LIDAR_ENDPOINT}",
        "lidar_source_mode": "robot",
        "bytes": 0,
        "packets": 0,
        "scans": 1,
        "status": "robot_pending",
    }


def get_lidar_info():
    if DATA_MODE == "robot":
        return get_robot_lidar_info()

    return get_file_lidar_info()


def get_scan(scan_index: int):
    if DATA_MODE == "robot":
        return get_robot_scan(scan_index)

    return get_file_scan(scan_index)