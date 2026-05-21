import json
from pathlib import Path

from src.clients.get_match_data_api import get_match_data_api
from src.clients.get_request import get_request
from src.evaluate_utils import evaluate_kingdom, evaluate_player
from src.fs_utils import get_YMD_current_date, read_json_file
from src.path_utils import (
    get_evaluated_kingdoms_json_path,
    get_kingdoms_kvk_history_json_path,
    get_kvk_match_json_path,
    get_players_json_path,
)


def fn(n):
    if abs(n) >= 1_000_000_000:
        return f"{n / 1_000_000_000:.2f}B"
    if abs(n) >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if abs(n) >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def pn(s: str):
    if not isinstance(s, str):
        return float(s)
    s = s.strip().upper()
    if s.endswith("B"):
        return float(s[:-1]) * 1_000_000_000
    if s.endswith("M"):
        return float(s[:-1]) * 1_000_000
    if s.endswith("K"):
        return float(s[:-1]) * 1_000
    return float(s) if "." in s else int(s)


def show_kvk_info_data(data: dict[str, dict]):
    data = dict(sorted(data.items(), key=lambda x: x[0], reverse=True))
    result_data = {"vcr": {}, "on_going": {}, "finished": {}}
    today = get_YMD_current_date()
    for k, v in data.items():
        if v.get("vcr", False):
            result_data["vcr"][k] = v
            continue
        if v["end"] < today:
            result_data["finished"][k] = v
        else:
            result_data["on_going"][k] = v
    return result_data


def total_kingdom(dkp_list, data_list, camp, kingdoms):
    group_total_kill = 0
    group_total_t4 = 0
    group_total_t5 = 0
    group_total_dead_t4 = 0
    group_total_dead_t5 = 0
    result = {"name": camp, "kingdoms_names": kingdoms, "kingdoms": [], "sum": {}}

    for d in data_list:
        total_kill = 0
        total_t4 = 0
        total_t5 = 0
        total_dead_t4 = 0
        total_dead_t5 = 0
        for p in d.get("data", []):
            total_kill += p.get("kill", 0)
            total_t4 += p.get("t4", 0)
            total_t5 += p.get("t5", 0)
            total_dead_t4 += p.get("dead_t4", 0)
            total_dead_t5 += p.get("dead_t5", 0)

        kingdom_json = {
            "KD": d.get("kingdom"),
            "PERIOD": f"{d['from_date']} ~ {d['to_date']}",
            "KILL": fn(total_kill),
            "T4-KILLED": fn(total_t4),
            "T5-KILLED": fn(total_t5),
            "T4-DEAD": fn(total_dead_t4),
            "T5-DEAD": fn(total_dead_t5),
            "DKP": fn(
                total_t4 * dkp_list.get("t4")
                + total_t5 * dkp_list.get("t5")
                + total_dead_t4 * dkp_list.get("t4_dead")
                + total_dead_t5 * dkp_list.get("t5_dead")
            ),
        }
        result["kingdoms"].append(kingdom_json)
        group_total_kill += total_kill
        group_total_t4 += total_t4
        group_total_t5 += total_t5
        group_total_dead_t4 += total_dead_t4
        group_total_dead_t5 += total_dead_t5

    result["kingdoms"].sort(key=lambda x: pn(x["DKP"]), reverse=True)
    result["sum"] = {
        "TOTAL-KILL": fn(group_total_kill),
        "TOTAL-T4-KILLED": fn(group_total_t4),
        "TOTAL-T5-KILLED": fn(group_total_t5),
        "TOTAL-T4-DEAD": fn(group_total_dead_t4),
        "TOTAL-T5-DEAD": fn(group_total_dead_t5),
        "TOTAL-DKP": fn(
            group_total_t4 * dkp_list.get("t4")
            + group_total_t5 * dkp_list.get("t5")
            + group_total_dead_t4 * dkp_list.get("t4_dead")
            + group_total_dead_t5 * dkp_list.get("t5_dead")
        ),
    }
    return result


def sum_dicts(dict_a: dict, dict_b: dict) -> dict:
    for k, v in dict_a.items():
        if k in dict_b:
            dict_a[k] += dict_b[k]
    return dict_a


