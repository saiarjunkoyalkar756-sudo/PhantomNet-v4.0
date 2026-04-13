import requests
import json


def greet(name):
    print(f"Inside sandboxed greet function, arg: {name}")
    return f"Hello from Test Plugin, {name}!"


def fetch_url(url):
    print(f"Inside sandboxed fetch_url function, arg: {url}")
    try:
        response = requests.get(url, timeout=5)
        return {
            "status_code": response.status_code,
            "content_length": len(response.text),
        }
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
