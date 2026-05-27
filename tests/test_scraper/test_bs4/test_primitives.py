import pytest
from pydantic import BaseModel

from src.scraper.routines.audible.schema import BookRecord
from src.scraper.bs4 import (
    BS4RecordSchema,
    BS4Locator,
    BS4TextField
)

# =============== TESTING COLLECTIONS ===============
class TestBS4RecordSchema:

    @staticmethod
    def test_happy_load() -> None:
        happy_schema = {
            "record_container": BS4Locator(selector=".fake"),
            "model": BookRecord,
            "skip_if_missing": ("name",),
            "fields": {
                "name": BS4TextField(locator=BS4Locator(selector="h3")),
                "author": BS4TextField(locator=BS4Locator(selector=".author")),
                "price": BS4TextField(locator=BS4Locator(selector=".price")),
            }
        }
        happy_schema = BS4RecordSchema.model_validate(happy_schema)

        assert happy_schema.fields.keys() == {"name", "author", "price"}
        assert set(happy_schema.skip_if_missing).issubset(happy_schema.target_model_fields)
        assert set(happy_schema.fields.keys()).issubset(happy_schema.target_model_fields)


    @staticmethod
    def test_skip_if_missing_invalid() -> None:
        invalid_schema = {
            "record_container": BS4Locator(selector=".fake"),
            "model": BookRecord,
            "skip_if_missing": ("i always feel like", "somebody", "is watching me"),
            "fields": {
                "name": BS4TextField(locator=BS4Locator(selector="h3")),
                "author": BS4TextField(locator=BS4Locator(selector=".author")),
                "price": BS4TextField(locator=BS4Locator(selector=".price")),
            }
        }

        with pytest.raises(ValueError):
            BS4RecordSchema.model_validate(invalid_schema)

    @staticmethod
    def test_fields_invalid() -> None:
        invalid_schema = {
            "record_container": BS4Locator(selector=".fake"),
            "model": BookRecord,
            "skip_if_missing": ("i always feel like", "somebody", "is watching me"),
            "fields": {
                "i always feel like": BS4TextField(locator=BS4Locator(selector="h3")),
                "somebody is": BS4TextField(locator=BS4Locator(selector=".author")),
                "watching me": BS4TextField(locator=BS4Locator(selector=".price")),
            }
        }

        with pytest.raises(ValueError):
            BS4RecordSchema.model_validate(invalid_schema)

    @staticmethod
    def test_adaptable_with_other_models() -> None:
        class OtherModel(BaseModel):
            i_always_feel_like: str
            somebody: str
            is_watching_me: str

        other_schema = {
            "record_container": BS4Locator(selector=".fake"),
            "model": OtherModel,
            "skip_if_missing": ("i_always_feel_like", "somebody"),
            "fields": {
                "i_always_feel_like": BS4TextField(locator=BS4Locator(selector="h3")),
                "somebody": BS4TextField(locator=BS4Locator(selector=".author")),
            }
        }
        other_schema = BS4RecordSchema.model_validate(other_schema)

        assert set(other_schema.fields) == {
            "i_always_feel_like",
            "somebody",
        }
        assert set(other_schema.skip_if_missing).issubset(other_schema.target_model_fields)
        assert set(other_schema.fields.keys()).issubset(other_schema.target_model_fields)
