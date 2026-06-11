import matplotlib.pyplot as plt

from lidar_delta2d_parser import (
    read_hex_file,
    parse_packets,
    split_into_scans,
    scan_to_points,
)


def main():
    raw = read_hex_file("Delta2D_HEX_Data.txt")
    packets = parse_packets(raw)
    scans = split_into_scans(packets)

    first_scan = scan_to_points(scans[0])

    x_values = [point["x"] for point in first_scan]
    y_values = [point["y"] for point in first_scan]

    plt.figure(figsize=(8, 8))
    plt.scatter(x_values, y_values, s=5)

    # Робот в центре
    plt.scatter([0], [0], s=80, marker="x")

    plt.title("Первый скан лидара Delta2D")
    plt.xlabel("X, мм")
    plt.ylabel("Y, мм")
    plt.axis("equal")
    plt.grid(True)

    plt.show()


if __name__ == "__main__":
    main()