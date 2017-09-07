import sys
import time
import requests
import json
import random

from os.path import dirname, abspath, basename
from nested_lookup import nested_lookup
from mycroft.skills.core import MycroftSkill
from mycroft.configuration import ConfigurationManager
from mycroft.messagebus.message import Message
from mycroft.util.log import getLogger
from adapt.intent import IntentBuilder

sys.path.append(abspath(dirname(__file__)))
Mopidy = __import__('mopidypost').Mopidy

logger = getLogger(abspath(__file__).split('/')[-2])
__author__ = 'Enverex'
## Original skill author: forslund


class MopidyLocalSkill(MycroftSkill):
	def __init__(self):
		super(MopidyLocalSkill, self).__init__('Mopidy Local Skill')
		self.mopidy = None
		self.volume_is_low = False
		self.connection_attempts = 0

	def _connect(self, message):
		url = 'http://localhost:6680'
		config = ConfigurationManager.get()
		self.base_conf = config.get('MopidySkill')

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

		playControllerIntent = IntentBuilder('PlayControllerIntent').require('Action').build()
		self.register_intent(playControllerIntent, self.handle_playlist_control)

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

		playDecadeWordIntent = IntentBuilder('PlayDecadeWordIntent').require('DecadeWord').build()
		self.register_intent(playDecadeWordIntent, self.handle_play_playlist)

		playPerformerIntent = IntentBuilder('PlayPerformerIntent').require('Performer').build()
		self.register_intent(playPerformerIntent, self.handle_play_playlist)

		self.add_event('mycroft.audio.service.pause', self.mopidy.pause())
		self.add_event('mycroft.audio.service.next', self.mopidy.next())
		self.add_event('mycroft.audio.service.prev', self.mopidy.previous())

	def initialize(self):
		logger.info('Mopidy: Initializing skill...')
		super(MopidyLocalSkill, self).initialize()
		self.load_data_files(dirname(__file__))

		self.add_event(self.name + '.connect', self._connect)
		self.emitter.emit(Message(self.name + '.connect'))


	def play(self, tracks):
		self.mopidy.clear_list()
		self.mopidy.add_list(tracks)
		self.mopidy.play()


	## Basic media controls
	def handle_playlist_control(self, message):
		performAction = message.data.get('Action')
		if performAction == 'next':
			self.mopidy.next()
		elif performAction == 'previous':
			self.mopidy.previous()
		elif performAction == 'play' or performAction == 'resume' or performAction == 'continue' or performAction == 'unpause':
			self.mopidy.resume()
		elif performAction == 'pause':
			self.mopidy.pause()
		elif performAction == 'stop':
			self.mopidy.stop()


	## Playlist additions
	def handle_play_playlist(self, message):
		keepUrls = ['local:track:']
		randomMode = False
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
			elif decadeWord == 'twenties': decade = 1
			else: logger.info('Mopidy: Unrecognised decade phrase ' + decadeWord)
			decade = str(decade)

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
			randomMode = True
			logger.info('Mopidy: Trying to play artist ' + artist)
			trackList = self.mopidy.library_search('artist', artist)

		## Play a genre
		elif genre:
			randomMode = True
			logger.info('Mopidy: Trying to play genre ' + genre)
			trackList = self.mopidy.library_search('genre', genre)

		## Play everything from a specific year
		elif year:
			randomMode = True
			logger.info('Mopidy: Trying to play year ' + year)
			trackList = self.mopidy.library_search('date', year)

		## Play random songs from a specific decade
		elif decade:
			randomMode = True
			## Remove the trailing 's' and zero (19x[xs] of match group)
			if len(decade) > 1: decade = decade[:-2]
			## Assume 19XX if only centuries provided (19[x]xs of match group)
			if len(decade) == 1: decade = '19' + decade;
			logger.info('Mopidy: Trying to play music from the ' + decade + '0s')
			trackList = self.mopidy.library_search('date', decade + '*')

		## Play tracks with a specific performer / member
		elif performer:
			randomMode = True
			logger.info('Mopidy: Trying to music tracks with performer ' + performer)
			trackList = self.mopidy.library_search('performer', '*' + performer + '*')

		## Crop tracklist to only proper track URIs
		trackList = list(nested_lookup('uri', trackList))
		trackList[:] = [l for l in trackList if any(sub in l for sub in keepUrls)]

		## Randomise the tracklist if required
		if randomMode: random.shuffle(trackList)

		## Shrink to a sane value (20 tracks) and send off to play
		trackList = trackList[:20]
		self.play(trackList)


	def stop(self, message=None):
		logger.info('Mopidy: Clearing playlist and stopping playback.')
		if self.mopidy:
			self.mopidy.clear_list()
			self.mopidy.stop()

	def handle_next(self, message):
		logger.info('Mopidy: Playing next track.')
		self.mopidy.next()

	def handle_prev(self, message):
		logger.info('Mopidy: Playing previous track.')
		self.mopidy.previous()

	def handle_pause(self, message):
		logger.info('Mopidy: Pausing playback.')
		self.mopidy.pause()

	def handle_play(self, message):
		## Resume works as play/resume
		logger.info('Mopidy: Starting/continuing playback.')
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
				data = {'current_track': current_track['name'], 'artist': current_track['album']['artists'][0]['name'], 'album': current_track['album']['name']}
				self.speak_dialog('currently_playing', data)
			time.sleep(8)
			self.mopidy.restore_volume()


def create_skill():
	return MopidyLocalSkill()
