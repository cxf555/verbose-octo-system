"""Snapshot model - represents one complete sampling moment."""

from dataclasses import dataclass, field
from datetime import datetime

from .process_info import ProcessInfo, SystemInfo


@dataclass
class Snapshot:
    timestamp: datetime = field(default_factory=datetime.now)
    system: SystemInfo = field(default_factory=SystemInfo)
    processes: list[ProcessInfo] = field(default_factory=list)
