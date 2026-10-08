import copy
import json
from pathlib import Path
import tempfile
import unittest

from compare_action_campaign import validate_cross_campaign


class ModelComparisonBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.manifests = []
        self.runs = []
        for name in ('control', 'candidate'):
            model = self.root / name
            model.mkdir()
            manifest = model / 'model_manifest.json'
            manifest.write_text(json.dumps({'feature_version': 'features-v2',
                                             'action_version': 'actions-v1',
                                             'rules_fingerprint': 'rules-a'}))
            self.manifests.append(manifest)
            self.runs.append({'nodes': 400000, 'stride': 1000, 'particles': 2048,
                              'inputs': {'/engine/benchmark': 'same-engine', '/data/seats.txt': 'same-seats',
                                         str(manifest): name + '-manifest',
                                         str(model / 'observe.onnx'): name + '-observe',
                                         str(model / 'score.onnx'): name + '-score'},
                              'arms': {name: {'settings': {'FOW_MODEL_DIR': str(model),
                                                           'FOW_OPPONENT_PRIOR': '1'}}}})

    def tearDown(self):
        self.temporary.cleanup()

    def validate(self, allow=False):
        validate_cross_campaign(*self.runs, 'control', 'candidate', allow)

    def test_model_change_requires_explicit_experiment(self):
        with self.assertRaises(ValueError):
            self.validate()
        self.validate(True)

    def test_model_permission_preserves_corpus_and_binary_checks(self):
        original = copy.deepcopy(self.runs)
        for name in ('/engine/benchmark', '/data/seats.txt'):
            with self.subTest(name=name):
                self.runs = copy.deepcopy(original)
                self.runs[1]['inputs'][name] = 'changed'
                with self.assertRaises(ValueError):
                    self.validate(True)

    def test_model_permission_preserves_settings_and_population(self):
        self.runs[1]['arms']['candidate']['settings']['FOW_OPPONENT_PRIOR'] = '2'
        with self.assertRaises(ValueError):
            self.validate(True)
        self.runs[1]['arms']['candidate']['settings']['FOW_OPPONENT_PRIOR'] = '1'
        self.runs[1]['particles'] = 4096
        with self.assertRaises(ValueError):
            self.validate(True)

    def test_feature_version_mismatch_or_missing_contract_is_rejected(self):
        data = json.loads(self.manifests[1].read_text())
        data['feature_version'] = 'features-v1'
        self.manifests[1].write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            self.validate(True)
        del data['feature_version']
        self.manifests[1].write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            self.validate(True)


if __name__ == '__main__':
    unittest.main()
