import datetime
import json
import os
import shutil
import sys
from src.clients.get_request import get_request
from src.clients.get_listed_kingdoms_member_info_api import get_listed_kingdoms_member_info_api
from src.consts import GITHUB_RAW_URL, KVK_CONFIG_JSON, MATCH_NEXT
from src.utility import (
    evaluate_kingdom,
    evaluate_player,
    get_evaluated_kingdoms_json_path,
    get_kingdoms_json_path,
    get_kvk_dkp_json_path,
    get_kvk_match_json_path,
    get_match_json_path,
    get_players_json_path,
    get_repo_json_file,
    read_json_file,
    show_kvk_match_data, 
    show_kvk_dkp,
    get_match_data_api,
    write_data_to_json_file
)

mode = os.environ["MODE"]

if mode == "match_data":
    try:
        kvk_map_id = sys.argv[1]
        kvk_infos = os.environ["KVK_INFOS"]
        info_list:dict = json.loads(kvk_infos)
        print("kvk_map_id:" + str(kvk_map_id))
        print("info_list:" + str(info_list))
        show_kvk_match_data(info_list.get(kvk_map_id))
    except Exception as e:
        print(str(e))
        raise e

elif mode == "dkp_data":
    try:
        kvk_map_id = sys.argv[1]
        kvk_infos = os.environ["KVK_INFOS"]
        info_list:dict = json.loads(kvk_infos)
        print("kvk_map_id:" + str(kvk_map_id))
        print("info_list:" + str(info_list))
        show_kvk_dkp(info_list.get(kvk_map_id))
    except Exception as e:
        print(str(e))
        raise e
    
elif mode == "save_kingdoms_data":
    id_from = sys.argv[1]
    id_to = sys.argv[2]
    for kingdom_id in range(int(id_from), int(id_to)):
        idx = kingdom_id // 100
        for p in [1,60,180]:
            os.makedirs(f"data/kingdoms/{p}d/{idx}", exist_ok=True)
            kingdoms_file_name = f"data/kingdoms/{p}d/{idx}/{kingdom_id}.json"
            from_date:str = (datetime.datetime.now() - datetime.timedelta(days=p)).strftime("%Y-%m-%d")
            to_date:str = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            response_dict = get_listed_kingdoms_member_info_api(
                from_date=from_date,
                to_date=to_date,
                kingdom_id=kingdom_id
                )
            data = response_dict.get("data")
            if not data:
                continue

            detail_data = {
                "kingdom":kingdom_id,
                "from_date":from_date,
                "to_date":to_date,
                "data":data
            }
            with open(kingdoms_file_name, "w", encoding="utf-8") as f:
                json.dump(detail_data, f, ensure_ascii=False, indent=2)

elif mode == "save_kvk_data":
    os.makedirs("data/kvk/",exist_ok=True)
    with open("data/kvk/next_run_datetime.json", "w", encoding="utf-8") as f:
        _datetime = datetime.datetime.now() + datetime.timedelta(hours=12)
        _datetime_dict = {"datetime":_datetime.isoformat()}
        json.dump(_datetime_dict, f, ensure_ascii=False, indent=2)

    data:dict = get_repo_json_file(KVK_CONFIG_JSON)
    for k,v in data.items():
        start:str = v["start"]
        end:str = v["end"]
        folder_name = v["kvk_map_id"] + "_" + start.replace("-","")
        os.makedirs(f"data/kvk/{folder_name}/match",exist_ok=True)
        os.makedirs(f"data/kvk/{folder_name}/dkp",exist_ok=True)
        now = datetime.datetime.now()
        days = 1
        if now.hour < 6:
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
                match_file_name = get_kvk_match_json_path(folder_name,k)
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

elif mode == "save_match_data":
    id_from = sys.argv[1]
    id_to = sys.argv[2]
    with open(MATCH_NEXT, "w", encoding="utf-8") as f:
        _datetime = datetime.datetime.now() + datetime.timedelta(days=1)
        _datetime_dict = {"datetime":_datetime.isoformat()}
        json.dump(_datetime_dict, f, ensure_ascii=False, indent=2)
    for kingdom_id in range(int(id_from), int(id_to)):
        idx = kingdom_id // 100
        os.makedirs(f"data/match/{idx}",exist_ok=True)
        match_file_name = get_match_json_path(idx,kingdom_id)
        response_dict = get_match_data_api(str(kingdom_id))
        data = response_dict.get("data")
        detail_data = {
            "kingdom":kingdom_id,
            "date":datetime.datetime.now().strftime("%Y-%m-%d"),
            "data":data
        }
        with open(match_file_name, "w", encoding="utf-8") as f:
            json.dump(detail_data, f, ensure_ascii=False, indent=2)

elif mode == "execute_player_list":
    id_from = sys.argv[1]
    id_to = sys.argv[2]
    
    working_file_list = {}
    os.makedirs("data/player", exist_ok=True)
    for kd in range(int(id_from), int(id_to)):
        idx = kd // 100
        file_name = get_kingdoms_json_path("1",idx,kd)
        if not os.path.exists(file_name):
            continue
        with open(file_name, "r", encoding="utf-8") as f:
            player_data = json.load(f)

        for p in player_data["data"]:
            pid = p["id"]
            idx = int(pid) // 1_000_000
            player_kd_list_file_name = get_players_json_path(idx)

            if player_kd_list_file_name in working_file_list:
                player_kd_list = working_file_list[player_kd_list_file_name]
            else:
                if not os.path.exists(player_kd_list_file_name):
                    player_kd_list = {}
                else:
                    try:
                        with open(file_name, "r", encoding="utf-8") as f:
                            player_kd_list = json.load(f)
                    finally:
                        pass
                        
            if pid in player_kd_list:
                past_kd_list = player_kd_list[p["id"]]
                if past_kd_list:
                    if player_data["kingdom"] != past_kd_list[-1]:
                        player_kd_list[p["id"]].append(player_data["kingdom"])
                    else:
                        pass
                else:
                    player_kd_list[p["id"]] = [player_data["kingdom"]]
            else:
                player_kd_list[p["id"]] = [player_data["kingdom"]]

            working_file_list[player_kd_list_file_name] = player_kd_list
            
    for n, d in working_file_list.items():
        with open(n, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)

elif mode == "evaluate_kingdom":
    id_from = sys.argv[1]
    id_to = sys.argv[2]
    
    working_file_list = {}
    for kingdom_id in range(int(id_from), int(id_to)):
        idx=int(kingdom_id) // 100
        result_data = {}
        for days in [60,180]:
            file_path = get_kingdoms_json_path(days=days,index=idx,kingdom_id=kingdom_id)
            data_temp = read_json_file(file_path)
            if not data_temp:
                break
            result_data[f"data_in_{days}"]= data_temp["data"]
        if not result_data:
            continue
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
        eva_result = evaluate_kingdom(data_list)
        output_data = {
            "kingdom":kingdom_id,
            "evaluated_result":eva_result,
            "data":data_list
        }
        out_put_file = get_evaluated_kingdoms_json_path(index=idx,kingdom_id=kingdom_id)
        os.makedirs(f"data/kingdoms/evaluated/{idx}/", exist_ok=True)
        write_data_to_json_file(out_put_file,output_data)