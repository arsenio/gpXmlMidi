class BasePostprocessor:
    def run(self, eventsAndMeta):
        """
        All postprocessors should expect as input a list of tuples,
        with the first element being a translated MidiEvent
        and the second being a dictionary of metadata to influence processing.

        Return a list of events+meta tuples
        """
        return eventsAndMeta
