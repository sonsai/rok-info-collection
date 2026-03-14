import os
import datetime
import requests

def get_listed_kingdoms_member_info_api(
        from_date:str = (datetime.datetime.now() - datetime.timedelta(days=180)).strftime("%Y-%m-%d"),
        to_date:str = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
        kingdom_id:str = "1545"
) -> list[dict]:
    
    btoken = os.environ["ROK_B_TOKEN"]
    ptoken = os.environ["ROK_P_TOKEN"]
    if not btoken or not ptoken:
        raise Exception("Bad request. btoken or ptoken is empty.")
    url = f"https://plat-rok-gametools-global-api.lilithgames.com/api/kindomMember?start={from_date}&end={to_date}&search=&server_id={kingdom_id}"
    headers = {
        "Bauthorization": f"Bearer {btoken}",
        "Pauthorization": f"Bearer {ptoken}",
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Request failed. Status code is {response.status_code}. from:{from_date} to:{to_date} kd:{kingdom_id}")

    # 打印返回的 JSON 数据
    try:
        return response.json()
    except:
        print("Response text:", response.text)
        raise Exception("Response is not JSON format.")