from flask import Flask, request, jsonify
import random
import math
import time

app = Flask(__name__)

setters = {
    "set1": 0,
    "set2": 0,
    "set3": 0,
    "set4": 0,
}

start_time = time.time()


@app.route("/")
def index():
    return """
    <h1>Mock Robot Server работает</h1>
    <p>Проверка API:</p>
    <ul>
        <li><a href="/api/get?num=1">/api/get?num=1</a></li>
        <li><a href="/api/get?num=2">/api/get?num=2</a></li>
        <li><a href="/api/get?num=3">/api/get?num=3</a></li>
        <li><a href="/api/get?num=4">/api/get?num=4</a></li>
        <li><a href="/api/get_setters">/api/get_setters</a></li>
    </ul>
    """


def generate_data(num: int):
    t = time.time() - start_time

    if num == 1:
        return round(50 + 20 * math.sin(t), 2)          # скорость
    elif num == 2:
        return round(90 + 45 * math.sin(t / 2), 2)      # угол поворота
    elif num == 3:
        return round(5 * math.sin(t / 3), 2)            # угол наклона
    elif num == 4:
        return max(0, round(100 - t / 60, 2))           # заряд
    elif 5 <= num <= 30:
        return random.randint(200, 3000)                # лидар
    else:
        return 0


@app.route("/api/get")
def get_data():
    num = int(request.args.get("num", 0))
    value = generate_data(num)
    return str(value)


@app.route("/api/set")
def set_data():
    num = int(request.args.get("num", 0))
    val = int(request.args.get("val", 0))

    if 1 <= num <= 4:
        setters[f"set{num}"] = val
        return f"OK: set_data{num} = {val}"

    return "ERROR: wrong setter number", 400


@app.route("/api/get_setters")
def get_setters():
    return jsonify(setters)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)