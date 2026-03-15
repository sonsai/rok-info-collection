import datetime
import json
import os
from pathlib import Path
import re

from src.clients.get_match_data_api import get_match_data_api
from src.clients.get_request import get_request
from src.consts import GITHUB_RAW_URL

def get_user_info(request):
    # 优先从代理头获取真实 IP
    if request.headers.getlist("X-Forwarded-For"):
        ip = request.headers.getlist("X-Forwarded-For")[0]
    else:
        ip = request.remote_addr
    print(f"Your IP is: {ip}")

def get_kvk_match_json_path(folder_name,kingdom_id):
    return f"data/kvk/{folder_name}/match/{kingdom_id}.json"

def get_kvk_dkp_json_path(folder_name,kingdom_id):
    return f"data/kvk/{folder_name}/dkp/{kingdom_id}.json"

def get_match_json_path(index,kingdom_id):
    return f"data/match/{index}/{kingdom_id}.json"

def get_kingdoms_json_path(days,index,kingdom_id):
    return f"data/kingdoms/{days}d/{index}/{kingdom_id}.json"

def get_evaluated_kingdoms_json_path(index,kingdom_id):
    return f"data/kingdoms/evaluated/{index}/{kingdom_id}.json"

def get_players_json_path(pidx):
    return f"data/player/player_list_{pidx}.json"

def read_json_file(file_path:str)->dict:
    if not os.path.exists(file_path):
        return None
    with open(file_path, "r", encoding="utf-8") as f:
        json_data:dict = json.load(f)
    return json_data

def write_data_to_json_file(file_path:str,data:dict):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def grade(value, thresholds):
    for limit, rank in thresholds:
        if float(value) >= limit:
            return rank
    return 1

def evaluate_kingdom(data_list:list[dict]):
    fighting_points = 0
    activation_points = 0
    fighters_count = 0
    for data in data_list:
        if int(data.get("grade_point_power")) > 1:
            fighters_count += 1
            fighting_points += max(
                int(data.get("grade_point_kill",0)),
                int(data.get("grade_point_dead",0))
            )
        activation_points += max(
                int(data.get("grade_point_collect",0)),
                int(data.get("grade_point_help",0))
            )
    thresholds =[
        (4, 5),
        (3, 4),
        (2, 3),
        (1, 2),
    ]
    points_2_grade_map = {
        1:"d",
        2:"c",
        3:"b",
        4:"a",
        5:"s"
    }
    grade_fighting = points_2_grade_map[grade(fighting_points/fighters_count,thresholds)] if fighters_count > 0 else "d"
    grade_activation = points_2_grade_map[grade(activation_points/len(data_list),thresholds)]
    return {
        "grade_fighting":grade_fighting,
        "grade_activation":grade_activation
    }


def evaluate_player(data):
    """
    输入示例:
    {
        "kill": 850000000,
        "dead": 1200000,
        "power": 120000000,
        "collect": 0,
        "help": 0
    }
    """

    # Kill thresholds
    kill_grade = max(
        grade(
            data.get("kill", 0),
            [
                (1_000_000_000, 5),  # 10亿
                (600_000_000, 4),    # 6亿
                (400_000_000, 3),    # 4亿
                (100_000_000, 2),    # 1亿
            ]
        ),
        grade(
            data.get("kill_180", 0) // 2,
            [
                (1_000_000_000, 5),  # 10亿
                (600_000_000, 4),    # 6亿
                (400_000_000, 3),    # 4亿
                (100_000_000, 2),    # 1亿
            ]
        )
    )

    # Dead thresholds
    dead_grade = max(
        grade(
            data.get("dead", 0),
            [
                (3_000_000, 5),   # 300万
                (2_000_000, 4),   # 200万
                (1_000_000, 3),   # 100万
                (500_000, 2),     # 50万
            ]
        ),
        grade(
            data.get("dead_180", 0) // 2,
            [
                (3_000_000, 5),   # 300万
                (2_000_000, 4),   # 200万
                (1_000_000, 3),   # 100万
                (500_000, 2),     # 50万
            ]
        )
    )

    # Power thresholds
    power_grade = grade(
        data.get("power", 0),
        [
            (150_000_000, 5),   # 1.5亿
            (100_000_000, 4),   # 1亿
            (80_000_000, 3),    # 8000万
            (60_000_000, 2),    # 6000万
        ]
    )

    # Collect & Help thresholds
    collect_grade =  max(
        grade(
            data.get("collect", 0),
            [
                (1_500_000_000, 5),   # 15亿
                (1_000_000_000, 4),   # 10亿
                (800_000_000, 3),    # 8亿
                (600_000_000, 2),    # 6亿
            ]
        ),
        grade(
            data.get("collect_180", 0) // 2,
            [
                (1_500_000_000, 5),   # 15亿
                (1_000_000_000, 4),   # 10亿
                (800_000_000, 3),    # 8亿
                (600_000_000, 2),    # 6亿
            ]
        )
    )
    help_grade = max(
        grade(
            data.get("help", 0),
            [
                (9_000, 5),   # 9000
                (6_000, 4),   # 6000
                (5_000, 3),    # 5000
                (3_600, 2),    # 3600
            ]
        ), grade(
            data.get("help_180", 0) // 2,
            [
                (9_000, 5),   # 9000
                (6_000, 4),   # 6000
                (5_000, 3),    # 5000
                (3_600, 2),    # 3600
            ]
        )
    )

    points_2_grade_map = {
        1:"d",
        2:"c",
        3:"b",
        4:"a",
        5:"s"
    }

    # 将评分结果写回输入 JSON
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



