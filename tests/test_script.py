import json
import os

from generator import script

TEST_SUBSCRIPTION = 'https://raw.githubusercontent.com/BruceZhang1993/MihomoConfigGenerator/refs/heads/master/example/subscribe.yml'
os.environ['SUBSCRIPTIONS'] = json.dumps([TEST_SUBSCRIPTION])


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
    print(template)
    assert type(template) == str
