import json

from flask import Flask, request, jsonify
from src.utility import show_kvk_match_data, json_to_match_data_html,show_kvk_dkp,json_to_dkp_data_html

app = Flask(__name__)


@app.get("/")
def root():
    html = """<!DOCTYPE html>
            <html lang="zh">
            <head>
            <meta charset="UTF-8">
            <title>ROK API Link</title>
            <style>
                body { font-family: Arial; padding: 20px; }
                input { padding: 8px; font-size: 16px; width: 200px; }
                button { padding: 8px 16px; font-size: 16px; margin-left: 10px; }
            </style>
            </head>
            <body>

            <h2>ROK Data API</h2>

            <input id="mapId" type="text" placeholder="输入 kvk_map_id，例如 C13049">
            <button onclick="match()">匹配数据查询</button>
            <button onclick="dkp()">DKP数据查询</button>

            <script>
                function match() {
                const id = document.getElementById("mapId").value.trim();
                if (!id) {
                    alert("请输入 kvk_map_id");
                    return;
                }

                const url = "https://rok-info-collection.onrender.com/rok-match-data?kvk_map_id=" + encodeURIComponent(id);
                window.location.href = url;
                }
                function dkp() {
                const id = document.getElementById("mapId").value.trim();
                if (!id) {
                    alert("请输入 kvk_map_id");
                    return;
                }

                const url = "https://rok-info-collection.onrender.com/rok-kvk-dkp-data?kvk_map_id=" + encodeURIComponent(id);
                window.location.href = url;
                }
            </script>

            </body>
            </html>
            """
    return html



@app.get("/rok-match-data")
def rok_match_data():
    kvk_map_id = request.args.get("kvk_map_id")
    try:
        with open("data/kvk/kvk_info.json", "r", encoding="utf-8") as f:
            detail_data:dict = json.load(f)
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
        with open("data/kvk/kvk_info.json", "r", encoding="utf-8") as f:
            detail_data:dict = json.load(f)
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
    app.run(host="0.0.0.0", port=10000)