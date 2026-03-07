from .utility import get_rok_api_headers
import requests

def get_match_data_api(
        btoken:str,
        ptoken:str,
        kingdomId:str = "1545"
    ) -> dict:

    if not btoken or not ptoken:
        raise Exception("Indivial input parameters. btoken or ptoken is empty.")
    url = f"https://plat-rok-gametools-global-api.lilithgames.com/api/kindomInformation?server_id={kingdomId}"
    headers = {
        "Bauthorization": f"Bearer {btoken}",
        "Pauthorization": f"Bearer {ptoken}",
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Request failed. Status code is {response.status_code}")

    # 打印返回的 JSON 数据
    try:
        return response.json()
    except:
        print("Response text:", response.text)
        raise Exception("Response is not JSON format.")