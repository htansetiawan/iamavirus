"""Coverage checks must reject a fresh but incomplete or mixed API snapshot."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from audit_backfill import audit, check_metadata, digest, instant, snapshot_rows


class CoverageChecks(unittest.TestCase):
    def setUp(self):
        self.cutoff = instant('2026-11-06T09:36:00Z')
        self.row = dict(id='abcdefgh', createdAt='2026-11-08T00:00:00Z',
                        white='Other', black='Else', result='1-0', plies=20,
                        whiteVersion=2, blackVersion=3)
        self.old = dict(self.row, id='ijklmnop', createdAt='2026-11-06T09:35:00Z')
        self.pages = [self.page([self.row], None, 'opaque-next'),
                      self.page([self.old], 'opaque-next', 'opaque-later')]

    def page(self, rows, incoming, outgoing):
        url = 'https://6s890.lids.mit.edu/api/games?sort=played&order=desc&limit=100'
        if incoming: url += '&cursor='+incoming
        return dict(fetched=dict(url=url,status=200), payload=dict(games=rows,
                    sort='played',order='desc',nextCursor=outgoing))

    def test_matching_chain_reaches_cutoff(self):
        self.assertEqual(snapshot_rows(self.pages, self.cutoff), [self.row, self.old])

    def test_fresh_timestamp_does_not_prove_coverage(self):
        with self.assertRaisesRegex(ValueError, 'cutoff'):
            snapshot_rows(self.pages[:1], self.cutoff)

    def test_different_cursor_or_filters_rejected(self):
        for suffix in ('&cursor=other-snapshot', '&cursor=opaque-next&player=some-team'):
            pages = deepcopy(self.pages)
            pages[1]['fetched']['url'] = pages[0]['fetched']['url']+suffix
            with self.assertRaisesRegex(ValueError, 'cursor'):
                snapshot_rows(pages, self.cutoff)

    def test_duplicate_game_rejected(self):
        pages = deepcopy(self.pages)
        pages[1]['payload']['games'].insert(0, self.row)
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            snapshot_rows(pages, self.cutoff)

    def test_wrong_version_or_replay_length_rejected(self):
        for field in ('whiteVersion', 'plies'):
            with self.assertRaisesRegex(ValueError, field):
                check_metadata(self.row, dict(self.row, **{field: 999}))
        check_metadata(self.row, dict(self.row, createdAt='2026-11-07T16:00:00-08:00'))

    def fixture(self, root):
        directory, raw = root/'backfill', root/'raw'
        directory.mkdir(); (raw/'games'/'abcdefgh').mkdir(parents=True)
        row = dict(self.row, plies=1)
        pages = deepcopy(self.pages); pages[0]['payload']['games'] = [row]
        for i, page in enumerate(pages, 1):
            (directory/f'page-{i:03}.json').write_text(json.dumps(page))
        plan = dict(source_sha256=digest(Path(__file__).with_name('backfill.py')),
                    cutoff='2026-11-06T09:36:00Z',started='2026-11-08T09:00:00Z')
        (directory/'plan.json').write_text(json.dumps(plan))
        receipt = dict(clean=True, historical_window_traversed=True,
                       reason='cutoff_reached', error=None,
                       counts=dict(pages=2,listed=2,accepted=1,fetch=1,
                                   before_cutoff=1,downloaded=1))
        (directory/'receipt.json').write_text(json.dumps(receipt))
        (directory/'accepted.jsonl').write_text(json.dumps(dict(id='abcdefgh'))+'\n')
        index = dict(row, moves_sha256=hashlib.sha256(b'e2e4').hexdigest())
        (raw/'accepted.jsonl').write_text(json.dumps(index)+'\n')
        replay = dict(row, frames=[dict(move=None),dict(move='e2e4')])
        (raw/'games'/'abcdefgh'/'replay.json').write_text(json.dumps(replay))
        return directory, raw

    def test_every_listed_other_game_must_be_in_archive(self):
        with tempfile.TemporaryDirectory() as temp:
            directory, raw = self.fixture(Path(temp))
            result = audit(directory, raw)
            self.assertEqual(result['other_team_games'], 1)
            (raw/'accepted.jsonl').write_text('')
            with self.assertRaisesRegex(ValueError, 'absent from index'):
                audit(directory, raw)

    def test_stored_content_must_match_acceptance(self):
        with tempfile.TemporaryDirectory() as temp:
            directory, raw = self.fixture(Path(temp))
            path = raw/'games'/'abcdefgh'/'replay.json'
            replay = json.loads(path.read_text()); replay['frames'][1]['move'] = 'd2d4'
            path.write_text(json.dumps(replay))
            with self.assertRaisesRegex(ValueError, 'move hash'):
                audit(directory, raw)

    def test_wall_cap_is_not_complete_recovery(self):
        with tempfile.TemporaryDirectory() as temp:
            directory, raw = self.fixture(Path(temp))
            path = directory/'receipt.json'; receipt = json.loads(path.read_text())
            receipt.update(reason='wall_cap', historical_window_traversed=False, clean=False)
            path.write_text(json.dumps(receipt))
            with self.assertRaisesRegex(ValueError, 'clean historical window'):
                audit(directory, raw)


if __name__ == '__main__':
    unittest.main()
