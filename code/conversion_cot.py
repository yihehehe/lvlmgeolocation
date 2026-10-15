#!/usr/bin/env python3
"""
Convert CSV with 'filename' and 'raw_res' columns into a new CSV with
'filename', 'latitude', 'longitude', 'city', 'country', 'continent', 'reasoning'.

Expected raw_res format (case-insensitive, whitespace-tolerant):
    1.LATITUDE: aaa; 2. LONGITUDE: bbb; 3. LOCATION: ccc, ddd, eee; 4: REASONING: fff.

The REASONING field is optional — missing rows get an empty string.
"""

import csv
import re
import argparse
from pathlib import Path
from typing import Optional, Union


# Two patterns: with and without REASONING.  Try extended first, fall back to basic.
PATTERN_EXTENDED = re.compile(
    r"1\s*\.\s*LATITUDE\s*:\s*([^;]+?)\s*;\s*"
    r"2\s*\.\s*LONGITUDE\s*:\s*([^;]+?)\s*;\s*"
    r"3\s*\.\s*LOCATION\s*:\s*([^,]+?)\s*,\s*([^,]+?)\s*,\s*([^,.]+?)\s*\.?\s*;\s*"
    r"4\s*:?\s*\.?\s*REASONING\s*:\s*(.+?)\s*\.?\s*$",
    re.IGNORECASE,
)

PATTERN_BASIC = re.compile(
    r"1\s*\.\s*LATITUDE\s*:\s*([^;]+?)\s*;\s*"
    r"2\s*\.\s*LONGITUDE\s*:\s*([^;]+?)\s*;\s*"
    r"3\s*\.\s*LOCATION\s*:\s*([^,]+?)\s*,\s*([^,]+?)\s*,\s*([^,.]+?)\s*\.?\s*$",
    re.IGNORECASE,
)


def parse_raw_res(raw: str) -> Optional[dict]:
    """Extract fields from a single raw_res string.  Returns None on failure."""
    if not raw or not isinstance(raw, str):
        return None

    text = raw.strip()

    # Try extended pattern first (includes reasoning)
    m = PATTERN_EXTENDED.search(text)
    if m:
        return {
            "latitude":  m.group(1).strip(),
            "longitude": m.group(2).strip(),
            "city":      m.group(3).strip(),
            "country":   m.group(4).strip(),
            "continent": m.group(5).strip(),
            "reasoning": m.group(6).strip(),
        }

    # Fall back to basic pattern (no reasoning)
    m = PATTERN_BASIC.search(text)
    if m:
        return {
            "latitude":  m.group(1).strip(),
            "longitude": m.group(2).strip(),
            "city":      m.group(3).strip(),
            "country":   m.group(4).strip(),
            "continent": m.group(5).strip(),
            "reasoning": "",
        }

    return None


def convert_csv(
    input_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    *,
    delimiter: str = ",",
) -> Path:
    """Convert *input_path* and write the result.  Returns the output path."""
    input_path = Path(input_path)
    if output_path is None:
        output_path = input_path.with_stem(input_path.stem + "_converted")
    else:
        output_path = Path(output_path)

    with open(input_path, "r", newline="", encoding="utf-8-sig") as fin:
        reader = csv.DictReader(fin, delimiter=delimiter)
        if reader.fieldnames is None:
            raise ValueError(f"Could not read header from {input_path}")

        header_map = {k.strip().lower(): k for k in reader.fieldnames}

        out_fields = [
            "filename", "latitude", "longitude",
            "city", "country", "continent", "reasoning",
        ]
        rows_written = 0
        errors = 0

        with open(output_path, "w", newline="", encoding="utf-8") as fout:
            writer = csv.DictWriter(fout, fieldnames=out_fields)
            writer.writeheader()

            for row in reader:
                filename = row.get(header_map.get("filename", "filename"), "")
                raw_res  = row.get(header_map.get("raw_res", "raw_res"), "")

                parsed = parse_raw_res(raw_res)
                if parsed is None:
                    errors += 1
                    parsed = {
                        "latitude": "", "longitude": "",
                        "city": "", "country": "", "continent": "",
                        "reasoning": "",
                    }

                writer.writerow({
                    "filename":  filename.strip(),
                    "latitude":  parsed["latitude"],
                    "longitude": parsed["longitude"],
                    "city":      parsed["city"],
                    "country":   parsed["country"],
                    "continent": parsed["continent"],
                    "reasoning": parsed["reasoning"],
                })
                rows_written += 1

    print(f"Done.  {rows_written} rows written to {output_path}")
    if errors:
        print(f"  Warning: {errors} row(s) could not be parsed — fields left empty.")
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Convert raw_res CSV (with optional REASONING field) to column-split CSV."
    )
    parser.add_argument("input", help="Path to the input CSV file.")
    parser.add_argument(
        "-o", "--output",
        help="Path to the output CSV file (default: <input>_converted.csv).",
    )
    parser.add_argument(
        "-d", "--delimiter", default=",",
        help="CSV delimiter used in the input file (default: ',').",
    )
    args = parser.parse_args()
    convert_csv(args.input, args.output, delimiter=args.delimiter)


if __name__ == "__main__":
    main()