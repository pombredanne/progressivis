from . import ProgressiveTest

from progressivis import Every
from progressivis.stats import Percentiles
from progressivis.io import CSVLoader
from progressivis.datasets import get_dataset

class TestPercentiles(ProgressiveTest):
    def test_percentile(self):
        s = self.scheduler()
        csv_module = CSVLoader(get_dataset('smallfile'), index_col=False, header=None, scheduler=s)
        module=Percentiles('_1', name='test_percentile',
                           percentiles=[0.1, 0.25, 0.5, 0.75, 0.9],
                           scheduler=s)
        module.input.table = csv_module.output.table
        prt = Every(proc=self.terse, name='print', scheduler=s)
        prt.input.df = module.output.percentiles
                
        s.start()
        s.join()
        #ret = module.trace_stats(max_runs=1)
        #print "Done. Run time: %gs, loaded %d rows" % (s['duration'].irow(-1), len(module.df()))
        #pd.set_option('display.expand_frame_repr', False)
        #print(repr(module.table()))

if __name__ == '__main__':
    ProgressiveTest.main()
