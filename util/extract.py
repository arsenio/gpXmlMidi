# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import music21
import re
import sys

"""
Extraction methods for retrieving and manipulating data from MusicXML
markup and Music21 objects.
"""

def standardizeExpressions(markup):
    """
    There are a number of permutations and traversals that we need to perform
    on Guitar Pro-generated MusicXML, before translating it into MIDI.
    """
    # Barlines can have repeats (codas); Guitar Pro likes putting the
    # "times" attribute in coda starts, but MusicXML technically does not.
    for repeat in markup("repeat"):
        if repeat.get("direction") == "forward":
            del repeat["times"]

    # Dynamics can technically live in multple places; Guitar Pro tends to
    # put them on the notes only, in a way that music21 seems to miss.
    for dynamics in markup("dynamics"):
        symbols = dynamics.findChildren()
        symbol = symbols[0].name if symbols else "mf"
        notations = dynamics.parent
        technicals = notations.technical or markup.new_tag("technical")
        expr = markup.new_tag("other-technical", class_="dynamics")
        expr.append("dynamics__{}".format(symbol.lower()))
        technicals.append(expr)

    # Palm mutes (guitar only)
    for mute in markup("play"):
        note = mute.parent
        notations = note.notations or markup.new_tag("notations")
        technicals = notations.technical or markup.new_tag("technical")
        if not technicals("other-technical.palmMute"):
            expr = markup.new_tag("other-technical", class_="palmMute")
            expr.append("palm-mute")
            technicals.append(expr)

    # Unpitched note (drums only)
    for unpitched in markup("unpitched"):
        note = unpitched.parent
        newPitch = "{}{}".format(unpitched.find("display-step").text,
                                 unpitched.find("display-octave").text)
        pitch = markup.new_tag("pitch")
        step = markup.new_tag("step")
        step.string = unpitched.find("display-step").text
        octave = markup.new_tag("octave")
        octave.string = unpitched.find("display-octave").text
        # TODO: map these squirrelly values into GM drum map values
        pitch.append(step)
        pitch.append(octave)
        note.append(pitch)

    # Guitar Pro 7 has a number of bizarre nonstandard entities
    # in their XML export.
    for note in markup("note"):
        noteText = str(note)
        if "GP7" in noteText:
            m = re.search(r"<\?GP7([^\?]+)\?>", noteText, re.M)
            if m:
                gp7 = BeautifulSoup(m.group(1), "xml")
                vibrato = gp7.find("vibrato")
                if vibrato:
                    notations = note.notations or markup.new_tag("notations")
                    technicals = notations.technical or markup.new_tag("technical")
                    if not technicals("other-technical.vibrato"):
                        expr = markup.new_tag("other-technical", class_="vibrato")
                        expr.append("vibrato")
                    technicals.append(expr)
                ring = gp7.find("letring")
                if ring:
                    notations = note.notations or markup.new_tag("notations")
                    technicals = notations.technical or markup.new_tag("technical")
                    if not technicals("other-technical.letring"):
                        expr = markup.new_tag("other-technical", class_="letring")
                        expr.append("letring")
                    technicals.append(expr)

        # Guitar Pro also support a variety of bends, with curve-based keystones,
        # that simply doesn't map to MusicXML.
        bends = note("bend")
        if bends:
            points = ["0"]
            for bend in bends:
                if bend.find("pre-bend"):
                    points = [bend.find("bend-alter").text]
                else:
                    points.append(bend.find("bend-alter").text)
            notations = note.notations or markup.new_tag("notations")
            technicals = notations.technical or markup.new_tag("technical")
            if not technicals("other-technical.bend"):
                expr = markup.new_tag("other-technical", class_="bend")
                expr.append("bend__{}".format(",".join(points)))
            technicals.append(expr)

def getStreamTempo(stream, ticksPerQuarterNote, verbose=False):
    """
    Given a Music21 stream object, return a map of tempo regions
    """
    tempos = {}
    try:
        assert stream.seconds # If this fails, there are no metronome marks to detect
        for startTime, endTime, mark in stream.metronomeMarkBoundaries():
            print(startTime, endTime, mark)
            tempo = mark.numberSounding or mark.number
            startTick = int(startTime * ticksPerQuarterNote)
            if startTick not in tempos or tempos[startTick] != tempo:
                tempos[startTick] = tempo
    except music21.exceptions21.StreamException:
        pass

    return tempos
