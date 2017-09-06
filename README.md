Mopidy Skill
=====================

`Still early days. I intend to extend this quite considerably.`

A skill for playing music with the help of the Mopidy music server. Currently the skill supports playing local music by track, artist, album, year or genre.

### Requirements

This skill require mopidy and some related packages to function:

- mopidy
- mopidy-local-mysql

Most of these requirements can be installed through the standard method for the OS. I recommend using the official [mopidy install guide](https://docs.mopidy.com/en/latest/installation/) to get the software for your specific system.

### Mycroft Setup

Mycroft needs to be pointed to the mopidy server. Add the following to `~/.mycroft/mycroft.conf` for a local mopidy server at the default port:

```json
  "Mopidy Skill": {
    "mopidy_url" = "http://localhost:6680"
  }
```

### Running the skill

Before starting Mycroft, *Mopidy* needs to be launched. This should probably be done as a system service.
All music is looked up "on the fly" so even music you've just added to your collection will be available for playback.

## Usage

- Your intent request performs a search within Mopidy, this can be a track, album, artist, etc.

Simple Examples:

```
play track Walking on Broken Glass by Annie Lennox
play the song Lady Writer by Dire Straits
play album The Pick Of Destiny by Tenacious D
play artist Peter Gabriel
play music from 1985
play some Rock music
play music from the 1970s
play tracks performed by Paul Burgess
```
Raw examples of what the skill will respond to:

`play (?:the )?(track|song) (?P<Track>.*) by (?P<Artist>.*)`
`play (?:the )?album (?P<Album>.*) by (?P<Artist>.*)`

```
play (?:the )?(artist|composer) (?P<Artist>.*)
play (?:music|something) by (?P<Artist>.*)
```
```
play (?:tracks|music) from (?:the )?(?P<Decade>(?:16|17|18|19|20)?\d{1}0s)
play (?:tracks|music) from (?:the )?(?P<WordDecade>thirties|fourties|fifties|sixties|seventies|eighties|nineties|naughties|tens)
```
`play (?:tracks|music) from the year (?P<Year>(?:16|17|18|19|20)\d{4})`

```
play (?:the )?genre (?P<Genre>.*)
play (?:(?:me|us) )?some (?P<Genre>.*) music
```
`play (?:tracks|music) (with band member|with performer|performed by) (?P<Performer>.*)`
