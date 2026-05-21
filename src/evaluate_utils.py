from collections import deque

from src.path_utils import get_kingdoms_json_path
from src.fs_utils import read_json_file


def grade(value, thresholds):
    for limit, rank in thresholds:
        if float(value) >= limit:
            return rank
    return 1


def evaluate_kingdom(data_list: list[dict]):
    fighting_points = 0
    activation_points = 0
    fighters_count = 0
    fighter_bukets = {"s": 0, "a": 0, "b": 0, "c": 0, "d": 0}

    for data in data_list:
        if data.get("kill_60", 0) > 0:
            fighter_bukets[data["grade_kill"]] += 1
        if int(data.get("grade_point_power", 0)) > 1:
            fighters_count += 1
            fighting_points += max(
                int(data.get("grade_point_kill", 0)),
                int(data.get("grade_point_dead", 0)),
            )
        activation_points += max(
            int(data.get("grade_point_collect", 0)),
            int(data.get("grade_point_help", 0)),
        )

    thresholds = [(4, 5), (3, 4), (2, 3), (1, 2)]
    points_2_grade_map = {1: "d", 2: "c", 3: "b", 4: "a", 5: "s"}

    grade_fighting = (
        points_2_grade_map[grade(fighting_points / fighters_count, thresholds)]
        if fighters_count > 0
        else "d"
    )
    grade_activation = points_2_grade_map[grade(activation_points / len(data_list), thresholds)]

    return {
        "grade_fighting": grade_fighting,
        "grade_activation": grade_activation,
        "fighter_bukets": fighter_bukets,
    }


def evaluate_player(data):
    """Convert raw player stats into graded fields."""
    kill_grade = max(
        grade(
            data.get("kill_60", 0),
            [(1_000_000_000, 5), (600_000_000, 4), (400_000_000, 3), (100_000_000, 2)],
        ),
        grade(
            data.get("kill_180", 0) // 2,
            [(1_000_000_000, 5), (600_000_000, 4), (400_000_000, 3), (100_000_000, 2)],
        ),
    )

    dead_grade = max(
        grade(
            data.get("dead_60", 0),
            [(3_000_000, 5), (2_000_000, 4), (1_000_000, 3), (500_000, 2)],
        ),
        grade(
            data.get("dead_180", 0) // 2,
            [(3_000_000, 5), (2_000_000, 4), (1_000_000, 3), (500_000, 2)],
        ),
    )

    power_grade = grade(
        data.get("power", 0),
        [(150_000_000, 5), (100_000_000, 4), (80_000_000, 3), (60_000_000, 2)],
    )

    collect_grade = max(
        grade(
            data.get("collect_60", 0),
            [(1_500_000_000, 5), (1_000_000_000, 4), (800_000_000, 3), (600_000_000, 2)],
        ),
        grade(
            data.get("collect_180", 0) // 3,
            [(1_500_000_000, 5), (1_000_000_000, 4), (800_000_000, 3), (600_000_000, 2)],
        ),
    )

    help_grade = max(
        grade(
            data.get("help_60", 0),
            [(9_000, 5), (6_000, 4), (5_000, 3), (3_600, 2)],
        ),
        grade(
            data.get("help_180", 0) // 2,
            [(9_000, 5), (6_000, 4), (5_000, 3), (3_600, 2)],
        ),
    )

    points_2_grade_map = {1: "d", 2: "c", 3: "b", 4: "a", 5: "s"}
    data["grade_kill"] = points_2_grade_map[kill_grade]
    data["grade_dead"] = points_2_grade_map[dead_grade]
    data["grade_power"] = points_2_grade_map[power_grade]
    data["grade_collect"] = points_2_grade_map[collect_grade]
    data["grade_help"] = points_2_grade_map[help_grade]
    data["grade_point_kill"] = kill_grade
    data["grade_point_dead"] = dead_grade
    data["grade_point_power"] = power_grade
    data["grade_point_collect"] = collect_grade
    data["grade_point_help"] = help_grade

    return data


def evaluate_kingdom_by_kingdom_id(kingdom_id: int):
    idx = kingdom_id // 100
    result_data = {}
    for days in [60, 180]:
        file_path = get_kingdoms_json_path(days=days, index=idx, kingdom_id=kingdom_id)
        data_temp = read_json_file(file_path)
        if not data_temp:
            raise FileNotFoundError(f"Missing kingdom data for {kingdom_id} at {file_path}")
        result_data[f"data_in_{days}"] = data_temp["data"]

    data_list = []
    for player in result_data["data_in_60"]:
        player_180 = next((p for p in result_data["data_in_180"] if p["id"] == player["id"]), None)
        if player_180:
            for key, value in player_180.items():
                player[f"{key}_180"] = value
        data_list.append(evaluate_player(player))

    return evaluate_kingdom(data_list)
