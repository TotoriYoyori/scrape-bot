from typing import Annotated

from pydantic import BaseModel, Field, field_validator, ValidationInfo


# =============== VALIDATION CONFIG OBJECT FOR EXTRACT ===============
class ExtractCSVSettings(BaseModel):
    data_source_url: str
    offset: int
    seed_limit: Annotated[int, Field(gt=0)]
    chunk_limit: Annotated[int, Field(gt=0, le=1_000, validate_default=True)]
    concurrent_batch_limit: Annotated[int, Field(gt=0, le=50)]
    sleep_dur: Annotated[float, Field(ge=1.0, le=10.0)]

    @field_validator("data_source_url")
    @classmethod
    def validate_data_source_url(cls, value: str) -> str:
        if not value.endswith(".csv"):
            raise ValueError("data_source_url must end with '.csv'.")

        return value

    @field_validator("chunk_limit")
    @classmethod
    def validate_chunk_limit(cls, value: int, info: ValidationInfo) -> int:
        seed_limit = info.data.get("seed_limit")
        if seed_limit is None:
            return value

        if value > seed_limit:
            raise ValueError(
                f"chunk_limit ({value}) cannot exceed seed_limit ({seed_limit}). "
                f"Either lower chunk_limit or raise seed_limit."
            )

        return value
