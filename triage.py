"""Report attach KPIs from anonymized, synthetic LTE attempt records."""
import argparse
import csv
from collections import Counter
from statistics import median

OUTCOMES = {
    "accepted": ("attach_complete", "none"),
    "auth_timeout": ("s6a_auth", "core/authentication"),
    "profile_missing": ("s6a_location_update", "core/subscriber provisioning"),
    "transport_timeout": ("s1_initial_ue", "RAN/transport"),
    "session_timeout": ("s11_create_session", "core/session establishment"),
}


def summarize(path):
    attempts = set()
    successes = []
    failures = Counter()
    with open(path, newline="", encoding="utf-8") as source:
        rows = csv.DictReader(source)
        required = {"attempt_id", "outcome", "stage", "latency_ms"}
        if not required.issubset(rows.fieldnames or ()):
            raise ValueError("Missing required CSV columns")
        for row in rows:
            attempt = row["attempt_id"]
            outcome = row["outcome"]
            if not attempt or attempt in attempts:
                raise ValueError(f"Blank or duplicate attempt ID: {attempt!r}")
            if outcome not in OUTCOMES or row["stage"] != OUTCOMES[outcome][0]:
                raise ValueError(f"Invalid outcome/stage for {attempt}")
            latency = int(row["latency_ms"])
            if latency < 0:
                raise ValueError(f"Negative latency for {attempt}")
            attempts.add(attempt)
            if outcome == "accepted":
                successes.append(latency)
            else:
                failures[outcome] += 1

    print(f"Attempts: {len(attempts)}")
    if attempts:
        print(f"Attach success: {len(successes)}/{len(attempts)} ({len(successes) / len(attempts):.1%})")
    else:
        print("Attach success: n/a")
    typical = f"{median(successes):g} ms" if successes else "n/a"
    print(f"Median successful attach latency: {typical}")
    for reason, count in sorted(failures.items()):
        stage, queue = OUTCOMES[reason]
        print(f"{reason}: {count} | {stage} | first check: {queue}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path")
    args = parser.parse_args()
    try:
        summarize(args.csv_path)
    except (OSError, TypeError, ValueError) as exc:
        parser.exit(2, f"{exc}\n")
