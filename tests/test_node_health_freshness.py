#!/usr/bin/env python3
"""Security/quality regression: public node cache is not live path proof."""
import datetime as dt
import pathlib
import sys
import unittest
from unittest.mock import patch

R = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / "app"))
import engine as E  # noqa: E402

NOW = dt.datetime.now(dt.timezone.utc)
FRESH = NOW.isoformat()
EXPIRED = (NOW - dt.timedelta(days=3)).isoformat()

class NodeFreshness(unittest.TestCase):
 def test_missing_invalid_future_and_expired_timestamps_fail_closed(self):
  self.assertFalse(E.node_proof_fresh({'ok':True}))
  self.assertFalse(E.node_proof_fresh({'ok':True,'checked':'not-a-date'}))
  self.assertFalse(E.node_proof_fresh({'ok':True,'checked':'2026-10-09T11:00:00'}))
  self.assertFalse(E.node_proof_fresh({'ok':True,'checked':EXPIRED},reference=NOW))
  self.assertFalse(E.node_proof_fresh({'ok':True,'checked':(NOW+dt.timedelta(minutes=2)).isoformat()},reference=NOW))
  self.assertTrue(E.node_proof_fresh({'ok':True,'checked':FRESH},reference=NOW))
  self.assertFalse(E.node_proof_fresh(None))
 def test_stale_high_speed_does_not_outrank_fresh_full_https(self):
  stale={'id':'expired','name':'a stale','protocol':'ss','performance_test':{'ok':True,'pingMs':1,'downloadMbps':1000,'checked':EXPIRED}}
  fresh={'id':'current','name':'b verified','protocol':'ss','performance_test':{'ok':True,'pingMs':80,'downloadMbps':20,'checked':FRESH}}
  ranked=E.node_public_rows({'nodes':[stale,fresh],'selected':'expired'})
  self.assertEqual(ranked[0]['id'],'current')
 def test_old_health_cannot_beat_fresh_verified_health(self):
  stale={'id':'stale','name':'a stale','protocol':'vmess','last_test':{'healthy':True,'checked':EXPIRED,'seconds':.1}}
  fresh={'id':'fresh','name':'b fresh','protocol':'vmess','last_test':{'healthy':True,'checked':FRESH,'seconds':.5}}
  rows=E.node_public_rows({'nodes':[stale,fresh],'selected':''})
  self.assertEqual(rows[0]['id'],'fresh')
 def test_ensure_node_attempts_fresh_proven_candidate_first(self):
  stale={'id':'stale','name':'a','protocol':'vmess','source':'A','performance_test':{'ok':True,'pingMs':1,'downloadMbps':900,'checked':EXPIRED}}
  fresh={'id':'fresh','name':'b','protocol':'ss','source':'B','performance_test':{'ok':True,'pingMs':60,'downloadMbps':20,'checked':FRESH}}
  selections=[]
  health={'healthy':True,'country':'AT','error':'','checked':FRESH}
  with patch.object(E,'node_store',return_value={'selected':'stale','nodes':[stale,fresh]}),patch.object(E,'owned',return_value=None),patch.object(E,'node_select',side_effect=lambda n:selections.append(n)),patch.object(E,'ensure',return_value=health),patch.object(E,'node_record_test'):
   out=E.ensure_node('AUTO')
  self.assertTrue(out['healthy']);self.assertEqual(selections,['fresh'])
 def test_gui_fails_closed_on_historical_pass(self):
  gui=(R/'app'/'FreeNetHub.ps1').read_text(encoding='utf-8-sig')
  self.assertIn('function Test-RecentNodeProof',gui)
  self.assertIn('STALE / retest',gui)
  self.assertIn("elseif($oldPerf){'STALE'}",gui)
  self.assertIn("elseif($oldPerf -or $oldLt -or $n.endpoint_test){'STALE'}",gui)

if __name__=='__main__':unittest.main()
