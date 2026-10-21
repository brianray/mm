from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

django = pytest.importorskip("django")

from django.conf import settings  # noqa: E402

if not settings.configured:
    settings.configure(
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes"],
        USE_TZ=False,
    )
    django.setup()

from django.db import connection, models  # noqa: E402

import mm  # noqa: E402
from mm import types as t  # noqa: E402
from mm.contrib.django import DjangoDataModel, DjangoGrid  # noqa: E402

from .helpers import sheet_values  # noqa: E402


class Author(models.Model):
    name = models.CharField(max_length=50)

    class Meta:
        app_label = "marmir_test"

    def __str__(self):
        return self.name


class AllBaseTypes(models.Model):
    BooleanField = models.BooleanField(default=False)
    CharField = models.CharField(max_length=50, verbose_name="Char field")
    DateField = models.DateField()
    DateTimeField = models.DateTimeField()
    DecimalField = models.DecimalField(max_digits=10, decimal_places=2)
    EmailField = models.EmailField()
    FloatField = models.FloatField()
    IntegerField = models.IntegerField()
    GenericIPAddressField = models.GenericIPAddressField()
    PositiveIntegerField = models.PositiveIntegerField()
    BigIntegerField = models.BigIntegerField()
    TextField = models.TextField()
    TimeField = models.TimeField()
    DurationField = models.DurationField()
    URLField = models.URLField()
    FileField = models.FileField(blank=True)
    null_char = models.CharField(max_length=10, null=True, blank=True)
    author = models.ForeignKey(Author, null=True, on_delete=models.SET_NULL)

    class Meta:
        app_label = "marmir_test"


@pytest.fixture(scope="module")
def queryset():
    with connection.schema_editor() as editor:
        editor.create_model(Author)
        editor.create_model(AllBaseTypes)
    author = Author.objects.create(name="Brian")
    for i in range(2):
        AllBaseTypes.objects.create(
            BooleanField=bool(i),
            CharField=f"row {i}",
            DateField=dt.date(2024, 1, 1 + i),
            DateTimeField=dt.datetime(2024, 1, 1, 12),
            DecimalField=Decimal("1.25"),
            EmailField="a@b.c",
            FloatField=1.5,
            IntegerField=i,
            GenericIPAddressField="127.0.0.1",
            PositiveIntegerField=3,
            BigIntegerField=10**12,
            TextField="text",
            TimeField=dt.time(8),
            DurationField=dt.timedelta(hours=1),
            URLField="https://example.com",
            author=author if i else None,
        )
    return AllBaseTypes.objects.order_by("id")


def test_django_document(queryset):
    doc = mm.Document(queryset, data_model_class=DjangoDataModel, grid_class=DjangoGrid)
    headers = dict(zip(doc.data_model.field_titles, doc.data_model.field_headers))
    assert headers["id"] is t.IntFieldType
    assert headers["BooleanField"] is t.BoolFieldType
    assert headers["DateTimeField"] is t.DateTimeFieldType
    assert headers["DateField"] is t.DateFieldType
    assert headers["DecimalField"] is t.DecimalFieldType
    assert headers["TimeField"] is t.TimeFieldType
    assert headers["DurationField"] is t.DurationFieldType
    assert headers["URLField"] is t.URLFieldType
    assert headers["FileField"] is t.NoneFieldType
    assert headers["author"] is t.StringFieldType
    values = sheet_values(doc.writestr())
    assert len(values) == 3
    row = dict(zip(values[0], values[2]))
    assert row["CharField"] == "row 1"
    assert row["author"] == "Brian"
    assert row["null_char"] is None


def test_django_order_types_and_verbose_names(queryset):
    doc = mm.Document(
        queryset,
        data_model_class=DjangoDataModel,
        grid_class=DjangoGrid,
        order=["CharField", "IntegerField"],
        column_types={"IntegerField": "string"},
    )
    assert doc.data_model.field_titles == ["CharField", "IntegerField"]
    assert doc.rows == [["row 0", "0"], ["row 1", "1"]]
    model = DjangoDataModel(queryset, order=["CharField"], verbose_names=True)
    assert model.field_titles == ["Char field"]
    with pytest.raises(ValueError, match="unknown field"):
        DjangoDataModel(queryset, order=["nope"])


def test_django_values_queryset_uses_default_model(queryset):
    doc = mm.Document(queryset.values("CharField", "IntegerField"))
    assert doc.rows == [["row 0", 0], ["row 1", 1]]


def test_django_list_of_instances(queryset):
    model = DjangoDataModel(list(queryset))
    assert "CharField" in model.field_titles
    with pytest.raises(mm.EmptyDataError):
        DjangoDataModel([])
