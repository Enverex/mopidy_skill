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
			logger.info('Mopidy: Connected to server. Initialising...')
		except:
			if self.connection_attempts < 1:
				logger.debug('Mopidy: Could not connect to server, will retry quietly')
			self.connection_attempts += 1
			time.sleep(10)
			self.emitter.emit(Message(self.name + '.connect'))
			return

		playTrackIntent = IntentBuilder('PlayTrackIntent').require('Track').require('Artist').build()
		self.register_intent(playTrackIntent, self.handle_play_playlist)

		playAlbumIntent = IntentBuilder('PlayAlbumIntent').require('Album').require('Artist').build()
		self.register_intent(playAlbumIntent, self.handle_play_playlist)

		playArtistIntent = IntentBuilder('PlayArtistIntent').require('Artist').build()
		self.register_intent(playArtistIntent, self.handle_play_playlist)

		playGenreIntent = IntentBuilder('PlayGenreIntent').require('Genre').build()
		self.register_intent(playGenreIntent, self.handle_play_playlist)

		playYearIntent = IntentBuilder('PlayYearIntent').require('Year').build()
		self.register_intent(playYearIntent, self.handle_play_playlist)

		playDecadeIntent = IntentBuilder('PlayDecadeIntent').require('Decade').build()
		self.register_intent(playDecadeIntent, self.handle_play_playlist)

	def initialize(self):
		logger.info('Mopidy: Initializing skill...')
		super(MopidyLocalSkill, self).initialize()
		self.load_data_files(dirname(__file__))

		self.emitter.on(self.name + '.connect', self._connect)
		self.emitter.emit(Message(self.name + '.connect'))

	def play(self, tracks):
		self.mopidy.clear_list()
		self.mopidy.add_list(tracks)
		self.mopidy.play()

	def handle_play_playlist(self, message):
		keepUrls = ['local:track:']

		artist = message.data.get('Artist')
		album = message.data.get('Album')
		track = message.data.get('Track')
		genre = message.data.get('Genre')
		year = message.data.get('Year')
		decade = message.data.get('Decade')
		decadeWord = message.data.get('DecadeWord')
		performer = message.data.get('Performer')

		## Translate a decade word into something usable by the normal decade block
		if decadeWord:
			if decadeWord == 'thirties': decade = 3
			elif decadeWord == 'fourties': decade = 4
			elif decadeWord == 'fifties': decade = 5
			elif decadeWord == 'sixties': decade = 6
			elif decadeWord == 'seventies': decade = 7
			elif decadeWord == 'eighties': decade = 8
			elif decadeWord == 'nineties': decade = 9
			elif decadeWord == 'naughties': decade = 0
			elif decadeWord == 'tens': decade = 1
			else: logger.info('Mopidy: Unrecognised decade phrase ' + decadeWord)

		## Play Track by specific artist
		if artist and track:
			logger.info('Mopidy: Trying to play track ' + track + ' by ' + artist)
			## Get track list
			trackList = self.mopidy.library_search('track_name', track, 'artist', artist)
			## Try again with known grammar replacements
			if not trackList:
				logger.info("Mopidy: No search matches, trying again with common word variations.")
				track.replace("we have", "we've")
				track.replace("they have", "they've")
				track.replace("they are", "they're")
				trackList = self.mopidy.library_search('track_name', track, 'artist', artist)
			
		## Todo: Playlist, Conversation, Moods?

		## Play album by a specific artist
		elif artist and album:
			logger.info('Mopidy: Trying to play album ' + album + ' by ' + artist)
			trackList = self.mopidy.library_search('album', album, 'artist', artist)

		## Play everything by a specific artist
		elif artist:
			logger.info('Mopidy: Trying to play artist ' + artist)
			trackList = self.mopidy.library_search('artist', artist)

		## Play a genre
		elif genre:
			logger.info('Mopidy: Trying to play genre ' + genre)
			trackList = self.mopidy.library_search('genre', genre)

		## Play everything from a specific year
		elif year:
			logger.info('Mopidy: Trying to play year ' + year)
			trackList = self.mopidy.library_search('date', year)

		## Play random songs from a specific decade
		elif decade:
			## Assume 19XX if only centuries provided
			if decade.len(1):
				decade = '19' + decade;
			logger.info('Mopidy: Trying to play decade ' + decade)
			trackList = self.mopidy.library_search('date', decade)

		## Play tracks with a specific performer / member
		elif performer:
			logger.info('Mopidy: Trying to music tracks with performer ' + performer)
			trackList = self.mopidy.library_search('performer', performer)

		## Reprocess track list to only local files
		trackList = list(nested_lookup('uri', trackList))
		trackList[:] = [l for l in trackList if any(sub in l for sub in keepUrls)]
		self.play(trackList)


	def stop(self, message=None):
		logger.info('Mopidy: Clearing playlist and stopping playback.')
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
		## Resume works as play/resume
		self.mopidy.resume()

	def lower_volume(self, message):
		logger.info('Mopidy: Lowering volume.')
		self.mopidy.lower_volume()
		self.volume_is_low = True

	def restore_volume(self, message):
		if self.volume_is_low:
			logger.info('Mopidy: Restoring volume.')
			self.mopidy.restore_volume()
			self.volume_is_low = False

	def handle_currently_playing(self, message):
		current_track = self.mopidy.currently_playing()
		if current_track is not None:
			self.mopidy.lower_volume()
			time.sleep(1)
			if 'album' in current_track:
				data = {'current_track': current_track['name'], 'artist': current_track['album']['artists'][0]['name']}
				self.speak_dialog('currently_playing', data)
			time.sleep(5)
			self.mopidy.restore_volume()


def create_skill():
	return MopidyLocalSkill()
