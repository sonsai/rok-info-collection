from collections import deque
import datetime
import json
from pathlib import Path
import shutil

import requests
from src.clients.get_listed_kingdoms_member_info_api import get_listed_kingdoms_member_info_api
from src.clients.get_request import get_request
from src.consts import DATA_NEXT, GITHUB_RAW_URL, KVK_CONFIG_JSON
from src.utility import (
    compute_temp_end,
    evaluate_kingdom,
    evaluate_player,
    get_evaluated_kingdoms_json_path,
    get_ex_evaluated_kingdoms_json_path,
    get_kingdoms_json_path,
    get_players_json_path,
    get_repo_json_file,
    read_json_file,
    set_history_info,
    write_data_to_json_file,
    get_evaluated_kingdoms_json_path,
    get_kingdoms_kvk_history_json_path,
    get_kvk_dkp_json_path,
    get_kvk_match_json_path,
    get_match_json_path,
    get_repo_json_file,
    get_match_data_api,
    pn,
    read_json_file,
    show_kvk_dkp,
    show_kvk_match_data,
    write_data_to_json_file,
)


def ensure_dir(path):
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def _as_list(value):
    return value if isinstance(value, list) else [value]


def _build_player_map(players):
    return {player["id"]: player for player in (players or [])}


def _merge_history(key, player, source_player):
    if source_player is None:
        return _as_list(player[key])

    source_value = source_player.get(key, [])
    source_history = _as_list(source_value)
    if source_player["dt"] >= player["dt"]:
        return source_history

    history_queue = deque(source_history, maxlen=60)
    history_queue.append(player[key])
    return list(history_queue)


def _load_player_info_list(path, cache):
    if path in cache:
        return cache[path]
    info = read_json_file(path) or {}
    cache[path] = info
    return info


def _load_previous_evaluation(player_id, player_info):
    if not player_info or len(player_info.get("kingdom", [])) <= 1:
        return None, None

    previous_kingdom = player_info["kingdom"][-2]
    prev_idx = int(previous_kingdom) // 100
    prev_path = Path(get_ex_evaluated_kingdoms_json_path(index=prev_idx, kingdom_id=previous_kingdom))
    if not prev_path.exists():
        return None, previous_kingdom

    prev_data = read_json_file(str(prev_path))
    return _build_player_map(prev_data.get("data", [])), previous_kingdom

