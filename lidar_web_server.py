from flask import Flask, jsonify, request, render_template_string

try:
    from config import DATA_MODE
except ImportError:
    DATA_MODE = "file"

try:
    from telemetry_source import get_telemetry
except ImportError:
    def get_telemetry():
        return {
            "enabled": False,
            "mode": "file",
            "source": "Delta2D_HEX_Data.txt",
            "connection": "file_mode",
            "message": "Телеметрия не подключена",
            "speed": None,
            "battery": None,
            "robot_angle": None,
            "tilt_angle": None,
        }

from lidar_source import (
    get_lidar_info,
    get_scan,
)


app = Flask(__name__)

lidar_info = get_lidar_info()

print("Источник лидара:", lidar_info["source"])
print("Режим:", lidar_info["mode"])
print("Сканов:", lidar_info["scans"])


HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Delta2D Viewer</title>

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #0d0f12;
            color: #f2f2f2;
        }

        header {
            height: 58px;
            padding: 14px 22px;
            background: #151922;
            border-bottom: 1px solid #2a2f3a;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        header h1 {
            margin: 0;
            font-size: 20px;
        }

        header span {
            color: #00ff99;
            font-size: 14px;
        }

        main {
            display: grid;
            grid-template-columns: 1fr 360px;
            gap: 18px;
            padding: 18px;
            height: calc(100vh - 58px);
        }

        main.map-hidden {
            grid-template-columns: 360px;
            justify-content: end;
        }

        .map-card,
        .panel {
            background: #151922;
            border: 1px solid #2a2f3a;
            border-radius: 14px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
        }

        .map-card {
            padding: 14px;
            display: flex;
            flex-direction: column;
            min-width: 0;
        }

        .map-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }

        .map-title {
            font-size: 16px;
            font-weight: 700;
        }

        .map-hint {
            color: #8d96a8;
            font-size: 13px;
        }

        canvas {
            width: 100%;
            height: 100%;
            background: #050608;
            border: 1px solid #303744;
            border-radius: 12px;
        }

        .panel {
            padding: 16px;
            overflow-y: auto;
        }

        h2 {
            margin: 0 0 12px;
            font-size: 18px;
        }

        h3 {
            margin: 18px 0 10px;
            font-size: 15px;
            color: #d9dde7;
        }

        .metric {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            padding: 8px 0;
            border-bottom: 1px solid #252b36;
            font-size: 14px;
        }

        .metric:last-child {
            border-bottom: none;
        }

        .label {
            color: #9aa3b5;
        }

        .value {
            color: #00ff99;
            font-weight: 700;
            text-align: right;
        }

        label {
            display: block;
            margin: 12px 0 6px;
            font-size: 13px;
            color: #b8c0d0;
        }

        input[type="range"],
        input[type="number"] {
            width: 100%;
        }

        input[type="number"] {
            padding: 8px;
            border-radius: 8px;
            border: 1px solid #333b49;
            background: #0d0f12;
            color: white;
        }

        .buttons {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            margin-top: 12px;
        }

        button {
            padding: 10px;
            border: 1px solid #334154;
            border-radius: 10px;
            background: #1e2633;
            color: white;
            cursor: pointer;
            font-weight: 600;
        }

        button:hover {
            background: #273244;
        }

        .primary {
            grid-column: span 2;
            background: #008f5a;
            border-color: #00b36f;
        }

        .primary:hover {
            background: #00a86b;
        }

        .danger {
            background: #5c2630;
            border-color: #8a3945;
        }

        .danger:hover {
            background: #73313d;
        }

        .module-switch {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            margin-top: 8px;
        }

        .module-switch label {
            margin: 0;
            padding: 8px;
            border: 1px solid #2a2f3a;
            border-radius: 8px;
            background: #0d0f12;
            font-size: 12px;
            cursor: pointer;
        }

        .module {
            margin-top: 14px;
        }

        .telemetry-box,
        .overview-box,
        .error-box {
            color: #c6ccda;
            font-size: 13px;
            line-height: 1.5;
            background: #0d0f12;
            border: 1px solid #2a2f3a;
            border-radius: 10px;
            padding: 10px;
        }

        .error-box {
            color: #ffb4b4;
            border-color: #663333;
        }

        pre {
            background: #080a0d;
            border: 1px solid #2a2f3a;
            border-radius: 10px;
            padding: 10px;
            max-height: 220px;
            overflow: auto;
            font-size: 12px;
            white-space: pre-wrap;
            color: #d8dee9;
        }

        .small-note {
            margin-top: 12px;
            color: #8d96a8;
            font-size: 12px;
            line-height: 1.4;
        }
    </style>
