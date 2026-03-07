import json

from flask import Flask, request, Response
from src.utility import show_kvk_match_data

app = Flask(__name__)

@app.get("/rok-match-data")
def hello():
    kvk_map_id = request.args.get("kvk_map_id")
    try:
        with open("data/kvk_info.json", "r", encoding="utf-8") as f:
            detail_data:dict = json.load(f)
        if kvk_map_id in detail_data:
            show_kvk_match_data(detail_data.get(kvk_map_id))
            with open("data/match_data_result.txt", "r", encoding="utf-8") as f:
                content = f.read()
        else:
            return Response(response=content, status=200)
    except Exception as e:
        print(str(e))
        raise e

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)