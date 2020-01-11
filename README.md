# tsuserver3 Origin

A Python based server for Attorney Online.

Currently targeting client [AO Classic](https://github.com/argoneuscze/AO2-Client), while `webAO` is unsupported.

Requires Python 3.8+.

## Motivation

Over the years, the original [tsuserver3](https://github.com/AttorneyOnlineVidya/tsuserver3) has been changed by various people and the codebase
has been inflated to the point where making any sort of change created a bigger mess than before.

Therefore *tsuserver3 Origin* aims to keep the old codebase simple and extend the code reasonably
while keeping it simple to add new features.

## TODO

There's a bunch of features currently missing from this version, as it's almost two years old.
I hope to implement those and more in time. These are:

* ~~AO2 Loading~~
* ~~AO2 Feature Support~~
* Evidence support
* ~~WebSockets~~
* Modcall reason
* Built-in support for Areas (pending client support)
* Improved banlist (SQLite)
* Server voting (SQLite)
* REST API
* Pairing
* Password/Token for areas
* Command overhaul [x]
* Improved targeting for OOC commands [x]

Items marked with [x] are currently in progress.


## How to use

* Rename `config_sample` to `config` and edit the values to your liking.  
* Run by using `start_server.py`. It's recommended that you use a separate virtual environment.

## Commands

### User Commands

* **/help**
  * Shows a link to this page.
* **/dc**
  * Disconnects other clients with your IP from the server. Useful if your client crashes.
* **/pos [position]**
  * If an argument is provided, changes your position to a new one, otherwise resets it to default.
  * Allowed positions: `def`, `pro`, `jud`, `wit`, `hld`, `hlp`
* **/bg [background]**
  * If an argument is provided, changes the background, otherwise
* **/status [status]**
  * If an argument is provided, changes the current area status, otherwise tells you the current status.
* **/doc [url]**
  * If an argument is provided, changes the current area's document, otherwise gives you the current one.
* **/cleardoc**
  * Clears the document of the current area.
* **/cm [name]**
  * If an argument is provided, changes the current area's CM, otherwise tells you who it is.
* **/clearcm**
  * Clears the CM of the current area.
* **/getarea**
  * Shows you a list of the characters in your current area.
* **/pm \<target>: \<message>**
  * Private message, matches first in order character name -> OOC name.
* **/g \<message>**
  * Global chat, shared between all areas.
* **/roll [maxvalue]**
  * Diee roll, default value is 6.
* **/coinflip**
  * Heads or tails.

### Mod Commands

* **/login \<password>**
  * Authenticates you as moderator.
* **/kick \<target>**
  * Kicks the target from the server.
* **/mute \<target>**
  * Prevents the target from talking IC.
* **/unmute \<target>**
  * Unmutes the target.
* **/banip \<IP>**
  * Adds the specified IP to the banlist and kicks all players using this IP.

## License

This server is licensed under the AGPLv3 license. See the
[LICENSE](LICENSE.md) file for more information.