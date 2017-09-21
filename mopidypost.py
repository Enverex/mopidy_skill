import requests
import json
import random
from copy import copy
from heapq import merge

MOPIDY_API = '/mopidy/rpc'
_base_dict = {'jsonrpc': '2.0', 'id': 1, 'params': {}}


class Mopidy(object):
	def __init__(self, url):
		self.is_playing = False
		self.url = url + MOPIDY_API
		self.volume = None
		self.clear_list(force=True)
		self.volume_low = 10
		self.volume_high = 100

	## Take up to 2 fields and values, then return a list of tracks matching those values
	def library_search(self, field, search, field2=None, search2=None):
		d = copy(_base_dict)
		d['method'] = 'core.library.search'

		if field2 is not None:
			d['params'] = {field: [search], field2: [search2], 'uri': ['local:']}
		else:
			d['params'] = {field: [search], 'uri': ['local:']}

		searchResponse =  requests.post(self.url, data=json.dumps(d)).json()

		try:
			return searchResponse["result"][0]["tracks"]
		except:
			return None

	## Take a list of genres and an artist name, return a list of tracks excluding ones by that artist
	def get_similar_tracks(self, genreList, excludeArtist):
		d = copy(_base_dict)
		d['method'] = 'core.library.search'
		d['params'] = {'genre': genreList, 'uri': ['local:']}

		searchResponse =  requests.post(self.url, data=json.dumps(d)).json()

		try:
			searchResponse = searchResponse["result"][0]["tracks"]
		except:
			return None

		trackList = []
		for thisTrack in searchResponse:
			if thisTrack["artists"][0]["name"].lower() != excludeArtist.lower(): trackList.append(thisTrack)

		if trackList:
			return trackList
		else:
			return None

	## Take an artist name (optionally a track name too) and return a list of genres
	def get_artist_genres(self, artist, track=None):
		d = copy(_base_dict)
		d['method'] = 'core.library.search'
		if track is not None:
			d['params'] = {'artist': [artist], 'track_name': [track], 'uri': ['local:']}
		else:
			d['params'] = {'artist': [artist], 'uri': ['local:']}

		searchResponse = requests.post(self.url, data=json.dumps(d)).json()

		try:
			searchResponse = searchResponse["result"][0]["tracks"]
		except:
			return None

		## Randomise the results, take the first 10 and get their genres
		genreList = []
		random.shuffle(searchResponse)
		searchResponse = searchResponse[:10]
		for thisTrack in searchResponse:
			if thisTrack["genre"] is not None:
				#genreList.extend(map(unicode.strip, thisTrack["genre"].split(";")))
				genreList = list(merge(map(unicode.strip, thisTrack["genre"].split(";")), genreList))

		## Return unique set
		genreList = list(set(genreList))
		return genreList


	## Get list of tracks from a specific playlist
	def playlist_search(self, filter=None):
		d = copy(_base_dict)
		d['method'] = 'core.playlists.as_list'
		trackArray = requests.post(self.url, data=json.dumps(d)).json()["result"]
		trackList = []
		for thisTrack in trackArray:
			trackList.append(thisTrack["tracks"])
			if len(trackList) > 50: break

		return trackList

	## Do an exact name search rather than normal wildcard search
	def exact_search(self, uris='null'):
		d = copy(_base_dict)
		d['method'] = 'core.library.find_exact'
		d['params'] = {'uris': uris}
		r = requests.post(self.url, data=json.dumps(d))
		return r.json()

	def browse(self, uri):
		d = copy(_base_dict)
		d['method'] = 'core.library.browse'
		d['params'] = {'uri': uri}
		r = requests.post(self.url, data=json.dumps(d))
		if 'result' in r.json():
			return r.json()['result']
		else:
			return None

	def switch_random(self, modeSet=True):
		d = copy(_base_dict)
		d['method'] = 'set_random'
		d['params'] = {'_random': modeSet}
		r = requests.post(self.url, data=json.dumps(d))
		return r

	def clear_list(self, force=False):
		if self.is_playing or force:
			d = copy(_base_dict)
			d['method'] = 'core.tracklist.clear'
			r = requests.post(self.url, data=json.dumps(d))
			return r

	def add_list(self, uri):
		d = copy(_base_dict)
		d['method'] = 'core.tracklist.add'
		if type(uri) == str or type(uri) == unicode:
			d['params'] = {'uri': uri}
		elif type(uri) == list:
			d['params'] = {'uris': uri}
		else:
			return None
		r = requests.post(self.url, data=json.dumps(d))
		return r

	def play(self):
		self.is_playing = True
		self.restore_volume()
		d = copy(_base_dict)
		d['method'] = 'core.playback.play'
		r = requests.post(self.url, data=json.dumps(d))

	def next(self):
		if self.is_playing:
			d = copy(_base_dict)
			d['method'] = 'core.playback.next'
			r = requests.post(self.url, data=json.dumps(d))

	def previous(self):
		if self.is_playing:
			d = copy(_base_dict)
			d['method'] = 'core.playback.previous'
			r = requests.post(self.url, data=json.dumps(d))

	def stop(self):
		if self.is_playing:
			d = copy(_base_dict)
			d['method'] = 'core.playback.stop'
			r = requests.post(self.url, data=json.dumps(d))
			self.is_playing = False

	def currently_playing(self):
		if self.is_playing:
			d = copy(_base_dict)
			d['method'] = 'core.playback.get_current_track'
			r = requests.post(self.url, data=json.dumps(d))
			return r.json()['result']
		else:
			return None

	def set_volume(self, percent):
		if self.is_playing:
			d = copy(_base_dict)
			d['method'] = 'core.mixer.set_volume'
			d['params'] = {'volume': percent}
			r = requests.post(self.url, data=json.dumps(d))

	def lower_volume(self):
		self.set_volume(self.volume_low)

	def restore_volume(self):
		self.set_volume(self.volume_high)

	def pause(self):
		if self.is_playing:
			d = copy(_base_dict)
			d['method'] = 'core.playback.pause'
			r = requests.post(self.url, data=json.dumps(d))

	def resume(self):
		if self.is_playing:
			d = copy(_base_dict)
			d['method'] = 'core.playback.resume'
			r = requests.post(self.url, data=json.dumps(d))
		else:
			self.play()

	def get_items(self, uri):
		d = copy(_base_dict)
		d['method'] = 'core.playlists.get_items'
		d['params'] = {'uri': uri}
		r = requests.post(self.url, data=json.dumps(d))
		if 'result' in r.json():
			return [e['uri'] for e in r.json()['result']]
		else:
			return None

	def get_tracks(self, uri):
		tracks = self.browse(uri)
		ret = [t['uri'] for t in tracks if t['type'] == 'track']

		sub_tracks = [t['uri'] for t in tracks if t['type'] != 'track']
		for t in sub_tracks:
			ret = ret + self.get_tracks(t)
		return ret

	def get_local_tracks(self):
		p = self.browse('local:directory?type=track')
		return {e['name']: e for e in p if e['type'] == 'track'}

	def get_local_albums(self):
		p = self.browse('local:directory?type=album')
		return {e['name']: e for e in p if e['type'] == 'album'}

	def get_local_artists(self):
		p = self.browse('local:directory?type=artist')
		return {e['name']: e for e in p if e['type'] == 'artist'}

	def get_local_genres(self):
		p = self.browse('local:directory?type=genre')
		return {e['name']: e for e in p if e['type'] == 'directory'}

	def get_local_playlists(self):
		p = self.get_playlists('m3u')
		return {e['name']: e for e in p}