def fn(n):
    if abs(n) >= 1_000_000_000:
        return f"{n / 1_000_000_000:.2f}B"
    elif abs(n) >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    elif abs(n) >= 1_000:
        return f"{n / 1_000:.1f}K"
    else:
        return str(n)

def get_YMD_current_date():
    return datetime.datetime.now().strftime("%Y-%m-%d")

def get_repo_json_file(path:str)->dict:
    url = GITHUB_RAW_URL + path
    response = get_request(url=url)
    return response.json()

def total_kingdom(data_list,camp,kingdoms):
    dkp_t4_dead = int(os.environ["DKP_T4_DEAD"])
    dkp_t5_dead = int(os.environ["DKP_T5_DEAD"])
    group_total_kill = 0
    group_total_dead_t4 = 0
    group_total_dead_t5 = 0
    result = {
        "name": camp,
        "kingdoms_names":kingdoms,
        "kingdoms":[],
        "sum":{}
    }
    for d in data_list:
        total_kill = 0
        total_dead_t4 = 0
        total_dead_t5 = 0

        # 遍历所有玩家
        for p in d.get("data"):
            total_kill += p.get("kill", 0)
            total_dead_t4 += p.get("dead_t4", 0)
            total_dead_t5 += p.get("dead_t5", 0)
        kingdom_json = {
            "KD":d.get("kingdom"),
            "PERIOD":d["from_date"] + " ~ " + d["to_date"],
            "KILL":fn(total_kill),
            "T4-DEAD":fn(total_dead_t4),
            "T5-DEAD":fn(total_dead_t5),
            "DKP":fn(total_kill + total_dead_t4 * dkp_t4_dead + total_dead_t5 * dkp_t5_dead)
        }
        result["kingdoms"].append(kingdom_json)
        group_total_kill += total_kill
        group_total_dead_t4 += total_dead_t4
        group_total_dead_t5 += total_dead_t5
    result["kingdoms"].sort(key=lambda x: float(x["DKP"][:-1]) if len(x["DKP"]) > 1 else float(x["DKP"]), reverse=True)
    sum = {
        "TOTAL-KILL":fn(group_total_kill),
        "TOTAL-T4_DEAD":fn(group_total_dead_t4),
        "TOTAL-T5_DEAD":fn(group_total_dead_t5),
        "TOTAL-DKP":fn(group_total_kill+group_total_dead_t4*dkp_t4_dead+group_total_dead_t5*dkp_t5_dead)
    }
    result["sum"] = sum
    return result

