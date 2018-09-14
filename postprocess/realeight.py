class RealEightPostprocessor:
    def run(self, eventsAndMeta):
        events = []
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

            events.append(event)

        return events
