import datetime
import json

from redis import Redis


def redis_get_json(r: Redis, key):
    json_str = r.get(key) or '{}'
    obj = json.loads(json_str)
    return obj


def redis_put_as_json(r: Redis, key, json_item, expires_on: datetime.datetime = None):

    json_str = json.dumps(json_item)
    seconds_to_expire = None
    if expires_on:
        seconds_to_expire = (expires_on - datetime.datetime.utcnow()).seconds
    json_str='abc'
    return r.set(key, json_str, ex=seconds_to_expire)
