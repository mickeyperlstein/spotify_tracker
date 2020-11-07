from datetime import datetime
from time import sleep
from celery import current_task
from .celery_app import celery_app, make_task_name
import redis

from ..spotify_app import settings
from ..spotify_app.AbsTracker import RedisPlaylistTracker
from ..utils.redis_utils import redis_get_json

TRACKING_CATEGORIES_KEY = '_tracking_categories'

r = redis.Redis(settings.redis_credentials) # move to a better and central location
tracker = RedisPlaylistTracker(redis_credentials=settings.redis_credentials)

@celery_app.task(acks_late=True)
def test_celery(word: str) -> str:
    for i in range(1, 11):
        sleep(1)
        current_task.update_state(state='PROGRESS',
                                  meta={'process_percent': i * 10})
    return f"test task return {word}"


@celery_app.task(acks_late=True)
def tsk_start_tracking_all():
    key = TRACKING_CATEGORIES_KEY
    categories = redis_get_json(key)

    if categories and 'items' in categories:
        for cat_item in categories['items']:
            tsk = tsk_track_category.delay(cat_item['id'], cat_item['name'])
        current_task.update_state(state='PROGRESS',
                                  meta={'categories tracked': len(categories['items'])})
        # add as children to current_task current_task
        # current_task.add


@celery_app.task(acks_late=True)
def tsk_track_category(category_id, category_name):
    """

    :param category_id:
    :param category_name:
    :return:
    """
    # check if category has been tracked in last 24h
    category_playlists = redis_get_json(f'playlist_{category_id}')
    if category_playlists is {}:
        # fill er up
        pass
    else:
        try:
            last = category_playlists['last_updated']
            if (datetime.today()) - (datetime.strptime(last, "%Y-%m-%d %H:%M:%S")).days < 1:
                return "No need to update, already run in last 24h"
        except (KeyError, ValueError):
            pass

        # need to start update
        playlists = tracker.get_playlists_for_category(category_id)
        current_task.update_state(state='LOAD PLAYLISTS',
                                  meta={'status': f'loading playlists ({len(playlists)})',
                                        'category': f'{category_name}'})
        task_name = make_task_name('tsk_track_playlist')
        for playlist in playlists:

            celery_app.send_task(task_name, args=[playlist['id'])  # need to attach as child when done


@celery_app.task(acks_late=True)
def tsk_track_playlist(playlist_id):
    """

    :param category_id:
    :param category_name:
    :return:
    """
    # check if category has been tracked in last 24h
    tracks = tracker.get_tracks_for_playlist(playlist_id)
