import unittest
from collect import normalized,stamp,validate_join

class MetadataContracts(unittest.TestCase):
    def row(self):return dict(id='fixture0',createdAt='2026-11-09T00:00:00.000000001Z',white='A',black='B',whitePlayerId='a',blackPlayerId='b',whiteVersion=1,blackVersion=2,result='1-0',reason='King capturable',plies=20,whiteCurrentVersion=5,whiteStaff=True)
    def test_only_played_immutable_fields(self):
        row=self.row();value=normalized(row);self.assertNotIn('whiteCurrentVersion',value);self.assertNotIn('whiteStaff',value)
        row['whiteCurrentVersion']=6;self.assertEqual(value,normalized(row))
    def test_id_ply_and_known_metadata_must_match(self):
        row=normalized(self.row());known=dict(created_at=row['createdAt'],white='A',black='B',white_version=1,black_version=2)
        validate_join(row,dict(plies=20),known)
        with self.assertRaises(AssertionError):validate_join(row,dict(plies=19),known)
        known['black_version']=3
        with self.assertRaises(AssertionError):validate_join(row,dict(plies=20),known)
    def test_exact_cutoff_nanoseconds_and_black_order(self):
        self.assertEqual(stamp('2026-11-09T00:00:00.000000002Z')-stamp('2026-11-09T00:00:00.000000001Z'),1)
        row=self.row();row['whiteVersion']=None;self.assertIsNone(normalized(row)['whiteVersion'])
        row['id']='../badid'
        with self.assertRaises(AssertionError):normalized(row)

if __name__=='__main__':unittest.main()
