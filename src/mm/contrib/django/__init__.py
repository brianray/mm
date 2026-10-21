"""Django integration: build sheets from QuerySets (``pip install 'marmir[django]'``).

Usage::

    from mm.contrib.django import DjangoDataModel, DjangoGrid

    doc = mm.Document(Book.objects.all(), data_model_class=DjangoDataModel,
                      grid_class=DjangoGrid)
"""

from .data_model import DjangoDataModel
from .grid import DjangoGrid

__all__ = ["DjangoDataModel", "DjangoGrid"]
