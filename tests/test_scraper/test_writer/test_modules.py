import csv

from pydantic import BaseModel

from src.scraper.writer import CsvWriterConfig, CsvWriterModule


class ExampleRecord(BaseModel):
    title: str
    author: str | None


def test_csv_writer_writes_pydantic_records(tmp_path) -> None:
    output_path = tmp_path / "records.csv"
    writer = CsvWriterModule(config=CsvWriterConfig(OUTPUT_PATH=output_path))

    rows_written = writer.write(
        [
            ExampleRecord(title="Book One", author="Author One"),
            ExampleRecord(title="Book Two", author=None),
        ]
    )

    with open(output_path, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))

    assert rows_written == 2
    assert rows == [
        {"title": "Book One", "author": "Author One"},
        {"title": "Book Two", "author": ""},
    ]


def test_csv_writer_appends_without_rewriting_header(tmp_path) -> None:
    output_path = tmp_path / "records.csv"
    writer = CsvWriterModule(config=CsvWriterConfig(OUTPUT_PATH=output_path))

    writer.write([ExampleRecord(title="Book One", author="Author One")])
    writer.write([ExampleRecord(title="Book Two", author="Author Two")])

    assert output_path.read_text(encoding="utf-8").splitlines() == [
        "title,author",
        "Book One,Author One",
        "Book Two,Author Two",
    ]


def test_csv_writer_empty_write_returns_zero(tmp_path) -> None:
    output_path = tmp_path / "records.csv"
    writer = CsvWriterModule(config=CsvWriterConfig(OUTPUT_PATH=output_path))

    assert writer.write([]) == 0
    assert not output_path.exists()
