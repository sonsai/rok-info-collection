import datetime
import json
import os
import re
import threading
import time
import logging

from werkzeug.exceptions import HTTPException
from flask import Flask, abort, jsonify, render_template, request
from src.consts import CHECK_INTERVAL, DATA_NEXT, GITHUB_RAW_URL, HEALTH_URL, KVK_CONFIG_JSON, KVK_NEXT, MATCH_NEXT
from src.clients.get_request import get_request
from src.clients.post_github_request_api import post_github_request_api
from src.utility import (
    evaluate_kingdom,
    evaluate_player,
    fn,
    get_YMD_current_date,
    get_evaluated_kingdoms_json_path,
    get_kingdoms_json_path,
    get_match_data,
    get_players_json_path,
    get_repo_json_file,
    kvk_player_data,
    read_json_file,
    show_kvk_match_data,
    show_kvk_dkp)

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

def task_execute_checker():
    while True:
        try:
            # 匹配数据获取
            next_run_datetime_json_url = GITHUB_RAW_URL + DATA_NEXT
            try:
              response = get_request(url=next_run_datetime_json_url)
              _datetime_dict = response.json()
              _datetime = datetime.datetime.fromisoformat(_datetime_dict.get("datetime"))
              if datetime.datetime.now() > _datetime:
                  event_type = "update_next_run_time"
                  post_github_request_api(event_type=event_type)
            except Exception:
              pass

            # KVK数据获取
            # next_run_datetime_json_url = GITHUB_RAW_URL + KVK_NEXT
            # try:
            #   response = get_request(url=next_run_datetime_json_url)
            #   _datetime_dict = response.json()
            #   _datetime = datetime.datetime.fromisoformat(_datetime_dict.get("datetime"))
            #   if datetime.datetime.now() > _datetime:
            #       event_type = "save-kvk-data"
            #       post_github_request_api(event_type=event_type)
            # except Exception:
            #   pass
        except Exception as e:
            print(e)

        time.sleep(300)

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
        
t1 = None
t2 = None
def start_background_thread():
    global t1, t2
    if t1 is None or not t1.is_alive():
        t1 = threading.Thread(target=health_check_loop, daemon=True)
        t1.start()

    if t2 is None or not t2.is_alive():
        t2 = threading.Thread(target=task_execute_checker, daemon=True)
        t2.start()

@app.route("/health")
def health():
    return "OK", 200

@app.get("/")
def root():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    ua = request.headers.get("User-Agent")
    referer = request.headers.get("Referer")
    path = request.path
    method = request.method
    args = request.args.to_dict()

    logging.info(f"[VISITOR] IP={ip} METHOD={method} PATH={path} ARGS={args} UA={ua} REFERER={referer}")
    try:
        data = get_repo_json_file(KVK_CONFIG_JSON)
        match_base_url = "/rok-match-data?kvk_map_id="
        dkp_base_url = "/rok-kvk-dkp-data?kvk_map_id="
        kvk_player_base_url = "/rok-kvk-player-data?kvk_map_id="
        return render_template(
            "index.html",
            data=data,
            current_date=get_YMD_current_date(),
            match_base_url=match_base_url,
            dkp_base_url=dkp_base_url,
            kvk_player_base_url=kvk_player_base_url,
            mode_kvk="active",
            mode_search="",
            mode_match=""
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
        detail_data = read_json_file(KVK_CONFIG_JSON)
        if kvk_map_id in detail_data:
            target_kvk = detail_data.get(kvk_map_id)
            dkp_list = target_kvk.get("dkp_list") 
            if not dkp_list:
                dkp_list = {
                    "t4" : 5,
                    "t5" : 10,
                    "t4_dead" : 15,
                    "t5_dead" : 15
                }
            dkp_calc_rule = target_kvk.get("dkp_calc_rule")
            if not dkp_calc_rule:
                dkp_calc_rule = "t4*5 + t5*10 + (t4_dead + t5_dead)*15"
            data = show_kvk_dkp(dkp_list, target_kvk)
            return render_template(
                "dkp.html",
                dkp_list=dkp_list,
                dkp_calc_rule=dkp_calc_rule,
                data=data
            )
        else:
            abort(404)
    except HTTPException:
        raise
    except Exception as e:
        print(e)
        abort(500)

@app.get("/rok-kvk-player-data")
def rok_kvk_player_data():
    kvk_map_id = request.args.get("kvk_map_id",type=str)
    max_len = request.args.get("max_len",type=int, default=600)
    try:
        detail_data = read_json_file(KVK_CONFIG_JSON)
        if kvk_map_id in detail_data:
            target_kvk = detail_data.get(kvk_map_id)
            data = kvk_player_data(target_kvk)
            return render_template(
                "kvk_player.html",
                kvk_info=target_kvk,
                data=data[:max_len]
            )
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
                kingdom_id = player_list[str(player_id)]["kingdom"][-1]
        eva_result = read_json_file(get_evaluated_kingdoms_json_path(int(kingdom_id)//100,kingdom_id))
        data_list =[]
        for player in eva_result.get("data"):
            if "kill_60" not in player.keys():
                player["kill_60"] = sum(player["kill"])
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
            kingdom_grade=eva_result["evaluated_result"],
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

@app.route("/api/data")
def api_data():
    page = int(request.args.get("page", 1))
    keyword = request.args.get("keyword", "").strip()
    total_page = 29

    # 防止越界
    if keyword:
        total_page = 1

    if page < 1:
        page = 1
    if page > total_page:
        page = total_page
    match_data_list = get_match_data(idx = page + 9, kingdom_id=keyword)
    return jsonify({
        "page": page,
        "total_page": total_page,
        "match_data_list": match_data_list
    })


if __name__ == "__main__":
    start_background_thread()
    app.run(host="0.0.0.0", port=10000)