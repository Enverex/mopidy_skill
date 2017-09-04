import sys
from os.path import dirname, abspath, basename

from adapt.intent import IntentBuilder
from mycroft.messagebus.message import Message

import time
import requests
import json

from os.path import dirname
from mycroft.util.log import getLogger
from nested_lookup import nested_lookup

sys.path.append(abspath(dirname(__file__)))
Mopidy = __import__('mopidypost').Mopidy
MediaSkill = __import__('media').MediaSkill

logger = getLogger(abspath(__file__).split('/')[-2])
__author__ = 'Enverex'
## Original skill author: forslund


class MopidyLocalSkill(MediaSkill):
    def __init__(self):
        super(MopidyLocalSkill, self).__init__('Mopidy Local Skill')
        self.mopidy = None
        self.volume_is_low = False
        self.connection_attempts = 0

    def _connect(self, message):
        url = 'http://localhost:6680'
        if self.base_conf:
            url = self.base_conf.get('mopidy_url', None)
        if self.config:
            url = self.config.get('mopidy_url', url)
        try:
            self.mopidy = Mopidy(url)
        except:
            if self.connection_attempts < 1:
                logger.debug('Could not connect to server, will retry quietly')
            self.connection_attempts += 1
            time.sleep(10)
            self.emitter.emit(Message(self.name + '.connect'))
            return

        logger.info('Connected to Mopidy server. Initialising...')
        self.tracks = {}
        self.albums = {}
        self.artists = {}
        self.genres = {}
        self.tracks = self.mopidy.get_local_tracks()
        self.albums = self.mopidy.get_local_albums()
        self.artists = self.mopidy.get_local_artists()
        self.genres = self.mopidy.get_local_genres()

        playTrackIntent = IntentBuilder('PlayTrackIntent').require('Track').require('Artist').build()
        self.register_intent(playTrackIntent, self.handle_play_playlist)

        playAlbumIntent = IntentBuilder('PlayAlbumIntent').require('Album').require('Artist').build()
        self.register_intent(playAlbumIntent, self.handle_play_playlist)

        playArtistIntent = IntentBuilder('PlayArtistIntent').require('Artist').build()
        self.register_intent(playArtistIntent, self.handle_play_playlist)

        playGenreIntent = IntentBuilder('PlayGenreIntent').require('Genre').build()
        self.register_intent(playGenreIntent, self.handle_play_playlist)

    def initialize(self):
        logger.info('Mopidy: Initializing skill...')
        super(MopidyLocalSkill, self).initialize()
        self.load_data_files(dirname(__file__))

        self.emitter.on(self.name + '.connect', self._connect)
        self.emitter.emit(Message(self.name + '.connect'))

    def play(self, tracks):
        logger.info("Mopidy: Trying to play.")
        self.mopidy.clear_list()
        self.mopidy.add_list(tracks)
        self.mopidy.play()

    def handle_play_playlist(self, message):
        artist = message.data.get('Artist')
        album = message.data.get('Album')
        track = message.data.get('Track')
        genre = message.data.get('Genre')
        keepUrls = ['local:track:']

        ## Play Track by specific artist
        if artist and track:
            logger.info('Mopidy: Trying to play track ' + track + ' by ' + artist)
            try:
                tracks = self.mopidy.find_track(track, artist)
            except:
                ## Try with known grammar replacements
                logger.info("Mopidy: No matches, trying again with word variations.")
                track.replace("we have", "we've")
                tracks = self.mopidy.find_track(track, artist)

        ## Play Album by specific artist
        elif artist and album:
            logger.info('Mopidy: Trying to play album ' + album + ' by ' + artist)
            tracks = self.mopidy.find_artist_album(album, artist)
        ## Play everything by a specific artist
        elif artist:
            logger.info('Mopidy: Trying to play artist ' + artist)
            tracks = self.mopidy.find_artist(artist)
        ## Play Genre
        elif genre:
            logger.info('Mopidy: Trying to play genre ' + genre)
            tracks = self.mopidy.find_genre(genre)

        tracks = list(nested_lookup('uri', tracks))
        tracks[:] = [l for l in tracks if any(sub in l for sub in keepUrls)]
        self.play(tracks)

    def stop(self, message=None):
        logger.info('Handling stop request')
        if self.mopidy:
            self.mopidy.clear_list()
            self.mopidy.stop()

    def handle_next(self, message):
        self.mopidy.next()

    def handle_prev(self, message):
        self.mopidy.previous()

    def handle_pause(self, message):
        self.mopidy.pause()

    def handle_play(self, message):
        """Resume playback if paused"""
        self.mopidy.resume()

    def lower_volume(self, message):
        logger.info('lowering volume')
        self.mopidy.lower_volume()
        self.volume_is_low = True

    def restore_volume(self, message):
        logger.info('maybe restoring volume')
        self.volume_is_low = False
        time.sleep(2)
        if not self.volume_is_low:
            logger.info('restoring volume')
            self.mopidy.restore_volume()

    def handle_currently_playing(self, message):
        current_track = self.mopidy.currently_playing()
        if current_track is not None:
            self.mopidy.lower_volume()
            time.sleep(1)
            if 'album' in current_track:
                data = {'current_track': current_track['name'], 'artist': current_track['album']['artists'][0]['name']}
                self.speak_dialog('currently_playing', data)
            time.sleep(6)
            self.mopidy.restore_volume()


def create_skill():
    return MopidyLocalSkill()