def save_kvk_data():
    """Save KVK match and DKP files for each configured KVK entry."""
    ensure_dir("data/kvk")
    kvk_configs = get_repo_json_file(KVK_CONFIG_JSON) or {}
    temp_end = compute_temp_end()

    for count, (kvk_id, config) in enumerate(kvk_configs.items(), start=1):
        start = config.get("data_start", config.get("start"))
        end = config.get("data_end", config.get("end"))
        folder_name = f"{config['kvk_map_id']}_{config['start'].replace('-','')}"
        ensure_dir(Path("data/kvk") / folder_name / "match")
        ensure_dir(Path("data/kvk") / folder_name / "dkp")

        if start > temp_end:
            start = temp_end
        if end >= temp_end:
            end = temp_end

        kingdoms = [kingdom for camp in config["camps"].values() for kingdom in camp]
        if not kingdoms:
            print(f"无任何王国，跳过处理: {kvk_id}")
            continue

        url = GITHUB_RAW_URL + get_kvk_match_json_path(folder_name, kingdoms[0])
        response = get_request(url=url)
        if end < temp_end and response.status_code == 200:
            continue

        for kingdom in kingdoms:
            kvk_match_file = Path(get_kvk_match_json_path(folder_name, kingdom))
            if not kvk_match_file.exists():
                shutil.copy(get_match_json_path(kingdom // 100, kingdom), kvk_match_file)

            response_data = get_listed_kingdoms_member_info_api(
                from_date=start,
                to_date=end,
                kingdom_id=kingdom,
            ).get("data")
            if not response_data:
                continue

            write_data_to_json_file(
                get_kvk_dkp_json_path(folder_name, kingdom),
                {"kingdom": kingdom, "from_date": start, "to_date": end, "data": response_data},
            )

        print(f"Processed {count} / {len(kvk_configs)}")


def save_match_data(id_from, id_to):
    """Save match data for a continuous kingdom ID range."""
    no_data_count = 0
    for kingdom_id in range(int(id_from), int(id_to)):
        idx = kingdom_id // 100
        ensure_dir(Path("data/match") / str(idx))
        response_data = get_match_data_api(str(kingdom_id)).get("data")
        if not response_data:
            no_data_count += 1
            if no_data_count > 2:
                break
            continue
        no_data_count = 0

        evaluated_data = read_json_file(get_evaluated_kingdoms_json_path(idx, kingdom_id))
        if evaluated_data:
            response_data["evaluated_result"] = evaluated_data.get("evaluated_result", {})

        write_data_to_json_file(
            get_match_json_path(idx, kingdom_id),
            {"kingdom": kingdom_id, "date": datetime.datetime.now().strftime("%Y-%m-%d"), "data": response_data},
        )


def save_kingdoms_data(id_from, id_to):
    """Update historical kingdom data for 1d/60d/180d windows."""
    update_kingdom_data(id_from, id_to, [1, 60, 180], datetime.datetime.now())


def update_next_run_time():
    """Refresh next execution marker for scheduled tasks."""
    write_data_to_json_file(
        DATA_NEXT,
        {"datetime": (datetime.datetime.now() + datetime.timedelta(days=1)).isoformat()},
    )


def save_kvk_history_data():
    """Generate and save per-kingdom KVK history summaries."""
    kvk_configs = read_json_file(KVK_CONFIG_JSON) or {}
    cutoff_date = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

    for kvk_key, config in kvk_configs.items():
        if config["end"] > cutoff_date:
            continue

        match_data = show_kvk_match_data(config)
        dkp_data = show_kvk_dkp(
            config.get("dkp_list")
            or {"t4": 5, "t5": 10, "t4_dead": 15, "t5_dead": 15},
            config,
        )

        match_camps = {camp["name"]: camp for camp in match_data["camps"]}
        dkp_camps = {camp["name"]: camp for camp in dkp_data["camps"]}

        for camp_name, kingdoms in config["camps"].items():
            match_camp = match_camps.get(camp_name, {})
            dkp_camp = dkp_camps.get(camp_name, {})
            match_kingdoms = match_camp.get("kingdoms", [])
            dkp_kingdoms = dkp_camp.get("kingdoms", [])
            match_total = pn(match_camp.get("sum", {}).get("TOTAL-KVK-SCORE"))
            dkp_total = pn(dkp_camp.get("sum", {}).get("TOTAL-DKP"))

            for kd in kingdoms:
                history_path = get_kingdoms_kvk_history_json_path(kd)
                history = read_json_file(history_path) or {}
                if kvk_key in history:
                    continue

                target_match = next((item for item in match_kingdoms if item["KD"] == kd), {})
                target_dkp = next((item for item in dkp_kingdoms if item["KD"] == kd), {})

                match_score_percent = (
                    pn(target_match.get("KVK-SCORE")) / match_total if match_total else 0
                )
                dkp_percent = pn(target_dkp.get("DKP")) / dkp_total if dkp_total else 0

                match_rank = (
                    f"{match_kingdoms.index(target_match) + 1} / {len(match_kingdoms)}"
                    if target_match
                    else "0 / 0"
                )
                dkp_rank = (
                    f"{dkp_kingdoms.index(target_dkp) + 1} / {len(dkp_kingdoms)}"
                    if target_dkp
                    else "0 / 0"
                )

                ratio = dkp_percent / match_score_percent if match_score_percent else 1.0
                evaluate = "s" if ratio > 1.5 else "a" if ratio >= 1.0 else "d"

                history[kvk_key] = {
                    "match_score_percent": f"{round(match_score_percent * 100, 2)}%",
                    "dkp_percent": f"{round(dkp_percent * 100, 2)}%",
                    "evaluate": evaluate,
                    "match_rank": match_rank,
                    "dkp_rank": dkp_rank,
                }

                ensure_dir(Path("data/kingdoms/history") / str(kd // 100))
                write_data_to_json_file(history_path, history)


def update_kvk_info():
    """Fetch remote KVK info and merge new entries to config."""
    api_url = "https://app.rokstats.online/api/kvk/lost-kingdoms/current"
    raw = fetch_kvk_data(api_url)
    converted = convert_to_custom_format(raw)

    kvk_infos = read_json_file(KVK_CONFIG_JSON) or {}
    kvk_infos.update({k: v for k, v in converted.items() if k not in kvk_infos})
    save_json(kvk_infos, KVK_CONFIG_JSON)

def update_kingdom_data(id_from, id_to, data_pattern, target_date):
    working_file_list = {}
    ensure_dir("data/player")
    no_data_cnt = 0

    for kingdom_id in range(int(id_from), int(id_to)):
        print(f"当前王国ID：{kingdom_id}")
        if no_data_cnt >= 9:
            break

        kingdom_index = kingdom_id // 100
        for days in data_pattern:
            dest_dir = Path("data/kingdoms") / f"{days}d" / str(kingdom_index)
            ensure_dir(dest_dir)
            kingdoms_file_path = dest_dir / f"{kingdom_id}.json"

            from_date = (target_date - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
            to_date = (target_date - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            response = get_listed_kingdoms_member_info_api(
                from_date=from_date,
                to_date=to_date,
                kingdom_id=kingdom_id,
            )

            data = response.get("data")
            if not data:
                no_data_cnt += 1
                continue

            no_data_cnt = 0
            write_data_to_json_file(
                str(kingdoms_file_path),
                {"kingdom": kingdom_id, "from_date": from_date, "to_date": to_date, "data": data},
            )

        daily_path = Path(get_kingdoms_json_path("1", kingdom_index, kingdom_id))
        if not daily_path.exists():
            continue

        player_data = read_json_file(str(daily_path))
        players_1d = player_data.get("data", [])
        if not players_1d:
            continue

        result_data = {}
        for days in data_pattern:
            history_file = Path(get_kingdoms_json_path(days=days, index=kingdom_index, kingdom_id=kingdom_id))
            history_data = read_json_file(str(history_file))
            if not history_data:
                result_data = {}
                break
            result_data[f"data_in_{days}"] = history_data["data"]

        if not result_data:
            continue

        now_eva_path = Path(get_ex_evaluated_kingdoms_json_path(index=kingdom_index, kingdom_id=kingdom_id))
        new_kingdom = not now_eva_path.exists()
        now_eva_map = _build_player_map(read_json_file(str(now_eva_path)).get("data", []) if now_eva_path.exists() else [])
        data_60_map = _build_player_map(result_data.get("data_in_60", []))
        data_180_map = _build_player_map(result_data.get("data_in_180", []))

        data_list = []
        for player in players_1d:
            player_id = player["id"]
            if new_kingdom:
                print(f"分类:新王国, 玩家ID:{player_id}")

            prev_player = now_eva_map.get(player_id)
            if prev_player is None:
                info_file = Path(get_players_json_path(int(player_id) // 1_000_000))
                player_info = _load_player_info_list(str(info_file), working_file_list).get(player_id)
                prev_map, previous_kingdom = _load_previous_evaluation(player_id, player_info)
                if prev_map is None and player_info and len(player_info.get("kingdom", [])) > 1:
                    print(f"分类:没有获取对象王国数据{previous_kingdom}, 玩家ID:{player_id}")
                prev_player = prev_map.get(player_id) if prev_map else None

            for stat_key in ("kill", "help", "collect"):
                player[stat_key] = _merge_history(stat_key, player, prev_player)

            player_60 = data_60_map.get(player_id)
            if player_60:
                for key, value in player_60.items():
                    if key not in {"id", "name", "max_power", "power", "dt"}:
                        player[f"{key}_60"] = value
            else:
                player["kill_60"] = sum(_as_list(player.get("kill", [])))
                player["help_60"] = sum(_as_list(player.get("help", [])))
                player["collect_60"] = sum(_as_list(player.get("collect", [])))

            player_180 = data_180_map.get(player_id)
            if player_180:
                for key, value in player_180.items():
                    if key not in {"id", "name", "max_power", "power", "dt"}:
                        player[f"{key}_180"] = value

            player = evaluate_player(player)
            player = set_history_info(player, working_file_list)
            data_list.append(player)

        eva_result = evaluate_kingdom(data_list)
        out_path = Path(get_evaluated_kingdoms_json_path(index=kingdom_index, kingdom_id=kingdom_id))
        ensure_dir(out_path.parent)
        write_data_to_json_file(
            str(out_path),
            {"kingdom": kingdom_id, "evaluated_result": eva_result, "data": data_list},
        )

    for path, data in working_file_list.items():
        write_data_to_json_file(path, data)


def fetch_kvk_data(API_URL):
    """Fetch KVK data from rokstats API."""
    response = requests.get(API_URL, timeout=10)
    response.raise_for_status()
    return response.json()


def convert_to_custom_format(raw):
    """Convert rokstats API format into custom KVK config format."""
    result = {}

    map_type = {
        "402": "heroic_anthem",
        "1401": "tides_of_war",
        "1902": "king_of_all_britain",
        "1001": "siege_of_orleans",
        "2001": "song_of_troy",
        "1102": "warriors_unbound",
    }

    map_info = {
        "tides_of_war": {"1": "FIRE", "2": "EARTH", "3": "WIND", "4": "WATER"},
        "heroic_anthem": {"1": "FIRE", "2": "EARTH", "3": "WIND", "4": "WATER"},
        "king_of_all_britain": {"1": "NORTHUMBRIA", "2": "EAST_ANGLIA", "3": "MERCIA", "4": "WESSEX"},
        "siege_of_orleans": {"1": "Brittany", "2": "Picardy", "3": "Bourbon", "4": "Auvergne", "5": "La Marche", "6": "Poitou"},
        "song_of_troy": {"1": "Aeolia", "2": "Dardania", "3": "Lycia", "4": "Mycenae"},
        "warriors_unbound": {"1": "FIRE", "2": "EARTH", "3": "WIND", "4": "WATER", "5": "GREENWOOD", "6": "DAYBREAK"},
    }

    for item in raw.get("lostKingdoms", []):
        kvk_id = f"C{item.get('code')}"
        start = item.get("battlePhaseStart", "").split("T")[0]
        end = item.get("immigrationBegins", "").split("T")[0]
        if not start or start < "2025-12-01":
            continue

        kvk_type = map_type.get(str(item.get("map", {}).get("code")))
        if not kvk_type:
            continue

        camps = {}
        vcr_flag = False
        for camp in item.get("participants", []):
            server_id = int(camp["serverId"]) + 1000
            if server_id == 1545:
                vcr_flag = True
            camp_name = map_info[kvk_type].get(str(camp["campNum"]), str(camp["campNum"]))
            camps.setdefault(camp_name, []).append(server_id)

        result[kvk_id] = {
            "kvk_map_id": kvk_id,
            "kvk_type": kvk_type,
            "vcr": vcr_flag,
            "kvk_type_cn": "",
            "end_apply": start,
            "start": start,
            "end": end,
            "data_start": start,
            "data_end": end,
            "dkp_list": {"t4": 5, "t5": 10, "t4_dead": 15, "t5_dead": 15},
            "dkp_calc_rule": "t4*5 + t5*10 + (t4_dead + t5_dead)*15",
            "camps": camps,
        }

    return result


def save_json(data, filename="kvk.json"):
    """Save JSON to file."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"Saved to {filename}")
