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

def update_kingdom_data(id_from,id_to,data_pattern,target_date):
    working_file_list = {}
    os.makedirs("data/player", exist_ok=True)
    no_data_cnt = 0
    for kingdom_id in range(int(id_from), int(id_to)):
        print(f"当前王国ID：{kingdom_id}")
        if no_data_cnt >= 9:
            break
        idx = kingdom_id // 100
        for p in data_pattern:
            os.makedirs(f"data/kingdoms/{p}d/{idx}", exist_ok=True)
            kingdoms_file_name = f"data/kingdoms/{p}d/{idx}/{kingdom_id}.json"
            from_date:str = (target_date - datetime.timedelta(days=p)).strftime("%Y-%m-%d")
            to_date:str = (target_date - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            response_dict = get_listed_kingdoms_member_info_api(
                from_date=from_date,
                to_date=to_date,
                kingdom_id=kingdom_id
                )
            data = response_dict.get("data")
            if not data:
                no_data_cnt += 1
                continue
            else:
                no_data_cnt = 0

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
        for days in data_pattern:
            file_path = get_kingdoms_json_path(days=days,index=idx,kingdom_id=kingdom_id)
            data_temp = read_json_file(file_path)
            if not data_temp:
                break
            result_data[f"data_in_{days}"]= data_temp["data"]
        if not result_data:
            continue

        new_kingdom_flg = True
        now_eva_file_path = get_ex_evaluated_kingdoms_json_path(index=idx,kingdom_id=kingdom_id)
        if os.path.exists(now_eva_file_path):
            new_kingdom_flg = False
            now_eva_dict=read_json_file(now_eva_file_path)
        data_list = []
        for player in result_data["data_in_1"]:
            log_flg = False
            def edit_queue_data(key,player,now_eva_dict,working_file_list,new_kingdom_flg, log_flg):
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
                            ex_eva_file_path = get_ex_evaluated_kingdoms_json_path(index=int(ex_kd) // 100,kingdom_id=ex_kd)
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
                                        if not log_flg:
                                            log_flg = True
                                            print(f"分类:移民玩家{ex_kd}→{player_info_list[player['id']]['kingdom'][-1]}, 玩家ID:{player['id']},keylist{player[key]}")
                                        break
                                if not player_in_now_kingdom_flg:
                                    if not log_flg:
                                        log_flg = True
                                        print(f"分类:前王国{ex_kd}无该玩家数据, 玩家ID:{player['id']}")
                                    player[key] = [player[key]]
                            else:
                                if not log_flg:
                                    log_flg = True
                                    print(f"分类:没有获取对象王国数据{ex_kd}, 玩家ID:{player['id']}")
                                player[key] = [player[key]]
                        else:
                            player[key] = [player[key]]
                else:
                    if not log_flg:
                        log_flg = True
                        print(f"分类:新王国, 玩家ID:{player['id']}")
                    player[key] = [player[key]]

                return log_flg

            log_flg = edit_queue_data("kill",player=player,now_eva_dict=now_eva_dict,working_file_list=working_file_list,new_kingdom_flg=new_kingdom_flg,log_flg=log_flg)
            log_flg = edit_queue_data("help",player=player,now_eva_dict=now_eva_dict,working_file_list=working_file_list,new_kingdom_flg=new_kingdom_flg,log_flg=log_flg)
            edit_queue_data("collect",player=player,now_eva_dict=now_eva_dict,working_file_list=working_file_list,new_kingdom_flg=new_kingdom_flg,log_flg=log_flg)
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
            player = set_history_info(player, working_file_list)
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