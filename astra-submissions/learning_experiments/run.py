"""Bounded, resumable representation pilots on a frozen replay split.

PYTHONPATH=astra-submissions:. .venv/bin/python -m learning_experiments.run \
  --manifest data/manifests/v3.json --variant attention --phase supervised \
  --output /media/henrytan/seagate/iamavirus/astra/representations/attention-pilot

CUDA requires an explicit --device cuda and an Astra GPU lease. Test data is
never loaded by this architecture-selection runner. SSL reads actor fields only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
import yaml

from learning import _native, dataset as ds
from learning.model import parameter_count
from learning.pretrain import compute_losses, to_device
from learning_experiments.evaluate import evaluate
from learning_experiments.models import ModelConfig, make_model, model_metadata
from learning_experiments.ssl import MaskedTeacherStudent, load_actor_histories, make_actor_batch

ROOT = Path(__file__).resolve().parents[2]


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    os.replace(temporary, path)


def isolate_rules(output):
    """Freeze native sources and build away from Fable's running shared library."""
    snapshot = output / "native-source"
    marker = snapshot / "sources.json"
    if not marker.exists():
        snapshot.mkdir(parents=True, exist_ok=True)
        sources = {}
        for name in _native.SOURCES + _native.HEADERS:
            content = (ROOT / name).read_bytes()
            (snapshot / name).write_bytes(content)
            sources[name] = hashlib.sha256(content).hexdigest()
        # Catch a concurrent edit during the snapshot, rather than silently mix it.
        if any(file_hash(ROOT / name) != digest for name, digest in sources.items()):
            raise RuntimeError("native sources changed during snapshot; use a new output directory")
        write_json(marker, sources)
    else:
        sources = json.loads(marker.read_text())
        if any(file_hash(snapshot / name) != digest for name, digest in sources.items()):
            raise RuntimeError("native snapshot was modified")
    _native.ROOT = snapshot
    _native.BUILD_DIR = snapshot / "build"
    _native.LIBRARY = _native.BUILD_DIR / "librules.so"
    library = _native.ensure_built()
    return {"sources": sources, "library_sha256": file_hash(library)}


def game_id(episode):
    return episode.game_id if hasattr(episode, "game_id") else episode.metadata.game_id


def select_games(episodes, limit):
    ids = sorted({game_id(e) for e in episodes}, key=lambda g: hashlib.sha256(g.encode()).hexdigest())
    chosen = set(ids[:limit] if limit else ids)
    return [e for e in episodes if game_id(e) in chosen]


def validate_splits(train, validation):
    a, b = {game_id(e) for e in train}, {game_id(e) for e in validation}
    if not a or not b or "" in a or "" in b:
        raise ValueError("nonempty identified train and validation games required")
    if a & b:
        raise ValueError("training/validation game overlap")


def save_checkpoint(path, module, optimizer, step, identity, metadata):
    model = module.student if isinstance(module, MaskedTeacherStudent) else module
    payload = {"state_dict": model.state_dict(), "training_module": module.state_dict(),
               "optimizer": optimizer.state_dict(), "step": step, "identity": identity,
               **metadata}
    temporary = path.with_suffix(".tmp")
    torch.save(payload, temporary)
    os.replace(temporary, path)


