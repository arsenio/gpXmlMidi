import music21

class RealEightPostprocessor:
    def run(self, eventsAndMeta):
        newEventsAndMeta = []

        priorVibrato = False
        for event, meta in eventsAndMeta:
            partName = meta.get("partName", "")

            # Palm mutes are on a separate channel
            if meta.get("palmMute"):
                event.channel = 3

            # Harmonics are on a separate channel, and an octave too high
            if meta.get("harmonic"):
                event.channel = 13
                if event.type in ["NOTE_ON", "NOTE_OFF"]:
                    event.pitch -= 12

            # Vibrato requires mod wheel events before and after this one
            if event.type == "NOTE_ON":
                if meta.get("vibrato"):
                    vibratoOn = music21.midi.MidiEvent(event.track)
                    vibratoOn.type = "CONTROLLER_CHANGE"
                    vibratoOn.time = 0
                    vibratoOn.pitch = 1      # CC 1 = Mod Wheel MSB
                    vibratoOn.velocity = 64
                    vibratoOn.channel = 1
                    newEventsAndMeta.append((vibratoOn, meta))

                    delta = music21.midi.DeltaTime(event.track)
                    delta.time = 0
                    newEventsAndMeta.append((delta, meta))

                    priorVibrato = True

                elif priorVibrato:
                    vibratoOff = music21.midi.MidiEvent(event.track)
                    vibratoOff.type = "CONTROLLER_CHANGE"
                    vibratoOff.time = 0
                    vibratoOff.pitch = 1     # CC 1 = Mod Wheel MSB
                    vibratoOff.velocity = 0
                    vibratoOff.channel = 1
                    newEventsAndMeta.append((vibratoOff, meta))

                    delta = music21.midi.DeltaTime(event.track)
                    delta.time = 0
                    newEventsAndMeta.append((delta, meta))

                    priorVibrato = False

            newEventsAndMeta.append((event, meta))

        return newEventsAndMeta
