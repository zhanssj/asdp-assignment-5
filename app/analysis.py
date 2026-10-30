"""Bounded CSV parsing and descriptive statistics independent of HTTP."""
import csv
import hashlib
import io
import math
import re
import statistics
from dataclasses import dataclass

MAX_BYTES = 5 * 1024 * 1024
MAX_ROWS = 10_000
MAX_COLUMNS = 50
MAX_FIELD = 2_000
DECIMAL = re.compile(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?\Z')
csv.field_size_limit(MAX_FIELD + 1)


class DataError(ValueError):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True)
class Dataset:
    columns: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    sha256: str


def number(text):
    if not DECIMAL.fullmatch(text):
        return None
    value = float(text)
    return value if math.isfinite(value) else None


def parse_csv(content: bytes) -> Dataset:
    if len(content) > MAX_BYTES:
        raise DataError('The CSV must not exceed 5 MiB.', 413)
    if not content:
        raise DataError('Choose a non-empty CSV file.')
    try:
        text = content.decode('utf-8-sig')
    except UnicodeDecodeError as exc:
        raise DataError('The CSV must use UTF-8 encoding.') from exc
    if '\x00' in text:
        raise DataError('NUL characters are not allowed in CSV data.')
    records = []
    try:
        for row in csv.reader(io.StringIO(text, newline=''), strict=True):
            if not row:  # Empty physical lines do not count as logical records.
                continue
            if len(row) > MAX_COLUMNS:
                raise DataError('The CSV must not exceed 50 columns.')
            if any(len(field) > MAX_FIELD for field in row):
                raise DataError('CSV fields must not exceed 2,000 characters.')
            records.append(tuple(field.strip() for field in row))
            if len(records) > MAX_ROWS + 1:
                raise DataError('The CSV must not exceed 10,000 data records.')
    except csv.Error as exc:
        raise DataError('Malformed CSV or a field exceeds the size limit.') from exc
    if not records:
        raise DataError('The CSV needs a header and at least one data record.')
    columns = records[0]
    if any(not c for c in columns) or len(set(columns)) != len(columns):
        raise DataError('CSV headers must be nonblank and unique after trimming.')
    if len(records) == 1:
        raise DataError('The CSV needs at least one data record.')
    for record, row in enumerate(records[1:], 2):
        if len(row) != len(columns):
            raise DataError(f'CSV record {record} has {len(row)} fields; expected {len(columns)}.')
    return Dataset(columns, tuple(records[1:]), hashlib.sha256(content).hexdigest())


def preview(dataset: Dataset, filename: str) -> dict:
    numeric = []
    for index, column in enumerate(dataset.columns):
        values = [row[index] for row in dataset.rows if row[index]]
        if values and all(number(v) is not None for v in values):
            numeric.append(column)
    return dict(filename=filename, columns=list(dataset.columns), numericColumns=numeric,
                rowCount=len(dataset.rows), previewRows=[list(r) for r in dataset.rows[:20]],
                sha256=dataset.sha256)


def calculate(values: list[float]) -> dict:
    if not values:
        raise DataError('The selected column contains no measurements.')
    try:
        # statistics.mean and stdev use accurate intermediate arithmetic.
        ordered = sorted(values)
        n = len(ordered)
        # Half first: averaging two large same-sign middle values must not overflow.
        if n % 2:
            median = ordered[n // 2]
        else:
            a, b = ordered[n // 2 - 1], ordered[n // 2]
            median = a + (b - a) / 2 if (a >= 0) == (b >= 0) else a / 2 + b / 2
        result = dict(count=n, minimum=min(values), maximum=max(values),
                      mean=float(statistics.mean(values)), median=median,
                      sampleStandardDeviation=statistics.stdev(values) if n > 1 else None)
        if any(v is not None and not math.isfinite(v) for v in result.values()):
            raise OverflowError
        return result
    except (OverflowError, ValueError) as exc:
        raise DataError('The statistics exceed the supported finite number range.') from exc


def analyze(dataset: Dataset, filename: str, column: str, unit: str, version: str) -> dict:
    if column not in dataset.columns:
        raise DataError('Select a column that exists in the CSV header.')
    unit = unit.strip()
    if len(unit) > 32 or any(ord(c) < 32 or 127 <= ord(c) <= 159 for c in unit):
        raise DataError('The unit must be at most 32 characters and contain no control characters.')
    index = dataset.columns.index(column)
    measurements = []
    for record, row in enumerate(dataset.rows, 2):
        text = row[index]
        if not text:
            continue
        value = number(text)
        if value is None:
            raise DataError(f"CSV record {record} in column '{column}' is not a finite decimal number.")
        measurements.append(dict(recordNumber=record, value=value))
    return dict(filename=filename, column=column, unit=unit, totalRows=len(dataset.rows),
                excludedBlankValues=len(dataset.rows) - len(measurements),
                statistics=calculate([m['value'] for m in measurements]),
                measurements=measurements, inputSha256=dataset.sha256, applicationVersion=version,
                standardDeviationMethod='sample (n - 1)',
                missingValuePolicy='exclude blank values; reject invalid nonblank values')
