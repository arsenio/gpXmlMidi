import sys

"""
Extraction methods for retrieving and manipulating data from Music21 objects.
"""

def getStreamTempo(stream, ticksPerQuarterNote, verbose=False):
    """
    Given a Music21 stream object, return a map of tempo regions
    """
    tempos = {0: 120}
    for startTime, endTime, mark in stream.metronomeMarkBoundaries():
        tempo = mark.numberSounding or mark.number
        startTick = int(startTime * ticksPerQuarterNote)
        if tempos[startTick] != tempo:
            tempos[startTick] = tempo
            if verbose:
                print("♫ Detected tempo: {} BPM at {} seconds".format(tempo, startTime), file=sys.stderr)

    return tempos
