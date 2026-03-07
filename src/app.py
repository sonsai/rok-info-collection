import json

from flask import Flask, request, Response, jsonify
from src.utility import show_kvk_match_data

app = Flask(__name__)

@app.get("/rok-match-data")
def hello():
    kvk_map_id = request.args.get("kvk_map_id")
    try:
        with open("data/kvk_info.json", "r", encoding="utf-8") as f:
            detail_data:dict = json.load(f)
        print(f"detail_data:{str(detail_data)}")
        if kvk_map_id in detail_data:
            result = show_kvk_match_data(detail_data.get(kvk_map_id))
            return jsonify(result)
        else:
            return Response(response={"msg":f"Kvk id not found. id={kvk_map_id}"}, status=500)
    except Exception as e:
        print(str(e))
        raise e

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)