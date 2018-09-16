from postprocess.base import BasePostprocessor
from postprocess.realeight import RealEightPostprocessor

POSTPROCESSORS = {
    "realeight": (RealEightPostprocessor,)
}

def checkForPreprocessor(a):
    return (a in POSTPROCESSORS.keys())

def selectPreprocessors(option):
    return POSTPROCESSORS[option] if option in POSTPROCESSORS else [BasePostprocessor]

def reduceEventsAndMeta(eventsAndMeta):
    return [event for event, meta in eventsAndMeta]
