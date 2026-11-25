"""Compare synthetic site KPIs before and after a planned change."""
import argparse
import csv
import json
from fractions import Fraction


def read_sites(path):
    sites = {}
    with open(path, newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        required = {"site_id", "window_minutes", "attempts", "successes", "median_latency_ms"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("Missing KPI columns")
        for row in reader:
            site = row["site_id"]
            window, attempts, successes, latency = (
                int(row[name]) for name in ("window_minutes", "attempts", "successes", "median_latency_ms")
            )
            if not site or site in sites or window <= 0 or not 0 <= successes <= attempts or latency < 0:
                raise ValueError(f"Invalid or duplicate KPI row for {site!r}")
            sites[site] = dict(window_minutes=window, attempts=attempts,
                               successes=successes, median_latency_ms=latency)
    return sites


def rate(successes, attempts):
    return Fraction(100 * successes, attempts) if attempts else None


def totals(rows):
    attempts = sum(row["attempts"] for row in rows.values())
    successes = sum(row["successes"] for row in rows.values())
    value = rate(successes, attempts)
    return dict(attempts=attempts, successes=successes,
                success_pct=float(value) if value is not None else None)


def compare(before, after, policy):
    minimum = policy["minimum_attempts"]
    threshold = Fraction(str(policy["rollback_drop_pp"]))
    if type(minimum) is not int or minimum <= 0 or not 0 < threshold <= 100:
        raise ValueError("Invalid lab thresholds")
    severity = {"pass": 0, "review": 1, "rollback recommendation": 2}
    decisions = []
    for site in sorted(before.keys() | after.keys()):
        left, right = before.get(site), after.get(site)
        entry = dict(site_id=site, before=left, after=right, change_pp=None)
        if left is None or right is None:
            decision, reason = "review", "missing site"
        elif left["window_minutes"] != right["window_minutes"]:
            decision, reason = "review", "incompatible window durations"
        elif min(left["attempts"], right["attempts"]) < minimum:
            decision, reason = "review", "insufficient attempts"
        else:
            previous = rate(left["successes"], left["attempts"])
            current = rate(right["successes"], right["attempts"])
            entry.update(before_pct=float(previous), after_pct=float(current),
                         change_pp=float(current - previous))
            if previous - current >= threshold:
                decision, reason = "rollback recommendation", "site drop meets rollback threshold"
            else:
                decision, reason = "pass", "site drop below rollback threshold"
        decisions.append(dict(entry, decision=decision, reason=reason))
    overall = max((entry["decision"] for entry in decisions), key=severity.get, default="review")
    return dict(change_id=policy["change_id"], rollback_drop_pp=float(threshold),
                minimum_attempts=minimum, decision=overall,
                before_totals=totals(before), after_totals=totals(after), sites=decisions)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("before", "after", "policy"):
        parser.add_argument(name)
    args = parser.parse_args()
    try:
        with open(args.policy, encoding="utf-8") as source:
            config = json.load(source)
        print(json.dumps(compare(read_sites(args.before), read_sites(args.after), config), indent=2))
    except (OSError, TypeError, ValueError, KeyError, ZeroDivisionError) as error:
        parser.exit(2, f"{error}\n")
