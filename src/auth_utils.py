import os

import requests
from src.clients.get_listed_kingdoms_member_info_api import get_listed_kingdoms_member_info_api


def check_tokens():
    try:
        get_listed_kingdoms_member_info_api()
        print("check_tokens success.")
        return
    except Exception:
        print("check_tokens failed.")

    session = requests.Session()
    params = {
        "timestamp": os.environ.get("cap_timestamp") or "1774368716235",
        "signature": os.environ.get("cap_signature") or "6925bddd2a2b57cd86f29b990611c0ef",
        "access_key": os.environ.get("cap_access_key") or "97r9ihrvxuh6d8kdrztw03ovlvxtssx4",
    }
    url = "https://passport-global-api.lilithgame.com/api/v2/passport-login/captcha"
    resp = session.get(url=url, params=params)
    result = resp.json()
    print(result)

    login_url = "https://passport-global-api.lilithgame.com/api/v2/passport-login/password"
    payload = {
        "pup_token": result["data"]["pup_token"],
        "client_id": "rok_game_tools_lglo",
        "username": "sonsai1988@gmail.com",
        "password": "76efa73c8eddd696eef21633e72d40e2",
        "account_type": 0,
        "login_free": True,
    }
    resp_login = session.post(url=login_url, json=payload)
    login_result = resp_login.json()
    print(login_result)
    p_token = login_result["data"]["jwt_token"]

    bind_role_url = "https://rok-game-tools-global-api.lilith.com/api/lilith/bind_role"
    bind_role_payload = {
        "app_id": 2104267,
        "app_uid": "45272230",
        "uid": 47913824,
        "svr_id": 1545,
    }
    bind_role_header = {"pauthorization": p_token}

    resp_bind_role = session.post(url=bind_role_url, json=bind_role_payload, headers=bind_role_header)
    bind_role_result = resp_bind_role.json()
    print(bind_role_result)
    b_token = bind_role_result["data"]["access_token"]

    os.environ["ROK_B_TOKEN"] = b_token
    os.environ["ROK_P_TOKEN"] = p_token

    try:
        get_listed_kingdoms_member_info_api()
        print("tokens reset succeed.")
        return
    except Exception:
        print("tokens reset failed.")
        raise
