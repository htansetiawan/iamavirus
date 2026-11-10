import tempfile
from pathlib import Path
import unittest
from pilot import score,futile,cleanup

class PilotAccounting(unittest.TestCase):
 def test_color_swapped_results(self):
  for result,white,black in [('1-0',1.,0.),('0-1',0.,1.),('1/2-1/2',.5,.5)]:
   self.assertEqual(score(result,'white'),white);self.assertEqual(score(result,'black'),black)
 def test_futility_is_mathematical_impossibility(self):
  rows=lambda scores:[dict(score=v,faults=[]) for v in scores]
  self.assertFalse(futile(rows([])));self.assertTrue(futile(rows([0.]*7)))
  self.assertFalse(futile(rows([1.]*4+[0.]*6))) # exactly ten remains reachable
  self.assertTrue(futile(rows([1.]*3+[.5]+[0.]*6))) # best possible9.5
  self.assertFalse(futile(rows([1.]*10+[0.]*6)));self.assertTrue(futile(rows([1.]*9+[0.]*7)))
 def test_faulty_or_invalid_rows_cannot_drive_futility(self):
  with self.assertRaises(AssertionError):futile([dict(score=None,faults=['technical'])])
  with self.assertRaises(AssertionError):score('*','white')
 def test_missing_process_registry_is_not_clean(self):
  with tempfile.TemporaryDirectory() as directory:self.assertTrue(cleanup(Path(directory)))

if __name__=='__main__':unittest.main()
