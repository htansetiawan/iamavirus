"""Exact finite-sample checks of a proposed estimator, NOT an engine change.

Enumerate every draw sequence of a tiny belief; do not estimate expected bias
or variance from a lucky Monte Carlo run. Policies/leaf values are fixed here.
"""
import itertools
import math
import unittest


def corrected(value, sampled_loss_probability, belief_loss_probability, terminal_loss=-2.):
    return value + terminal_loss*(belief_loss_probability-sampled_loss_probability)


def exact_moments(probabilities, values, loses, draws):
    loss_probability = sum(p for p,lost in zip(probabilities,loses) if lost)
    mean = sum(p*v for p,v in zip(probabilities,values))
    first = [0.,0.]; variance = [0.,0.]
    for sequence in itertools.product(range(len(values)), repeat=draws):
        mass = math.prod(probabilities[i] for i in sequence)
        sampled = sum(values[i] for i in sequence)/draws
        corrected_value = corrected(sampled, sum(loses[i] for i in sequence)/draws, loss_probability)
        for k,v in enumerate((sampled, corrected_value)):
            first[k] += mass*v; variance[k] += mass*(v-mean)**2
    return mean, first, variance


class RootControlVariateTests(unittest.TestCase):
    def test_every_draw_sequence_preserves_mean_and_reduces_variance(self):
        truth, means, variances = exact_moments([.05,.35,.60], [-2.,.8,-.4], [1,0,0], 4)
        for mean in means:
            self.assertAlmostEqual(mean, truth)
        self.assertAlmostEqual(variances[0], .1291)
        self.assertAlmostEqual(variances[1], .0796)

    def test_known_terminal_component_has_zero_sampling_variance(self):
        truth, means, variances = exact_moments([.01,.99], [-2.,0.], [1,0], 5)
        self.assertAlmostEqual(truth, -.02)
        self.assertAlmostEqual(means[1], truth)
        self.assertAlmostEqual(variances[1], 0.)
        self.assertGreater(variances[0], 0.)

    def test_subtracts_existing_sampled_penalty_instead_of_counting_twice(self):
        self.assertAlmostEqual(corrected(-2/32, 1/32, .01), -.02)
        self.assertAlmostEqual(corrected(.4, .2, .2), .4)  # enumerated belief: no correction


if __name__ == '__main__':
    unittest.main()
