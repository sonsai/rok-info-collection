import datetime
import json
import re
import threading
import time

from werkzeug.exceptions import HTTPException
from flask import Flask, abort, render_template, request
from src.get_request import get_request
from src.post_github_request_api import post_github_request_api
from src.utility import (
    fn,
    get_YMD_current_date,
    get_kvk_info_json,
    show_kvk_match_data,
    show_kvk_dkp)

app = Flask(__name__)

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

        time.sleep(300)

def start_background_thread():
    t1 = threading.Thread(target=task_execute_checker, daemon=True)
    t1.start()

@app.route("/health")
def health():
    return "OK", 200

@app.get("/")
def root():
    try:
        data = get_kvk_info_json()
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
        detail_data = get_kvk_info_json()
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
        detail_data = get_kvk_info_json()
        print(f"detail_data:{str(detail_data)}")
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
            player_kd_list_file_name = f"data/player/player_list_{pidx}.json"
            with open(player_kd_list_file_name, "r", encoding="utf-8") as f:
                player_list:dict = json.load(f)
                kingdom_id = player_list[str(player_id)][-1]
        idx=int(kingdom_id) // 100
        result_data = {}
        for days in [60,180]:
            with open(f"data/kingdoms/{days}d/{idx}/{kingdom_id}.json", "r", encoding="utf-8") as f:
                data_temp:dict = json.load(f)
            if player_id is not None:
                data_temp[f"data"] = [d for d in data_temp["data"] if d["id"]==player_id]
            for d in data_temp[f"data"]:
                for k,v in d.items():
                    d[k] = fn(v) if isinstance(v, int) and not re.match(r".*t[1-5]$", k) else v
            result_data[f"data_in_{days}"]= data_temp["data"]
            result_data["kingdom"]= data_temp["kingdom"]
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

            data_list.append(player)

        return render_template(
            "show_kingdom_player.html",
            kingdom=result_data["kingdom"],
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