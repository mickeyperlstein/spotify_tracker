import uuid

import pytest
import redis

from app.spotify_app import settings
from app.utils import redis_utils

lst = [
    {'id': '1234', 'name': 'my name', 'href': 'http://somewhere.com/1234'},
    {'id': '12345', 'name': 'my name', 'href': 'http://somewhere.com/1234'}
]
dict_obj = {'123': 456, 'items': [1, 2, 3, 4], 'others': [{'name': 'john', 'age': 31}, {'someone': '1', 'age': 13}]}


@pytest.mark.parametrize("item", [lst, dict_obj])
def test_put_to_redis(item):
    r = redis.Redis(**settings.redis_credentials)

    key = f'mapping_test_{uuid.uuid1()}'
    redis_utils.redis_put_as_json(r, key, item)
    assert True
    assert r.delete(key)
    assert True


