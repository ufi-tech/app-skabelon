"""Stien til roden af repoet.

Den ligger i sin egen fil og ikke i en conftest: der er en conftest i api/tests/ i
forvejen, og to filer med samme navn og uden pakke ville skygge for hinanden, når
pytest samler begge mapper op.
"""

from __future__ import annotations

from pathlib import Path

#: Roden af repoet. Prøverne kører med arbejdsmappe api/, så stien regnes ud og gættes ikke.
REPO = Path(__file__).resolve().parents[1]
