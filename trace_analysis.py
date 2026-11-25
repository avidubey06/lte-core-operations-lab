"""Summarize the S6a exchanges seen in a synthetic LTE event capture."""
import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime, timezone

REQUEST = "authentication_information_request_sent"
TERMINAL = {
    "authentication_information_answer_received": "answer observed",
    "authentication_information_timeout": "timeout observed",
}
FIELDS = ("attempt_id", "timestamp_utc", "component", "event", "exchange_id")


def read_events(source):
    reader = csv.DictReader(source)
    if not set(FIELDS).issubset(reader.fieldnames or []):
        raise ValueError("Missing required trace columns")
    attempts = defaultdict(set)
    for line, row in enumerate(reader, 2):
        attempt, stamp, component, event, exchange = (row[key] for key in FIELDS)
        try:
            timestamp = datetime.fromisoformat((stamp or "").replace("Z", "+00:00"))
            if timestamp.utcoffset() is None:
                raise ValueError("timestamp needs a UTC offset")
            timestamp = timestamp.astimezone(timezone.utc)
        except ValueError as error:
            raise ValueError(f"Line {line}: invalid timestamp {stamp!r}") from error
        if not all((attempt, component, event)) or exchange is None:
            raise ValueError(f"Line {line}: missing event fields")
        if (event == REQUEST or event in TERMINAL) and not exchange:
            raise ValueError(f"Line {line}: missing S6a exchange ID")
        attempts[attempt].add((timestamp, component, event, exchange))
    return attempts


def milliseconds(end, start):
    delta = end - start
    return (delta.days * 86400000000 + delta.seconds * 1000000 + delta.microseconds) / 1000


def analyze(source):
    result = []
    for attempt, events in sorted(read_events(source).items()):
        timeline = sorted(events)
        start = timeline[0][0]
        by_exchange = defaultdict(list)
        for timestamp, component, event, exchange in timeline:
            if component == "MME" and (event == REQUEST or event in TERMINAL):
                by_exchange[exchange].append((timestamp, event))
        for exchange, messages in sorted(by_exchange.items()):
            requests = [time for time, event in messages if event == REQUEST]
            if not requests:
                continue
            if len(requests) != 1:
                raise ValueError(f"{attempt}/{exchange}: repeated request with distinct timestamps")
            request = requests[0]
            replies = sorted((time, event) for time, event in messages
                             if event in TERMINAL and time >= request)
            if len(replies) > 1 and replies[0][0] == replies[1][0]:
                raise ValueError(f"{attempt}/{exchange}: ambiguous first terminal event")
            terminal, event = replies[0] if replies else (None, None)
            result.append({
                "attempt_id": attempt,
                "exchange_id": exchange,
                "status": TERMINAL.get(event, "trace incomplete"),
                "request_elapsed_ms": milliseconds(request, start),
                "terminal_elapsed_ms": milliseconds(terminal, start) if terminal else None,
                "request_to_terminal_ms": milliseconds(terminal, request) if terminal else None,
            })
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace_csv")
    args = parser.parse_args()
    try:
        with open(args.trace_csv, newline="", encoding="utf-8") as source:
            print(json.dumps(analyze(source), indent=2))
    except (OSError, ValueError) as error:
        parser.exit(2, f"{error}\n")


if __name__ == "__main__":
    main()
