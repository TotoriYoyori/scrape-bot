# YETL

YETL is a small ETL framework for building data transformation pipelines with
plain Python functions. It is pronounced like "Yee-tle".

It is designed for data engineers who like pandas, but do not want production
cleaning logic to become a long notebook cell that nobody wants to touch again.

The core idea is simple:

1. 🏭 A step factory creates a transformation step.
2. 📦 A step receives a `pandas.DataFrame`.
3. ✨ A step returns a new `pandas.DataFrame`.
4. 🚆 `transform_data()` runs the steps in order.

This gives you the directness of pandas, but with a structure that reads like a
pipeline instead of a pile of operations.

## Extract Framework ⚡

Before data can be transformed, it has to arrive.

YETL's extract layer is built for I/O-bound work: APIs, files, browsers,
databases, and object stores. Instead of waiting through a long serial request
chain, extract functions can split work into chunks, run batches concurrently,
pause when the source needs breathing room, and combine the results into one
DataFrame.

```python
offset_checkpoints = range(0, seed_limit, chunk_limit)
all_results = []

async with AsyncClient() as client:
    for batch in batched(offset_checkpoints, concurrent_batch_limit):
        async with asyncer.create_task_group() as tg:
            tasks = [
                tg.soonify(_fetch_api_page)(
                    client,
                    data_source_url,
                    offset,
                    chunk_limit,
                )
                for offset in batch
            ]

        all_results.extend(tasks)
        await asyncio.sleep(sleep_dur)

df = pd.concat((task.value for task in all_results), ignore_index=True)
```

Fast extraction should still have a contract. YETL validates extract settings
with Pydantic before request fan-out starts. That contract can check things
like:

- the source URL has the expected shape
- requested record counts are positive
- per-request chunk sizes stay within source limits
- concurrency stays within a safe range
- pauses between batches stay reasonable

The result is an extract layer that can be fast without being reckless.

## Transform Pipelines 🚆

In YETL, a pipeline is just a list of callables.

```python
import pandas as pd

from yetl.transform import (
    DateTransform,
    DTypeTransform,
    NullTransform,
    StringTransform,
    transform_data,
)


steps = [
    NullTransform.nullify_value({
        "status": "UNKNOWN",
        "created_date": "",
    }),
    DateTransform.parse_date_columns({
        "created_date": "%Y-%m-%d",
    }),
    StringTransform.normalize_trim_case({
        "title": ["city", "street_name"],
        "capitalize": ["status"],
    }),
    DTypeTransform.upgrade_dtype(),
    DTypeTransform.cast_categorical(pct_threshold=0.05),
]

df = pd.read_csv("dirty.csv")
clean_df = transform_data(steps, df)
```

There is no hidden pipeline object, no class to instantiate, and no special
runtime. If you know how to call a function with a DataFrame, you already know
the execution model.

## Step Factories 🏭

A step factory is a function that returns a step.

For example:

```python
DateTransform.parse_date_columns({
    "created_date": "%Y-%m-%d",
})
```

This does not transform data immediately. It returns a callable that knows how
to transform a DataFrame later, when the pipeline runs.

That callable has this shape:

```python
def step(df: pd.DataFrame) -> pd.DataFrame:
    ...
    return transformed_df
```

This pattern gives you two useful things:

- 🧭 configuration happens once, when you define the pipeline
- ⚙️ execution happens later, when `transform_data()` receives real data

## Why Factories? 🧩

Most DataFrame operations need some configuration.

For example, parsing dates requires column names and date formats. Replacing
null-like values requires knowing which values should become nulls. Converting
low-cardinality strings to categories requires a threshold.

You could write those transformations inline every time. It works, but it tends
to grow into this:

```python
df = pd.read_csv("dirty.csv")

df["created_date"] = pd.to_datetime(
    df["created_date"].str.slice(0, 10),
    format="%Y-%m-%d",
    errors="coerce",
)

df["status"] = df["status"].replace("UNKNOWN", None)
df["city"] = df["city"].astype("string").str.strip().str.title()
df["street_name"] = df["street_name"].astype("string").str.strip().str.title()
df["amount"] = df["amount"].astype("Float64")

low_cardinality_columns = []
for column in df.columns:
    if df[column].dtype in ["str", "string", "object"]:
        non_null_count = df[column].notna().sum()
        unique_count = df[column].nunique()
        if non_null_count and unique_count / non_null_count <= 0.05:
            low_cardinality_columns.append(column)

df = df.astype({
    column: "category"
    for column in low_cardinality_columns
})
```

That code is not wrong. But the business intent is buried inside mechanics:
slicing, coercing, replacing, trimming, looping, calculating ratios, and
casting.

With YETL step factories, the same kind of work reads like a recipe:

