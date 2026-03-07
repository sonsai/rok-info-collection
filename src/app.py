import json

from flask import Flask, request, jsonify
from src.utility import show_kvk_match_data, json_to_match_data_html,show_kvk_dkp,json_to_dkp_data_html

app = Flask(__name__)


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