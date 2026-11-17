"""Unit fixtures are not historical data and never enter research outputs."""
import unittest
from run import fee,state,choose,ledger,TEST_START,END
class Tests(unittest.TestCase):
 def test_fee(self):self.assertEqual(fee(.9,.07),.63)
 def test_state_sizes_and_features(self):
  o={'k':4,'up':.6,'momentum':.03,'volatility':.04,'asset':'btc'}
  self.assertEqual(len(state(o,'small')),2);self.assertEqual(len(state(o,'medium')),4);self.assertEqual(len(state(o,'large')),5)
 def test_market_no_fabricated_advantage(self):
  self.assertIsNone(choose('edge05_no_filter',{}, {},True))
 def test_no_trade_portfolio(self):
  t,c,s=ledger([],'fees');self.assertEqual(s['final_equity'],10000);self.assertEqual(s['trades'],0);self.assertEqual(c[0]['t'],TEST_START);self.assertEqual(c[-1]['t'],END)
 def test_gate_is_not_win_probability(self):
  p={'p':.96,'regime_support':50,'persistence':.86};o={'up':.9,'down':.11,'k':1}
  self.assertIsNone(choose('edge05_p87',o,p));self.assertEqual(choose('edge05_no_filter',o,p)[0],'Up')

 def fixture(self,mid,q,won,t=None,settle=None):
  t=t or TEST_START+300;settle=settle or TEST_START+3600
  return {'market_id':str(mid),'q_observed':q,'q_next':q,'signal_ts':t,'end_ts':settle,'settle_ts':settle,'fee_rate':.07,'fee_exponent':1,'won':won}
 def test_same_second_settlements_are_batched(self):
  tr,curve,s=ledger([self.fixture('a',.5,1),self.fixture('b',.5,0)],'fees')
  self.assertAlmostEqual(s['net_pnl'],-3.5);self.assertAlmostEqual(s['max_drawdown'],3.5)
 def test_cash_constraint(self):
  tr,curve,s=ledger([self.fixture(i,.99,1) for i in range(101)],'fees')
  self.assertEqual(len(tr),100);self.assertEqual(s['skips']['insufficient_cash'],1)
 def test_settlement_before_entry_same_second(self):
  t=TEST_START+3600
  tr,curve,s=ledger([self.fixture('a',.9,1),self.fixture('b',.9,1,t,t+3600)],'fees')
  rr=next(x for x in tr if x['market_id']=='b')
  self.assertAlmostEqual(rr['cash_after_entry'],10000+9.37-90.63)

if __name__=='__main__':unittest.main()
