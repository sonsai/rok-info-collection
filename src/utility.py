import datetime
import json
import os
from pathlib import Path

import requests

from src.clients.get_listed_kingdoms_member_info_api import get_listed_kingdoms_member_info_api
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

def get_kingdoms_kvk_history_json_path(kingdom_id):
    index = kingdom_id // 100
    return f"data/kingdoms/history/{index}/{kingdom_id}.json"

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
    fighter_bukets={
        "s":0,
        "a":0,
        "b":0,
        "c":0,
        "d":0,
    }
    for data in data_list:
        if data.get("kill_60",0) > 0:
            fighter_bukets[data["grade_kill"]] += 1
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
        "grade_activation":grade_activation,
        "fighter_bukets":fighter_bukets
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
            data.get("kill_60", 0),
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
            data.get("dead_60", 0),
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
            data.get("collect_60", 0),
            [
                (1_500_000_000, 5),   # 15亿
                (1_000_000_000, 4),   # 10亿
                (800_000_000, 3),    # 8亿
                (600_000_000, 2),    # 6亿
            ]
        ),
        grade(
            data.get("collect_180", 0) // 3,
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
            data.get("help_60", 0),
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

def set_history_info(data):
    id = int(data.get("id"))
    player_list_data_path = get_players_json_path(id//1_000_000)
    player_list_data = read_json_file(player_list_data_path)
    past_player_data = player_list_data.get(str(id))
    if past_player_data:
        past_kingdom_list = past_player_data.get("kingdom")
        if len(past_kingdom_list) > 1:
            data["past_kingdoms"] = past_kingdom_list[-2:-5:-1]
        past_name_list = past_player_data.get("name")
        if len(past_name_list) > 1:
            data["past_names"] = past_name_list[-2:-5:-1]
    return data

def get_player_from_kingdom(player_id,kingdom_data) -> dict:
    for player in kingdom_data["data"]:
        if player["id"] == player_id:
            return player
    return {}

def fn(n):
    if abs(n) >= 1_000_000_000:
        return f"{n / 1_000_000_000:.2f}B"
    elif abs(n) >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    elif abs(n) >= 1_000:
        return f"{n / 1_000:.1f}K"
    else:
        return str(n)
def pn(s: str):
    s = s.strip().upper()
    if s.endswith("B"):
        return float(s[:-1]) * 1_000_000_000
    elif s.endswith("M"):
        return float(s[:-1]) * 1_000_000
    elif s.endswith("K"):
        return float(s[:-1]) * 1_000
    else:
        return float(s) if "." in s else int(s)

def get_YMD_current_date():
    return datetime.datetime.now().strftime("%Y-%m-%d")

def get_repo_json_file(path:str)->dict:
    url = GITHUB_RAW_URL + path
    response = get_request(url=url)
    return response.json()

def show_kvk_info_data(data:dict[str,dict]):
    data = dict(sorted(data.items(), key=lambda x: x[0], reverse=True))

    result_data = {}
    result_data["vcr"] = {}
    result_data["on_going"] = {}
    result_data["finished"] = {}
    for k, v in data.items():
        if v.get("vcr",False):
            result_data["vcr"][k] = v
            continue
        if v["end"] < datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"):
            result_data["finished"][k] = v
        else:
            result_data["on_going"][k] = v
    return result_data

def total_kingdom(dkp_list,data_list,camp,kingdoms):
    group_total_kill = 0
    group_total_t4 = 0
    group_total_t5 = 0
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
        total_t4 = 0
        total_t5 = 0
        total_dead_t4 = 0
        total_dead_t5 = 0

        # 遍历所有玩家
        for p in d.get("data"):
            total_kill += p.get("kill", 0)
            total_t4 += p.get("t4", 0)
            total_t5 += p.get("t5", 0)
            total_dead_t4 += p.get("dead_t4", 0)
            total_dead_t5 += p.get("dead_t5", 0)
        kingdom_json = {
            "KD":d.get("kingdom"),
            "PERIOD":d["from_date"] + " ~ " + d["to_date"],
            "KILL":fn(total_kill),
            "T4-KILLED":fn(total_t4),
            "T5-KILLED":fn(total_t5),
            "T4-DEAD":fn(total_dead_t4),
            "T5-DEAD":fn(total_dead_t5),
            "DKP":fn(
                total_t4 * dkp_list.get("t4")+ 
                total_t5 * dkp_list.get("t5")+ 
                total_dead_t4 * dkp_list.get("t4_dead") + 
                total_dead_t5 * dkp_list.get("t5_dead"))
        }
        result["kingdoms"].append(kingdom_json)
        group_total_kill += total_kill
        group_total_t4 += total_t4
        group_total_t5 += total_t5
        group_total_dead_t4 += total_dead_t4
        group_total_dead_t5 += total_dead_t5
    result["kingdoms"].sort(key=lambda x: pn(x["DKP"]), reverse=True)
    sum = {
        "TOTAL-KILL":fn(group_total_kill),
        "TOTAL-T4-KILLED":fn(group_total_t4),
        "TOTAL-T5-KILLED":fn(group_total_t5),
        "TOTAL-T4-DEAD":fn(group_total_dead_t4),
        "TOTAL-T5-DEAD":fn(group_total_dead_t5),
        "TOTAL-DKP":fn(
                group_total_t4 * dkp_list.get("t4")+ 
                group_total_t5 * dkp_list.get("t5")+ 
                group_total_dead_t4 * dkp_list.get("t4_dead") + 
                group_total_dead_t5 * dkp_list.get("t5_dead"))
    }
    result["sum"] = sum
    return result


def sum_dicts(dict_a:dict, dict_b:dict) -> dict:
    for k,v in dict_a.items():
        if k in dict_b:
            dict_a[k]+=dict_b[k]
        else:
            continue
    return dict_a

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
        total_fighter_points = 0
        total_fighter_bukets={
            "s":0,
            "a":0,
            "b":0,
            "c":0,
            "d":0,
        }
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
            if "kvkKillScore" in detail_data["data"]:
                kvk_score = detail_data["data"]["kvkKillScore"]
            else:
                kvk_score = 0
            eva_dict = read_json_file(get_evaluated_kingdoms_json_path(k//100,k))
            fighter_points = 0
            if eva_dict:
                eva_result = eva_dict.get("evaluated_result")
                fighter_bukets = eva_result.get("fighter_bukets",{})
                fighter_points += int(fighter_bukets.get("s")) * 10
                fighter_points += int(fighter_bukets.get("a")) * 6
                fighter_points += int(fighter_bukets.get("b")) * 4
                fighter_points += int(fighter_bukets.get("c")) * 1

            else:
                eva_result = {}
            history_file_name = get_kingdoms_kvk_history_json_path(k)
            history_data={}
            if Path(history_file_name).exists():
                with open(history_file_name, "r", encoding="utf-8") as ff:
                    history_data = json.load(ff)
            history_evaluate = "-"
            if history_data:
                history_evaluate = ""
                last_items = list(history_data.items())[-3:]
                for kvk, v in last_items:
                    if history_evaluate:
                        history_evaluate = history_evaluate+"<br>"
                    history_evaluate = history_evaluate+f"{kvk}: <img src='/static/media/rank/level_{v['evaluate']}.png' class='stat-icon-small' title='匹配分占比：{v['match_score_percent']}&#10;DKP占比：{v['dkp_percent']}'>"
            if show_kingdom:
                kingdom_json = {
                    "KD":k,
                    "FIGHTING-RANK":eva_result.get("grade_fighting","-"),
                    "FIHGHTER-BUKETS":eva_result.get("fighter_bukets","-"),
                    "ACTIVATION-RANK":eva_result.get("grade_activation","-"),
                    "UPDATED-AT":detail_data["data"]["day"],
                    "KVK-SCORE":fn(kvk_score),
                    "POWER":fn(power),
                    "DEAD":fn(dead),
                    "KILL":fn(kill),
                    "KVK-HISTORY":history_evaluate,
                    "FIGHTER-POINTS":fighter_points
                }
                camp["kingdoms"].append(kingdom_json)
            total_dead += dead
            total_kill += kill
            total_power += power
            total_score += kvk_score
            total_fighter_points += fighter_points
            total_fighter_bukets = sum_dicts(total_fighter_bukets, eva_result.get("fighter_bukets","-"))
        camp["kingdoms"].sort(key=lambda x: float(x["KVK-SCORE"][:-1]) if len(x["KVK-SCORE"]) > 1 else float(x["KVK-SCORE"]), reverse=True)
        if show_sum:
            sum_json = {
                "TOTAL-FIGHTER-BUKETS":total_fighter_bukets,
                "TOTAL-FIGHTER-POINTS":total_fighter_points,
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

def show_kvk_dkp(dkp_list, kvk_info):

    start = kvk_info.get("start")
    end = kvk_info.get("end")
    data_start = kvk_info.get("data_start")
    data_end = kvk_info.get("data_end")
    camps:dict = kvk_info.get("camps")
    
    result = {
        "map":kvk_info.get("kvk_map_id", "Unknown"),
        "start":start,
        "end":end,
        "data_start":data_start,
        "data_end":data_end,
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
        camp = total_kingdom(dkp_list,data_list=data_list,camp=key,kingdoms=kingdoms)
        result["camps"].append(camp)

    result["camps"].sort(key=lambda x: pn(x["sum"]["TOTAL-DKP"]), reverse=True)
    return result

def kvk_player_data(kvk_info):
    camps:dict = kvk_info.get("camps")
    folder_name = kvk_info["kvk_map_id"] + "_" + kvk_info["start"].replace("-","")

    result = []
    for key in camps.keys(): 
        kingdoms = camps.get(key)
        for kingdom_id in kingdoms:
            file_name = f"data/kvk/{folder_name}/dkp/{kingdom_id}.json"
            if os.path.exists(file_name):
                kingdom_data = read_json_file(file_name)
                for player in kingdom_data["data"]:
                    for k,v in player.items():
                        if isinstance(v,int):
                            player[k]=fn(v)
                    player["camp"] = key
                    player["kingdom"] = kingdom_id
                    result.append(player)
            else:
                continue
    
    result.sort(key=lambda x: pn(x["kill"]), reverse=True)
    return result

def check_tokens():

    try:
        get_listed_kingdoms_member_info_api()
        print("check_tokens success.")
        return
    except:
        print("check_tokens failed.")
        pass

    session = requests.Session()
    params = {
        "timestamp":os.environ.get("cap_timestamp") or "1774368716235",
        "signature":os.environ.get("cap_signature") or "6925bddd2a2b57cd86f29b990611c0ef",
        "access_key":os.environ.get("cap_access_key") or "97r9ihrvxuh6d8kdrztw03ovlvxtssx4"
    }
    url = "https://passport-global-api.lilithgame.com/api/v2/passport-login/captcha"
    resp = session.get(
        url=url,
        params=params
    )
    result = resp.json()
    print(result)
    login_url="https://passport-global-api.lilithgame.com/api/v2/passport-login/password"
    payload = {
        "pup_token":result["data"]["pup_token"],
        "client_id":"rok_game_tools_lglo",
        "username":"sonsai1988@gmail.com",
        "password":"76efa73c8eddd696eef21633e72d40e2",
        "account_type":0,
        "login_free":True
    }
    resp_login = session.post(
        url=login_url,
        json=payload
    )
    login_result = resp_login.json()
    print(login_result)
    p_token = login_result["data"]["jwt_token"]

    bind_role_url = "https://rok-game-tools-global-api.lilith.com/api/lilith/bind_role"
    bind_role_payload={
        "app_id":2104267,
        "app_uid":"45272230",
        "uid":47913824,
        "svr_id":1545
    }
    bind_role_header ={
        "pauthorization":p_token
    }

    resp_bind_role = session.post(
        url=bind_role_url,
        json=bind_role_payload,
        headers=bind_role_header
    )
    bind_role_result =resp_bind_role.json()
    print(bind_role_result)
    b_token = bind_role_result["data"]["access_token"]
    
    os.environ["ROK_B_TOKEN"]=b_token
    os.environ["ROK_P_TOKEN"]=p_token

    try:
        get_listed_kingdoms_member_info_api()
        print("tokens reset succeed.")
        return
    except:
        print("tokens reset failed.")
        raise

def get_match_data(idx:int, kingdom_id:str):
    match_data_list = []
    if kingdom_id:
        ranges = kingdom_id.split(" ")
    else:
        ranges = range((idx)*100,(idx+1)*100)
    for k in ranges:
        try:
            k = int(k)
        except:
            continue
        if kingdom_id:
            idx = k // 100

        history_file_name = get_kingdoms_kvk_history_json_path(k)
        history_data={}
        if Path(history_file_name).exists():
            with open(history_file_name, "r", encoding="utf-8") as ff:
                history_data = json.load(ff)

        file_name = f"data/match/{idx}/{k}.json"
        if Path(file_name).exists():
            with open(file_name, "r", encoding="utf-8") as ff:
                detail_data = json.load(ff)

            if not detail_data["data"]:
                continue
            dead = detail_data["data"]["dead"]
            kill = detail_data["data"]["kill"]
            power = detail_data["data"]["power"]
            if "kvkKillScore" in detail_data["data"]:
                kvk_score = detail_data["data"]["kvkKillScore"]
            else:
                kvk_score = 0
            eva_result = read_json_file(get_evaluated_kingdoms_json_path(k//100,k)).get("evaluated_result")
            fighter_points = 0
            fighter_bukets = eva_result.get("fighter_bukets",{})
            fighter_points += int(fighter_bukets.get("s")) * 10
            fighter_points += int(fighter_bukets.get("a")) * 6
            fighter_points += int(fighter_bukets.get("b")) * 4
            fighter_points += int(fighter_bukets.get("c")) * 1
            history_evaluate = "-"
            if history_data:
                history_evaluate = ""
                last_items = list(history_data.items())[-3:]
                for kvk, v in last_items:
                    if history_evaluate:
                        history_evaluate = history_evaluate+"<br>"
                    history_evaluate = history_evaluate+f"""
                    <span onclick="location.href='/rok-match-data?kvk_map_id={kvk}'">{kvk}</span>:
                    <img src="/static/media/rank/level_{v['evaluate']}.png"
                        class="stat-icon-small"
                        title="匹配分占比：{v['match_score_percent']}&#10;DKP占比：{v['dkp_percent']}">
                    """
                    # history_evaluate = history_evaluate+f"{kvk}:匹配分占比 {v['match_score_percent']} ,DKP占比 {v['dkp_percent']} ,KVK表现评价 <img src='/static/media/rank/level_{v['evaluate']}.png' class='stat-icon-small'>"
            
            kingdom_json = {
                "KD":k,
                "FIGHTING-RANK":eva_result["grade_fighting"],
                "FIHGHTER-BUKETS":eva_result["fighter_bukets"],
                "FIHGHTER-POINTS":fighter_points,
                "ACTIVATION-RANK":eva_result["grade_activation"],
                "UPDATED-AT":detail_data["data"]["day"],
                "KVK-SCORE":fn(kvk_score),
                "POWER":fn(power),
                "DEAD":fn(dead),
                "KILL":fn(kill),
                "KVK-HISTORY":history_evaluate
            }

            match_data_list.append(kingdom_json)
    return match_data_list