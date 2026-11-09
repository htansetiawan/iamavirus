"""Record the human-uploaded experimental v38 bytes, preserving the failed gate.

This is separate from package.py's ordinary gate-passing release path. Requires
Fable's same-archive acceptance and the already recorded human trial decision.
It never uploads to the arena or changes the historical gate.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys
import zipfile

from package import ASTRA, BASE, BASE_HASH, NAME, OUT, ROOT, STAGED, sha, version_rule, write


def main(snapshot):
    snapshot = Path(snapshot).resolve()
    manifest = json.loads((OUT / 'staged.json').read_text())
    digest = manifest['archive_sha256']
    assert version_rule.next_version() == 38
    assert sha(STAGED) == digest and sha(BASE) == BASE_HASH
    validation = json.loads((OUT / 'zip-validation.json').read_text())
    assert validation['passed'] and validation['archive_sha256'] == digest
    assert sha(OUT / 'scorer-validation.json') == manifest['scorer_validation_sha256']
    review = ROOT / 'chatroom/267-fable-v38-zip-acceptance-and-recommendation.md'
    assert digest in review.read_text() and 'The exact ZIP: accepted' in review.read_text()
    ledger = [json.loads(line) for line in (ROOT / 'chatroom/ledger.jsonl').read_text().splitlines() if line]
    decision = next(row for row in ledger if row.get('from') == 'fable'
                    and row.get('type') == 'decision' and 'Henry approves' in row.get('subject', '')
                    and digest in row.get('body', ''))
    versions = json.loads((snapshot / 'versions.json').read_text())
    arena = next(v for v in versions['versions'] if v['version'] == 38)
    gate_path = ROOT / 'astra-submissions/analysis/sf-opponent-20261108/stopped-review.json'
    gate = json.loads(gate_path.read_text())
    assert gate['completed'] == 29 and gate['gate_pass'] is False
    with zipfile.ZipFile(STAGED) as z:
        assert len(z.namelist()) == manifest['files']
        for name, expected in manifest['source_sha256'].items():
            assert hashlib.sha256(z.read(name)).hexdigest() == expected, name
    acceptance = dict(reviewer='fable', passed=True, archive_sha256=digest,
                      report_path=str(review.relative_to(ROOT)), report_sha256=sha(review),
                      reviewed_at='2026-11-08T16:19:47.163563+00:00',
                      scope='Runtime/package acceptance, not a playing-strength claim')
    acceptance_path = OUT / 'independent-review-acceptance.json'
    assert not acceptance_path.exists()
    assert not (ASTRA / NAME).exists() and not (ASTRA / 'v38-manifest.json').exists()
    write(acceptance_path, acceptance)
    with STAGED.open('rb') as source, (ASTRA / NAME).open('xb') as destination:
        shutil.copyfileobj(source, destination)
    assert sha(ASTRA / NAME) == digest and version_rule.next_version() == 38
    manifest.update(archive=NAME, uploaded_name_alias='v38-review.zip',
                    status='human-uploaded experimental arena trial; historical local gate failed',
                    recorded_at=datetime.now(timezone.utc).isoformat(),
                    release_route='Explicit human experimental-trial decision; ordinary gate unchanged',
                    release_decision=decision,
                    local_opponent_gate_passed=False,
                    local_opponent_gate_path=str(gate_path.relative_to(ROOT)),
                    local_opponent_gate_sha256=sha(gate_path),
                    zip_validation_sha256=sha(OUT / 'zip-validation.json'),
                    independent_review_acceptance_sha256=sha(acceptance_path),
                    arena=dict(version=38, created_at=arena['createdAt'],
                               observed_active=arena['active'], snapshot=str(snapshot.relative_to(ROOT)),
                               public_api_verifies_zip_hash=False,
                               archive_mapping_basis='Human upload statement and Fable same-bytes decision'),
                    withdrawal_rule=dict(own_technical_failure='withdraw and inspect',
                                         first_48='z <= -2 versus fixed 0.543 reference',
                                         first_300='retain only if score >= 0.543',
                                         operational_not_significance_test=True))
    write(ASTRA / 'v38-manifest.json', manifest)
    print(json.dumps(dict(archive=NAME, sha256=digest, arena_version=38,
                          experimental=True, local_gate_passed=False)))


if __name__ == '__main__':
    main(sys.argv[1])
