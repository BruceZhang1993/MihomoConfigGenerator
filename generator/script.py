import json
import os
import sys
from pathlib import Path
from typing import List
from urllib.parse import urlparse
from loguru import logger

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
    if response.status_code != 200:
        logger.error(f'Failed to get proxies from {sub}, http code: {response.status_code}!')
        return []
    sub_text = response.text
    data = yaml.load(sub_text, Loader=yaml.FullLoader)
    proxies = data.get('proxies')
    if proxies is None:
        return []
    logger.info(f'Got {len(proxies)} proxies from {sub}!')
    return [mark_proxy_name(proxy, sub) for proxy in proxies]


def parse_proxies_from_env() -> List[dict]:
    # Read from subscription links
    subs = os.environ.get('SUBSCRIPTIONS')
    if subs is None:
        logger.warning('Please set SUBSCRIPTIONS GitHub Actions variable!')
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
        logger.info(f'Reading proxies from file {file}!')
        file_proxies = yaml.load(file, Loader=yaml.FullLoader)
        if file_proxies is not None:
            logger.info(f'Got {len(file_proxies.get("proxies"))} proxies from file!')
            proxy_list.extend([mark_proxy_name(proxy, 'FILE') for proxy in file_proxies.get('proxies')])
        else:
            logger.info(f'Got 0 proxies from file {file}!')
    return proxy_list


def merge_proxies_into_template(proxies: List[dict]) -> str:
    logger.info(f'Merging {len(proxies)} proxies into template!')
    template = os.environ.get("TEMPLATE")
    if template is None:
        logger.error('Please set TEMPLATE GitHub Actions variable!')
        sys.exit(1)
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
