import datetime
import json
import os
import sys
from .utility import show_kvk_match_data, show_kvk_dkp,get_listed_kingdoms_member_info_api

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
elif mode == "save_data":
    id_from = sys.argv[1]
    id_to = sys.argv[2]
    os.makedirs("data/kingdoms/",exist_ok=True)
    for kingdom_id in range(int(id_from), int(id_to)):
        file_name = f"data/kingdoms/{kingdom_id}.json"
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
        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(detail_data, f, ensure_ascii=False, indent=2)