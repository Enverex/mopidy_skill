## Mopidy Local Player
This skill lets you play music using your local Mopidy server.

## Description 
### Requirements
This skill require Mopidy and some related packages to function:
- mopidy
- mopidy-local-mysql

Most of these requirements can be installed through the standard method for the OS (e.g. apt, pacman, yum, etc). I recommend using the official [mopidy install guide](https://docs.mopidy.com/en/latest/installation/) to get the software for your specific system.

### Custom Mopidy Mycroft Setup
If you're running Mopidy locally on the default port, you don't need to do anything. If you're connecting to a remote Mopidy server then Mycroft will need to be pointed to that mopidy server. Add the following to `~/.mycroft/mycroft.conf` for a local mopidy server at the default port:

```json
  "Mopidy Skill": {
    "mopidy_url" = "http://localhost:6680"
  }
```

### Running the Skill
Before starting Mycroft, *Mopidy* needs to be launched. This should probably be done as a system service.
All music is looked up "on the fly" so even music you've just added to your collection will be available for playback as long as you've told Mopidy to rescan.

Audio controls are also implemented, so you can use the common phrases *next track*, *previous track*, *pause*, *resume*, *stop*, etc to control the music.

## Examples 
* "play track Walking on Broken Glass by Annie Lennox"
* "play the song Lady Writer by Dire Straits"
* "play the album Pick Of Destiny by Tenacious D"
* "play artist Peter Gabriel"
* "play music by Craig David"
* "play something by Don Ross"
* "play music from 1985"
* "play some music from 1999"
* "play music from the 1970s"
* "play tracks from the sixties"
* "play some Rock music"
* "play us some smooth jazz"
* "play tracks performed by Paul Burgess"
* "play music with band member Dave Grohl"
* "play tracks similar to Are You In by Incubus"
* "play music like the band Alphabeat"

## Credits 
Enverex
