"""Verbatim Ledgeris excerpt for parsing and Romanian number presentation.

The two functions below come from ``accounting/reports.py`` in the private
product repository. Only their standard-library imports and shared zero
constant are included here.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any


ZERO = Decimal("0")


def _decimal(value: Any) -> Decimal:
    """Convert a supported balance value without introducing binary floats."""

    if value is None or value == "":
        return ZERO
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):
        return Decimal(int(value))
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        # Inputs should normally already be Decimal; str() avoids the exact
        # binary representation when an Excel reader supplied a float.
        return Decimal(str(value))
    text = str(value).strip().replace("\u00a0", "").replace(" ", "")
    if not text:
        return ZERO
    negative = text.startswith("(") and text.endswith(")")
    if negative:
        text = text[1:-1]
    # Be liberal with Romanian-formatted strings while keeping ordinary
    # Decimal strings unchanged.
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(",", ".")
    try:
        number = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"Valoare numerică invalidă: {value!r}") from exc
    return -number if negative else number


def _romanian_number(value: Any) -> str:
    text = f"{_decimal(value):,.2f}"
    return text.replace(",", "_").replace(".", ",").replace("_", ".")
