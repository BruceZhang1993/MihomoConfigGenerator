import json
import os
from pathlib import Path
from time import sleep

import ruamel.yaml as ry

from generator import script
from generator.mihomo import MihomoCore

yaml = ry.YAML()
yaml.preserve_quotes = True
yaml.allow_unicode = True

TEST_SUBSCRIPTION = 'https://raw.githubusercontent.com/BruceZhang1993/MihomoConfigGenerator/refs/heads/master/example/subscribe.yml'
os.environ['SUBSCRIPTIONS'] = json.dumps([{'name': 'TEST', 'url': TEST_SUBSCRIPTION}])
f = open(Path(__file__).parent.parent / "example" / "template.yml", 'r')
os.environ['TEMPLATE'] = f.read()
f.close()


def test_parse_proxies_from_sub():
    sub_list = script.parse_proxies_from_sub(TEST_SUBSCRIPTION)
    assert type(sub_list) == list
    assert len(sub_list) > 0
    assert type(sub_list[0]) == dict
    assert sub_list[0].get('server') is not None


def test_parse_proxies_from_env():
    sub_list = script.parse_proxies_from_env()
    assert type(sub_list) == list
    assert len(sub_list) > 0
    assert type(sub_list[0]) == dict
    assert sub_list[0].get('server') is not None


def test_merge_proxies_into_template():
    sub_list = script.parse_proxies_from_env()
    template = script.merge_proxies_into_template(sub_list)
    assert type(template) == str


def test_proxy_delay_test():
    core = MihomoCore(None)
    core.start_mihomo_core_process()
    assert core.is_running
    with open(Path(__file__).parent.parent / "example" / "generated.yml", 'r') as file:
        data = yaml.load(file, Loader=yaml.FullLoader)
        core.put_configs(data)
    sleep(3)
    print("==============================")
    for k, v in core.proxies()['proxies'].items():
        if k in ('COMPATIBLE', 'DIRECT', 'GLOBAL', 'PASS', 'PROXY', 'REJECT', 'REJECT-DROP'):
            continue
        result = core.proxy_delay(k)
        print(k, '=>', result)
    sleep(3)
    core.stop()

def test_bad_yaml_data():
    yaml.add_constructor('str', lambda loader, node: node.value, yaml.Loader)
    data1 = 'type: trojan\npassword: !<str> 123456'
    resolved1 = yaml.load(data1, Loader=yaml.Loader)
    print(resolved1)

def test_proxy_after_handle():
    script.proxy_after_handle({'name': 'test', 'type': 'trojan', 'password': '123456', 'reality-opts': {'short-id': '7266000000'}}, 'test')
