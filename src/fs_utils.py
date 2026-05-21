import datetime
import json
import os
from pathlib import Path

from src.clients.get_request import get_request
from src.consts import GITHUB_RAW_URL


def ensure_dir(path):
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def read_json_file(file_path: str) -> dict:
    if not os.path.exists(file_path):
        return None
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_data_to_json_file(file_path: str, data: dict):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_YMD_current_date():
    return datetime.datetime.now().strftime("%Y-%m-%d")


def compute_temp_end():
    now = datetime.datetime.now()
    delay_days = 2 if now.hour < 3 else 1
    return (now - datetime.timedelta(days=delay_days)).strftime("%Y-%m-%d")


def get_repo_json_file(path: str) -> dict:
    url = GITHUB_RAW_URL + path
    response = get_request(url=url)
    return response.json()
