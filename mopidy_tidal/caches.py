from __future__ import unicode_literals

from lru_cache import LruCache

import logging

from utils import remove_watermark

logger = logging.getLogger(__name__)

album_tracks = LruCache()  # key = album uri, val = list of tracks
albums = LruCache()        # key = album uri
searches = LruCache()      # key = SearchKey


class SearchKey(object):
    """
    Immutable object representing a search.
    Used as key for the Lru Cache dictionary.
    """
    def __init__(self, exact, query):
        self._query = tuple(sorted(query.iteritems()))
        self._exact = exact
        self._hash = None

    def __hash__(self):
        if self._hash is None:
            self._hash = hash(self._exact)
            self._hash ^= hash(repr(self._query))

        return self._hash

    def __eq__(self, other):
        if not isinstance(other, SearchKey):
            return False

        return self._exact == other._exact and \
            self._query == other._query


def search_in_cache(exact, query):
    cached_result = None
    query = _fix_query(query)
    if exact:
        for (field, values) in query.iteritems():
            if not hasattr(values, '__iter__'):
                values = [values]

            val = remove_watermark(values[0])
            if field == "album":
                album = next(
                    (a for a in albums.values() if a.name == val), None)
                if album:
                    cached_result = [], [album], (album_tracks[album.uri] or [])

    if not cached_result:
        key = SearchKey(exact, query)
        cached_result = searches.hit(key)

    return cached_result


def save_search_in_cache(exact, query, results):
    key = SearchKey(exact, query)
    searches[key] = results
    if exact:
        res_artists, res_albums, res_tracks = results
        albums.put_by_uri(res_albums)


def _fix_query(query):
        """
        Removes some query parameters that otherwise will lead to a cache miss.
        Eg: 'track_no' since we can't query TIDAL for a specific album's track.
        :param query: query dictionary
        :return: sanitized query dictionary
        """
        query.pop("track_no", None)
        return query
