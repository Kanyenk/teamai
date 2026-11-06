"""Génération d'étiquettes code-barres (SVG)."""
from __future__ import annotations

import io

import barcode
from barcode.writer import SVGWriter


def generate_label_svg(code: str, barcode_type: str = "ean13") -> str:
    """Génère une étiquette SVG pour un code-barres.

    Lève une exception si le type ou le code est invalide.
    """
    cls = barcode.get_barcode_class(barcode_type)
    buffer = io.BytesIO()
    cls(code, writer=SVGWriter()).write(buffer)
    return buffer.getvalue().decode("utf-8")
