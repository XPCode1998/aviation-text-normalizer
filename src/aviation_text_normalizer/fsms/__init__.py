from aviation_text_normalizer.fsms.callsign import CallsignFSM
from aviation_text_normalizer.fsms.flight_level import FlightLevelFSM
from aviation_text_normalizer.fsms.frequency import FrequencyFSM
from aviation_text_normalizer.fsms.heading import HeadingFSM
from aviation_text_normalizer.fsms.qnh import QNHFSM
from aviation_text_normalizer.fsms.runway import RunwayFSM
from aviation_text_normalizer.fsms.taxiway import TaxiwayFSM
from aviation_text_normalizer.fsms.value import ValueFSM

DEFAULT_FSMS = [
    CallsignFSM(),
    FlightLevelFSM(),
    RunwayFSM(),
    TaxiwayFSM(),
    HeadingFSM(),
    FrequencyFSM(),
    QNHFSM(),
    ValueFSM(),
]

__all__ = [
    "DEFAULT_FSMS",
    "CallsignFSM",
    "FlightLevelFSM",
    "RunwayFSM",
    "TaxiwayFSM",
    "HeadingFSM",
    "FrequencyFSM",
    "QNHFSM",
    "ValueFSM",
]
