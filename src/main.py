import json
import os
import sys
from .utility import show_kvk_match_data

mode = os.environ["MODE"]

if mode == "match_data":
    try:
        kvk_map_id = sys.argv[1]
        kvk_infos = os.environ["KVK_INFOS"]
        info_list:dict = json.loads(kvk_infos)
        show_kvk_match_data(info_list.get(kvk_map_id))
    except Exception as e:
        print(str(e))
        raise e