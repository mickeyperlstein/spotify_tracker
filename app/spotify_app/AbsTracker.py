import datetime
import json

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from cachier import cachier
import logging
import redis

from app.utils import redis_utils

MAX = 100
log = logging.getLogger(__name__)


def get_next_url_as_key(args, kwargs):
    obj = args[1]
    if obj and 'next' in obj:
        return obj['next']
    else:
        return None


class AbsSpotifyTracker:

    def __init__(self, spotify_credentials=None):
        from . import settings
        settings.load_dotenv()
        log.info('loaded settings')
        auth_manager = SpotifyClientCredentials()
        self.sp = spotipy.Spotify(auth_manager=spotify_credentials or auth_manager)

    @cachier(stale_after=datetime.timedelta(weeks=1), cache_dir='.', hash_params=get_next_url_as_key)
    def get_next(self, obj):
        return self.sp.next(obj)


class PlaylistTracker(AbsSpotifyTracker):

    def get_categories(self, limit=MAX):
        log.info('loading all categories')
        cats = self.sp.categories()
        if cats and 'categories' in cats:
            log.debug(f"TOTAL: {cats['categories']['total']}")

        categories_lookup = dict()
        while cats and cats['categories']:
            c = cats['categories']
            for i, cat in enumerate(c['items']):
                if i + c['offset'] > limit:
                    cats = None

                categories_lookup[cat['id']] = {'id': cat['id'], 'name': cat['name'], 'href': cat['href']}
            if len(categories_lookup.keys) > limit:
                cats = None
            else:
                cats = self.get_next(cats)

        return categories_lookup

    def get_playlists_for_category(self, category_id, limit=MAX):
        log.debug(f'loading playlists for category {category_id}')
        playlists_for_category = self.sp.category_playlists(category_id)
        lst_playlists = list()

        if playlists_for_category:
            log.debug('-->', playlists_for_category['playlists']['total'])
        while playlists_for_category:
            p = playlists_for_category['playlists']
            for i, playlist in enumerate(p['items']):

                item = {'id': playlist['id'], 'uri': playlist['uri'], 'name': playlist['name']}
                lst_playlists.append(item)
            if len(lst_playlists) > limit:
                playlists_for_category = None
            else:
                playlists_for_category = self.get_next(p)

        return lst_playlists

    def get_tracks_for_playlist(self, playlist_id, limit=MAX):
        log.debug(f'loading tracks for playlist id {playlist_id}')
        tracks_for_playlist = self.sp.playlist_items(playlist_id, limit=limit, additional_types=['track'])
        lst_tracks = list()

        if tracks_for_playlist:
            log.debug('-->', tracks_for_playlist['total'])

        while tracks_for_playlist:
            tracks = tracks_for_playlist['items']
            for i, track in enumerate(tracks):
                track_item = track['track']
                item = {'Popularity': track_item.get('popularity'),
                        'id': track_item['id'],
                        'trackName': track_item.get('name'),
                        'trackIndex': i,
                        'artistNames': [x['name'] for x in track_item.get('artists')]}

                lst_tracks.append(item)

            if len(lst_tracks) > limit:
                tracks_for_playlist = None
            else:
                tracks_for_playlist = self.get_next(tracks_for_playlist)

        # update with audio_features
        extra_tracks = self._get_extra_fields_for_tracks(lst_tracks)
        for i, track in enumerate(lst_tracks):
            fields_ = extra_tracks[track['id']]
            lst_tracks[i].update(fields_)

        return lst_tracks

    def _get_extra_fields_for_tracks(self, track_list):
        # split track list into
        limit = 100  # as per API
        chunks = [track_list[x:x + limit] for x in range(0, len(track_list), limit)]
        final_track_lookup = dict()
        for chunk in chunks:
            extended_chunk = {
                x['id']:
                    {
                        'id': x['id'],
                        'Loudness': x['loudness'],
                        'Danceability': x['danceability']
                    } for x in
                self.sp.audio_features(tracks=[x['id'] for x in chunk])}

            final_track_lookup.update(extended_chunk)

        return final_track_lookup


class RedisPlaylistTracker (PlaylistTracker):

    def __init__(self, spotify_credentials, redis_credentials):
        super().__init__(spotify_credentials)
        self.r = redis.Redis(**redis_credentials)

    def _redis_get_json(self, key):
        return redis_utils.redis_get_json(self.r, key)

    def _redis_put_as_json(self, key, obj, expires_on):
        return redis_utils.redis_put_as_json(self.r, key, obj, expires_on)

    def get_categories(self, limit=MAX):
        key = 'all_categories_list'
        all_categories_list = self._redis_get_json(key)
        if not all_categories_list:
            all_categories_list = super().get_categories(limit)
            self._redis_put_as_json(key)

        return all_categories_list

    def get_playlists_for_category(self, category_id, limit=MAX, expires_on=None):
        """

        :param expires_on: kind of a cheat, it will only get the info from spotify if its expired,
                however testing what went wrong or checking historical data will be done through the flower jobs
                and not directly on the redis db. this might not be the best solution, but its faster to implement

        """
        if not expires_on:
            expires_on = midnight_utc = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        key = f'playlists_for_category_{category_id}'
        playlists = self._redis_get_json(key)
        if not playlists:
            playlists = super().get_playlists_for_category(category_id, limit)

            self._redis_put_as_json(key, playlists, expires_on=expires_on)
        return playlists

    def get_tracks_for_playlist(self, playlist_id, limit=MAX):
        key = f'playlist_{playlist_id}'
        tracks = self._redis_get_json(key)
        if not tracks:
            tracks = super().get_tracks_for_playlist(playlist_id, limit)
            self._redis_put_as_json(key, tracks)
        return tracks


