#!/usr/bin/env python3
import argparse, gzip, hashlib, json, shutil, subprocess, tempfile
from pathlib import Path

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--out",type=Path,required=True);args=ap.parse_args()
    root=Path(__file__).resolve().parent; receipt={"extractor_sha256":sha(root/"build/extract"),"source_sha256":sha(root/"extract.c"),"splits":{}}
    for split in ("train","validation","test"):
        with tempfile.TemporaryDirectory(prefix="astra-temporal-") as td:
            td=Path(td);txt=td/"in.txt";raw=td/"features.bin"
            with gzip.open(args.out/(split+".txt.gz"),"rb") as f,txt.open("wb") as w:shutil.copyfileobj(f,w)
            run=subprocess.run([str(root/"build/extract"),str(txt),str(raw)],capture_output=True,text=True)
            (args.out/(split+"-extract.stderr")).write_text(run.stderr)
            if run.returncode:raise RuntimeError(run.stderr)
            assert raw.stat().st_size<1_500_000_000
            dest=args.out/(split+".features.bin.gz")
            with raw.open("rb") as f,dest.open("wb") as w:
                with gzip.GzipFile(filename="",fileobj=w,mode="wb",mtime=0,compresslevel=1) as z:shutil.copyfileobj(f,z)
            receipt["splits"][split]={"input_sha256":sha(txt),"features_sha256":sha(raw),"gzip_sha256":sha(dest),"raw_bytes":raw.stat().st_size,"compressed_bytes":dest.stat().st_size,"counts":json.loads(run.stderr)}
            print(split,json.dumps(receipt["splits"][split]),flush=True)
            (args.out/"extraction.json").write_text(json.dumps(receipt,indent=2)+"\n")
if __name__=="__main__":main()
