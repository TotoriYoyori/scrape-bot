from __future__ import annotations

import csv
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Iterable

from src.scraper.primitives import ScrapeBotModule
from src.scraper.writer.settings import writer_settings


class CsvWriterModule(ScrapeBotModule):
    """Generic CSV writer module used by scrape routines."""

    name = "writer"

    def __init__(
        self,
        output_path: str | Path | None = None,
        *,
        fieldnames: list[str] | None = None,
    ) -> None:
        self.output_path = Path(output_path or writer_settings.output_path)
        self.fieldnames = fieldnames
        self.header_written = False
        self.records_written = 0

    def write(
        self,
        records: Iterable[Any],
        *,
        fieldnames: list[str] | None = None,
    ) -> bool:
        rows = [self._to_row(record) for record in records]
        if not rows:
            return True

        columns = fieldnames or self.fieldnames or list(rows[0].keys())
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.output_path, "a", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
            if not self.header_written:
                writer.writeheader()
                self.header_written = True
            writer.writerows(rows)

        self.records_written += len(rows)
        return True

    @staticmethod
    def _to_row(record: Any) -> dict[str, Any]:
        if isinstance(record, dict):
            return record
        if is_dataclass(record):
            return asdict(record)
        if hasattr(record, "model_dump"):
            return record.model_dump()
        raise TypeError(f"Unsupported CSV record type: {type(record)!r}")


# =============== MODULE FACTORY ACCESSOR ===============
def create_csv_writer(
    output_path: str | Path | None = None,
    *,
    fieldnames: list[str] | None = None,
) -> CsvWriterModule:
    return CsvWriterModule(
        output_path,
        fieldnames=fieldnames,
    )
