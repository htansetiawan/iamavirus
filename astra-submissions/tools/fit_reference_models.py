#!/usr/bin/env python3
"""Bounded current-data refresh of old opponent policies, with untouched test data.

Policy prediction is necessary evidence, not a claim of opponent strength.
The export remains experimental until closed-loop calibration passes.
"""
import argparse
import contextlib
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
import torch  # noqa: E402
from learning import pretrain, feature_cache, export, dataset  # noqa: E402


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('dataset',type=Path)
    args=ap.parse_args();base=args.dataset
    torch.set_num_threads(2);torch.set_num_interop_threads(1)
    if not torch.cuda.is_available():raise RuntimeError('GPU unavailable; do not silently start long CPU training')
    manifest=json.loads((base/'manifest.json').read_text());test=feature_cache.CachedSplit(base/'cache/test')
    report={'classification':'current-data imitation pilot; uncalibrated as playing opponents','teams':{}}
    for label in ('instructors','duck'):
        began=time.monotonic();cfg=pretrain.load_config(base/f'{label}-config.yaml')['pretrain']
        output=base.parent/'models'/label;output.mkdir(parents=True,exist_ok=True)
        if (output/'evaluation.json').exists():raise FileExistsError('Completed model evaluation already exists; use a new experiment directory')
        old_sha=hashlib.sha256(Path(cfg['init_checkpoint']).read_bytes()).hexdigest()
        with (output/'training.log').open('w') as log, contextlib.redirect_stderr(log):
            pretrain.train(base/f'{label}-config.yaml',base/'manifest.json',output,max_steps=270)
        # Exactly once after validation-based selection; batch=1 avoids repeated
        # tail decisions when evaluating unequal-length episodes in old helpers.
        indices=[i for i,p in enumerate(test.players) if p in cfg['players']]
        ecfg={**cfg,'sequences_per_batch':1}
        metrics={}
        for variant,path in [('old',Path(cfg['init_checkpoint'])),('refreshed',output/'best.pt')]:
            model,payload=pretrain.load_model(path,'cuda')
            metrics[variant]=pretrain.evaluate_cached(model,test,indices,ecfg,torch.device('cuda'))
            del model;torch.cuda.empty_cache()
        model,payload=pretrain.load_model(output/'best.pt','cpu')
        release=output/'release';release.mkdir(exist_ok=True)
        graphs=export.export_graphs(model,release)
        episodes=[e for e in dataset.load_episodes(Path(manifest['shards']['validation'])) if e.metadata.player_id in cfg['players']][:4]
        parity=export.parity_check(model,graphs,episodes,max_episodes=4)
        if parity['failure_count']:raise ValueError(f'{label}: ONNX parity failed')
        export.write_manifest(release,output/'best.pt',payload,graphs,parity,str(output/'evaluation.json'),model)
        record={'test_episodes':len(indices),'metrics':metrics,'onnx_parity':parity,'seconds':time.monotonic()-began,
                'initial_checkpoint_sha256':old_sha,
                'training_config_sha256':hashlib.sha256((base/f'{label}-config.yaml').read_bytes()).hexdigest(),
                'selected_by':'validation policy NLL; test never used for checkpoint choice','release':str(release)}
        (output/'evaluation.json').write_text(json.dumps(record,indent=2)+'\n')
        report['teams'][label]=record
        (base.parent/'model-evaluation.json').write_text(json.dumps(report,indent=2)+'\n')
        print(label,json.dumps({'test_episodes':len(indices),'metrics':metrics,'seconds':record['seconds']}),flush=True)


if __name__=='__main__':main()
