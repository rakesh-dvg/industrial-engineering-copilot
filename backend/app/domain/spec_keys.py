"""Canonical product specification keys for deterministic validation."""

from enum import StrEnum


class SpecKey(StrEnum):
    OUTPUT_VOLTAGE = "output_voltage"
    OUTPUT_CURRENT_MAX = "output_current_max"
    INPUT_VOLTAGE = "input_voltage"
    MOUNTING = "mounting"
    IP_RATING = "ip_rating"
    ETHERNET_PORTS = "ethernet_ports"
    SUPPORTS_MODBUS_TCP = "supports_modbus_tcp"
    OPERATING_TEMP_MIN = "operating_temp_min"
    OPERATING_TEMP_MAX = "operating_temp_max"
    DIN_RAIL_MOUNTABLE = "din_rail_mountable"


ALL_SPEC_KEYS: frozenset[str] = frozenset(key.value for key in SpecKey)
