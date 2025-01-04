import json
import os
import sys
from pathlib import Path
from typing import List
from urllib.parse import urlparse

import requests
import yaml

TOKEN = os.environ.get("MY_TOKEN")


def mark_proxy_name(proxy, sub):
    if sub == 'FILE':
        proxy['name'] = f'{proxy["name"]} [FILE]'
    else:
        proxy['name'] = f'{proxy["name"]} [{urlparse(sub).hostname}]'
    return proxy


def parse_proxies_from_sub(sub: str) -> List[dict]:
    headers = {'User-Agent': 'clash.meta'}
    if TOKEN is not None:
        headers['Authorization'] = f'token {TOKEN}'
    response = requests.get(sub, headers=headers)
    sub_text = response.text
    data = yaml.load(sub_text, Loader=yaml.FullLoader)
    proxies = data.get('proxies')
    if proxies is None:
        return []
    return [mark_proxy_name(proxy, sub) for proxy in proxies]


def parse_proxies_from_env() -> List[dict]:
    # Read from subscription links
    subs = os.environ.get('SUBSCRIPTIONS')
    if subs is None:
        return []
    sub_list = json.loads(subs)
    if sub_list is None:
        return []
    proxy_list = []
    for sub in sub_list:
        proxy_list.extend(parse_proxies_from_sub(sub))
    # Read from config file
    file = os.environ.get('FILE')
    if file is not None:
        file_proxies = yaml.load(file, Loader=yaml.FullLoader)
        if file_proxies is not None:
            proxy_list.extend([mark_proxy_name(proxy, 'FILE') for proxy in file_proxies.get('proxies')])
    return proxy_list


def merge_proxies_into_template(proxies: List[dict]) -> str:
    template = os.environ.get("TEMPLATE")
    data = yaml.load(template, Loader=yaml.FullLoader)
    data['proxies'] = proxies
    return yaml.dump(data)


def main():
    proxies = parse_proxies_from_env()
    if proxies is None or len(proxies) == 0:
        sys.exit(0)
    yaml_str = merge_proxies_into_template(proxies)
    home = Path(__file__).parent.parent
    (home / 'result').mkdir(exist_ok=True)
    with (home / 'result' / 'config.yml').open('w') as f:
        f.write(yaml_str)
