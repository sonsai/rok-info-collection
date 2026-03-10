import datetime
import json
import os
import sys
from .get_request import get_request
from .utility import (
    get_kvk_info_json,
    show_kvk_match_data, 
    show_kvk_dkp,
    get_listed_kingdoms_member_info_api,
    get_match_data_api
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
        os.makedirs(f"data/kingdoms/{idx}", exist_ok=True)
        kingdoms_file_name = f"data/kingdoms/{idx}/{kingdom_id}.json"
        from_date:str = (datetime.datetime.now() - datetime.timedelta(days=180)).strftime("%Y-%m-%d")
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
        _datetime = datetime.datetime.now() + datetime.timedelta(hours=6)
        _datetime_dict = {"datetime":_datetime.isoformat()}
        json.dump(_datetime_dict, f, ensure_ascii=False, indent=2)

    data:dict = get_kvk_info_json()
    for k,v in data.items():
        start:str = v["start"]
        end:str = v["end"]
        folder_name = v["kvk_map_id"] + "_" + start.replace("-","")
        os.makedirs(f"data/kvk/{folder_name}",exist_ok=True)
        now = datetime.datetime.now()
        days = 1
        temp_end = (now - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
        if start > temp_end:
            start = temp_end
        if end >= temp_end:
            end = temp_end
        camps:dict = v["camps"]
        try_get_kd = camps.values()[0][0] if camps.values() else None
        if try_get_kd:
            url = f"https://raw.githubusercontent.com/sonsai/rok-info-collection/refs/heads/main/data/kvk/{folder_name}/{camps}.json"
            response = get_request(url=url)
        else:
            print(f'无任何王国,跳过处理. {v["kvk_map_id"]}')
            continue

        if end < temp_end and response.status_code == 200:
            # kvk end,no more update
            continue
        
        kingdoms_list = []
        for l in camps.values():
            kingdoms_list.extend(l)
        
        for k in kingdoms_list:
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
            kingdoms_file_name = f"data/kvk/{folder_name}/{k}.json"
            with open(kingdoms_file_name, "w", encoding="utf-8") as f:
                json.dump(detail_data, f, ensure_ascii=False, indent=2)

elif mode == "save_match_data":
    id_from = sys.argv[1]
    id_to = sys.argv[2]
    with open("data/match/next_run_datetime.json", "w", encoding="utf-8") as f:
        _datetime = datetime.datetime.now() + datetime.timedelta(days=1)
        _datetime_dict = {"datetime":_datetime.isoformat()}
        json.dump(_datetime_dict, f, ensure_ascii=False, indent=2)
    for kingdom_id in range(int(id_from), int(id_to)):
        idx = kingdom_id // 100
        os.makedirs(f"data/match/{idx}",exist_ok=True)
        match_file_name = f"data/match/{idx}/{kingdom_id}.json"
        response_dict = get_match_data_api(str(kingdom_id))
        data = response_dict.get("data")
        detail_data = {
            "kingdom":kingdom_id,
            "date":datetime.datetime.now().strftime("%Y-%m-%d"),
            "data":data
        }
        with open(match_file_name, "w", encoding="utf-8") as f:
            json.dump(detail_data, f, ensure_ascii=False, indent=2)
