import io
import json
import unittest
from pathlib import Path

from trace_analysis import analyze

ROOT = Path(__file__).parent


class TraceAnalysisTests(unittest.TestCase):
    def test_checked_in_reports(self):
        for name in ('attach-events', 'examples/answer', 'examples/timeout', 'examples/incomplete', 'examples/retry'):
            with self.subTest(name=name):
                fixture = (ROOT / f'{name}.csv').read_text()
                expected = json.loads((ROOT / f'{name}.json').read_text())
                self.assertEqual(analyze(io.StringIO(fixture)), expected)

    def test_shuffled_rows_and_duplicate_events(self):
        header, *rows = (ROOT / 'attach-events.csv').read_text().splitlines()
        parse = lambda rows: analyze(io.StringIO('\n'.join([header, *rows])))
        self.assertEqual(parse(rows), parse([*reversed(rows), rows[1]]))

    def test_invalid_timestamp(self):
        sample = (ROOT / 'examples/answer.csv').read_text().replace('2026-01-01T09:00:00.020Z', 'bad')
        with self.assertRaisesRegex(ValueError, 'invalid timestamp'):
            analyze(io.StringIO(sample))

    def test_answer_with_different_exchange_id_leaves_trace_incomplete(self):
        sample = (ROOT / 'examples/answer.csv').read_text().replace(
            'answer_received,s6a-a01', 'answer_received,another-exchange')
        [exchange] = analyze(io.StringIO(sample))
        self.assertEqual(exchange['status'], 'trace incomplete')
        self.assertIsNone(exchange['terminal_elapsed_ms'])

    def test_retry_exchanges_within_one_attempt_are_independent(self):
        with (ROOT / 'examples/retry.csv').open() as source:
            first, retry = analyze(source)
        self.assertEqual((first['exchange_id'], first['status']), ('s6a-first', 'timeout observed'))
        self.assertEqual((retry['exchange_id'], retry['status']), ('s6a-retry', 'answer observed'))
        self.assertEqual(first['request_to_terminal_ms'], 1180)
        self.assertEqual(retry['request_to_terminal_ms'], 25)