</head>

<body>
<header>
    <h1>Delta2D LiDAR Viewer</h1>
    <span>{{ lidar_source }}</span>
</header>

<main id="mainLayout">
    <section id="mapModule" class="map-card">
        <div class="map-header">
            <div class="map-title">Карта одного скана</div>
            <div id="mapHint" class="map-hint">Точки рассчитаны из angle + distance</div>
        </div>

        <canvas id="canvas" width="1050" height="780"></canvas>
    </section>

    <aside class="panel">
        <h2>Управление</h2>

        <div class="metric">
            <span class="label">Режим</span>
            <span class="value">{{ data_mode }}</span>
        </div>

        <div class="metric">
            <span class="label">Источник карты</span>
            <span class="value">{{ lidar_mode }}</span>
        </div>

        <div class="metric">
            <span class="label">Всего сканов</span>
            <span class="value">{{ total_scans }}</span>
        </div>

        <div class="metric">
            <span class="label">Всего пакетов</span>
            <span class="value">{{ total_packets }}</span>
        </div>

        <div class="metric">
            <span class="label">Текущий скан</span>
            <span id="scanNumber" class="value">0</span>
        </div>

        <h3>Модули</h3>

        <div class="module-switch">
            <label>
                <input type="checkbox" id="showMap" checked>
                Карта
            </label>

            <label>
                <input type="checkbox" id="showOverview" checked>
                Обзор скана
            </label>

            <label>
                <input type="checkbox" id="showTelemetry" checked>
                Телеметрия
            </label>
        </div>

        <h3>Выбор скана</h3>

        <label>
            Номер скана
            <input id="scanInput" type="range" min="0" max="{{ max_scan }}" value="0">
        </label>

        <label>
            Точный номер скана
            <input id="scanNumberInput" type="number" min="0" max="{{ max_scan }}" value="0">
        </label>

        <div class="buttons">
            <button onclick="previousScan()">← Назад</button>
            <button onclick="nextScan()">Вперёд →</button>
            <button class="primary" onclick="loadScan()">Обновить карту</button>
        </div>

        <label>
            Интервал воспроизведения, мс
            <input id="playbackIntervalInput" type="number" min="100" max="5000" value="300">
        </label>

        <div class="metric">
            <span class="label">Воспроизведение</span>
            <span id="playbackStatus" class="value">выключено</span>
        </div>

        <div class="buttons">
            <button class="primary" onclick="startAutoPlayback()">Старт автопрокрутки</button>
            <button class="danger" onclick="stopAutoPlayback()">Стоп</button>
        </div>

        <h3>Отображение</h3>

        <label>
            Масштаб: <span id="scaleValue" class="value">0.08</span>
            <input id="scaleInput" type="range" min="0.02" max="0.20" step="0.01" value="0.08">
        </label>

        <label>
            Размер точки: <span id="pointSizeValue" class="value">2</span>
            <input id="pointSizeInput" type="range" min="1" max="5" step="1" value="2">
        </label>

        <label>
            Минимальная дистанция, мм
            <input id="minDistanceInput" type="number" min="0" value="1">
        </label>

        <label>
            Максимальная дистанция, мм
            <input id="maxDistanceInput" type="number" min="1" value="30000">
        </label>

        <div class="buttons">
            <button class="primary" onclick="clearCanvas()">Очистить карту</button>
        </div>

        <div class="module">
            <h3>Метрики скана</h3>

            <div class="metric">
                <span class="label">Точек после фильтра</span>
                <span id="pointCount" class="value">0</span>
            </div>

            <div class="metric">
                <span class="label">Углы скана</span>
                <span id="angleRangeText" class="value">-</span>
            </div>

            <div class="metric">
                <span class="label">Шаг угла</span>
                <span id="angleStepText" class="value">-</span>
            </div>

            <div class="metric">
                <span class="label">Дистанции</span>
                <span id="distanceRangeText" class="value">-</span>
            </div>

            <div class="metric">
                <span class="label">Ближняя точка</span>
                <span id="nearestPointText" class="value">-</span>
            </div>
        </div>

        <div id="overviewModule" class="module">
            <h3>Обзор скана</h3>

            <div class="overview-box">
                <div id="quadrantStats">Скан ещё не загружен</div>
            </div>

            <pre id="scanPointsTable">Скан ещё не загружен</pre>
        </div>

        <div id="telemetryModule" class="module">
            <h3>Телеметрия</h3>

            <div id="telemetryBlock" class="telemetry-box">
                Телеметрия пока не проверялась.
            </div>

            <div class="buttons">
                <button class="primary" onclick="updateTelemetry()">Проверить робота</button>
            </div>
        </div>

        <div id="errorBlock" class="small-note"></div>

        <div class="small-note">
            В режиме file карта читается из Delta2D_HEX_Data.txt.  
            Автопрокрутка в file-режиме — это replay записанных сканов.  
            В режиме robot карта и телеметрия пробуют читаться с робота.
        </div>
    </aside>
