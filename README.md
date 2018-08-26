# Arrangr
Load up a Midi-file and define a range of ensemble instruments.

This program will then attempt to create an arrangement using all defined instruments. Both taking care of range and other individual differences.

This tool was tested on Windows using Python 2.7.

Start by running MidiMagic.py

Necessary packages are:
- Tkinter (GUI interface)
- mido (reading midi files)
- munkres (using the Kuhn-Munkres algorithm when splitting tones between instruments)
- guitarpro (if exporting to Guitarpro format)

Features include: (all in need of further improvement)
- Reading both simple piano songs and complex symphonic pieces
- rearranging notes to be simpler to play for individual instruments
- identifying melodies and keeping it intact
- exporting to GuitarPro format and text-format guitar sheet music
- identifying chords in polyphonic and also tone-rich monophonic environments (think Bach Cello Sonata 1)
