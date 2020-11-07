import json
import logging
import os

import redis
from fastapi import FastAPI, BackgroundTasks

from app.spotify_app import settings
from app.worker.celery_app import celery_app, make_task_name
from app.worker.celery_worker import TRACKING_CATEGORIES_KEY
from spotify_app.AbsTracker import RedisPlaylistTracker

log = logging.getLogger(__name__)

app = FastAPI()
r = redis.Redis(**settings.redis_credentials)  # will be moved to other config


def celery_on_message(meta):
    log.warning(meta)


def background_on_message(task):
    tsk = task.get(on_message=celery_on_message, propagate=False)
    log.warning(tsk)


@app.get("/{word}")
async def root(word: str, background_task: BackgroundTasks):

    task_name = make_task_name('test_task')

    task = celery_app.send_task(task_name, args=[word])
    print(task)
    background_task.add_task(background_on_message, task)

    return {"message": "Word received"}


def redis_get_json(key):
    obj_json_str = r.get(key) or '{}'
    dictionary_item = json.loads(obj_json_str)
    return dictionary_item


def redis_put_as_json(key, json_item):
    json_str = json.dumps(json_item)
    return r.set(key, json_str)


@app.get("/track")
async def start_tracking_all():
    task_name = make_task_name('tsk_start_tracking_all')
    task = celery_app.send_task(task_name)
    return "started tracking"


@app.get("/entity/create/{category_id}/{category_name}")
async def add_category(category_id, category_name):
    key = TRACKING_CATEGORIES_KEY
    categories = redis_get_json(key)
    updated_categories = list(set(categories).add((category_id, category_name)))
    return redis_put_as_json(key, updated_categories)


@app.get("/entity/remove/{category_id}")
async def add_category(category_id, category_name):
    key = TRACKING_CATEGORIES_KEY
    categories = redis_get_json(key)
    updated_categories = [x for x in categories
                          if x[0] != category_id]

    return redis_put_as_json(key, updated_categories)


@app.get("/categories")
async def show_all_spotify_categories():
    tracker = RedisPlaylistTracker(redis_credentials=settings.redis_credentials)
    return tracker.get_categories()

if __name__ == '__main__' and not os.environ.get('DOCKER', None):

    from hypercorn.config import Config

    config = Config()
    config.bind = ["localhost:8000"]  # As an example configuration setting
    config.debug = True

    import asyncio
    from hypercorn.asyncio import serve

    asyncio.run(serve(app, Config()))


