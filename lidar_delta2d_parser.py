import math
import re
from pathlib import Path


HEADER = b"\xAA\x55"
PACKET_SIZE = 39
DISTANCES_COUNT = 15
ANGLE_DIVIDER = 128.0


def read_hex_file(file_path: str) -> bytes:
    """
    Читает HEX-файл и возвращает поток байтов.
    """
    text = Path(file_path).read_text(encoding="utf-8", errors="ignore")
    hex_values = re.findall(r"\b[0-9A-Fa-f]{2}\b", text)
    return bytes(int(value, 16) for value in hex_values)


def u16_le(data: bytes, index: int) -> int:
    """
    Little Endian: 80 07 -> 0x0780.
    """
    return data[index] | (data[index + 1] << 8)


def calculate_checksum(packet: bytes) -> int:
    """
    Считаем контрольную сумму без байтов checksum.
    Сейчас используем только для отладки, пакеты не отбрасываем.
    """
    return (sum(packet[:7]) + sum(packet[9:])) & 0xFFFF


def parse_delta2d_packets(raw: bytes) -> list[dict]:
    """
    Парсит поток байтов Delta2D.

    Формат:
    0-1   AA 55
    2     1E
    3-4   start_angle
    5-6   end_angle
    7-8   checksum
    9-38  15 расстояний
    """
    packets = []
    i = 0

    while i <= len(raw) - PACKET_SIZE:
        if raw[i:i + 2] == HEADER and raw[i + 2] == 0x1E:
            packet = raw[i:i + PACKET_SIZE]

            start_angle_raw = u16_le(packet, 3)
            end_angle_raw = u16_le(packet, 5)

            start_angle = start_angle_raw / ANGLE_DIVIDER
            end_angle = end_angle_raw / ANGLE_DIVIDER

            checksum = u16_le(packet, 7)
            calculated_checksum = calculate_checksum(packet)

            distances = []

            for n in range(DISTANCES_COUNT):
                distance_index = 9 + n * 2
                distance = u16_le(packet, distance_index)
                distances.append(distance)

            packets.append({
                "raw": packet.hex(" ").upper(),
                "start_angle": start_angle,
                "end_angle": end_angle,
                "checksum": checksum,
                "calculated_checksum": calculated_checksum,
                "distances": distances,
            })

            i += PACKET_SIZE
        else:
            i += 1

    return packets


def packet_to_measurements(packet: dict) -> list[dict]:
    """
    Один пакет Delta2D -> 15 измерений angle/distance.
    """
    start_angle = packet["start_angle"]
    end_angle = packet["end_angle"]

    if end_angle < start_angle:
        end_angle += 360.0

    distances = packet["distances"]

    if len(distances) > 1:
        angle_step = (end_angle - start_angle) / (len(distances) - 1)
    else:
        angle_step = 0.0

    measurements = []

    for index, distance in enumerate(distances):
        angle = (start_angle + angle_step * index) % 360.0

        measurements.append({
            "angle": round(angle, 3),
            "distance": distance,
        })

    return measurements


def measurement_to_point(measurement: dict) -> dict:
    """
    angle/distance -> x/y.
    """
    angle = measurement["angle"]
    distance = measurement["distance"]

    angle_rad = math.radians(angle)

    x = distance * math.cos(angle_rad)
    y = distance * math.sin(angle_rad)

    return {
        "angle": angle,
        "distance": distance,
        "x": round(x, 3),
        "y": round(y, 3),
    }


def packet_to_points(packet: dict) -> list[dict]:
    """
    Один пакет -> 15 точек x/y.
    """
    measurements = packet_to_measurements(packet)
    return [measurement_to_point(m) for m in measurements]


def split_into_scans(packets: list[dict]) -> list[list[dict]]:
    """
    Делит поток пакетов на сканы.
    Новый скан начинается, когда угол снова становится меньше.
    """
    scans = []
    current_scan = []
    previous_angle = None

    for packet in packets:
        start_angle = packet["start_angle"]

        if previous_angle is not None and start_angle < previous_angle:
            if current_scan:
                scans.append(current_scan)
            current_scan = []

        current_scan.append(packet)
        previous_angle = start_angle

    if current_scan:
        scans.append(current_scan)

    return scans


def scan_to_measurements(scan: list[dict]) -> list[dict]:
    """
    Один скан -> список angle/distance.
    """
    measurements = []

    for packet in scan:
        measurements.extend(packet_to_measurements(packet))

    return measurements


def scan_to_points(scan: list[dict]) -> list[dict]:
    """
    Один скан -> список x/y.
    """
    measurements = scan_to_measurements(scan)
    return [measurement_to_point(m) for m in measurements]


# Совместимость со старым кодом сайта
parse_packets = parse_delta2d_packets


def main():
    file_path = "Delta2D_HEX_Data.txt"

    raw = read_hex_file(file_path)
    packets = parse_delta2d_packets(raw)
    scans = split_into_scans(packets)

    print("Файл:", file_path)
    print("Всего байтов:", len(raw))
    print("Найдено пакетов Delta2D:", len(packets))
    print("Найдено сканов:", len(scans))

    if not packets:
        print("Пакеты не найдены")
        return

    first_packet = packets[0]

    print()
    print("Первый пакет:")
    print("start_angle:", first_packet["start_angle"])
    print("end_angle:", first_packet["end_angle"])
    print("checksum:", first_packet["checksum"])
    print("calculated_checksum:", first_packet["calculated_checksum"])
    print("distances:", first_packet["distances"])

    print()
    print("Первые 15 измерений первого пакета:")
    measurements = packet_to_measurements(first_packet)

    for measurement in measurements:
        print(measurement)

    print()
    print("Первые 15 точек первого пакета:")
    points = packet_to_points(first_packet)

    for point in points:
        print(point)

    print()
    for index, scan in enumerate(scans[:5]):
        scan_points = scan_to_points(scan)
        print(f"Скан {index}: пакетов={len(scan)}, точек={len(scan_points)}")


if __name__ == "__main__":
    main()