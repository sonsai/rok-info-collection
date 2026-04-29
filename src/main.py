from collections import deque
import datetime
import json
import os
import shutil
import sys
from src.clients.get_request import get_request
from src.clients.get_listed_kingdoms_member_info_api import get_listed_kingdoms_member_info_api
from src.consts import DATA_NEXT, GITHUB_RAW_URL, KVK_CONFIG_JSON, MATCH_NEXT
from src.utility import (
    check_tokens,
    evaluate_kingdom,
    evaluate_player,
    get_evaluated_kingdoms_json_path,
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
    show_kvk_match_data, 
    show_kvk_dkp,
    get_match_data_api,
    write_data_to_json_file
)

mode = os.environ["MODE"]

check_tokens()

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
    
elif mode == "save_kvk_data":
    os.makedirs("data/kvk/",exist_ok=True)
    data:dict = get_repo_json_file(KVK_CONFIG_JSON)
    for k,v in data.items():
        start:str = v.get("data_start", v.get("start"))
        end:str = v.get("data_end", v.get("end"))
        folder_name = v["kvk_map_id"] + "_" + v["start"].replace("-","")
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

elif mode == "save_match_data":
    id_from = sys.argv[1]
    id_to = sys.argv[2]
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

elif mode == "save_kingdoms_data":
    id_from = sys.argv[1]
    id_to = sys.argv[2]
    
    working_file_list = {}
    os.makedirs("data/player", exist_ok=True)

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

        idx = kingdom_id // 100
        file_name = get_kingdoms_json_path("1",idx,kingdom_id)
        if not os.path.exists(file_name):
            continue
        player_data = read_json_file(file_name)

        for p in player_data["data"]:
            pid = p["id"]
            idx = int(pid) // 1_000_000
            player_info_list_file_name = get_players_json_path(idx)

            if player_info_list_file_name in working_file_list:
                player_info_list = working_file_list[player_info_list_file_name]
            else:
                if not os.path.exists(player_info_list_file_name):
                    player_info_list = {}
                else:
                    try:
                        player_info_list = read_json_file(player_info_list_file_name)
                    finally:
                        pass
                        
            if pid in player_info_list:
                player_info = player_info_list[pid]
                if player_data["kingdom"] != player_info["kingdom"][-1]:
                    player_info["kingdom"].append(player_data["kingdom"])
                else:
                    pass
                if p["name"] != player_info["name"][-1]:
                    player_info["name"].append(p["name"])
                else:
                    pass
            else:
                player_info_list[pid] = {
                    "kingdom":[player_data["kingdom"]],
                    "name":[p["name"]]
                }
  
            working_file_list[player_info_list_file_name] = player_info_list
    
    # for kingdom_id in range(int(id_from), int(id_to)):
        idx=int(kingdom_id) // 100
        result_data = {}
        for days in [1,60,180]:
            file_path = get_kingdoms_json_path(days=days,index=idx,kingdom_id=kingdom_id)
            data_temp = read_json_file(file_path)
            if not data_temp:
                break
            result_data[f"data_in_{days}"]= data_temp["data"]
        if not result_data:
            continue

        new_kingdom_flg = True
        now_eva_file_path = get_evaluated_kingdoms_json_path(index=idx,kingdom_id=kingdom_id)
        if os.path.exists(now_eva_file_path):
            new_kingdom_flg = False
            now_eva_dict=read_json_file(now_eva_file_path)
        data_list = []
        for player in result_data["data_in_1"]:

            def edit_queue_data(key,player,now_eva_dict,working_file_list,new_kingdom_flg):
                if not new_kingdom_flg:
                    player_in_now_kingdom_flg = False
                    for now_player in now_eva_dict["data"]:
                        if now_player["id"] == player["id"]:
                            player_in_now_kingdom_flg = True
                            if now_player["dt"] >= player["dt"]:
                                if isinstance(now_player[key],int):
                                    player[key] = [now_player[key]]
                                else:
                                    player[key] = now_player[key]
                            else:
                                key_list = now_player[key]
                                if isinstance(key_list,int):
                                    key_list = [key_list]
                                dq=deque(iterable=key_list,maxlen=60)
                                dq.append(player[key])
                                player[key] = list(dq)
                            break
                    if not player_in_now_kingdom_flg:
                        player_info_list_file_name = get_players_json_path(int(player["id"])//1_000_000)
                        player_info_list = working_file_list[player_info_list_file_name]
                        kd_list = player_info_list[player["id"]]["kingdom"]
                        if len(kd_list) > 1:
                            ex_kd= player_info_list[player["id"]]["kingdom"][-2]
                            ex_eva_file_path = get_evaluated_kingdoms_json_path(index=int(ex_kd) // 100,kingdom_id=ex_kd)
                            if os.path.exists(ex_eva_file_path):
                                ex_eva_dict = read_json_file(ex_eva_file_path)
                                for ex_player in ex_eva_dict["data"]:
                                    if ex_player["id"] == player["id"]:
                                        player_in_now_kingdom_flg = True
                                        if ex_player["dt"] >= player["dt"]:
                                            if isinstance(ex_player[key],int):
                                                player[key] = [ex_player[key]]
                                            else:
                                                player[key] = ex_player[key]
                                        else:
                                            key_list = ex_player[key]
                                            if isinstance(key_list,int):
                                                key_list = [key_list]
                                            dq=deque(iterable=key_list,maxlen=60)
                                            dq.append(player[key])
                                            player[key] = list(dq)
                                        break
                                if not player_in_now_kingdom_flg:
                                    player[key] = [player[key]]
                            else:
                                player[key] = [player[key]]
                        else:
                            player[key] = [player[key]]
                else:
                    player[key] = [player[key]]

            edit_queue_data("kill",player=player,now_eva_dict=now_eva_dict,working_file_list=working_file_list,new_kingdom_flg=new_kingdom_flg)
            edit_queue_data("help",player=player,now_eva_dict=now_eva_dict,working_file_list=working_file_list,new_kingdom_flg=new_kingdom_flg)
            edit_queue_data("collect",player=player,now_eva_dict=now_eva_dict,working_file_list=working_file_list,new_kingdom_flg=new_kingdom_flg)
            player_60 = None
            player_180 = None
            for p in result_data.get("data_in_60",{}):  
                if p["id"] == player["id"]:
                    player_60 = p
                    break
            if player_60:
                for k,v in player_60.items():
                    if k not in ["id","name","max_power","power","dt"]:
                        player[f"{k}_60"] = v
            else:
                player["kill_60"] = sum(player["kill"])
                player["help_60"] = sum(player["help"])
                player["collect_60"] = sum(player["collect"])
            for p in result_data.get("data_in_180",{}):  
                if p["id"] == player["id"]:
                    player_180 = p
                    break
            if player_180:
                for k,v in player_180.items():
                    if k not in ["id","name","max_power","power","dt"]:
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
        
    for n, d in working_file_list.items():
        write_data_to_json_file(n,d)

elif mode=="update_next_run_time":
    with open(DATA_NEXT, "w", encoding="utf-8") as f:
        _datetime = datetime.datetime.now() + datetime.timedelta(days=1)
        _datetime_dict = {"datetime":_datetime.isoformat()}
        json.dump(_datetime_dict, f, ensure_ascii=False, indent=2)

elif mode=="save_kvk_history_data":
    kvk_datas:dict = get_repo_json_file(KVK_CONFIG_JSON)
    for kvk,data in kvk_datas.items():
        if "updated" in data:
            continue
        if data["end"] > datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"):
            continue
        else:
            data["updated"]=True
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
                    match_score_percent = pn(target_kd["KVK-SCORE"]) / pn(target_camp["sum"]["TOTAL-KVK-SCORE"])
                    match_rank = f"{target_camp['kingdoms'].index(target_kd) + 1} / {len(target_camp['kingdoms'])}"
                    target_camp = next((c for c in dkp_data["camps"] if c["name"] == camp), {})
                    target_kd = next((t for t in target_camp["kingdoms"] if t["KD"] == kd), {})
                    dkp_percent = pn(target_kd["DKP"]) / pn(target_camp["sum"]["TOTAL-DKP"])
                    dkp_rank= f"{target_camp['kingdoms'].index(target_kd) + 1} / {len(target_camp['kingdoms'])}"
                    evaluate = "d"
                    rate = dkp_percent / match_score_percent
                    if rate > 1.2:
                        evaluate = "s"
                    elif rate > 1.0:
                        evaluate = "a"
                    elif rate > 0.9:
                        evaluate = "b"
                    elif rate > 0.7:
                        evaluate = "c"
                        
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


