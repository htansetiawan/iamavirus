import unittest
from m4_dilemma_certificates import certificate,verify


class CertificateTests(unittest.TestCase):
    def test_pair_and_irreducible_triple(self):
        for n in (2,3):
            group={'replies':[f'r{i}' for i in range(n)],
                   'fatal_matrix':{f'a{i}':[i==j for j in range(n)] for i in range(n)}}
            proof=certificate(group)
            self.assertEqual((proof['loss_numerator'],proof['loss_denominator']),(1,n))
            verify(group,proof)
            if n==3:
                # Every pair has a common safe response; only the full triple
                # creates a conflict. A pair-only detector is insufficient.
                for i in range(n):
                    for j in range(i):
                        self.assertTrue(any(not row[i] and not row[j] for row in group['fatal_matrix'].values()))

    def test_dominated_duplicate_and_invalid_certificate(self):
        group={'replies':['r0','r1','duplicate'],
               'fatal_matrix':{'a0':[1,0,1],'a1':[0,1,0],'always_loses':[1,1,1],'duplicate':[1,0,1]}}
        proof=certificate(group);verify(group,proof)
        self.assertEqual((proof['loss_numerator'],proof['loss_denominator']),(1,2))
        bad=dict(proof,loss_numerator=0)
        with self.assertRaises(AssertionError):verify(group,bad)

    def test_safe_action(self):
        group={'replies':['r0','r1'],'fatal_matrix':{'safe':[0,0],'bad':[1,1]}}
        proof=certificate(group);verify(group,proof)
        self.assertEqual(proof['loss_numerator'],0)


if __name__=='__main__':unittest.main()
