import csv
from typing import Iterable

from pydantic import BaseModel

from src.scraper.primitives import ScrapeBotModule
from src.scraper.writer.settings import CsvWriterConfig


class CsvWriterModule(ScrapeBotModule):
    """Generic CSV writer module used by scrape routines."""

    name = "writer"

    def __init__(self, config: CsvWriterConfig | None = None) -> None:
        self.config = config or CsvWriterConfig()

    def write(self, records: Iterable[BaseModel]) -> int:
        records = list(records)
        if not records:
            return 0

        record_type = type(records[0])
        columns = list(record_type.model_fields)
        rows = [record.model_dump(mode="json") for record in records]
        output_path = self.config.OUTPUT_PATH
        output_path.parent.mkdir(parents=True, exist_ok=True)
        write_header = not output_path.exists() or output_path.stat().st_size == 0

        with open(output_path, "a", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
            if write_header:
                writer.writeheader()

            writer.writerows(rows)

        return len(rows)
