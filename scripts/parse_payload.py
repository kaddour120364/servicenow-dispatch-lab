#!/usr/bin/env python3
"""
parse_payload.py - Reads the workflow_dispatch event, validates the
{name, country} inputs and writes them to a JSON file.

In GitHub Actions, the full event is in the file $GITHUB_EVENT_PATH.
Locally, pass a sample event:  --event-file sample_event.json
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

MAX_LEN = 100


def load_event(event_file):
    path = event_file or os.environ.get("GITHUB_EVENT_PATH")
    if not path:
        sys.exit("No event: set GITHUB_EVENT_PATH or use --event-file")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def clean(field, value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"'{field}' is missing or empty")
    value = value.strip()
    if len(value) > MAX_LEN:
        raise ValueError(f"'{field}' is longer than {MAX_LEN} characters")
    return value


def parse_payload(event):
    """Return the normalized document written to the JSON file."""
    inputs = event.get("inputs") or {}
    return {
        "name": clean("name", inputs.get("name")),
        "country": clean("country", inputs.get("country")),
        "received_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "event": os.environ.get("GITHUB_EVENT_NAME", "workflow_dispatch"),
            "repository": (event.get("repository") or {}).get("full_name"),
            "ref": event.get("ref"),
            # With a GitHub App token the sender is "<app-slug>[bot]"
            "sender": (event.get("sender") or {}).get("login"),
            "run_id": os.environ.get("GITHUB_RUN_ID"),
        },
    }


def write_summary(doc):
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write("### Payload received from ServiceNow\n\n")
            f.write(f"| Field | Value |\n|---|---|\n")
            f.write(f"| name | {doc['name']} |\n| country | {doc['country']} |\n")
            f.write(f"| sender | {doc['source']['sender']} |\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--event-file", help="local event JSON (for testing)")
    parser.add_argument("--output", default="payload.json")
    args = parser.parse_args()

    try:
        doc = parse_payload(load_event(args.event_file))
    except ValueError as err:
        sys.exit(f"Invalid payload: {err}")

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
    write_summary(doc)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