def show_kvk_match_data(
        kvk_info,
        show_kingdom:bool=True, 
        show_sum:bool=True
    ):
    folder_name = kvk_info["kvk_map_id"] + "_" + kvk_info["start"].replace("-","")
    camps:dict = kvk_info.get("camps")
    result = {
        "map":kvk_info.get("kvk_map_id", "Unknown"),
        "camps":[]
    }
    for key in camps.keys():
        kingdoms = camps.get(key)
        camp = {
            "name": key ,
            "kingdoms_names": kingdoms,
            "kingdoms":[],
        }
        total_dead = 0
        total_kill = 0
        total_power = 0
        total_score = 0
        for k in kingdoms:
            file_name = f"data/kvk/{folder_name}/match/{k}.json"
            if Path(file_name).exists():
                with open(file_name, "r", encoding="utf-8") as ff:
                    detail_data = json.load(ff)
            else:
                response_dict = get_match_data_api(str(k))
                data = response_dict.get("data")
                detail_data = {
                    "kingdom":k,
                    "date":datetime.datetime.now().strftime("%Y-%m-%d"),
                    "data":data
                }
            dead = detail_data["data"]["dead"]
            kill = detail_data["data"]["kill"]
            power = detail_data["data"]["power"]
            kvk_score = detail_data["data"]["kvkKillScore"]
            eva_result = read_json_file(get_evaluated_kingdoms_json_path(k//100,k)).get("evaluated_result")
            if show_kingdom:
                kingdom_json = {
                    "KD":k,
                    "FIGHTING-RANK":eva_result["grade_fighting"],
                    "ACTIVATION-RANK":eva_result["grade_activation"],
                    "UPDATED-AT":detail_data["data"]["day"],
                    "KVK-SCORE":fn(kvk_score),
                    "POWER":fn(power),
                    "DEAD":fn(dead),
                    "KILL":fn(kill)
                }
                camp["kingdoms"].append(kingdom_json)
            total_dead += dead
            total_kill += kill
            total_power += power
            total_score += kvk_score
        camp["kingdoms"].sort(key=lambda x: float(x["KVK-SCORE"][:-1]) if len(x["KVK-SCORE"]) > 1 else float(x["KVK-SCORE"]), reverse=True)
        if show_sum:
            sum_json = {
                "TOTAL-KVK-SCORE":fn(total_score),
                "TOTAL-POWER":fn(total_power),
                "TOTAL-DEAD":fn(total_dead),
                "TOTAL-KILL":fn(total_kill)
            }
            camp["sum"] = sum_json

        result["camps"].append(camp)
    result["camps"].sort(key=lambda x: float(x["sum"]["TOTAL-KVK-SCORE"][:-1] if len(x["sum"]["TOTAL-KVK-SCORE"]) > 1 else float(x["sum"]["TOTAL-KVK-SCORE"])), reverse=True)
    return result

def evaluate_kingdom_by_kingdom_id(kingdom_id:int):
    idx=int(kingdom_id) // 100
    result_data = {}
    for days in [60,180]:
        file_path = get_kingdoms_json_path(days=days,index=idx,kingdom_id=kingdom_id)
        with open(file_path, "r", encoding="utf-8") as f:
            data_temp:dict = json.load(f)
        result_data[f"data_in_{days}"]= data_temp["data"]
    data_list = []
    for player in result_data["data_in_60"]:
        player_180 = None
        for p in result_data["data_in_180"]:  
            if p["id"] == player["id"]:
                player_180 = p
                break
        if player_180:
            for k,v in player_180.items():
                player[f"{k}_180"] = v
        player = evaluate_player(player)
        data_list.append(player)
    return evaluate_kingdom(data_list)

def show_kvk_dkp(kvk_info):
    start = kvk_info.get("start")
    end = kvk_info.get("end")
    camps:dict = kvk_info.get("camps")
    
    result = {
        "map":kvk_info.get("kvk_map_id", "Unknown"),
        "start":start,
        "end":end,
        "camps":[]
    }
    folder_name = kvk_info["kvk_map_id"] + "_" + kvk_info["start"].replace("-","")
    for key in camps.keys():
        kingdoms = camps.get(key)
        data_list = []
        for k in kingdoms:
            file_name = f"data/kvk/{folder_name}/dkp/{k}.json"
            if Path(file_name).exists():
                with open(file_name, "r", encoding="utf-8") as ff:
                    detail_data = json.load(ff)
            else:
                url = f"https://raw.githubusercontent.com/sonsai/rok-info-collection/refs/heads/main/data/kvk/{folder_name}/dkp/{k}.json"
                response = get_request(url=url)
                detail_data = response.json()
            data_list.append(detail_data)
        camp = total_kingdom(data_list=data_list,camp=key,kingdoms=kingdoms)
        result["camps"].append(camp)

    result["camps"].sort(key=lambda x: float(x["sum"]["TOTAL-DKP"][:-1]) if len(x["sum"]["TOTAL-DKP"]) > 1 else float(x["sum"]["TOTAL-DKP"]), reverse=True)
    return result