import requests
from config import BASE_URL, DATA_COUNT


def get_data(num: int):
    try:
        response = requests.get(
            f"{BASE_URL}/api/get",
            params={"num": num},
            timeout=1
        )
        response.raise_for_status()
        return response.text.strip()
    except requests.RequestException as error:
        return f"ERROR: {error}"


def set_data(num: int, value: int):
    try:
        response = requests.get(
            f"{BASE_URL}/api/set",
            params={"num": num, "val": value},
            timeout=1
        )
        response.raise_for_status()
        return response.text.strip()
    except requests.RequestException as error:
        return f"ERROR: {error}"


def get_setters():
    try:
        response = requests.get(
            f"{BASE_URL}/api/get_setters",
            timeout=1
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as error:
        return {"error": str(error)}


def get_all_data():
    data = {}

    for i in range(1, DATA_COUNT + 1):
        data[f"data{i}"] = get_data(i)

    return data