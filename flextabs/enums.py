from enum import Enum


class TabPosition(Enum):
    """Tab opener positions."""

    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"


class CloseMode(Enum):
    """Tab closing behavior modes."""

    ACTIVE_ONLY = "active_only"
    ANY_VISIBLE = "any_visible"
    BOTH = "both"


class CloseConfirmationType(Enum):
    """Types of close confirmation dialogs."""

    NONE = "none"
    YESNO = "yesno"
    WARNING = "warning"
    INFO = "info"