def train(args):
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    metadata_path = output / "run.json"
    if metadata_path.exists() and not args.resume:
        raise ValueError("run already exists; --resume it or use a new output directory")
    config = ModelConfig(args.variant)
    config.validate()
    torch.set_num_threads(args.threads)
    torch.manual_seed(args.seed)
    if args.device == "cuda":
        lease = Path("/tmp/gpu_queue/claimed_by")
        if not lease.exists() or not lease.read_text().strip().lower().startswith("astra"):
            raise RuntimeError("Astra must hold the coordinated GPU lease before CUDA training")
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA requested but unavailable")
    device = torch.device(args.device)
    manifest = json.loads(args.manifest.read_text())
    manifest_sha = file_hash(args.manifest)
    shards = {name: Path(manifest["shards"][name]) for name in ("train", "validation")}
    shards = {name: path if path.is_absolute() else ROOT / path for name, path in shards.items()}
    shard_hashes = {name: file_hash(path) for name, path in shards.items()}
    common = yaml.safe_load((ROOT / "learning/configs/replay_ppo.yaml").read_text())["pretrain"]
    identity = {"phase": args.phase, "model_config": asdict(config), "seed": args.seed,
                "window": args.window, "batch": args.batch, "learning_rate": args.learning_rate,
                "weight_decay": 1e-4, "grad_clip": 1.0, "manifest_sha256": manifest_sha,
                "shard_sha256": shard_hashes, "train_games": args.train_games,
                "validation_games": args.validation_games, "loss_weights": common["loss_weights"],
                "player_weights": common.get("player_weights"), "mask_fraction": args.mask_fraction}
    native = isolate_rules(output)
    loader = load_actor_histories if args.phase == "ssl" else ds.load_episodes
    train_episodes, validation = loader(shards["train"]), loader(shards["validation"])
    validate_splits(train_episodes, validation)
    train_episodes = select_games(train_episodes, args.train_games)
    validation = select_games(validation, args.validation_games)
    if args.phase == "supervised":
        train_episodes = [e for e in train_episodes if e.num_decisions]
    if len(train_episodes) < args.batch:
        raise ValueError("not enough training histories for the batch")
    if args.phase == "ssl":
        module = MaskedTeacherStudent(config).to(device)
    else:
        module = make_model(config).to(device)
    optimizer = torch.optim.AdamW([p for p in module.parameters() if p.requires_grad],
                                  lr=args.learning_rate, weight_decay=1e-4)
    first_step = 0
    source_files = list((ROOT / "learning").glob("*.py")) + list(Path(__file__).parent.glob("*.py"))
    source_hashes = {str(p.relative_to(ROOT)): file_hash(p) for p in sorted(source_files)}
    metadata = {**model_metadata(config), "identity": identity, "native": native,
                "source_sha256": source_hashes, "torch": torch.__version__, "device": str(device),
                "train_episodes": len(train_episodes), "validation_episodes": len(validation),
                "model_parameters": parameter_count(module.student if args.phase == "ssl" else module),
                "requested_steps": args.steps, "test_shard_used": False}
    if args.resume:
        checkpoint = torch.load(output / "latest.pt", map_location=device, weights_only=False)
        if checkpoint["identity"] != identity:
            raise ValueError("resume identity differs: data, model, or training configuration changed")
        if checkpoint["source_sha256"] != source_hashes:
            raise ValueError("source changed since checkpoint; start a new run with --initialize")
        module.load_state_dict(checkpoint["training_module"])
        optimizer.load_state_dict(checkpoint["optimizer"])
        first_step = checkpoint["step"]
    elif args.initialize:
        checkpoint = torch.load(args.initialize, map_location=device, weights_only=False)
        if checkpoint["architecture"] != config.architecture:
            raise ValueError("initialization architecture differs")
        target = module.student if args.phase == "ssl" else module
        target.load_state_dict(checkpoint["state_dict"])
        if args.phase == "ssl":
            module.teacher.load_state_dict(target.state_dict())
        metadata["initialized_from"] = {"path": str(args.initialize), "sha256": file_hash(args.initialize)}
    if args.steps <= first_step:
        raise ValueError("requested steps already completed")
    write_json(metadata_path, metadata)
    write_json(output / "dataset-manifest.json", manifest)
    started = time.monotonic()
    stamp = datetime.now(timezone.utc).isoformat()
    status = {"state": "running", "pid": os.getpid(), "started_at": stamp, "phase": args.phase,
              "variant": args.variant, "step": first_step, "target_steps": args.steps}
    write_json(output / "status.json", status)
    module.train()
    try:
        with (output / "train.jsonl").open("a") as log:
            for step in range(first_step + 1, args.steps + 1):
                rng = random.Random(args.seed + step * 104729)
                group = rng.sample(train_episodes, args.batch)
                optimizer.zero_grad(set_to_none=True)
                if args.phase == "supervised":
                    batch = to_device(ds.make_batch(group, args.window, rng,
                                      player_weights=common.get("player_weights")), device)
                    loss, metrics = compute_losses(module, batch, common["loss_weights"])
                    if not metrics.get("decisions"):
                        raise RuntimeError("sampled no decisions; fix sampling before counting an update")
                else:
                    batch = {k: torch.from_numpy(v).to(device) for k, v in make_actor_batch(group, args.window, rng).items()}
                    hs, ht = module.burn_prefix(batch["prefix_planes"], batch["prefix_scalars"], batch["prefix_lengths"])
                    generator = torch.Generator(device=device).manual_seed(args.seed + step * 104729)
                    loss, metrics, _, _ = module.window_loss(batch["planes"], batch["scalars"],
                        batch["lengths"], hs, ht, generator, mask_fraction=args.mask_fraction,
                        observed_symbols=batch['observed_symbols'])
                if not torch.isfinite(loss):
                    raise RuntimeError("nonfinite loss")
                loss.backward()
                norm = torch.nn.utils.clip_grad_norm_(module.parameters(), 1.0, error_if_nonfinite=True)
                optimizer.step()
                if args.phase == "ssl":
                    module.update_teacher()
                metrics.update(step=step, elapsed_seconds=time.monotonic() - started, grad_norm=float(norm))
                log.write(json.dumps(metrics, allow_nan=False) + "\n")
                log.flush()
                status.update(step=step, elapsed_seconds=metrics["elapsed_seconds"])
                write_json(output / "status.json", status)
                if step == first_step + 1 or step % 10 == 0:
                    print(json.dumps({"phase": args.phase, "variant": args.variant, **metrics}), flush=True)
                if step % args.evaluate_every == 0 or step == args.steps:
                    save_checkpoint(output / "latest.pt", module, optimizer, step, identity, metadata)
                    if args.phase == "supervised":
                        report = evaluate(module, validation, device)
                        write_json(output / f"validation-{step:06d}.json", report)
                        print(json.dumps({"step": step, "validation": report["groups"]["all"]}), flush=True)
                    else:
                        # Label-free held-out corruption task. Fine-tuning is a separate run.
                        module.eval()
                        with torch.no_grad():
                            group = select_games(validation, 8)
                            batch = {k: torch.from_numpy(v).to(device) for k, v in
                                     make_actor_batch(group, args.window, random.Random(0)).items()}
                            hs, ht = module.burn_prefix(batch["prefix_planes"], batch["prefix_scalars"], batch["prefix_lengths"])
                            _, report, _, _ = module.window_loss(batch["planes"], batch["scalars"], batch["lengths"],
                                hs, ht, torch.Generator(device=device).manual_seed(0), mask_fraction=args.mask_fraction,
                                observed_symbols=batch['observed_symbols'])
                            write_json(output / f"ssl-validation-{step:06d}.json", report)
                        module.train()
                        # A low SSL loss from a nearly constant representation
                        # is a failure, not a successful compression result.
                        if step >= 250 and report['normalized_projection_std'] < 0.005 and report['effective_covariance_rank'] < 2:
                            raise RuntimeError('held-out SSL representation collapsed; stop this pilot')
                    save_checkpoint(output / f"step-{step:06d}.pt", module, optimizer, step, identity, metadata)
        status.update(state="complete", completed_at=datetime.now(timezone.utc).isoformat())
    except BaseException as error:
        status.update(state="failed", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        write_json(output / "status.json", status)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--variant", choices=["cnn", "attention", "compressed_attention"], required=True)
    parser.add_argument("--phase", choices=["supervised", "ssl"], default="supervised")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    parser.add_argument("--steps", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=253)
    parser.add_argument("--window", type=int, default=32)
    parser.add_argument("--batch", type=int, default=4)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--mask-fraction", type=float, default=0.4)
    parser.add_argument("--train-games", type=int, default=None)
    parser.add_argument("--validation-games", type=int, default=64)
    parser.add_argument("--evaluate-every", type=int, default=250)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--resume", action="store_true")
    group.add_argument("--initialize", type=Path)
    args = parser.parse_args()
    if min(args.steps, args.window, args.batch, args.threads, args.evaluate_every, args.validation_games) < 1:
        parser.error("steps, window, batch, threads, evaluation interval and validation games must be positive")
    if args.train_games is not None and args.train_games < 1:
        parser.error("train games must be positive")
    if args.learning_rate <= 0 or not 0 < args.mask_fraction < 1:
        parser.error("invalid learning rate or mask fraction")
    train(args)


if __name__ == "__main__":
    main()
