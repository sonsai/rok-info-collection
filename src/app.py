import datetime
import json
import threading
import time

from flask import Flask, render_template_string, request, jsonify
from src.web.html_temp import kingdom_player_html
from src.get_request import get_request
from src.post_github_request_api import post_github_request_api
from src.utility import (
    fn,
    get_kvk_info_json,
    get_user_info,
    json_to_root_data,
    show_kvk_match_data,
    json_to_match_data_html,
    show_kvk_dkp,
    json_to_dkp_data_html)

app = Flask(__name__)


HEALTH_URL = "https://rok-info-collection.onrender.com/"
CHECK_INTERVAL = 300  # 每 300 秒检查一次

server_is_healthy = True
def task_execute_checker():
    while True:
        try:
            # 匹配数据获取
            next_run_datetime_json_url = "https://raw.githubusercontent.com/sonsai/rok-info-collection/refs/heads/main/data/match/next_run_datetime.json"
            try:
              response = get_request(url=next_run_datetime_json_url)
              _datetime_dict = response.json()
              _datetime = datetime.datetime.fromisoformat(_datetime_dict.get("datetime"))
              if datetime.datetime.now() > _datetime:
                  event_type = "save-match-data"
                  post_github_request_api(event_type=event_type)
            except Exception:
              pass

            # KVK数据获取
            next_run_datetime_json_url = "https://raw.githubusercontent.com/sonsai/rok-info-collection/refs/heads/main/data/kvk/next_run_datetime.json"
            try:
              response = get_request(url=next_run_datetime_json_url)
              _datetime_dict = response.json()
              _datetime = datetime.datetime.fromisoformat(_datetime_dict.get("datetime"))
              if datetime.datetime.now() > _datetime:
                  event_type = "save-kvk-data"
                  post_github_request_api(event_type=event_type)
            except Exception:
              pass
        except Exception as e:
            print(e)

        time.sleep(3600)

def health_check_loop():
    global server_is_healthy

    while True:
        try:
            res = get_request(HEALTH_URL)
            if res.status_code == 200:
                server_is_healthy = True
                print("[HealthCheck] OK")
            else:
                server_is_healthy = False
                print("[HealthCheck] ERROR: status", res.status_code)

        except Exception as e:
            server_is_healthy = False
            print("[HealthCheck] FAILED:", e)

        time.sleep(CHECK_INTERVAL)
        
def start_background_thread():
    t1 = threading.Thread(target=health_check_loop, daemon=True)
    t1.start()
    t2 = threading.Thread(target=task_execute_checker, daemon=True)
    t2.start()

@app.route("/health")
def health():
    return "OK", 200

@app.get("/")
def root():
    get_user_info(request=request)
    data = get_kvk_info_json()
    return json_to_root_data(data)


@app.get("/rok-match-data")
def rok_match_data():
    kvk_map_id = request.args.get("kvk_map_id")
    try:
        detail_data = get_kvk_info_json()
        print(f"detail_data:{str(detail_data)}")
        if kvk_map_id in detail_data:
            result = show_kvk_match_data(detail_data.get(kvk_map_id))
            print(str(result))
            return json_to_match_data_html(result)
        else:
            error = {"msg":"Kvk id not found."}
            return jsonify(error)
    except Exception as e:
        print(str(e))
        raise e
    

@app.get("/rok-kvk-dkp-data")
def rok_kvk_dkp_data():
    kvk_map_id = request.args.get("kvk_map_id")
    try:
        detail_data = get_kvk_info_json()
        print(f"detail_data:{str(detail_data)}")
        if kvk_map_id in detail_data:
            result = show_kvk_dkp(detail_data.get(kvk_map_id))
            print(str(result))
            return json_to_dkp_data_html(result)
        else:
            error = {"msg":"Kvk id not found."}
            return jsonify(error)
    except Exception as e:
        print(str(e))
        raise e
    
@app.get("/kingdom-player")
def kingdom_player():
    try:
        player_id = None
        kingdom_id= None
        xid = request.args.get("id")
        if int(xid) > 10000:
            player_id = xid
        elif 1000 < int(xid):
            kingdom_id = xid
        else:
            return {"msg":"Wrong id."}
        if not kingdom_id and not player_id:
            return
        if not kingdom_id and player_id:
            pidx = int(player_id) // 1_000_000
            player_kd_list_file_name = f"data/player/player_list_{pidx}.json"
            with open(player_kd_list_file_name, "r", encoding="utf-8") as f:
                player_list:dict = json.load(f)
                kingdom_id = player_list[str(player_id)][-1]
        idx=int(kingdom_id) // 100
        with open(f"data/kingdoms/{idx}/{kingdom_id}.json", "r", encoding="utf-8") as f:
            data:dict = json.load(f)
        if player_id is not None:
            data["data"] = [d for d in data["data"] if d["id"]==player_id]
        for d in data["data"]:
            for k,v in d.items():
                d[k] = fn(v) if isinstance(v, int) else v

        return render_template_string(
        kingdom_player_html,
        kingdom=data["kingdom"],
        start=data["from_date"],
        end=data["to_date"],
        players=data["data"]
        )
    except Exception as e:
        return str(e)

if __name__ == "__main__":
    start_background_thread()
    app.run(host="0.0.0.0", port=10000)