import csv

from lidar_delta2d_parser import (
    read_hex_file,
    parse_delta2d_packets,
    split_into_scans,
    scan_to_points,
)


def main():
    raw = read_hex_file("Delta2D_HEX_Data.txt")
    packets = parse_delta2d_packets(raw)
    scans = split_into_scans(packets)

    print("Пакетов:", len(packets))
    print("Сканов:", len(scans))

    scan_index = 0
    points = scan_to_points(scans[scan_index])

    angles = [p["angle"] for p in points]
    distances = [p["distance"] for p in points]

    print("Проверка первого скана")
    print("Точек:", len(points))
    print("Минимальный угол:", min(angles))
    print("Максимальный угол:", max(angles))
    print("Минимальная дистанция:", min(distances))
    print("Максимальная дистанция:", max(distances))

    print()
    print("Первые 20 точек:")
    for point in points[:20]:
        print(point)

    output_file = "delta2d_scan_0_points.csv"

    with open(output_file, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["angle", "distance", "x", "y"])
        writer.writeheader()
        writer.writerows(points)

    print()
    print("CSV сохранён:", output_file)


if __name__ == "__main__":
    main()