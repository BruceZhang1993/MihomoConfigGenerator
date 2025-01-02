import json
import os
import sys

import requests
from typing import List

import yaml


def parse_proxies_from_sub(sub: str) -> List[dict]:
    response = requests.get(sub, headers={'User-Agent': 'clash.meta'})
    sub_text = response.text
    data = yaml.load(sub_text, Loader=yaml.FullLoader)
    print(data)
    proxies = data.get('proxies')
    if proxies is None:
        return []
    return proxies


def parse_proxies_from_env() -> List[dict]:
    subs = os.environ.get('SUBSCRIPTIONS')
    if subs is None:
        return []
    sub_list = json.loads(subs)
    if sub_list is None:
        return []
    proxy_list = []
    for sub in sub_list:
        proxy_list.extend(parse_proxies_from_sub(sub))
    return proxy_list
