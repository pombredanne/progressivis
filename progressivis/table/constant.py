from __future__ import absolute_import, division, print_function

from .table import Table
from .module import TableModule

class Constant(TableModule):
    def __init__(self, table, **kwds):        
        super(Constant, self).__init__(**kwds)
        assert table is None or isinstance(table, Table)
        self._table = table

    def predict_step_size(self, duration):
        return 1
    
    def run_step(self,run_number,step_size,howlong):
        raise StopIteration()
