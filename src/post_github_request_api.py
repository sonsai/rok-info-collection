import requests
import json
import os


def post_github_request_api(event_type:str):
    # GitHub 仓库信息
    OWNER = "sonsai"
    REPO = "rok-info-collection"

    # 你的 GitHub Token（需要 repo 权限）
    TOKEN = os.environ["GITHUB_API_ACCESS_TOKEN"]

    # API URL
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/dispatches"

    # 请求头
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"token {TOKEN}"
    }

    # 请求体
    payload = {
        "event_type": event_type
    }

    # 发送 POST 请求
    response = requests.post(url, headers=headers, data=json.dumps(payload))

    # 输出结果
    print("Status Code:", response.status_code)
    print("Response:", response.text)
