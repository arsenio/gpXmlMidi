# -*- coding: utf-8 -*-

import music21
import sys

"""
Translation methods for creating MIDI events from various data formats.
"""

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
                if articulation.displayText == "palm-mute":
                    meta["palmMute"] = True

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

            index = 0
            while index < len(noteEvents):
                event = noteEvents[index]

                event.channel = 1

                if isinstance(event, music21.midi.DeltaTime):
                    offset += event.time
#
#                    nextEvent = noteEvents[index + 1]
#                    if nextEvent.type == "NOTE_ON":
#                        if nextEvent.pitch in skips:
#                            if skips[nextEvent.pitch]["on"]:
#                                index += 2
#                                continue
#
#                    if nextEvent.type == "NOTE_OFF":
#                        if nextEvent.pitch in skips:
#                            if skips[nextEvent.pitch]["off"]:
#                                index += 2
#                                continue

                # Guitar Pro for some reason shifts basslines down an octave
                if "bass" in partName:
                    if event.type == "NOTE_ON" or event.type == "NOTE_OFF":
                        event.pitch += 12

                # Scale up the velocities so that GP max = MIDI max
                if event.type == "NOTE_ON":
                    event.velocity = min(int(event.velocity * 1.42), 127)

                wrapped = music21.base.ElementWrapper(event)
                eventsAndMeta.append((wrapped, meta))

                index += 1

    return eventsAndMeta
