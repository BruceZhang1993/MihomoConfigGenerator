import json
import os
import sys
from pathlib import Path
from typing import List
from urllib.parse import urlparse
from loguru import logger

import requests
import yaml

from generator.mihomo import MihomoCore

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
    try:
        response = requests.get(sub, headers=headers)
    except Exception as e:
        logger.warning(f'Failed to get proxies from {sub}, exception: {e}!')
        return []
    if response.status_code != 200:
        logger.warning(f'Failed to get proxies from {sub}, http code: {response.status_code}!')
        return []
    sub_text = response.text
    data = yaml.load(sub_text, Loader=yaml.FullLoader)
    if data is None:
        logger.warning(f'Failed to get proxies from {sub}, data is empty!')
        return []
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
        logger.info(f'Reading proxies from file!')
        file_proxies = yaml.load(file, Loader=yaml.FullLoader)
        if file_proxies is not None:
            logger.info(f'Got {len(file_proxies.get("proxies"))} proxies from file!')
            proxy_list.extend([mark_proxy_name(proxy, 'FILE') for proxy in file_proxies.get('proxies')])
        else:
            logger.info(f'Got 0 proxies from file {file}!')
    return proxy_list


def proxy_unique_key(proxy):
    type_ = proxy['type'] or None
    server = proxy['server'] or None
    port = proxy['port'] or None
    return f'{type_}_{server}_{port}'


def merge_proxies_into_template(proxies: List[dict]) -> str:
    logger.info(f'Merging {len(proxies)} proxies into template!')
    template = os.environ.get("TEMPLATE")
    if template is None:
        logger.error('Please set TEMPLATE GitHub Actions variable!')
        sys.exit(1)
    data = yaml.load(template, Loader=yaml.FullLoader)
    unique_proxies = list({proxy_unique_key(v): v for v in proxies}.values())
    name_set = set()
    for i, proxy in enumerate(unique_proxies):
        name = proxy.get('name')
        if name is None:
            continue
        if name in name_set:
            unique_proxies[i]['name'] = f'{name}_{i}'
        name_set.add(name)
    data['proxies'] = unique_proxies
    return yaml.dump(data, allow_unicode=True)


def exclude_timeout_proxies():
    home = Path(__file__).parent.parent
    with (home / 'result' / 'config.yml').open('r') as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
    core = MihomoCore((home / 'result' / 'config.yml').as_posix())
    core.start_mihomo_core_process()
    if not core.is_running:
        logger.error('Failed to start mihomo core!')
        sys.exit(1)
    new_proxies = []
    for proxy in data['proxies']:
        result = core.proxy_delay(proxy['name'])
        if result is None or result.get('delay') is None:
            # delay timeout > 5000ms
            logger.warning(f'Proxy {proxy["name"]} is removed for timeout, err: {result}')
            continue
        logger.info(f'Proxy {proxy["name"]} is ok, result: {result}')
        proxy['delay'] = result['delay']
        new_proxies.append(proxy)
    new_proxies = sorted(new_proxies, key=lambda x: x['delay'])
    data['proxies'] = new_proxies[0:50]
    with (home / 'result' / 'config_best_50.yml').open('w') as f:
        f.write(yaml.dump(data, allow_unicode=True))
        f.flush()
    data['proxies'] = new_proxies[0:100]
    with (home / 'result' / 'config_best_100.yml').open('w') as f:
        f.write(yaml.dump(data, allow_unicode=True))
        f.flush()
    core.stop()


def speedtest():
    config_url = 'https://github.com/BruceZhang1993/MihomoConfigGenerator/releases/download/pre-release/config.yml'
    response = requests.get(config_url, stream=True)
    home = Path(__file__).parent.parent
    (home / 'result').mkdir(exist_ok=True)
    with (home / 'result' / 'config.yml').open('wb') as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
        f.flush()
    exclude_timeout_proxies()


def main():
    proxies = parse_proxies_from_env()
    if proxies is None or len(proxies) == 0:
        sys.exit(0)
    yaml_str = merge_proxies_into_template(proxies)
    home = Path(__file__).parent.parent
    (home / 'result').mkdir(exist_ok=True)
    with (home / 'result' / 'config.yml').open('w') as f:
        f.write(yaml_str)
        f.flush()
