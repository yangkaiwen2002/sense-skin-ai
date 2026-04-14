"""Inline SVG icon helpers."""


def price_icon(size: int = 16, color: str = "#f0a500") -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'xmlns="http://www.w3.org/2000/svg" style="vertical-align:middle">'
        f'<circle cx="12" cy="12" r="10" stroke="{color}" stroke-width="1.5"/>'
        f'<path d="M12 6v1.5M12 16.5V18M9 9.5h4.5a1.5 1.5 0 0 1 0 3H10.5a1.5 1.5 0 0 0 0 3H15" '
        f'stroke="{color}" stroke-width="1.5" stroke-linecap="round"/>'
        f'</svg>'
    )


def trend_up_icon(size: int = 16, color: str = "#4caf50") -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'xmlns="http://www.w3.org/2000/svg" style="vertical-align:middle">'
        f'<polyline points="23 6 13.5 15.5 8.5 10.5 1 18" stroke="{color}" '
        f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<polyline points="17 6 23 6 23 12" stroke="{color}" '
        f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
        f'</svg>'
    )


def trend_down_icon(size: int = 16, color: str = "#f44336") -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'xmlns="http://www.w3.org/2000/svg" style="vertical-align:middle">'
        f'<polyline points="23 18 13.5 8.5 8.5 13.5 1 6" stroke="{color}" '
        f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<polyline points="17 18 23 18 23 12" stroke="{color}" '
        f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
        f'</svg>'
    )


def score_icon(size: int = 16, color: str = "#4db6d4") -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'xmlns="http://www.w3.org/2000/svg" style="vertical-align:middle">'
        f'<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 '
        f'5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" '
        f'stroke="{color}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>'
        f'</svg>'
    )


def search_icon(size: int = 18, color: str = "#8899aa") -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'xmlns="http://www.w3.org/2000/svg" style="vertical-align:middle">'
        f'<circle cx="11" cy="11" r="8" stroke="{color}" stroke-width="1.8"/>'
        f'<line x1="21" y1="21" x2="16.65" y2="16.65" stroke="{color}" '
        f'stroke-width="1.8" stroke-linecap="round"/>'
        f'</svg>'
    )


def fire_icon(size: int = 14, color: str = "#ff6b35") -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="{color}" '
        f'xmlns="http://www.w3.org/2000/svg" style="vertical-align:middle">'
        f'<path d="M12 2C12 2 8 7 8 12a4 4 0 0 0 8 0c0-2-1-4-1-4s2 2 2 5a6 6 0 0 1-12 0C5 7 12 2 12 2z"/>'
        f'</svg>'
    )