```python
steps = [
    NullTransform.nullify_value({"status": "UNKNOWN"}),
    DateTransform.parse_date_columns({"created_date": "%Y-%m-%d"}),
    StringTransform.normalize_trim_case({
        "title": ["city", "street_name"],
    }),
    DTypeTransform.upgrade_dtype(),
    DTypeTransform.cast_categorical(pct_threshold=0.05),
]
```

The implementation details still live in normal Python code, but the pipeline
itself is declarative, scannable, and reviewable. That matters when ETL leaves
the notebook and becomes something your team has to run, debug, and trust.

## The Orchestrator 🚆

`transform_data()` is intentionally small.

```python
def transform_data(steps, df):
    for step in steps:
        df = step(df)

    return df
```

That is the whole contract. It does not inspect the DataFrame. It does not know
what a "date transform" or a "string transform" is. It simply applies each step
in order and passes the result to the next one.

This is why YETL can stay lightweight. The orchestration model is boring on
purpose, because the interesting part is the clarity of the pipeline.

## Transform Domains 🗂️

YETL groups step factories by domain.

```python
from yetl.transform import (
    DateTransform,
    DTypeTransform,
    NullTransform,
    SimpleTransform,
    StringTransform,
)
```

Each domain is a collection of related step factories.

### `SimpleTransform` 🧰

Small wrappers around common DataFrame operations.

Examples:

- drop columns
- reset the index
- rename columns
- cast specific columns
- fill nulls
- rename columns by string replacement

### `NullTransform` 🕳️

Operations for handling missing or invalid values.

Examples:

- replace column-specific null-like values
- nullify values outside an allowed numeric range
- drop rows based on null percentage thresholds

### `DateTransform` 📅

Operations for date and time parsing.

Examples:

- parse date columns with explicit formats
- parse military time values into timedeltas
- combine date and time columns into one datetime column

### `StringTransform` 🔤

Operations for string cleanup and normalization.

Examples:

- normalize repeated whitespace
- trim and normalize casing
- merge multiple string columns
- replace values in one column

### `DTypeTransform` 🧬

Operations for dtype cleanup.

Examples:

- upgrade pandas dtypes to nullable native dtypes
- cast low-cardinality string columns to categories

## Discovering Steps 🔎

Each transform domain inherits from `TransformStepCollection`.

That means each domain can describe itself:

```python
StringTransform.methods()
```

```python
StringTransform.help()
```

```python
StringTransform.describe("normalize_trim_case")
```

This is useful while exploring a dataset in a notebook or building a new
pipeline. You do not have to keep every available step in your head. The
framework can tell you what it knows how to do.

## Why This Works Better For ETL ⚡

Traditional ETL code often starts simple:

```python
df = extract()
df = clean(df)
load(df)
```

Then the real world arrives.

Dates come in multiple formats. Nulls are encoded as strings. Categories need
stable dtypes. Text fields need cleanup. One source adds a new column. Another
source changes a label. The pipeline still "works", but nobody is fully sure
which part did what.

YETL tries to keep that complexity visible. The pipeline is not a black box. It
is a list. The steps are not magic. They are callables. The domains are not
arbitrary. They map to the kind of cleanup data engineers already think about:
nulls, dates, strings, dtypes, and simple DataFrame operations.

That gives you a practical middle ground:

- 🐼 keep pandas as the data engine
- 🧱 keep transformations modular
- 👀 make pipelines readable in code review
- 🧪 make steps testable without running the whole ETL job
- 🧭 keep one-off source logic out of the general framework

It is not trying to replace pandas. It is trying to make pandas pipelines easier
to ship.

## FastAPI-Inspired Design Mindset 🚀

YETL borrows from the design mindset that makes FastAPI productive: normal
Python functions, explicit types and validation, async-friendly I/O where it
matters, and a user-facing API that stays direct.

For ETL, that means keeping extraction fast and validation close to the system
boundary. Once data is in a DataFrame, YETL keeps transform steps ordinary and
synchronous, because pandas work is clearest as plain local Python.

It also means treating pipeline failures as data contract failures. A page
changed, a CSV introduced a new null marker, a column is missing, or a numeric
field now contains text. YETL leans on Pydantic-style validation for settings,
records, and source schemas, then uses explicit transform steps for DataFrame
cleanup. The goal is not to hide bad data. The goal is to make assumptions
visible, close to the code that depends on them.

A data engineer should be able to open a pipeline and quickly answer: What
columns are parsed as dates? What values are treated as nulls? When are dtypes
upgraded? Which string columns are normalized? That is the real productivity
win: clearer code in the places that change the most.

## Public API 📦

The transform package exports the main pieces directly:

```python
from yetl.transform import (
    DateTransform,
    DTypeTransform,
    NullTransform,
    SimpleTransform,
    StringTransform,
    TransformStepCollection,
    transform_data,
)
```

For most transform work, this is the only import you need.
