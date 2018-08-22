"Test for Range Query"
#import numpy as np
from progressivis.table.constant import Constant
from progressivis.table.table import Table
from progressivis import Print
from progressivis.stats import  RandomTable, Min, Max
from progressivis.core.bitmap import bitmap
from progressivis.table.hist_index import HistogramIndex
from progressivis.table.percentiles import Percentiles
import numpy as np
from . import ProgressiveTest, main, skip
from progressivis.table.range_query import RangeQuery


class TestPercentiles(ProgressiveTest):
    "Tests for HistIndex based percentiles"
    def tearDown(self):
        TestPercentiles.cleanup()

    def _impl_tst_percentiles(self, accuracy):
        """
        """
        s = self.scheduler()
        random = RandomTable(2, rows=10000, scheduler=s)
        hist_index = HistogramIndex(column='_1', scheduler=s)
        hist_index.input.table = random.output.table
        t_percentiles = Table(name=None,
                        dshape='{_25: float64, _50: float64, _75: float64}',
                        data={'_25': [25.0], '_50': [50.0], '_75': [75.0]})
        which_percentiles = Constant(table=t_percentiles, scheduler=s)
        percentiles = Percentiles(hist_index, accuracy=accuracy, scheduler=s)
        percentiles.input.table = random.output.table
        percentiles.input.percentiles = which_percentiles.output.table
        prt = Print(proc=self.terse, scheduler=s)
        prt.input.df = percentiles.output.table
        s.start()
        s.join()
        pdict = percentiles.table().last().to_dict()
        v = random.table()['_1'].values
        p25 = np.percentile(v, 25.0)
        p50 = np.percentile(v, 50.0)
        p75 = np.percentile(v, 75.0)
        print("Table=> accuracy: ", accuracy," 25:", p25, pdict['_25'], " 50:", p50, pdict['_50'], " 75:", p75, pdict['_75'])
        self.assertAlmostEqual(p25, pdict['_25'], delta=0.01)        
        self.assertAlmostEqual(p50, pdict['_50'], delta=0.01)        
        self.assertAlmostEqual(p75, pdict['_75'], delta=0.01)
    def test_percentiles_fast(self):
        """test_percentiles: Simple test for HistIndex based percentiles
        low accurracy => faster mode
        """
        return self._impl_tst_percentiles(2.0)
    def test_percentiles_accurate(self):
        """test_percentiles: Simple test for HistIndex based percentiles
        higher accurracy => slower mode
        """
        return self._impl_tst_percentiles(0.2)
    def _impl_tst_percentiles_rq(self, accuracy):
        """
        """
        s = self.scheduler()
        random = RandomTable(2, rows=10000, scheduler=s)
        t_min = Table(name=None, dshape='{_1: float64}', data={'_1':[0.3]})
        min_value = Constant(table=t_min, scheduler=s)
        t_max = Table(name=None, dshape='{_1: float64}', data={'_1':[0.8]})
        max_value = Constant(table=t_max, scheduler=s)
        range_qry = RangeQuery(column='_1', scheduler=s)
        range_qry.create_dependent_modules(random, 'table',
                                           min_value=min_value,
                                           max_value=max_value)
        
        hist_index = range_qry.hist_index
        t_percentiles = Table(name=None,
                        dshape='{_25: float64, _50: float64, _75: float64}',
                        data={'_25': [25.0], '_50': [50.0], '_75': [75.0]})
        which_percentiles = Constant(table=t_percentiles, scheduler=s)
        percentiles = Percentiles(hist_index, accuracy=accuracy, scheduler=s)
        percentiles.input.table = range_qry.output.table
        percentiles.input.percentiles = which_percentiles.output.table
        prt = Print(proc=self.terse, scheduler=s)
        prt.input.df = percentiles.output.table
        s.start()
        s.join()
        pdict = percentiles.table().last().to_dict()
        v = range_qry.table()['_1'].values
        p25 = np.percentile(v, 25.0)
        p50 = np.percentile(v, 50.0)
        p75 = np.percentile(v, 75.0)
        print("TSV=> accuracy: ", accuracy," 25:",p25, pdict['_25'], " 50:", p50, pdict['_50'], " 75:", p75, pdict['_75'])
        self.assertAlmostEqual(p25, pdict['_25'], delta=0.01)        
        self.assertAlmostEqual(p50, pdict['_50'], delta=0.01)        
        self.assertAlmostEqual(p75, pdict['_75'], delta=0.01)
    def test_percentiles_fast_rq(self):
        """test_percentiles: Simple test for HistIndex based percentiles
        low accurracy => faster mode
        """
        return self._impl_tst_percentiles_rq(2.0)
    def test_percentiles_accurate_rq(self):
        """test_percentiles: Simple test for HistIndex based percentiles
        higher accurracy => slower mode
        """
        return self._impl_tst_percentiles_rq(0.2)
if __name__ == '__main__':
    main()
