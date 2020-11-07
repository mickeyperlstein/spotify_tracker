import pytest

from app.spotify_app.AbsTracker import *
import logging

MAX = 100
logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s - %(levelname)s - %(message)s",
                    handlers=[logging.StreamHandler()])
log = logging.getLogger('AbsTracker')
log.setLevel(logging.DEBUG)


def test_get_categories_schema():
    pt = PlaylistTracker(spotify_credentials={'password': 'password123'})
    categories = pt.get_categories(limit=MAX)
    assert len(categories)
    assert 'pop' in categories

    for k, v in categories.items():
        for key in ['id', 'name', 'href']:
            assert key in v


@pytest.mark.parametrize("category_id, category_name", [
    ('pop', 'Pop'),
    ('soul', 'Soul')])
def test_get_playlists_from_category(category_id, category_name):
    pt = PlaylistTracker()
    playlists = pt.get_playlists_for_category(category_id)
    assert len(playlists)

    for item in playlists:
        for key in ['id', 'name', 'uri']:
            assert key in item


@pytest.mark.parametrize("playlist_id, playlist_name",
                         [('37i9dQZF1DXcBWIGoYBM5M', 'Todays Top Hits'), ('37i9dQZF1DWUa8ZRTfalHk', 'Pop Rising')])
def test_tracks_from_playlist(playlist_id, playlist_name):
    pt = PlaylistTracker()
    tracks = pt.get_tracks_for_playlist(playlist_id)

    assert len(tracks)
    for item in tracks:
        for key in ['artistNames', 'Danceability', 'id', 'Loudness', 'Popularity', 'trackIndex', 'trackName']:
            assert key in item
