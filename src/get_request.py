
import requests


def get_request(url):

    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(f"Request failed. Status code is {response.status_code}")

    # 打印返回的 JSON 数据
    try:
        return response.json()
    except:
        print("Response text:", response.text)