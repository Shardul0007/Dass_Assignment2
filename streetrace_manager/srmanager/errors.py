"""Domain-specific exceptions for StreetRace Manager."""


class StreetRaceError(Exception):
    """Base exception for StreetRace Manager."""


class NotRegisteredError(StreetRaceError):
    """Raised when an operation requires a registered crew member."""


class BusinessRuleError(StreetRaceError):
    """Raised when a business rule is violated."""


class NotFoundError(StreetRaceError):
    """Raised when an entity (car, member, race, mission) cannot be found."""
