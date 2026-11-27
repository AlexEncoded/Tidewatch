"""Shared operational states used by fleet and maintenance rules."""

from typing import Literal

BuoyOperationalStatus = Literal["active", "maintenance", "inactive"]
