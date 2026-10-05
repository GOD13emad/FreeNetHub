import pathlib,sys,tempfile,unittest
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/"app"))
import engine as E

PS=(ROOT/"app"/"FreeNetHub.ps1").read_text(encoding="utf-8-sig")
XAML=(ROOT/"app"/"View.xaml").read_text(encoding="utf-8-sig")

class R49ResilienceInputs(unittest.TestCase):
 def test_bridge_clipboard_controls_exist_and_are_wired(self):
  for name in ("ImportWebClipboard","ImportObfsClipboard"):
   self.assertIn(f'Name="{name}"',XAML)
   self.assertIn(name,PS)
  self.assertIn("[Windows.Clipboard]::GetText()",PS)
  self.assertIn("bridge-import-",PS)

 def test_temporary_clipboard_bridge_file_is_deleted_after_successful_import(self):
  line="obfs4 192.0.2.10:443 0123456789ABCDEF0123456789ABCDEF01234567 cert=abc iat-mode=0"
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);(root/"jobs").mkdir();(root/"data").mkdir();(root/"backup").mkdir()
   f=root/"jobs"/"bridge-import-test.txt";f.write_text(line+"\n",encoding="utf-8")
   with patch.object(E,"ROOT",root):
    out=E.dispatch("Import","OBFS4",str(f))
   self.assertEqual(out["imported"],1)
   self.assertFalse(f.exists())
   self.assertEqual((root/"data"/"bridges_obfs4.txt").read_text(encoding="utf-8").strip(),line)

 def test_temporary_clipboard_bridge_file_is_deleted_after_validation_failure(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);(root/"jobs").mkdir();(root/"data").mkdir();(root/"backup").mkdir()
   f=root/"jobs"/"bridge-import-test.txt";f.write_text("not a bridge\n",encoding="utf-8")
   with patch.object(E,"ROOT",root):
    with self.assertRaises(ValueError):
     E.dispatch("Import","OBFS4",str(f))
   self.assertFalse(f.exists())

 def test_normal_user_bridge_file_is_not_deleted(self):
  line="obfs4 192.0.2.10:443 0123456789ABCDEF0123456789ABCDEF01234567 cert=abc iat-mode=0"
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);(root/"jobs").mkdir();(root/"data").mkdir();(root/"backup").mkdir()
   f=root/"user-bridge.txt";f.write_text(line+"\n",encoding="utf-8")
   with patch.object(E,"ROOT",root):
    out=E.dispatch("Import","OBFS4",str(f))
   self.assertEqual(out["imported"],1)
   self.assertTrue(f.exists())

if __name__=="__main__":
 unittest.main()
