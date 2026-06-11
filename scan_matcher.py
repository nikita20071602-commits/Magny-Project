import math
from dataclasses import dataclass


@dataclass
class Pose:
    x: float = 0.0
    y: float = 0.0
    angle_deg: float = 0.0


class ScanMatcherMap:
    """
    Упрощённый scan matching без одометрии.

    Идея:
    - первый скан кладём как основу;
    - следующий скан пробуем чуть сдвинуть и повернуть;
    - выбираем положение, где больше точек совпадает с уже построенной картой;
    - добавляем выровненный скан в карту.
    """

    def __init__(
        self,
        cell_size: int = 120,
        max_distance: int = 8000,
        xy_search_range: int = 300,
        xy_step: int = 100,
        angle_search_range: int = 8,
        angle_step: int = 2,
    ):
        self.cell_size = cell_size
        self.max_distance = max_distance

        self.xy_search_range = xy_search_range
        self.xy_step = xy_step

        self.angle_search_range = angle_search_range
        self.angle_step = angle_step

        self.pose = Pose()
        self.map_cells = {}
        self.scan_count = 0
        self.last_score = 0

    def reset(self):
        self.pose = Pose()
        self.map_cells = {}
        self.scan_count = 0
        self.last_score = 0

    def point_to_cell(self, x: float, y: float):
        cell_x = round(x / self.cell_size)
        cell_y = round(y / self.cell_size)
        return cell_x, cell_y

    def cell_to_point(self, cell):
        cell_x, cell_y = cell

        return {
            "x": cell_x * self.cell_size,
            "y": cell_y * self.cell_size,
            "angle": None,
            "distance": None,
        }

    def transform_point(self, point: dict, pose: Pose):
        angle_rad = math.radians(pose.angle_deg)

        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        local_x = point["x"]
        local_y = point["y"]

        global_x = pose.x + local_x * cos_a - local_y * sin_a
        global_y = pose.y + local_x * sin_a + local_y * cos_a

        return {
            "angle": point.get("angle"),
            "distance": point.get("distance"),
            "x": round(global_x, 3),
            "y": round(global_y, 3),
        }

    def transform_scan(self, points: list[dict], pose: Pose):
        return [self.transform_point(point, pose) for point in points]

    def get_candidate_poses(self):
        poses = []

        for dx in range(-self.xy_search_range, self.xy_search_range + 1, self.xy_step):
            for dy in range(-self.xy_search_range, self.xy_search_range + 1, self.xy_step):
                for da in range(
                    -self.angle_search_range,
                    self.angle_search_range + 1,
                    self.angle_step,
                ):
                    poses.append(
                        Pose(
                            x=self.pose.x + dx,
                            y=self.pose.y + dy,
                            angle_deg=self.pose.angle_deg + da,
                        )
                    )

        return poses

    def is_valid_point(self, point: dict):
        distance = point.get("distance")

        if distance is None:
            return True

        return 0 < distance <= self.max_distance

    def score_pose(self, points: list[dict], pose: Pose):
        """
        Чем больше точек нового скана попало в уже занятые клетки карты,
        тем лучше положение.
        """
        if not self.map_cells:
            return 0

        score = 0

        # Берём не каждую точку, чтобы не тормозить
        sampled_points = points[::3]

        for point in sampled_points:
            if not self.is_valid_point(point):
                continue

            transformed = self.transform_point(point, pose)
            cell = self.point_to_cell(transformed["x"], transformed["y"])

            # Проверяем не только саму клетку, но и соседние
            cx, cy = cell

            if (cx, cy) in self.map_cells:
                score += 5
            elif (cx + 1, cy) in self.map_cells:
                score += 2
            elif (cx - 1, cy) in self.map_cells:
                score += 2
            elif (cx, cy + 1) in self.map_cells:
                score += 2
            elif (cx, cy - 1) in self.map_cells:
                score += 2

        # Маленький штраф за сильное движение, чтобы скан не улетал
        move_penalty = (
            abs(pose.x - self.pose.x) / 200
            + abs(pose.y - self.pose.y) / 200
            + abs(pose.angle_deg - self.pose.angle_deg) / 4
        )

        return score - move_penalty

    def find_best_pose(self, points: list[dict]):
        if not self.map_cells:
            return Pose(0.0, 0.0, 0.0), 0

        best_pose = self.pose
        best_score = -10**9

        for candidate_pose in self.get_candidate_poses():
            score = self.score_pose(points, candidate_pose)

            if score > best_score:
                best_score = score
                best_pose = candidate_pose

        return best_pose, best_score

    def add_points_to_map(self, points: list[dict]):
        for point in points:
            if not self.is_valid_point(point):
                continue

            cell = self.point_to_cell(point["x"], point["y"])

            if cell not in self.map_cells:
                self.map_cells[cell] = 0

            self.map_cells[cell] += 1

    def align_and_add_scan(self, points: list[dict]):
        """
        Главная функция:
        вход: точки одного скана в локальных координатах лидара;
        выход: стабильная карта в глобальных координатах.
        """
        best_pose, best_score = self.find_best_pose(points)

        transformed_points = self.transform_scan(points, best_pose)

        self.pose = best_pose
        self.last_score = round(best_score, 3)
        self.scan_count += 1

        self.add_points_to_map(transformed_points)

        return {
            "pose": {
                "x": round(self.pose.x, 3),
                "y": round(self.pose.y, 3),
                "angle_deg": round(self.pose.angle_deg, 3),
            },
            "score": self.last_score,
            "scan_count": self.scan_count,
            "map_cell_count": len(self.map_cells),
            "matched_points": transformed_points,
            "map_points": self.get_map_points(),
        }

    def get_map_points(self):
        return [self.cell_to_point(cell) for cell in self.map_cells.keys()]