import json

import requests

url = "http://localhost:6565/generate_outline/"
title = "Фотосинтез"
topic_num = "3"
language = "en"
uuid = "121312312"
data = {"title": title, "topic_num": topic_num, "language": language, "uuid": uuid}

headers = {"Content-type": "application/json"}

with requests.post(url, data=json.dumps(data), headers=headers, stream=True) as r:
    for chunk in r.iter_content(1024):
        print(chunk)
