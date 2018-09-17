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

BEND_INCREMENT_TICKS = 16

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

def _createBend(bendValues, duration, track):
    events = []

    valueCount = len(bendValues) - 1
    segmentDuration = int(duration / valueCount)
    timeTally = 0
    lastValue = 0
    index = 0

    while index < valueCount:
        start = float(bendValues[index])
        end = float(bendValues[index + 1])
        increment = int(segmentDuration / BEND_INCREMENT_TICKS)
        subTimeTally = 0
        for step in range(0, increment):
            moment = step * (end - start) / increment
            actual = round(100 * (start + moment))

            delta = music21.midi.DeltaTime(track)
            delta.time = BEND_INCREMENT_TICKS
            events.append(delta)

            bend = music21.midi.MidiEvent(track, type="PITCH_BEND", channel=1)
            bend.setPitchBend(actual)
            events.append(bend)

            subTimeTally += BEND_INCREMENT_TICKS
            timeTally += BEND_INCREMENT_TICKS
        index += 1

    if timeTally < duration:
        delta = music21.midi.DeltaTime(track)
        delta.time = timeTally - duration
        events.append(delta)

    delta = music21.midi.DeltaTime(track)
    delta.time = 0
    events.append(delta)

    bend = music21.midi.MidiEvent(track, type="PITCH_BEND", channel=1)
    bend.time = 0
    bend.setPitchBend(0)
    events.append(bend)

    return events

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
                    if articulation.displayText.startswith("bend__"):
                        bend = articulation.displayText[6:]
                        meta["bend"] = bend

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
            eventLength = len(noteEvents)
            wasGraced = False

            while index < eventLength:
                event = noteEvents[index]
                event.channel = 1

                if isinstance(event, music21.midi.DeltaTime):
                    offset += event.time
                    if meta.get("bend"):
                        if index < eventLength - 1:
                            nextEvent = noteEvents[index + 1]
                            if nextEvent.type == "NOTE_OFF":
                                bendValues = meta.get("bend").split(",")
                                bendEvents = _createBend(bendValues, event.time, track)

                                for bend in bendEvents:
                                    wrapped = music21.base.ElementWrapper(bend)
                                    eventsAndMeta.append((wrapped, meta))
                            event.time = 0

                if "bass" in partName:
                    if event.type == "NOTE_ON" or event.type == "NOTE_OFF":
                        if event.pitch:
                            event.pitch += 12

                if event.type == "NOTE_ON":
                    event.velocity = velocity

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
                eventsAndMeta.append((event, meta))

                index += 1

    return eventsAndMeta
