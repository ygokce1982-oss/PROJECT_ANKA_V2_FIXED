"""Acceptance tests with independent reference values and guardrails."""
from datetime import date, timedelta
import math
import unittest
from core.multi_asset_comparison import AssetHistory, compare_assets


def hist(name, days, prices, currency="USD", demo=True):
    return AssetHistory(
        name, currency, tuple(zip(days, prices, strict=True)),
        "UNIT_TEST_SYNTHETIC",
        "2026-10-11T18:00:00Z", demo,
    )


class MultiAssetComparisonTests(unittest.TestCase):
    def setUp(self):
        self.days = [(date(2025, 1, 1)+timedelta(days=i)).isoformat() for i in range(120)]

    def test_two_asset_aligned_cumulative_return_percent(self):
        a=hist("A",self.days[:4],[100,110,121,133.1])
        b=hist("B",self.days[:4],[50,40,60,30])
        out=compare_assets([a,b],window=2,risk_free_annual=0)
        self.assertEqual(out.currency,"USD")
        self.assertEqual(out.dates,tuple(self.days[:4]))
        self.assertEqual(out.series[0].cumulative_percent[0],0)
        self.assertAlmostEqual(out.series[0].cumulative_percent[2],21)
        self.assertAlmostEqual(out.series[0].cumulative_percent[3],33.1)
        self.assertAlmostEqual(out.series[1].cumulative_percent[-1],-40)

    def test_rolling_sharpe_annualized_sample_std(self):
        # 4 prices -> 3 daily returns [0.1, -0.05, 0.2].
        price=[100,110,104.5,125.4]
        a=hist("A",self.days[:4],price)
        b=hist("B",self.days[:4],[100,99,102,101])
        out=compare_assets([a,b],window=3,risk_free_annual=0,periods_per_year=252)
        self.assertEqual(out.series[0].rolling_sharpe[:3],(None,None,None))
        returns=[.1,-.05,.2]
        avg=sum(returns)/3
        sample_sd=math.sqrt(sum((r-avg)**2 for r in returns)/2)
        expected=avg/sample_sd*math.sqrt(252)
        self.assertAlmostEqual(out.series[0].rolling_sharpe[3],expected,places=10)

    def test_riskfree_period_conversion(self):
        annual_rf=(1.01**252)-1
        a=hist("A",self.days[:4],[100,101,102.01,103.0301])
        b=hist("B",self.days[:4],[100,99,98.01,97.0299])
        out=compare_assets([a,b],window=2,risk_free_annual=annual_rf)
        self.assertIsNone(out.series[0].rolling_sharpe[-1])
        self.assertTrue(out.demo)

    def test_missing_sessions_use_intersection_no_ffill(self):
        a=hist("A",self.days[:4],[100,110,120,130])
        b=hist("B",[self.days[0],self.days[2],self.days[3]],[100,125,150])
        o=compare_assets([a,b],window=2,risk_free_annual=0)
        self.assertEqual(o.dates,(self.days[0],self.days[2],self.days[3]))
        self.assertAlmostEqual(o.series[0].cumulative_percent[-1],30)
        self.assertAlmostEqual(o.series[1].cumulative_percent[-1],50)

    def test_zero_volatility_ratio_undefined(self):
        a=hist("A",self.days[:5],[100]*5)
        b=hist("B",self.days[:5],[99]*5)
        o=compare_assets([a,b],window=3,risk_free_annual=0)
        self.assertEqual(o.series[0].rolling_sharpe,(None,None,None,None,None))

    def test_90_requires_91_common_closes(self):
        p=[100+i*0.2 for i in range(91)]
        a=hist("A",self.days[:91],p)
        b=hist("B",self.days[:91],[x*1.2 for x in p])
        o=compare_assets([a,b],window=90)
        self.assertEqual(len(o.series[0].rolling_sharpe),91)
        self.assertEqual(sum(x is not None for x in o.series[0].rolling_sharpe),1)
        small=compare_assets([hist("A",self.days[:90],p[:90]),hist("B",self.days[:90],p[:90])],window=90)
        self.assertTrue(all(x is None for x in small.series[0].rolling_sharpe))
        self.assertTrue(any("Insufficient" in x for x in small.warnings))

    def test_currency_mismatch_fails_closed(self):
        a=hist("BIST",self.days[:3],[100,101,102],"TRY")
        b=hist("SP",self.days[:3],[100,101,102],"USD")
        with self.assertRaisesRegex(ValueError,"MIXED_CURRENCY"):
            compare_assets([a,b])

    def test_invalid_prices_dates_and_duplicate_names_rejected(self):
        a=hist("A",self.days[:3],[100,101,102])
        for bad_prices in ([100,0,102],[100,float('nan'),102],[100,float('inf'),102],[100,False,102]):
            with self.subTest(bad_prices=bad_prices):
                with self.assertRaises(ValueError):
                    compare_assets([a,hist("B",self.days[:3],bad_prices)])
        with self.assertRaises(ValueError):
            compare_assets([a, a])
        with self.assertRaises(ValueError):
            compare_assets([a,hist("B",[self.days[1],self.days[1]],[100,101])])
        with self.assertRaises(ValueError):
            compare_assets([a,hist("B",[self.days[2],self.days[1]],[100,101])])

    def test_bad_parameters_rejected(self):
        a=hist("A",self.days[:3],[100,101,102])
        b=hist("B",self.days[:3],[100,101,102])
        for params in ({"window":1},{"window":True},{"periods_per_year":1},
                       {"risk_free_annual":-1},{"risk_free_annual":float("nan")}):
            with self.subTest(params=params):
                with self.assertRaises(ValueError):
                    compare_assets([a,b],**params)

    def test_no_common_period_rejected(self):
        a=hist("A",self.days[:2],[100,101])
        b=hist("B",self.days[2:4],[100,101])
        with self.assertRaisesRegex(ValueError,"NO_COMMON"):
            compare_assets([a,b])


if __name__ == "__main__":
    unittest.main()
