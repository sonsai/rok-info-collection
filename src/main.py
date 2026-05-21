from collections import deque
import datetime
import json
import os
import shutil
import sys
from src.actions import update_kingdom_data
from src.clients.get_request import get_request
from src.clients.get_listed_kingdoms_member_info_api import get_listed_kingdoms_member_info_api
from src.consts import DATA_NEXT, GITHUB_RAW_URL, KVK_CONFIG_JSON, MATCH_NEXT
from src.utility import (
    check_tokens,
    evaluate_kingdom,
    evaluate_player,
    get_evaluated_kingdoms_json_path,
    get_ex_evaluated_kingdoms_json_path,
    get_kingdoms_json_path,
    get_kingdoms_kvk_history_json_path,
    get_kvk_dkp_json_path,
    get_kvk_match_json_path,
    get_match_json_path,
    get_player_from_kingdom,
    get_players_json_path,
    get_repo_json_file,
    pn,
    read_json_file,
    set_history_info,
    show_kvk_match_data, 
    show_kvk_dkp,
    get_match_data_api,
    write_data_to_json_file
)

mode = os.environ["MODE"]

check_tokens()

if mode == "save_kvk_data":
    os.makedirs("data/kvk/",exist_ok=True)
    data:dict = get_repo_json_file(KVK_CONFIG_JSON)
    cnt = 0
    all = len(data.items())
    for k,v in data.items():
        cnt+=1
        start:str = v.get("data_start", v.get("start"))
        end:str = v.get("data_end", v.get("end"))
        folder_name = str(v["kvk_map_id"]) + "_" + v["start"].replace("-","")
        os.makedirs(f"data/kvk/{folder_name}/match",exist_ok=True)
        os.makedirs(f"data/kvk/{folder_name}/dkp",exist_ok=True)
        now = datetime.datetime.now()
        days = 1
        if now.hour < 3:
            days = 2
        temp_end = (now - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
        if start > temp_end:
            start = temp_end
        if end >= temp_end:
            end = temp_end
        camps:dict = v["camps"]
        kingdoms_list = []
        for l in camps.values():
            kingdoms_list.extend(l)

        if kingdoms_list:
            url = GITHUB_RAW_URL + get_kvk_match_json_path(folder_name,kingdoms_list[0])
            response = get_request(url=url)
        else:
            print(f'无任何王国,跳过处理. {v["kvk_map_id"]}')
            continue

        if end < temp_end and response.status_code == 200:
            # kvk end,no more update
            continue
        
        for k in kingdoms_list:
            kvk_match_file_name = get_kvk_match_json_path(folder_name,k)
            if os.path.exists(kvk_match_file_name):
                pass
            else:
                idx = k // 100
                match_file_name = get_match_json_path(idx,k)
                shutil.copy(match_file_name, kvk_match_file_name)

            response_dict = get_listed_kingdoms_member_info_api(
                from_date=start,
                to_date=end,
                kingdom_id=k
            )

            data = response_dict.get("data")
            if not data:
                continue

            detail_data = {
                "kingdom":k,
                "from_date":start,
                "to_date":end,
                "data":data
            }
            kingdoms_file_name = get_kvk_dkp_json_path(folder_name,k)
            with open(kingdoms_file_name, "w", encoding="utf-8") as f:
                json.dump(detail_data, f, ensure_ascii=False, indent=2)
        print(f"Now {cnt} in {all}")

elif mode == "save_match_data":
    id_from = sys.argv[1]
    id_to = sys.argv[2]
    no_data_cnt = 0
    for kingdom_id in range(int(id_from), int(id_to)):
        idx = kingdom_id // 100
        os.makedirs(f"data/match/{idx}",exist_ok=True)
        match_file_name = get_match_json_path(idx,kingdom_id)
        response_dict = get_match_data_api(str(kingdom_id))
        data = response_dict.get("data")
        if not data:
            no_data_cnt += 1
            if no_data_cnt > 2:
                break
            else:
                continue
        else:
            no_data_cnt = 0
        evaluate_data = read_json_file(get_evaluated_kingdoms_json_path(idx,kingdom_id))
        if evaluate_data:
            data["evaluated_result"] = evaluate_data.get("evaluated_result",{})
        detail_data = {
            "kingdom":kingdom_id,
            "date":datetime.datetime.now().strftime("%Y-%m-%d"),
            "data":data
        }
        with open(match_file_name, "w", encoding="utf-8") as f:
            json.dump(detail_data, f, ensure_ascii=False, indent=2)

elif mode == "save_kingdoms_data":
    id_from = sys.argv[1]
    id_to = sys.argv[2]
    
    target_date = datetime.datetime.now()
    data_pattern = [1,60,180]
    update_kingdom_data(id_from,id_to,data_pattern,target_date)


elif mode=="update_next_run_time":
    with open(DATA_NEXT, "w", encoding="utf-8") as f:
        _datetime = datetime.datetime.now() + datetime.timedelta(days=1)
        _datetime_dict = {"datetime":_datetime.isoformat()}
        json.dump(_datetime_dict, f, ensure_ascii=False, indent=2)

elif mode=="save_kvk_history_data":
    kvk_datas:dict = read_json_file(KVK_CONFIG_JSON)
    for kvk,data in kvk_datas.items():
        if data["end"] > datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"):
            continue
        else:
            match_data=show_kvk_match_data(data)
            dkp_list = data.get("dkp_list") 
            if not dkp_list:
                dkp_list = {
                    "t4" : 5,
                    "t5" : 10,
                    "t4_dead" : 15,
                    "t5_dead" : 15
                }
            dkp_data=show_kvk_dkp(dkp_list,data)
            kingdom_list = []
            for camp,kds in data["camps"].items():
                for kd in kds:
                    file_path = get_kingdoms_kvk_history_json_path(kd)
                    kd_history_dict = {}
                    if os.path.exists(file_path):
                        kd_history_dict = read_json_file(file_path)
                        if kvk in kd_history_dict:
                            continue
                    target_camp = next((c for c in match_data["camps"] if c["name"] == camp), {})
                    target_kd = next((t for t in target_camp["kingdoms"] if t["KD"] == kd), {})
                    if pn(target_camp["sum"]["TOTAL-KVK-SCORE"]) != 0:
                        match_score_percent = pn(target_kd["KVK-SCORE"]) / pn(target_camp["sum"]["TOTAL-KVK-SCORE"])
                    else:
                        match_score_percent = 0
                    match_rank = f"{target_camp['kingdoms'].index(target_kd) + 1} / {len(target_camp['kingdoms'])}"
                    target_camp = next((c for c in dkp_data["camps"] if c["name"] == camp), {})
                    target_kd = next((t for t in target_camp["kingdoms"] if t["KD"] == kd), {})
                    dkp_percent = pn(target_kd["DKP"]) / pn(target_camp["sum"]["TOTAL-DKP"])
                    dkp_rank= f"{target_camp['kingdoms'].index(target_kd) + 1} / {len(target_camp['kingdoms'])}"
                    evaluate = "d"
                    if match_score_percent !=0:
                        rate = dkp_percent / match_score_percent
                    else:
                        rate = 1.0
                    if rate > 1.5:
                        evaluate = "s"
                    elif rate >= 1.0:
                        evaluate = "a"
                        
                    kd_history_dict[kvk] = {
                        "match_score_percent":f"{round(match_score_percent*100,2)}%",
                        "dkp_percent":f"{round(dkp_percent*100,2)}%",
                        "evaluate":evaluate,
                        "match_rank":match_rank,
                        "dkp_rank":dkp_rank
                    }
                    index = kd // 100
                    os.makedirs(f"data/kingdoms/history/{index}/", exist_ok=True)
                    write_data_to_json_file(file_path,kd_history_dict)


elif mode=="update_kvk_info":
    import requests
    import json

    API_URL = "https://app.rokstats.online/api/kvk/lost-kingdoms/current"
    # API_URL = "https://app.rokstats.online/api/kvk/lost-kingdoms/history"
    def fetch_kvk_data():
        """Fetch KVK data from rokstats API."""
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        return response.json()

    def convert_to_custom_format(raw):
        """
        Convert rokstats API format → your custom KVK JSON format.
        """
        result = {}

        for item in raw["lostKingdoms"]:
            kvk_id = "C" + str(item.get("code"))  # e.g., "C13089"
            start = item.get("battlePhaseStart").split("T")[0]
            end = item.get("immigrationBegins").split("T")[0]
            if start < "2025-12-01":
                continue
            # Camps
            camps_raw = item.get("participants", [])
            camps = {}

            map_type={
                "402":"heroic_anthem",
                "1401":"tides_of_war",
                "1902":"king_of_all_britain",
                "1001":"siege_of_orleans",
                "2001":"song_of_troy",
                "1102":"warriors_unbound"
            }
            
            map_info = {
                "tides_of_war":{
                    "1":"FIRE",
                    "2":"EARTH",
                    "3":"WIND",
                    "4":"WATER"
                },
                "heroic_anthem":{
                    "1":"FIRE",
                    "2":"EARTH",
                    "3":"WIND",
                    "4":"WATER"
                },
                "king_of_all_britain":{
                    "1":"NORTHUMBRIA",
                    "2":"EAST_ANGLIA",
                    "3":"MERCIA",
                    "4":"WESSEX"
                },
                "siege_of_orleans":{
                    "1":"Brittany",
                    "2":"Picardy",
                    "3":"Bourbon",
                    "4":"Auvergne",
                    "5":"La Marche",
                    "6":"Poitou"
                },
                "song_of_troy":{
                    "1":"Aeolia",
                    "2":"Dardania",
                    "3":"Lycia",
                    "4":"Mycenae"
                },
                "warriors_unbound":{
                    "1":"FIRE",
                    "2":"EARTH",
                    "3":"WIND",
                    "4":"WATER",
                    "5":"GREENWOOD",
                    "6":"DAYBREAK"
                }
            }

            map_code = str(item.get("map").get("code"))
            kvk_type = map_type.get(map_code,None)
            if not kvk_type:
                continue
            vcr_flg = False
            for k in camps_raw:
                serverId = int(k["serverId"]) + 1000
                if serverId == 1545:
                    vcr_flg = True
                camp_num = str(k["campNum"])
                camp_name = map_info.get(kvk_type,{}).get(camp_num,camp_num)
                if camp_name in camps:
                    clean_list = camps[camp_name]
                    clean_list.append(serverId)
                else:
                    camps[camp_name] = [serverId]

            result[kvk_id] = {
                "kvk_map_id": kvk_id,
                "kvk_type": kvk_type,
                "vcr": vcr_flg,
                "kvk_type_cn": "",  # You can fill this manually if needed
                "end_apply": start,
                "start": start,
                "end": end,
                "data_start": start,
                "data_end": end,
                "dkp_list": {
                    "t4": 5,
                    "t5": 10,
                    "t4_dead": 15,
                    "t5_dead": 15
                },
                "dkp_calc_rule": "t4*5 + t5*10 + (t4_dead + t5_dead)*15",
                "camps": camps
            }

        return result

    def save_json(data, filename="kvk.json"):
        """Save JSON to file."""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"Saved to {filename}")


    print("Fetching KVK data...")
    raw = fetch_kvk_data()
    print("Converting format...")
    converted = convert_to_custom_format(raw)
    kvk_infos = read_json_file(KVK_CONFIG_JSON)
    for k,v in converted.items():
        if k in kvk_infos:
            continue
        kvk_infos[k]=v
    save_json(kvk_infos,KVK_CONFIG_JSON)
