import datetime
import threading
import time

from flask import Flask, request, jsonify
from src.get_request import get_request
from src.post_github_request_api import post_github_request_api
from src.utility import (
    get_kvk_info_json,
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
            next_run_datetime_json_url = "https://raw.githubusercontent.com/sonsai/rok-info-collection/refs/heads/main/data/match/next_run_datetime.json"
            try:
              response = get_request(url=next_run_datetime_json_url)
              _datetime_dict = response.json()
              _datetime = datetime.datetime.fromisoformat(_datetime_dict.get("datetime"))
              if datetime.datetime.now() > _datetime:
                  event_type = "save-match-data"
                  post_github_request_api(event_type=event_type)
            except Exception:
              event_type = "save-match-data"
              post_github_request_api(event_type=event_type)
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
    data = get_kvk_info_json()
    match_base_url = "https://rok-info-collection.onrender.com/rok-match-data?kvk_map_id="
    dkp_base_url = "https://rok-info-collection.onrender.com/rok-kvk-dkp-data?kvk_map_id="

    html = """
    <!DOCTYPE html>
    <html lang="zh">
    <head>
      <meta charset="UTF-8">
      <title>KVK 列表</title>
      <style>
        body { font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }
        .item {
          background-size: cover;
          background-position: center;
          background-repeat: no-repeat;
          padding: 30px;
          border-radius: 10px;
          color: white;
        }
        .tides_of_war  { background-image: url('/static/media/s14tides_of_war_cover.png'); }
        .king_of_all_britain { background-image: url('/static/media/s19king_of_all_britain_cover.png'); }
        .item-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }
        .item-title {
          font-size: 25px;
          font-weight: bold;
        }
        .item-meta {
          font-size: 20px;
          color: #fff;
        }
        .camps { margin-top: 8px; font-size: 14px; }
        .camp-line { 
          font-size: 23px;
          margin: 2px 0; 
        }
        a.button-link {
          padding: 6px 12px;
          background: #007bff;
          color: #fff;
          text-decoration: none;
          border-radius: 4px;
          font-size: 14px;
        }
        a.button-link:hover { background: #0056b3; }
        .kd-item {
          display: inline-block;
          padding: 4px 8px;
          margin: 3px;
          background: gray;
          border-radius: 4px;
          font-size: 20px;
        }
      </style>
    </head>
    <body>
      <h1>KINGDOM 1545 内部数据分析</h1>
      <h2>KVK 列表</h2>
    """

    for key, item in data.items():
        html += f"""
        <div class="item {item['kvk_type'] or 'N/A'}">
          <div class="item-header">
            <div class="item-title">{key}</div>
          </div>
          
          <div class="item-meta">
            KVK ID: {item['kvk_map_id']} |
            类型: {item.get("kvk_type_cn") or item['kvk_type'] or 'N/A'} |
            时间: {item['start']} ~ {item['end']}
          </div>
          <div class="camps">
        """

        for camp_name, kds in item["camps"].items():
            html += f'<div class="camp-line">{camp_name}:</div>'
            for kd in kds:
                html += f'<div class="kd-item">{kd}</div>'

        html += f"""
          </div>
          <br>
          <div>
            <a class="button-link" href="{match_base_url}{key}" target="_blank">匹配数据</a>
            <a class="button-link" href="{dkp_base_url}{key}" target="_blank">DKP数据</a>
          </div>
        </div>
        <br>
        <br>
        """

    html += """
    </body>
    </html>
    """

    return html


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

if __name__ == "__main__":
    start_background_thread()
    app.run(host="0.0.0.0", port=10000)