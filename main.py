import time
from robot_api import get_all_data, set_data, get_setters


def main():
    print("Запуск клиента мониторинга")
    print("Чтение данных с имитатора робота")
    print("-" * 40)

    print(set_data(1, 100))
    print("Текущие setters:", get_setters())
    print("-" * 40)

    while True:
        data = get_all_data()

        print("Телеметрия:")
        print(f"Скорость: {data['data1']}")
        print(f"Угол поворота: {data['data2']}")
        print(f"Угол наклона: {data['data3']}")
        print(f"Заряд: {data['data4']}%")

        lidar_values = [data[f"data{i}"] for i in range(5, 31)]
        print(f"Лидар: {lidar_values}")

        print("-" * 40)
        time.sleep(1)


if __name__ == "__main__":
    main()