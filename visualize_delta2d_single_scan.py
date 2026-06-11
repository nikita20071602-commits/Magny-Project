import sys
import matplotlib.pyplot as plt

from lidar_delta2d_parser import (
    read_hex_file,
    parse_delta2d_packets,
    split_into_scans,
    scan_to_points,
)


def main():
    scan_index = int(sys.argv[1]) if len(sys.argv) > 1 else 0

    raw = read_hex_file("Delta2D_HEX_Data.txt")
    packets = parse_delta2d_packets(raw)
    scans = split_into_scans(packets)

    if scan_index < 0 or scan_index >= len(scans):
        print(f"Ошибка: скан должен быть от 0 до {len(scans) - 1}")
        return

    points = scan_to_points(scans[scan_index])

    # Берём все валидные точки
    valid_points = [
        p for p in points
        if p["distance"] > 0
    ]

    x_values = [p["x"] for p in valid_points]
    y_values = [p["y"] for p in valid_points]

    print("Скан:", scan_index)
    print("Пакетов в скане:", len(scans[scan_index]))
    print("Точек всего:", len(points))
    print("Валидных точек:", len(valid_points))
    print("Первые 10 точек:")
    for p in valid_points[:10]:
        print(p)

    plt.figure(figsize=(8, 8))

    # Точки лидара
    plt.scatter(x_values, y_values, s=4)

    # Робот / лидар в центре
    plt.scatter([0], [0], s=80, marker="x")

    plt.title(f"Delta2D: один скан №{scan_index}")
    plt.xlabel("X, мм")
    plt.ylabel("Y, мм")
    plt.axis("equal")
    plt.grid(True)

    plt.show()


if __name__ == "__main__":
    main() 