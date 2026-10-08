import copy
import unittest

from learning_experiments.compare_pilots import validate_run_identity


def run():
    return {'identity': {'model_config': {'variant': 'cnn'}, 'seed': 253,
                         'train_games': 512, 'manifest_sha256': 'manifest-a',
                         'shard_sha256': {'train': 'train-a', 'validation': 'validation-a'},
                         'validation_games': 64, 'batch': 4},
            'feature_version': 2, 'action_version': 1, 'rules_fingerprint': 'rules-a',
            'source_sha256': {'train.py': 'source-a'},
            'native': {'sources': {'rules.cc': 'native-a'}}}


class ComparisonBoundaryTests(unittest.TestCase):
    def test_pool_change_requires_an_explicit_experiment(self):
        a = run()
        b = copy.deepcopy(a)
        b['identity'].update(train_games=3766, manifest_sha256='manifest-b')
        with self.assertRaises(ValueError):
            validate_run_identity([a, b])
        self.assertTrue(validate_run_identity([a, b], True))

    def test_pool_permission_does_not_allow_validation_or_training_shard_changes(self):
        for split in ('train', 'validation'):
            with self.subTest(split=split):
                a, b = run(), run()
                b['identity']['shard_sha256'][split] = 'changed'
                with self.assertRaises(ValueError):
                    validate_run_identity([a, b], True)

    def test_pool_permission_does_not_mix_architecture_seed_or_rules_changes(self):
        for target in ('model_config', 'seed', 'source_sha256', 'rules_fingerprint'):
            with self.subTest(target=target):
                a, b = run(), run()
                if target in b['identity']:
                    b['identity'][target] = 'changed'
                else:
                    b[target] = 'changed'
                with self.assertRaises(ValueError):
                    validate_run_identity([a, b], True)

    def test_architecture_comparison_still_requires_identical_source(self):
        a, b = run(), run()
        b['identity']['model_config'] = {'variant': 'attention'}
        self.assertFalse(validate_run_identity([a, b]))
        b['source_sha256']['train.py'] = 'changed'
        with self.assertRaises(ValueError):
            validate_run_identity([a, b])


if __name__ == '__main__':
    unittest.main()
