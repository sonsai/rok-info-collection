import datetime
import json
import re
import threading
import time

from werkzeug.exceptions import HTTPException
from flask import Flask, abort, render_template, request
from src.consts import CHECK_INTERVAL, GITHUB_RAW_URL, HEALTH_URL, KVK_CONFIG_JSON, KVK_NEXT, MATCH_NEXT
from src.clients.get_request import get_request
from src.clients.post_github_request_api import post_github_request_api
from src.utility import (
    evaluate_kingdom,
    evaluate_player,
    fn,
    get_YMD_current_date,
    get_evaluated_kingdoms_json_path,
    get_kingdoms_json_path,
    get_players_json_path,
    get_repo_json_file,
    read_json_file,
    show_kvk_match_data,
    show_kvk_dkp)

app = Flask(__name__)

def task_execute_checker():
    while True:
        try:
            # 匹配数据获取
            next_run_datetime_json_url = GITHUB_RAW_URL + MATCH_NEXT
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
            next_run_datetime_json_url = GITHUB_RAW_URL + KVK_NEXT
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

    while True:
        try:
            res = get_request(HEALTH_URL + "/health")
            if res.status_code == 200:
                print("[HealthCheck] OK")
            else:
                print("[HealthCheck] ERROR: status", res.status_code)

        except Exception as e:
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
    try:
        data = get_repo_json_file(KVK_CONFIG_JSON)
        match_base_url = "/rok-match-data?kvk_map_id="
        dkp_base_url = "/rok-kvk-dkp-data?kvk_map_id="
        return render_template(
            "index.html",
            data=data,
            current_date=get_YMD_current_date(),
            match_base_url=match_base_url,
            dkp_base_url=dkp_base_url
        )
    except Exception as e:
        print(e)
        abort(500)


@app.get("/rok-match-data")
def rok_match_data():
    kvk_map_id = request.args.get("kvk_map_id")
    try:
        detail_data = get_repo_json_file(KVK_CONFIG_JSON)
        if kvk_map_id in detail_data:
            data = show_kvk_match_data(detail_data.get(kvk_map_id))
            return render_template(
                "match.html",
                data=data
            )
        else:
            abort(404)
    except HTTPException:
        raise
    except Exception as e:
        print(e)
        abort(500)
    

@app.get("/rok-kvk-dkp-data")
def rok_kvk_dkp_data():
    kvk_map_id = request.args.get("kvk_map_id")
    try:
        detail_data = get_repo_json_file(KVK_CONFIG_JSON)
        if kvk_map_id in detail_data:
            data = show_kvk_dkp(detail_data.get(kvk_map_id))
            return render_template("dkp.html", data=data)
        else:
            abort(404)
    except HTTPException:
        raise
    except Exception as e:
        print(e)
        abort(500)
    
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
            abort(400)
        if not kingdom_id and not player_id:
            abort(400)
        if not kingdom_id and player_id:
            pidx = int(player_id) // 1_000_000
            player_kd_list_file_name = get_players_json_path(pidx)
            with open(player_kd_list_file_name, "r", encoding="utf-8") as f:
                player_list:dict = json.load(f)
                kingdom_id = player_list[str(player_id)][-1]
        eva_result = read_json_file(get_evaluated_kingdoms_json_path(int(kingdom_id)//100,kingdom_id))
        data_list =[]
        for player in eva_result.get("data"):
            for k,v in player.items():
                player[k] = fn(v) if isinstance(v, int) and not re.match(r".*t[1-5]$", k) else v
            if player_id:
                if player.get("id") == player_id:
                    data_list = [player]
                    break
            else:
                data_list.append(player)
        return render_template(
            "show_kingdom_player.html",
            kingdom=eva_result["kingdom"],
            kingdom_grade=eva_result.get("evaluated_result"),
            players=data_list
        )
    except HTTPException:
        raise
    except Exception as e:
        app.logger.error(str(e))
        abort(500)


@app.errorhandler(404)
def not_found(e):
    return render_template(
        "error.html",
        code=404,
        message_cn="页面不存在",
        message_en="Page Not Found",
        e=e
    ), 404

@app.errorhandler(400)
def bad_request(e):
    return render_template(
        "error.html",
        code=400,
        message_cn="请求错误",
        message_en="Bad Request",
        e=e
    ), 400


@app.errorhandler(500)
def server_error(e):
    return render_template(
        "error.html",
        code=500,
        message_cn="服务器内部错误",
        message_en="Internal Server Error",
        e=e
    ), 500

if __name__ == "__main__":
    start_background_thread()
    app.run(host="0.0.0.0", port=10000)