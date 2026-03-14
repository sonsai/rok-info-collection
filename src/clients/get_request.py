
import requests

def get_request(url):
     return requests.get(url, timeout=60)