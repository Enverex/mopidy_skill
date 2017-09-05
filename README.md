Mopidy Skill
=====================

`Still early days. I intend to extend this quite considerably.`

A skill for playing music with the help of the Mopidy music server. Currently the skill supports playing local music by track, artist, album or genre.

### Requirements

This skill require mopidy and some related packages to function:

- mopidy
- mopidy-local-mysql

Most of these requirements can be installed through the standard method for the OS. I recommend using the official [mopidy install guide](https://docs.mopidy.com/en/latest/installation/) to get the software for your specific system.

### Mopidy Setup

Mopidy configuration is complex and this description will only touch the areas that are relevant for the skill.

Mopidy settings are made in *~/.config/mopidy/mopidy.conf* for a desktop install and under */etc/mopidy/mopidy.conf* for picroft/Mark-1 (if it doesn't exist it needs to be created).

Below the basic configuration needed is listed, for more details check out the official documentation at https://www.mopidy.com

#### Local music

For playing music from the local file system or file share check under the heading

`[local]`

and make sure the following config options are set according to your system

```
enabled = true
library = sqlite
media_dir = PATH_TO_YOUR_MUSIC
```

after this is done scan the local collection by running

` mopidy local scan `

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

Examples:

`play track Walking on Broken Glass by Annie Lennox`

`play album `

`play artist Terry Scott Taylor`

`play some Rock Music`

Regex raw examples:

```
play (?:the )?track (?P<Track>.*) by (?P<Artist>.*)
play (?:the )?song (?P<Track>.*) by (?P<Artist>.*)

play (?:the )?album (?P<Album>.*) by (?P<Artist>.*)

play (?:the )?artist (?P<Artist>.*)
play (?:the )?composer (?P<Artist>.*)
play something by (?P<Artist>.*)

play (?:the )?genre (?P<Genre>.*)
play some (?P<Genre>.*) music

play music from the year (?P<Year>\d+)
play music from (?P<Year>19\d+)
````
