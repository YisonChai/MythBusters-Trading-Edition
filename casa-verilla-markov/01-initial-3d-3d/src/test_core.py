"""Unit fixtures only; never used as research input or performance data."""
import unittest
from backtest import fee,bucket,asof,choose,portfolio
class Tests(unittest.TestCase):
 def test_fee(self):self.assertEqual(fee(100,.9,.07),.63)
 def test_bucket_endpoints(self):
  self.assertEqual(bucket(1),19);self.assertEqual(bucket(0),0);self.assertEqual(bucket(.5),10)
 def test_no_future_or_stale_observation(self):
  fixture=[(120,.3,60),(180,.4,120)]
  self.assertIsNone(asof(fixture,119));self.assertEqual(asof(fixture,179)[1],.3);self.assertIsNone(asof(fixture,271))
 def test_market_has_no_own_price_edge(self):self.assertIsNone(choose('market_edge',{},{}))
 def test_empty_portfolio(self):
  rr,s=portfolio([],'fee_only');self.assertEqual(s['final_cash'],10000);self.assertEqual(s['max_realized_drawdown'],0)
 def test_signal_thresholds(self):
  p={'state_support':100,'p_terminal':.96,'p_market':.9,'persistent':.86,'p_calibrated':.96}
  o={'up':.9,'down':.11,'k':2}
  self.assertIsNone(choose('terminal_e05_p87',o,p))
  self.assertIsNotNone(choose('terminal_e05_nofilter',o,p))
if __name__=='__main__':unittest.main()
