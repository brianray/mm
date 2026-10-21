"""PrettyTable output (``pip install 'marmir[prettytable]'``).

Marmir has a built-in text table format (``format="text"``); this composer is kept for
code that relied on PrettyTable objects.
"""

from .composers import ComposerPrettyTable, pretty_table

__all__ = ["ComposerPrettyTable", "pretty_table"]
