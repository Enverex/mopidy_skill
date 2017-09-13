#### Todo:
## Mood Tag Support - not possible until Python.GST bindings are updated to include this tag
##		and then Mopidy is updated to support that, then Mopidy-SQLite is updated to support that.
## Randomise - Randomise the current track listing.
## Enqueue - Ability to add to the current playlist queue rather than always starting a new one.
## Conversation - Multi-part ability to ask for info on something, e.g. albums by artist and then
##		respond which you want

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


class MopidyLocalSkill(MycroftSkill):
	def __init__(self):
		super(MopidyLocalSkill, self).__init__('Mopidy Local Skill')
		self.mopidy = None
		self.volume_is_low = False
		self.connection_attempts = 0

	def _connect(self, message):
		## Use user specified URL, otherwise fall back to Mopidy default
		try:
			confirUrl = ConfigurationManager.get().get('MopidySkill').get('mopidy_url', None)
			url = confirUrl
		except:
			url = 'http://localhost:6680'

		## Try and connect, retry after a delay if it fails
		try:
			self.mopidy = Mopidy(url)
			logger.info('Mopidy: Connected to server. Initialising...')
		except:
			if self.connection_attempts < 1:
				logger.debug('Mopidy: Could not connect to server, will retry in 10 seconds.')
			self.connection_attempts += 1
			time.sleep(10)
			self.emitter.emit(Message(self.name + '.connect'))
			return

	def initialize(self):
		logger.info('Mopidy: Initializing skill...')
		super(MopidyLocalSkill, self).initialize()
		self.load_data_files(dirname(__file__))

		## Connection loop
		self.add_event(self.name + '.connect', self._connect)
		self.emitter.emit(Message(self.name + '.connect'))

		## Set up intents
		playControllerIntent = IntentBuilder('playControllerIntent').require('Action').build()
		self.register_intent(playControllerIntent, self.handle_playlist_control)

		currentlyPlayingIntent = IntentBuilder('currentlyPlayingIntent').require('CurrentlyPlayingKeyword')
		self.register_intent(currentlyPlayingIntent, self.handle_currently_playing)

		playTrackIntent = IntentBuilder('playTrackIntent').require('Track').require('Artist').build()
		self.register_intent(playTrackIntent, self.handle_play_playlist)

		playAlbumIntent = IntentBuilder('playAlbumIntent').require('Album').require('Artist').build()
		self.register_intent(playAlbumIntent, self.handle_play_playlist)

		playArtistIntent = IntentBuilder('playArtistIntent').require('Artist').build()
		self.register_intent(playArtistIntent, self.handle_play_playlist)

		playGenreIntent = IntentBuilder('playGenreIntent').require('Genre').build()
		self.register_intent(playGenreIntent, self.handle_play_playlist)

		playYearIntent = IntentBuilder('playYearIntent').require('Year').build()
		self.register_intent(playYearIntent, self.handle_play_playlist)

		playDecadeIntent = IntentBuilder('playDecadeIntent').require('Decade').build()
		self.register_intent(playDecadeIntent, self.handle_play_playlist)

		playDecadeWordIntent = IntentBuilder('playDecadeWordIntent').require('DecadeWord').build()
		self.register_intent(playDecadeWordIntent, self.handle_play_playlist)

		playPerformerIntent = IntentBuilder('playPerformerIntent').require('Performer').build()
		self.register_intent(playPerformerIntent, self.handle_play_playlist)

		playLikeTrackIntent = IntentBuilder('playLikeTrackIntent').require('LikeSong').require('LikeArtist').build()
		self.register_intent(playLikeTrackIntent, self.handle_play_playlist)

		playLikeIntent = IntentBuilder('PlayLikeIntent').require('LikeArtist').build()
		self.register_intent(playLikeIntent, self.handle_play_playlist)

		## Listen for event requests from Mycroft core
		self.add_event('mycroft.audio.service.pause', self.handle_pause)
		self.add_event('mycroft.audio.service.stop', self.handle_stop)
		self.add_event('mycroft.audio.service.next', self.handle_next)
		self.add_event('mycroft.audio.service.prev', self.handle_prev)
		self.add_event('recognizer_loop:record_begin', self.lower_volume)
		self.add_event('recognizer_loop:audio_output_start', self.lower_volume)
		self.add_event('recognizer_loop:record_end', self.restore_volume)
		self.add_event('recognizer_loop:audio_output_end', self.restore_volume)


	## Do play
	def play(self, tracks):
		self.mopidy.clear_list()
		self.mopidy.add_list(tracks)
		self.mopidy.play()


	## Basic media controls
	def handle_playlist_control(self, message):
		performAction = message.data.get('Action')
		if performAction == 'next':
			self.handle_next()
		elif performAction == 'previous':
			self.handle_prev()
		elif performAction == 'play' or performAction == 'resume' or performAction == 'continue' or performAction == 'unpause':
			self.handle_play()
		elif performAction == 'pause':
			self.handle_pause()
		elif performAction == 'stop':
			self.handle_stop()


	## Playlist additions
	def handle_play_playlist(self, message):
		keepUrls = ['local:track:']
		trackList = None
		randomMode = False
		artist = message.data.get('Artist')
		album = message.data.get('Album')
		track = message.data.get('Track')
		genre = message.data.get('Genre')
		year = message.data.get('Year')
		decade = message.data.get('Decade')
		decadeWord = message.data.get('DecadeWord')
		performer = message.data.get('Performer')
		likeSong = message.data.get('LikeSong')
		likeArtist = message.data.get('LikeArtist')

		## Translate a decade word into something usable by the normal decade block
		if decadeWord:
			if decadeWord == 'naughties': decade = 0
			elif decadeWord == 'tens': decade = 1
			elif decadeWord == 'twenties': decade = 2
			elif decadeWord == 'thirties': decade = 3
			elif decadeWord == 'fourties': decade = 4
			elif decadeWord == 'fifties': decade = 5
			elif decadeWord == 'sixties': decade = 6
			elif decadeWord == 'seventies': decade = 7
			elif decadeWord == 'eighties': decade = 8
			elif decadeWord == 'nineties': decade = 9
			else: logger.info('Mopidy: Unrecognised decade phrase ' + decadeWord)
			## String needed for later concatination
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

		## Play album by a specific artist
		elif artist and album:
			logger.info('Mopidy: Trying to play album ' + album + ' by ' + artist)
			trackList = self.mopidy.library_search('album', album, 'artist', artist)

		## Play everything by a specific artist
		elif artist:
			randomMode = True
			logger.info('Mopidy: Trying to play artist ' + artist)
			trackList = self.mopidy.library_search('artist', artist)

		## Try and find music like the requested artist (optionally a specific song) by matching their genres
		elif likeArtist:
			randomMode = True

			## Look for specific song, not just artist
			if likeSong:
				logger.info('Mopidy: Trying to find music like ' + likeSong + ' by ' + likeArtist)
				artistGenres = self.mopidy.get_artist_genres(likeArtist, likeSong)
			else:
				logger.info('Mopidy: Trying to find music like artist ' + likeArtist)
				artistGenres = self.mopidy.get_artist_genres(likeArtist)

			## Genres found
			if artistGenres is not None:
				trackList = self.mopidy.get_similar_tracks(artistGenres, likeArtist)
				## No matches, remove the lest significant genre and try again
				if not trackList and len(artistGenres) > 1:
					artistGenres = artistGenres[:-1]
					trackList = self.mopidy.get_similar_tracks(artistGenres, likeArtist)
					if not trackList and len(artistGenres) > 1:
						## No matches, remove the lest significant genre and try again
						artistGenres = artistGenres[:-1]
						trackList = self.mopidy.get_similar_tracks(artistGenres, likeArtist)
				if not trackList:
					logger.info('Mopidy: Unable to find any music like ' + likeArtist)
			else:
				logger.info('Mopidy: Aborting like lookup due to no genres.')

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

		if trackList is not None:
			## Crop tracklist to only proper track URIs
			trackList = list(nested_lookup('uri', trackList))
			trackList[:] = [l for l in trackList if any(sub in l for sub in keepUrls)]

			## Randomise the tracklist if required
			if randomMode: random.shuffle(trackList)

			## Shrink to a sane value (50 tracks) and send off to play
			trackList = trackList[:50]
			self.play(trackList)
		else:
			logger.info('Mopidy: No tracks found to play.')
			self.speak("No matching music found")


	def handle_stop(self, message=None):
		logger.info('Mopidy: Clearing playlist and stopping playback.')
		if self.mopidy:
			self.mopidy.clear_list()
			self.mopidy.stop()

	def handle_next(self, message=None):
		logger.info('Mopidy: Playing next track.')
		self.mopidy.next()

	def handle_prev(self, message=None):
		logger.info('Mopidy: Playing previous track.')
		self.mopidy.previous()

	def handle_pause(self, message=None):
		logger.info('Mopidy: Pausing playback.')
		self.mopidy.pause()

	def handle_play(self, message=None):
		## Resume works as play/resume
		logger.info('Mopidy: Starting/continuing playback.')
		self.mopidy.resume()

	def lower_volume(self, message=None):
		logger.info('Mopidy: Lowering volume.')
		self.mopidy.lower_volume()
		self.volume_is_low = True

	def restore_volume(self, message=None):
		if self.volume_is_low:
			logger.info('Mopidy: Restoring volume.')
			self.mopidy.restore_volume()
			self.volume_is_low = False

	def handle_currently_playing(self, message=None):
		logger.info('Mopidy: Reporting currently playing track.')
		current_track = self.mopidy.currently_playing()
		if current_track is not None and current_track['name'] is not '':
			if 'album' in current_track:
				self.mopidy.lower_volume()
				time.sleep(1)
				data = {'current_track': current_track['name'], 'artist': current_track['album']['artists'][0]['name'], 'album': current_track['album']['name']}
				self.speak_dialog('currently_playing', data)
				time.sleep(8)
				self.mopidy.restore_volume()
				return

		self.speak("Nothing is currently playing")
		time.sleep(3)
		self.mopidy.restore_volume()


def create_skill():
	return MopidyLocalSkill()