</main>

<script>
    const DATA_MODE = "{{ data_mode }}";

    const mainLayout = document.getElementById("mainLayout");

    const mapModule = document.getElementById("mapModule");
    const overviewModule = document.getElementById("overviewModule");
    const telemetryModule = document.getElementById("telemetryModule");

    const showMap = document.getElementById("showMap");
    const showOverview = document.getElementById("showOverview");
    const showTelemetry = document.getElementById("showTelemetry");

    const canvas = document.getElementById("canvas");
    const ctx = canvas.getContext("2d");

    const scanInput = document.getElementById("scanInput");
    const scanNumberInput = document.getElementById("scanNumberInput");
    const scanNumber = document.getElementById("scanNumber");

    const playbackIntervalInput = document.getElementById("playbackIntervalInput");
    const playbackStatus = document.getElementById("playbackStatus");

    const scaleInput = document.getElementById("scaleInput");
    const scaleValue = document.getElementById("scaleValue");

    const pointSizeInput = document.getElementById("pointSizeInput");
    const pointSizeValue = document.getElementById("pointSizeValue");

    const minDistanceInput = document.getElementById("minDistanceInput");
    const maxDistanceInput = document.getElementById("maxDistanceInput");

    const pointCount = document.getElementById("pointCount");
    const angleRangeText = document.getElementById("angleRangeText");
    const angleStepText = document.getElementById("angleStepText");
    const distanceRangeText = document.getElementById("distanceRangeText");
    const nearestPointText = document.getElementById("nearestPointText");

    const quadrantStats = document.getElementById("quadrantStats");
    const scanPointsTable = document.getElementById("scanPointsTable");

    const telemetryBlock = document.getElementById("telemetryBlock");
    const mapHint = document.getElementById("mapHint");
    const errorBlock = document.getElementById("errorBlock");

    const maxScan = {{ max_scan }};

    let scale = Number(scaleInput.value);
    let pointSize = Number(pointSizeInput.value);
    let currentPoints = [];
    let playbackTimer = null;

    function updateModuleVisibility() {
        mapModule.style.display = showMap.checked ? "flex" : "none";
        overviewModule.style.display = showOverview.checked ? "block" : "none";
        telemetryModule.style.display = showTelemetry.checked ? "block" : "none";

        if (showMap.checked) {
            mainLayout.classList.remove("map-hidden");
        } else {
            mainLayout.classList.add("map-hidden");
        }
    }

    showMap.addEventListener("change", updateModuleVisibility);
    showOverview.addEventListener("change", updateModuleVisibility);
    showTelemetry.addEventListener("change", updateModuleVisibility);

    function getMinDistance() {
        const value = Number(minDistanceInput.value);
        return Number.isNaN(value) ? 1 : value;
    }

    function getMaxDistance() {
        const value = Number(maxDistanceInput.value);
        return Number.isNaN(value) ? 30000 : value;
    }

    function filterPoints(points) {
        const minDistance = getMinDistance();
        const maxDistance = getMaxDistance();

        return points.filter(point => {
            return point.distance >= minDistance && point.distance <= maxDistance;
        });
    }

    function clearCanvas() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        drawMapBase();

        pointCount.textContent = "0";
        angleRangeText.textContent = "-";
        angleStepText.textContent = "-";
        distanceRangeText.textContent = "-";
        nearestPointText.textContent = "-";
        quadrantStats.textContent = "Карта очищена";
        scanPointsTable.textContent = "Карта очищена";
        errorBlock.textContent = "";
    }

    function drawMapBase() {
        drawBackgroundGrid();
        drawRobot();
    }

    function drawBackgroundGrid() {
        ctx.strokeStyle = "#111820";
        ctx.lineWidth = 1;

        for (let x = 0; x <= canvas.width; x += 60) {
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, canvas.height);
            ctx.stroke();
        }

        for (let y = 0; y <= canvas.height; y += 60) {
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(canvas.width, y);
            ctx.stroke();
        }
    }

    function drawRobot() {
        const cx = canvas.width / 2;
        const cy = canvas.height / 2;

        const radius = 34;

        ctx.strokeStyle = "#ffcc00";
        ctx.lineWidth = 4;
        ctx.beginPath();
        ctx.arc(cx, cy, radius, 0, Math.PI * 2);
        ctx.stroke();

        ctx.fillStyle = "#ffcc00";
        ctx.beginPath();
        ctx.arc(cx, cy, 5, 0, Math.PI * 2);
        ctx.fill();

        ctx.strokeStyle = "#ffcc00";
        ctx.lineWidth = 4;
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.lineTo(cx, cy - radius + 4);
        ctx.stroke();
    }

    function calculateAngleStep(angles) {
        if (angles.length < 2) {
            return null;
        }

        const sortedAngles = [...new Set(angles.map(a => Number(a.toFixed(3))))].sort((a, b) => a - b);
        const diffs = [];

        for (let i = 1; i < sortedAngles.length; i++) {
            const diff = sortedAngles[i] - sortedAngles[i - 1];

            if (diff > 0 && diff < 20) {
                diffs.push(diff);
            }
        }

        if (diffs.length === 0) {
            return null;
        }

        const sum = diffs.reduce((a, b) => a + b, 0);
        return sum / diffs.length;
    }

    function getQuadrantName(angle) {
        if (angle >= 0 && angle < 90) return "0°–90°";
        if (angle >= 90 && angle < 180) return "90°–180°";
        if (angle >= 180 && angle < 270) return "180°–270°";
        return "270°–360°";
    }

    function updateStats(points) {
        const filteredPoints = filterPoints(points);

        pointCount.textContent = filteredPoints.length;

        if (filteredPoints.length === 0) {
            angleRangeText.textContent = "-";
            angleStepText.textContent = "-";
            distanceRangeText.textContent = "-";
            nearestPointText.textContent = "-";
            quadrantStats.textContent = "Нет точек после фильтрации";
            scanPointsTable.textContent = "Нет точек после фильтрации";
            return filteredPoints;
        }

        const distances = filteredPoints.map(point => point.distance);
        const angles = filteredPoints.map(point => point.angle);

        const minDistance = Math.min(...distances);
        const maxDistance = Math.max(...distances);

        const minAngle = Math.min(...angles);
        const maxAngle = Math.max(...angles);
        const angleStep = calculateAngleStep(angles);

        const nearestPoint = filteredPoints.reduce((best, point) => {
            return point.distance < best.distance ? point : best;
        }, filteredPoints[0]);

        angleRangeText.textContent = minAngle.toFixed(1) + "° — " + maxAngle.toFixed(1) + "°";
        angleStepText.textContent = angleStep !== null ? angleStep.toFixed(2) + "°" : "-";
        distanceRangeText.textContent = minDistance + " — " + maxDistance + " мм";
        nearestPointText.textContent = nearestPoint.distance + " мм / " + nearestPoint.angle + "°";

        updateOverview(filteredPoints);

        return filteredPoints;
    }

    function updateOverview(points) {
        const quadrants = {
            "0°–90°": 0,
            "90°–180°": 0,
            "180°–270°": 0,
            "270°–360°": 0,
        };

        for (const point of points) {
            const normalizedAngle = ((point.angle % 360) + 360) % 360;
            const quadrant = getQuadrantName(normalizedAngle);
            quadrants[quadrant] += 1;
        }

        quadrantStats.innerHTML =
            "Точек по секторам:<br>" +
            "0°–90°: " + quadrants["0°–90°"] + "<br>" +
            "90°–180°: " + quadrants["90°–180°"] + "<br>" +
            "180°–270°: " + quadrants["180°–270°"] + "<br>" +
            "270°–360°: " + quadrants["270°–360°"];

        const visiblePoints = points.slice(0, 20);

        let table = "№ | angle | distance | x | y\\n";
        table += "----------------------------------------\\n";

        visiblePoints.forEach((point, index) => {
            table +=
                index + " | " +
                point.angle + "° | " +
                point.distance + " мм | " +
                point.x + " | " +
                point.y + "\\n";
        });

        scanPointsTable.textContent = table;
    }

    function drawPoints(points) {
        const filteredPoints = updateStats(points);

        ctx.clearRect(0, 0, canvas.width, canvas.height);
        drawMapBase();

        const cx = canvas.width / 2;
        const cy = canvas.height / 2;

        ctx.fillStyle = "#00ff99";

        for (const point of filteredPoints) {
            const x = cx + point.x * scale;
            const y = cy - point.y * scale;

            ctx.beginPath();
            ctx.arc(x, y, pointSize, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    function setScanIndex(index) {
        let value = Number(index);

        if (Number.isNaN(value)) {
            value = 0;
        }

        if (value < 0) {
            value = 0;
        }

        if (value > maxScan) {
            value = maxScan;
        }

        scanInput.value = value;
        scanNumberInput.value = value;
    }

    async function loadScan() {
        const scanIndex = Number(scanInput.value);

        const response = await fetch(`/api/scan?index=${scanIndex}`);
        const data = await response.json();

        scanNumber.textContent = data.scan_index;
        currentPoints = data.points || [];

        if (data.status === "error") {
            errorBlock.innerHTML =
                "<div class='error-box'>Ошибка карты: " + data.error + "</div>";
            mapHint.textContent = "Ошибка чтения карты";
            drawPoints([]);
            return;
        }

        errorBlock.textContent = "";
        mapHint.textContent = "Источник: " + data.source;

        drawPoints(currentPoints);
    }

    function previousScan() {
        const index = Number(scanInput.value) - 1;
        setScanIndex(index);
        loadScan();
    }

    function nextScan() {
        const index = Number(scanInput.value) + 1;
        setScanIndex(index);
        loadScan();
    }

    function getPlaybackInterval() {
        const value = Number(playbackIntervalInput.value);

        if (Number.isNaN(value) || value < 100) {
            return 300;
        }

        return value;
    }

    function startAutoPlayback() {
        if (playbackTimer !== null) {
            return;
        }

        const interval = getPlaybackInterval();

        if (DATA_MODE === "robot") {
            playbackStatus.textContent = "live-обновление";

            playbackTimer = setInterval(() => {
                loadScan();
                updateTelemetry();
            }, interval);

            return;
        }

        playbackStatus.textContent = "replay записи";

        playbackTimer = setInterval(() => {
            let index = Number(scanInput.value);

            if (index >= maxScan) {
                index = 0;
            } else {
                index += 1;
            }

            setScanIndex(index);
            loadScan();
        }, interval);
    }

    function stopAutoPlayback() {
        if (playbackTimer === null) {
            return;
        }

        clearInterval(playbackTimer);
        playbackTimer = null;

        playbackStatus.textContent = "выключено";
    }

    async function updateTelemetry() {
        const response = await fetch("/api/telemetry");
        const data = await response.json();

        if (!data.enabled) {
            telemetryBlock.innerHTML =
                data.message + "<br>" +
                "Режим: " + data.mode + "<br>" +
                "Связь: " + data.connection;

            if (data.error) {
                telemetryBlock.innerHTML += "<br>Ошибка: " + data.error;
            }

            return;
        }

        telemetryBlock.innerHTML =
            "Источник: " + data.source + "<br>" +
            "Связь: " + data.connection + "<br>" +
            "Скорость: " + data.speed + "<br>" +
            "Заряд: " + data.battery + "<br>" +
            "Угол робота: " + data.robot_angle + "<br>" +
            "Наклон: " + data.tilt_angle;
    }

    scaleInput.addEventListener("input", () => {
        scale = Number(scaleInput.value);
        scaleValue.textContent = scale.toFixed(2);
        drawPoints(currentPoints);
    });

    pointSizeInput.addEventListener("input", () => {
        pointSize = Number(pointSizeInput.value);
        pointSizeValue.textContent = pointSize;
        drawPoints(currentPoints);
    });

    minDistanceInput.addEventListener("input", () => {
        drawPoints(currentPoints);
    });

    maxDistanceInput.addEventListener("input", () => {
        drawPoints(currentPoints);
    });

    scanInput.addEventListener("input", () => {
        setScanIndex(scanInput.value);
        loadScan();
    });

    scanNumberInput.addEventListener("change", () => {
        setScanIndex(scanNumberInput.value);
        loadScan();
    });

    updateModuleVisibility();
    clearCanvas();
    loadScan();
    updateTelemetry();

    if (DATA_MODE === "robot") {
        setInterval(updateTelemetry, 1000);
    }
</script>
</body>
</html>
"""


@app.route("/")
def index():
    info = get_lidar_info()

    total_scans = info.get("scans", 1)
    total_packets = info.get("packets", 0)

    if total_scans < 1:
        total_scans = 1

    return render_template_string(
        HTML,
        lidar_source=info["source"],
        lidar_mode=info.get("lidar_source_mode", DATA_MODE),
        total_scans=total_scans,
        total_packets=total_packets,
        max_scan=total_scans - 1,
        data_mode=DATA_MODE,
    )


@app.route("/api/info")
def api_info():
    return jsonify(get_lidar_info())


@app.route("/api/scan")
def api_scan():
    scan_index = int(request.args.get("index", 0))
    return jsonify(get_scan(scan_index))


@app.route("/api/telemetry")
def api_telemetry():
    return jsonify(get_telemetry())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001, debug=True)