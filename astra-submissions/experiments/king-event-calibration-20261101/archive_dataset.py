#!/usr/bin/env python3
"""Archive the immutable collected probabilities, labels, logs and provenance."""
import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'astra-submissions/analysis/king-event-calibration-20261101'
receipt=json.loads((OUT/'receipt.json').read_text());assert receipt['state']=='complete'
target=OUT/'collected-games.tar.gz';assert not target.exists()
members={}
with target.open('xb') as raw:
    with gzip.GzipFile(filename='',fileobj=raw,mode='wb',mtime=0,compresslevel=6) as compressed:
        with tarfile.open(fileobj=compressed,mode='w') as archive:
            for path in sorted((OUT/'games').iterdir()):
                if path.suffix not in ('.jsonl','.json','.stderr'):continue
                payload=path.read_bytes();name=str(path.relative_to(OUT))
                info=tarfile.TarInfo(name);info.size=len(payload);info.mode=0o644
                archive.addfile(info,io.BytesIO(payload))
                members[name]={'bytes':len(payload),'sha256':hashlib.sha256(payload).hexdigest()}
manifest={'archive':target.name,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
          'compressed_bytes':target.stat().st_size,'members':members,
          'restore':'Extract in this analysis directory to restore games/ for fit.py; the test report refuses overwrite.'}
(OUT/'dataset-archive.json').write_text(json.dumps(manifest,indent=2)+'\n')
print({'members':len(members),'bytes':manifest['compressed_bytes'],'sha256':manifest['sha256']})
