# Subito

Generate rehearsal files for choristers. 

## Philosophy

It's helpful as a chorister to have "rehearsal files" - MIDIs or MP3s that play your part so you can sing along. 
However, it can be tedious to generate them. 

The core of this script takes a MIDI file (or set of files) with a different part on each track. (As you would find with open-score SATB.)
For each part, it outputs a MIDI with that part foregrounded and others backgrounded (by volume and instrumention).

Optionally, it can start with MuseScore files and output MP3s (both require MuseScore to be installed, in order to perform the conversion). 
MIDIs will also be output for each part. 


## Setup

Put this whereever you normally put random shell scripts. 
If you do that you might want to put `config.ini` somewhere else - modify the second line of `Subito.py` like so: 

```python3
CONFIGPATH = "/path/to/your/config.ini"
```
