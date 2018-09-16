# -*- coding: utf-8 -*-

import music21
import sys

"""
Transformation methods for creating MIDI events from various data formats.
"""

DYNAMICS_VELOCITY_MAP = {
    "ppp": 16,
    "pp": 33,
    "p": 49,
    "mp": 64,
    "mf": 80,
    "f": 96,
    "ff": 112,
    "fff": 127
}

def _findTieSkips(note):
    skips = {}
    innerNotes = note if note.isChord else [note]

    for innerNote in innerNotes:
        on = False
        off = False

        currentTie = innerNote.tie
        if currentTie:
            if currentTie.type == "start":
                on = False
                off = True
            elif currentTie.type == "continue":
                on = True
                off = True
            elif currentTie.type == "stop":
                on = True
                off = False

        skips[innerNote.pitch.midi] = {"on": on, "off": off}

    return skips

def createMIDIEvents(part, track, verbose=False):

    partName = part.partName.casefold()

    notesAndRests = part.flat.notesAndRests

    eventsAndMeta = []
    meta = {}

    offset = 0
    cumulativeDifference = 0
    skips = []

    velocity = 80
    for note in notesAndRests:

        meta = {"partName": partName}

        noteEvents = []

        for articulation in note.articulations:
            if isinstance(articulation, music21.articulations.StringHarmonic):
                meta["harmonic"] = articulation.harmonicType

                if note.isChord:
                    nonHighest = note.pitches[0:-1]
                    for pitch in nonHighest:
                        note.remove(pitch)

            if isinstance(articulation, music21.articulations.TechnicalIndication):
                if articulation.displayText:
                    if articulation.displayText == "palm-mute":
                        meta["palmMute"] = True
                    if articulation.displayText == "vibrato":
                        meta["vibrato"] = True
                    if articulation.displayText.startswith("dynamics__"):
                        dynamics = articulation.displayText[10:]
                        meta["dynamics"] = dynamics
                        if dynamics in DYNAMICS_VELOCITY_MAP:
                            velocity = DYNAMICS_VELOCITY_MAP[dynamics]
                        else:
                            print(dynamics)

        computedOffset = music21.midi.translate.offsetToMidi(note.offset) + cumulativeDifference

        if computedOffset > offset:
            difference = computedOffset - offset
            cumulativeDifference += difference

            delta = music21.midi.DeltaTime(track)
            delta.time = difference

            off = music21.midi.MidiEvent(track)
            off.type = "NOTE_OFF"
            off.time = difference
            off.pitch = 1
            off.velocity = 1
            off.channel = 1

            noteEvents.append(delta)
            noteEvents.append(off)
            offset = computedOffset

        if not note.isRest:
            skips = _findTieSkips(note)

            if note.isChord:
                noteEvents.extend(music21.midi.translate.chordToMidiEvents(note))
            else:
                noteEvents.extend(music21.midi.translate.noteToMidiEvents(note))

            for event in noteEvents:
                event.channel = 1

                if isinstance(event, music21.midi.DeltaTime):
                    offset += event.time

                if "bass" in partName:
                    if event.type == "NOTE_ON" or event.type == "NOTE_OFF":
                        if event.pitch:
                            event.pitch += 12

                if event.type == "NOTE_ON":
                    event.velocity = velocity
#                # Scale up the velocities so that GP max = MIDI max
#                if event.type == "NOTE_ON":
#                    event.velocity = min(int(event.velocity * 1.42), 127)

                # All skips are rendered as null pitches, which preserves
                # timings
                if event.type in ["NOTE_ON", "NOTE_OFF"]:
                    if event.type == "NOTE_ON":
                        if event.pitch in skips:
                            if skips[event.pitch]["on"]:
                                event.pitch = 0

                    if event.type == "NOTE_OFF":
                        if event.pitch in skips:
                            if skips[event.pitch]["off"]:
                                event.pitch = 0

                # Guitar Pro for some reason shifts basslines down an octave
                wrapped = music21.base.ElementWrapper(event)
                eventsAndMeta.append((wrapped, meta))

    return eventsAndMeta
