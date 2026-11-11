"""Read-only source audit of v38's Stockfish/NNUE frontier path.

The numerical examples are derived from source. This does not execute a
network, bot, new game, model fit, performance benchmark or deployment.
"""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / 'astra-submissions/iamavirus-v38-mist-c-allchildren.zip'
OUT = ROOT / 'astra-submissions/analysis/frontier-source-audit-20261111'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    assert sha(ARCHIVE) == 'ba6610f299c1589118ae335f3c46fbff802bf158456db9260ac911dce0d4f69f'
    manifest = json.loads((ROOT / 'astra-submissions/v38-manifest.json').read_text())
    members = ['run.sh', 'src/sfeval.c', 'src/gtcfr.c', 'src/eval.c',
               'third_party/stockfish19/astra-allchildren.patch', 'third_party/stockfish19/ASTRA-NOTICE.md',
               'third_party/stockfish19/src/evaluate.h', 'third_party/stockfish19/src/evaluate.cpp',
               'third_party/stockfish19/src/uci.cpp', 'third_party/stockfish19/src/search.cpp',
               'third_party/stockfish19/src/nnue/network.h', 'third_party/stockfish19/src/nnue/network.cpp',
               'third_party/stockfish19/src/nnue/nnue_architecture.h',
               'third_party/stockfish19/src/nnue/nnue_feature_transformer.h',
               'third_party/stockfish19/src/nnue/nnue_common.h',
               'third_party/stockfish19/src/nnue/features/half_ka_v2_hm.h',
               'third_party/stockfish19/src/nnue/features/full_threats.h',
               'third_party/stockfish19/src/nnue/features/pp_3wide.h',
               'third_party/stockfish19/src/nnue/layers/affine_transform.h',
               'third_party/stockfish19/src/nnue/layers/affine_transform_sparse_input.h']
    source, hashes, evidence = {}, {}, []
    with zipfile.ZipFile(ARCHIVE) as archive:
        for name in members:
            data = archive.read(name)
            digest = hashlib.sha256(data).hexdigest()
            assert digest == manifest['source_sha256'][name], name
            source[name], hashes[name] = data.decode(), digest

    def has(name, pattern, meaning):
        match = re.search(pattern, source[name], re.S)
        assert match, (name, meaning)
        start = source[name].count('\n', 0, match.start()) + 1
        end = source[name].count('\n', 0, match.end()) + 1
        evidence.append(dict(member=name, first_line=start, last_line=end, meaning=meaning))
        return match

    sf, gt = 'src/sfeval.c', 'src/gtcfr.c'
    has('run.sh', r'export ASTRA_SF_ALLCHILDREN=1', 'Launcher enables the opt-in scorer.')
    has(sf, r'Threads value 1\\nsetoption name Hash value 16\\nsetoption name MultiPV value %d', 'Each worker: one thread, 16 MiB hash, requested MultiPV.')
    has(sf, r'MIST_SF_WORKERS[^;]+:\s*2;', 'Two Stockfish workers by default.')
    has(sf, r'MIST_SF_MULTIPV[^;]+:\s*256;', 'MultiPV 256 by default.')
    has(sf, r'position fen %s\\ngo depth 1\\n', 'A parent FEN and depth-one request, not one request per child.')
    has(sf, r'return !is_attacked\(p, king_square\(p, p->side \^ 1\), p->side\);', 'Reject parent positions where the mover can already take the other king.')
    has(sf, r'if \(strcmp\(uci\[i\], move\) == 0\)', 'Match returned PV first moves to FoW move entries.')
    has(gt, r'const int ranked = sf > 0 && sf >= sf_multipv\(\);', 'Missing-score floor is conditional on receiving the requested MultiPV count.')
    has(gt, r'if \(sf > 0 && sf_found\[a\]\).*?value = mover == us \? v : -v;.*?else if \(ranked\).*?value = mover == us \? floor_v : -floor_v;.*?else \{\s*value = evaluate\(&q, us\);', 'Scored child conversion, conditional floor, otherwise native child fallback.')
    has(gt, r'tanh\(sf_cp\[a\] / 400\.0\)', 'Map UCI centipawn score to a bounded heuristic utility.')
    has(gt, r'if \(mover_left_king_capturable\(&q\)\)', 'Exact FoW king-loss handling precedes heuristic child value assignment.')
    has(gt, r't.root_loss = params->king_risk > 1.0 \? -params->king_risk : -1.0;', 'Root own-king loss can use the configured extra penalty.')
    patch = 'third_party/stockfish19/astra-allchildren.patch'
    has(patch, r'limits.depth == 1.*?Threads.*?== 1.*?!skill.enabled\(\).*?!tbConfig.rootInTB.*?multiPV == rootMoves.size\(\)', 'Modified mode is conditional on depth, threads, strength/tablebase state and full legal-root coverage.')
    has('src/eval.c', r'MIST_FOG_LINE.*?\) : 0;', 'Native fallback optional fog-line term defaults to zero.')
    has('src/eval.c', r'MIST_FOG_KNIGHT.*?\) : 0;', 'Native fallback optional fog-knight term defaults to zero.')
    has('src/eval.c', r'double evaluate\(const Position \*p, int us\) \{ return tanh\(evaluate_cp\(p, us\) / 400.0\); \}', 'Native fallback also uses bounded utility, without a neural head.')

    prefix = 'third_party/stockfish19/src/'
    architecture = prefix + 'nnue/nnue_architecture.h'
    l1 = int(has(architecture, r'IndexType L1 = (\d+);', 'Feature vector length.').group(1))
    l2 = int(has(architecture, r'int\s+L2 = (\d+);', 'First affine output width.').group(1))
    l3 = int(has(architecture, r'int\s+L3 = (\d+);', 'Second affine output width.').group(1))
    stacks = int(has(architecture, r'IndexType LayerStacks = (\d+);', 'Small-network material buckets.').group(1))
    netname = has(prefix + 'evaluate.h', r'#define EvalFileDefaultName "([^"]+)"', 'Default pretrained network filename.').group(1)
    netsha = has('third_party/stockfish19/ASTRA-NOTICE.md', r'Network SHA256: ([a-f0-9]{64})', 'Declared embedded upstream network hash; not independently exported here.').group(1)
    has(prefix + 'nnue/network.cpp', r'const int\s+bucket\s*= \(pos.count<ALL_PIECES>\(\) - 1\) / 4;', 'Piece count selects a shared-transformer head.')
    has(prefix + 'nnue/network.h', r'NetworkArchitecture network\[LayerStacks\];', 'Eight heads share one feature transformer, not eight full separate networks.')
    has(prefix + 'nnue/network.cpp', r'load_internal\(evalFile\)', 'Default embedded network loading exists.')
    has(prefix + 'nnue/nnue_feature_transformer.h', r'const Color perspectives\[2\]\s*= \{pos.side_to_move\(\), ~pos.side_to_move\(\)\};', 'Both board perspectives contribute to the transformed input.')
    has(prefix + 'nnue/nnue_feature_transformer.h', r'offset = \(HalfDimensions / 2\) \* perspective;', 'Each perspective contributes half the transformed input.')
    has(prefix + 'nnue/nnue_common.h', r'using BiasType\s*= i16;', 'Feature-transformer biases use 16-bit integers.')
    has(prefix + 'nnue/nnue_common.h', r'using WeightType\s*= i16;', 'Piece-square feature-transformer weights use 16-bit integers.')
    has(prefix + 'nnue/nnue_common.h', r'using ThreatWeightType\s*= i8;', 'Threat/pawn-pair transformer weights use 8-bit integers.')
    has(prefix + 'nnue/nnue_common.h', r'using PSQTWeightType\s*= i32;', 'PSQT weights use 32-bit integers.')
    has(prefix + 'nnue/nnue_common.h', r'using TransformedFeatureType = u8;', 'Transformed inputs occupy unsigned 8-bit integers.')
    has(prefix + 'nnue/layers/affine_transform.h', r'using WeightType = i8;', 'Dense affine weights use signed 8-bit integers.')
    has(prefix + 'nnue/layers/affine_transform.h', r'using OutputType = i32;', 'Affine outputs/biases use 32-bit integers.')
    has(prefix + 'nnue/features/half_ka_v2_hm.h', r'PS_NB\s*= 11 \* SQUARE_NB', 'Eleven piece-square categories.')
    has(prefix + 'nnue/features/half_ka_v2_hm.h', r'static_cast<IndexType>\(SQUARE_NB\) \* static_cast<IndexType>\(PS_NB\) / 2', 'Piece-square index-space formula.')
    threats = int(has(prefix + 'nnue/features/full_threats.h', r'IndexType Dimensions = (\d+);', 'Threat-feature index-space size.').group(1))
    has(prefix + 'nnue/features/pp_3wide.h', r'PawnIds\s*= COLOR_NB \* 48;', 'Ninety-six pawn-square identities.')
    has(prefix + 'nnue/features/pp_3wide.h', r'Dimensions = PawnIds \* \(PawnIds - 1\) / 2;', 'Pawn-pair index-space formula.')
    has(prefix + 'uci.cpp', r'return int\(std::round\(100 \* int\(v\) / a\)\);', 'UCI centipawns normalize internal evaluation units; raw NNUE output is not passed directly to CFR.')
    has(prefix + 'evaluate.cpp', r'network.evaluate\(pos, accumulators, caches\)', 'Ordinary evaluation calls the pretrained NNUE.')
    assert (l1, l2, l3, stacks) == (1024, 32, 32, 8)
    psq, pairs = 64 * (11 * 64) // 2, 96 * 95 // 2
    examples = [dict(parent_mover=m, our_color=u, uci_cp=cp,
                     cfr_utility=math.tanh(cp / 400.) * (1 if m == u else -1))
                for m in ['white', 'black'] for u in ['white', 'black'] for cp in [100, 400]]
    result = dict(at=datetime.now(timezone.utc).isoformat(), archive_sha256=sha(ARCHIVE), source_sha256=hashes,
                  audit_source_sha256=sha(Path(__file__)), source_evidence=evidence,
                  worker_defaults=dict(processes=2, threads_per_process=1, hash_mib_per_process=16, multipv=256, requested_depth=1),
                  network=dict(default_name=netname, declared_embedded_sha256=netsha, feature_index_spaces=dict(piece_square=psq, threats=threats, pawn_pairs=pairs, total=psq + threats + pairs),
                               transformed_input=l1, perspective_accumulator_width=l1, contributed_features_per_perspective=l1 // 2,
                               fc0=[l1, l2], fc1=[2 * l2, l3], fc2=[2 * l2 + 2 * l3, 1], material_heads=stacks,
                               note='Clipped and squared activations concatenate; final scalar also has an fc0 skip and a separate learned PSQT contribution. This is not simply a linear 1024-32-32-1 stack.'),
                  source_derived_score_examples=examples,
                  missing_child_score_rule='Use worst scored sibling only if sf>0 and sf>=requested MultiPV; otherwise native evaluate(child, us). Normal default is 256 requested lines, not the number of legal moves.',
                  scope='Read-only bundled-source/model-declaration audit with source-derived arithmetic. No neural inference, new bot game, fit, performance benchmark, candidate or deployment.',
                  limitations=['Source declarations and packaged network notices are inspected; embedded model weights are not exported/rehash-verified by this audit.',
                               'No live counts of fallback frequency, active modified-mode calls, worker RSS or network latency are measured.',
                               'No FoW policy/value network or online NNUE training is established by the presence of Stockfish NNUE.',
                               'Neither conditional fallback nor ordinary-chess evaluation is established here as the cause of a particular loss.'])
    OUT.mkdir(exist_ok=False)
    with (OUT / 'result.json').open('x') as stream:
        stream.write(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps(dict(source_members=len(hashes), evidence_checks=len(evidence), worker_defaults=result['worker_defaults'], network=result['network']), indent=2))


if __name__ == '__main__':
    main()
