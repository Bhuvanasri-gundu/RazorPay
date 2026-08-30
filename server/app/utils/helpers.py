"""Utility helpers for formatting currency, amounts, and dates."""

def format_currency_inr(amount: float) -> str:
    """Format float amount into INR representation safely for Windows terminal."""
    return f"INR {amount:,.2f}"


def paise_to_inr(paise: int) -> float:
    """Convert paise to INR rupees."""
    return paise / 100.0


def inr_to_paise(inr: float) -> int:
    """Convert INR rupees to paise."""
    return int(round(inr * 100))
