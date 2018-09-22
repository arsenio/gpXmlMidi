import music21

class NormalizePostprocessor:
    def run(self, eventsAndMeta):
        newEventsAndMeta = []
        maxVelocity = max(event.velocity for event, meta in eventsAndMeta if event.velocity)
        factor = 127 / maxVelocity

        for event, meta in eventsAndMeta:
            if event.velocity:
                event.velocity = round(event.velocity * factor)
            newEventsAndMeta.append((event, meta))

        return newEventsAndMeta