def show_kvk_match_data(kvk_info, show_kingdom: bool = True, show_sum: bool = True):
    folder_name = kvk_info["kvk_map_id"] + "_" + kvk_info["start"].replace("-", "")
    camps = kvk_info.get("camps", {})
    result = {"map": kvk_info.get("kvk_map_id", "Unknown"), "camps": []}

    for camp_name, kingdoms in camps.items():
        camp = {"name": camp_name, "kingdoms_names": kingdoms, "kingdoms": []}
        total_dead = total_kill = total_power = total_score = total_fighter_points = 0
        total_fighter_bukets = {"s": 0, "a": 0, "b": 0, "c": 0, "d": 0}

        for kingdom_id in kingdoms:
            file_name = Path(f"data/kvk/{folder_name}/match/{kingdom_id}.json")
            if file_name.exists():
                detail_data = json.loads(file_name.read_text(encoding="utf-8"))
            else:
                response_dict = get_match_data_api(str(kingdom_id))
                data = response_dict.get("data")
                detail_data = {"kingdom": kingdom_id, "date": get_YMD_current_date(), "data": data}

            dead = detail_data["data"]["dead"]
            kill = detail_data["data"]["kill"]
            power = detail_data["data"]["power"]
            kvk_score = detail_data["data"].get("kvkKillScore", 0)

            eva_result = detail_data["data"].get("evaluated_result")
            if not eva_result:
                eva_result = read_json_file(get_evaluated_kingdoms_json_path(kingdom_id // 100, kingdom_id)).get("evaluated_result")

            fighter_points = 0
            if eva_result:
                fighter_bukets = eva_result.get("fighter_bukets", {})
                fighter_points += int(fighter_bukets.get("s", 0)) * 10
                fighter_points += int(fighter_bukets.get("a", 0)) * 6
                fighter_points += int(fighter_bukets.get("b", 0)) * 4
                fighter_points += int(fighter_bukets.get("c", 0)) * 1
            else:
                eva_result = {}

            history_data = {}
            history_file_name = Path(get_kingdoms_kvk_history_json_path(kingdom_id))
            if history_file_name.exists():
                history_data = json.loads(history_file_name.read_text(encoding="utf-8"))

            history_evaluate = "-"
            if history_data:
                history_evaluate = ""
                last_items = list(history_data.items())[-3:]
                for kvk, v in last_items:
                    if history_evaluate:
                        history_evaluate += "<br>"
                    history_evaluate += f"{kvk}: <img src='/static/media/rank/level_{v['evaluate']}.png' class='stat-icon-small' title='匹配分占比：{v['match_score_percent']}&#10;DKP占比：{v['dkp_percent']}'>"

            if show_kingdom:
                camp["kingdoms"].append(
                    {
                        "KD": kingdom_id,
                        "FIGHTING-RANK": eva_result.get("grade_fighting", "-"),
                        "FIHGHTER-BUKETS": eva_result.get("fighter_bukets", "-"),
                        "ACTIVATION-RANK": eva_result.get("grade_activation", "-"),
                        "UPDATED-AT": detail_data["data"]["day"],
                        "KVK-SCORE": fn(kvk_score),
                        "POWER": fn(power),
                        "DEAD": fn(dead),
                        "KILL": fn(kill),
                        "KVK-HISTORY": history_evaluate,
                        "FIGHTER-POINTS": fighter_points,
                    }
                )

            total_dead += dead
            total_kill += kill
            total_power += power
            total_score += kvk_score
            total_fighter_points += fighter_points
            total_fighter_bukets = sum_dicts(total_fighter_bukets, eva_result.get("fighter_bukets", {}))

        camp["kingdoms"].sort(
            key=lambda x: float(x["KVK-SCORE"][:-1]) if len(x["KVK-SCORE"]) > 1 else float(x["KVK-SCORE"]),
            reverse=True,
        )

        if show_sum:
            camp["sum"] = {
                "TOTAL-FIGHTER-BUKETS": total_fighter_bukets,
                "TOTAL-FIGHTER-POINTS": total_fighter_points,
                "TOTAL-KVK-SCORE": fn(total_score),
                "TOTAL-POWER": fn(total_power),
                "TOTAL-DEAD": fn(total_dead),
                "TOTAL-KILL": fn(total_kill),
            }

        result["camps"].append(camp)

    result["camps"].sort(
        key=lambda x: float(x["sum"]["TOTAL-KVK-SCORE"][:-1]) if len(x["sum"]["TOTAL-KVK-SCORE"]) > 1 else float(x["sum"]["TOTAL-KVK-SCORE"]),
        reverse=True,
    )
    return result


def evaluate_kingdom_by_kingdom_id(kingdom_id: int):
    idx = kingdom_id // 100
    result_data = {}
    for days in [60, 180]:
        file_path = Path(f"data/kingdoms/{days}d/{idx}/{kingdom_id}.json")
        with open(file_path, "r", encoding="utf-8") as f:
            data_temp = json.load(f)
        result_data[f"data_in_{days}"] = data_temp["data"]

    data_list = []
    for player in result_data["data_in_60"]:
        player_180 = next((p for p in result_data["data_in_180"] if p["id"] == player["id"]), None)
        if player_180:
            for k, v in player_180.items():
                player[f"{k}_180"] = v
        data_list.append(evaluate_player(player))
    return evaluate_kingdom(data_list)


def show_kvk_dkp(dkp_list, kvk_info):
    start = kvk_info.get("start")
    end = kvk_info.get("end")
    data_start = kvk_info.get("data_start")
    data_end = kvk_info.get("data_end")
    camps = kvk_info.get("camps", {})
    result = {"map": kvk_info.get("kvk_map_id", "Unknown"), "start": start, "end": end, "data_start": data_start, "data_end": data_end, "camps": []}
    folder_name = kvk_info["kvk_map_id"] + "_" + kvk_info["start"].replace("-", "")

    for camp_name, kingdoms in camps.items():
        data_list = []
        for kingdom_id in kingdoms:
            file_name = Path(f"data/kvk/{folder_name}/dkp/{kingdom_id}.json")
            if file_name.exists():
                detail_data = json.loads(file_name.read_text(encoding="utf-8"))
            else:
                url = f"https://raw.githubusercontent.com/sonsai/rok-info-collection/refs/heads/main/data/kvk/{folder_name}/dkp/{kingdom_id}.json"
                detail_data = get_request(url=url).json()
            data_list.append(detail_data)

        result["camps"].append(total_kingdom(dkp_list, data_list=data_list, camp=camp_name, kingdoms=kingdoms))

    result["camps"].sort(key=lambda x: pn(x["sum"]["TOTAL-DKP"]), reverse=True)
    return result


def kvk_player_data(kvk_info):
    camps = kvk_info.get("camps", {})
    folder_name = kvk_info["kvk_map_id"] + "_" + kvk_info["start"].replace("-", "")
    result = []

    for camp_name, kingdoms in camps.items():
        for kingdom_id in kingdoms:
            file_name = Path(f"data/kvk/{folder_name}/dkp/{kingdom_id}.json")
            if not file_name.exists():
                continue
            kingdom_data = read_json_file(str(file_name))
            for player in kingdom_data.get("data", []):
                for k, v in list(player.items()):
                    if isinstance(v, int):
                        player[k] = fn(v)
                player["camp"] = camp_name
                player["kingdom"] = kingdom_id
                result.append(player)

    result.sort(key=lambda x: pn(x["kill"]), reverse=True)
    return result


def check_tokens():
    from src.auth_utils import check_tokens as auth_check_tokens
    return auth_check_tokens()


def get_match_data(idx: int, kingdom_id: str):
    match_data_list = []
    ranges = kingdom_id.split(" ") if kingdom_id else range(idx * 100, (idx + 1) * 100)
    for item in ranges:
        try:
            k = int(item)
        except ValueError:
            continue

        if kingdom_id:
            idx = k // 100

        history_file_name = Path(get_kingdoms_kvk_history_json_path(k))
        history_data = json.loads(history_file_name.read_text(encoding="utf-8")) if history_file_name.exists() else {}

        file_name = Path(f"data/match/{idx}/{k}.json")
        if not file_name.exists():
            continue

        detail_data = json.loads(file_name.read_text(encoding="utf-8"))
        if not detail_data["data"]:
            continue

        dead = detail_data["data"]["dead"]
        kill = detail_data["data"]["kill"]
        power = detail_data["data"]["power"]
        kvk_score = detail_data["data"].get("kvkKillScore", 0)

        evaluate_data = detail_data["data"].get("evaluated_result")
        if not evaluate_data:
            evaluate_data = read_json_file(get_evaluated_kingdoms_json_path(k // 100, k)).get("evaluated_result", {})

        fighter_points = 0
        if evaluate_data:
            fighter_bukets = evaluate_data.get("fighter_bukets", {})
            fighter_points += int(fighter_bukets.get("s", 0)) * 10
            fighter_points += int(fighter_bukets.get("a", 0)) * 6
            fighter_points += int(fighter_bukets.get("b", 0)) * 4
            fighter_points += int(fighter_bukets.get("c", 0)) * 1

        history_evaluate = "-"
        if history_data:
            history_evaluate = ""
            last_items = list(history_data.items())[-3:]
            for kvk, v in last_items:
                if history_evaluate:
                    history_evaluate += "<br>"
                history_evaluate += (
                    f"<span onclick=\"location.href='/rok-match-data?kvk_map_id={kvk}'\">{kvk}</span>:"
                    f"<img src=\"/static/media/rank/level_{v['evaluate']}.png\" class=\"stat-icon-small\""
                    f" title=\"匹配分占比：{v['match_score_percent']}&#10;DKP占比：{v['dkp_percent']}\">"
                )

        match_data_list.append(
            {
                "KD": k,
                "FIGHTING-RANK": evaluate_data.get("grade_fighting", "d"),
                "FIHGHTER-BUKETS": evaluate_data.get("fighter_bukets", {}),
                "FIHGHTER-POINTS": fighter_points,
                "ACTIVATION-RANK": evaluate_data.get("grade_activation", "d"),
                "UPDATED-AT": detail_data["data"]["day"],
                "KVK-SCORE": fn(kvk_score),
                "POWER": fn(power),
                "DEAD": fn(dead),
                "KILL": fn(kill),
                "KVK-HISTORY": history_evaluate,
            }
        )

    return match_data_list
