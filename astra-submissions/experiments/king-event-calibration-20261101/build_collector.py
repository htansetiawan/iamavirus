#!/usr/bin/env python3
"""Build a print-only collector from the original v35 archive."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
ARCHIVE=ROOT/'fable-submissions/iamavirus-v35-mist-c-v14.zip'
DIGEST='24791ca64a429f5ae931466ce3c1af36c6974e1295203e99a00a991976955b4c'
assert hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()==DIGEST
BUILD=HERE/'build';BUILD.mkdir(exist_ok=True)
with zipfile.ZipFile(ARCHIVE) as z:z.extractall(BUILD)
shutil.copyfile(HERE/'collector.h',BUILD/'src/astra_collector.h')
path=BUILD/'src/main.c';text=path.read_text()
assert text.count('int main(void) {')==1
text=text.replace('int main(void) {','#include "astra_collector.h"\n\nint main(void) {')
anchor='        view_moves(view, us, front.castle, &allowed);'
assert text.count(anchor)==1
text=text.replace(anchor,anchor+'\n        if (getenv("ASTRA_KING_CALIB")) astra_king_events(&b, &allowed, decisions, guard_temp);')
path.write_text(text)
result=subprocess.run(['bash','build.sh'],cwd=BUILD,capture_output=True,text=True)
(HERE/'build.log').write_text(result.stdout+result.stderr);result.check_returncode()
manifest={'base_archive':str(ARCHIVE.relative_to(ROOT)),'base_sha256':DIGEST,
          'collector_sha256':hashlib.sha256((HERE/'collector.h').read_bytes()).hexdigest(),
          'main_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
          'binary_sha256':hashlib.sha256((BUILD/'mist').read_bytes()).hexdigest(),
          'history_sha256':hashlib.sha256((BUILD/'data/history.bin').read_bytes()).hexdigest(),
          'compiler':subprocess.check_output(['gcc','--version'],text=True).splitlines()[0],
          'changes':'print-only hook before forced decision, no policy/model/source change elsewhere',
          'release':False}
(HERE/'build-provenance.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
