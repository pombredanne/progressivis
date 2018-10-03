from __future__ import absolute_import
from . import ProgressiveTest, skip
from progressivis.io import CSVLoader
from progressivis.table.constant import Constant
from progressivis.table.table import Table
from progressivis.datasets import (get_dataset, get_dataset_bz2,
                                       get_dataset_gz,
                                       get_dataset_lzma, DATA_DIR)
from progressivis.core.utils import RandomBytesIO
from progressivis.stats.counter import Counter

#import logging, sys
from multiprocessing import Process
import time, os
import requests
from requests.packages.urllib3.exceptions import ReadTimeoutError
from requests.exceptions import ConnectionError
from progressivis.core.utils import decorate, ModulePatch

from RangeHTTPServer import RangeRequestHandler
import six
import shutil
if six.PY3:
    import http.server as http_srv
else:
    import SimpleHTTPServer as http_srv

BZ2 = 'csv.bz2'
GZ = 'csv.gz'
XZ = 'csv.xz'
#TRAVIS = os.getenv("TRAVIS")

PORT = 8000
HOST = 'localhost'
SLEEP = 5

def _close(module):
    try:
        module.parser._input._stream.close()
    except:
        pass

class Patch1(ModulePatch):
    max_steps = 10000
    def before_run_step(self, m, *args, **kwargs):
        if m._table is not None and len(m._table) >Patch1.max_steps :
            print("Simulate a crash ...")
            m.scheduler().stop()
            #if hasattr(m._table, '__append'):
            #    return
            #m._table.__append = m._table.append

def make_url(name, ext='csv'):
    return 'http://{host}:{port}/{name}.{ext}'.format(host=HOST,
                                                        port=PORT,
                                                        name=name, ext=ext)

def run_simple_server():
    _ = get_dataset('smallfile')
    _ = get_dataset('bigfile')
    _ = get_dataset_bz2('smallfile')
    _ = get_dataset_bz2('bigfile')
    _ = get_dataset_gz('smallfile')
    _ = get_dataset_gz('bigfile')
    #if six.PY3:
    #    _ = get_dataset_lzma('smallfile')
    #    _ = get_dataset_lzma('bigfile')
    os.chdir(DATA_DIR)
    if six.PY2:
        import SimpleHTTPServer
        import RangeHTTPServer
        from RangeHTTPServer import RangeRequestHandler
        import sys
        sys.argv[1] = 8000
        SimpleHTTPServer.test(HandlerClass=RangeRequestHandler)
    else:
        import RangeHTTPServer.__main__

class _HttpSrv(object):
    def __init__(self):
        _HttpSrv.start(self)

    def stop(self):
        if self._http_proc is not None:
            try:
                self._http_proc.terminate()
                time.sleep(SLEEP)
            except:
                pass

    def start(self):
        p = Process(target=run_simple_server, args=())
        p.start()
        self._http_proc = p
        time.sleep(SLEEP)

    def restart(self):
        self.stop()
        self.start()

        
class TestProgressiveLoadCSVCrash(ProgressiveTest):
    def setUp(self):
        super(TestProgressiveLoadCSVCrash, self).setUp()        
        self._http_srv = None

    def tearDown(self):
        TestProgressiveLoadCSVCrash.cleanup()
        if self._http_srv is not None:
            try:
                self._http_srv.stop()
            except:
                pass
    def test_01_read_http_csv_with_crash(self):
        #if TRAVIS: return
        self._http_srv =  _HttpSrv()
        s=self.scheduler()
        url = make_url('bigfile')
        module=CSVLoader(url, index_col=False, header=None, scheduler=s)
        self.assertTrue(module.table() is None)
        Patch1.max_steps = 200000
        decorate(s, Patch1("csv_loader_1"))
        s.start()
        s.join()
        self._http_srv.restart()
        s=self.scheduler()
        module=CSVLoader(url, recovery=True, index_col=False, header=None, scheduler=s)
        self.assertTrue(module.table() is None)
        s.start()
        s.join()
        self.assertEqual(len(module.table()), 1000000)

    def test_01_read_http_csv_with_crash_and_counter(self):
        #if TRAVIS: return
        self._http_srv =  _HttpSrv()
        s=self.scheduler()
        url = make_url('bigfile')
        module=CSVLoader(url, index_col=False, header=None, scheduler=s)
        self.assertTrue(module.table() is None)
        Patch1.max_steps = 200000
        decorate(s, Patch1("csv_loader_1"))
        s.start()
        s.join()
        self._http_srv.restart()
        s=self.scheduler()
        csv=CSVLoader(url, recovery=True, index_col=False, header=None, scheduler=s)
        counter = Counter(scheduler=s)
        counter.input.table = csv.output.table
        self.assertTrue(csv.table() is None)
        s.start()
        s.join()
        self.assertEqual(len(csv.table()), 1000000)
        self.assertEqual(counter.table()['counter'].loc[0], 1000000)

    def test_02_read_http_csv_bz2_with_crash(self):
        #if TRAVIS: return
        self._http_srv =  _HttpSrv()
        s=self.scheduler()
        url = make_url('bigfile', ext=BZ2)
        module=CSVLoader(url, index_col=False, header=None, scheduler=s)
        self.assertTrue(module.table() is None)
        Patch1.max_steps = 200000
        decorate(s, Patch1("csv_loader_1"))
        s.start()
        s.join()
        self._http_srv.restart()
        s=self.scheduler()
        module=CSVLoader(url, recovery=True, index_col=False, header=None, scheduler=s)
        self.assertTrue(module.table() is None)
        s.start()
        s.join()
        self.assertEqual(len(module.table()), 1000000)

    def test_03_read_http_multi_csv_no_crash(self):
        #if TRAVIS: return
        self._http_srv =  _HttpSrv()
        s=self.scheduler()
        module=CSVLoader([make_url('smallfile'),make_url('smallfile')], index_col=False, header=None, scheduler=s)
        self.assertTrue(module.table() is None)
        #decorate(s, Patch1("csv_loader_1"))
        s.start()
        s.join()
        self.assertEqual(len(module.table()), 60000)

    def test_04_read_http_multi_csv_bz2_no_crash(self):
        #if TRAVIS: return
        self._http_srv =  _HttpSrv()
        s=self.scheduler()
        module=CSVLoader([make_url('smallfile', ext=BZ2)]*2, index_col=False, header=None, scheduler=s)
        self.assertTrue(module.table() is None)
        #decorate(s, Patch1("csv_loader_1"))
        s.start()
        s.join()
        self.assertEqual(len(module.table()), 60000)

    def test_05_read_http_multi_csv_with_crash(self):
        #if TRAVIS: return
        self._http_srv =  _HttpSrv()
        s=self.scheduler()
        url_list = [make_url('bigfile'),make_url('bigfile')]
        module=CSVLoader(url_list, index_col=False, header=None, scheduler=s)
        self.assertTrue(module.table() is None)
        Patch1.max_steps = 1200000
        decorate(s, Patch1("csv_loader_1"))
        s.start()
        s.join()
        self._http_srv.restart()
        s=self.scheduler()
        module=CSVLoader(url_list, recovery=True, index_col=False, header=None, scheduler=s)
        self.assertTrue(module.table() is None)
        s.start()
        s.join()
        self.assertEqual(len(module.table()), 2000000)

    def test_06_read_http_multi_csv_bz2_with_crash(self):
        #if TRAVIS: return
        self._http_srv =  _HttpSrv()
        s=self.scheduler()
        url_list = [make_url('bigfile', ext=BZ2)]*2
        module=CSVLoader(url_list, index_col=False, header=None, scheduler=s)
        self.assertTrue(module.table() is None)
        Patch1.max_steps = 1200000
        decorate(s, Patch1("csv_loader_1"))
        s.start()
        s.join()
        self._http_srv.restart()
        s=self.scheduler()
        module=CSVLoader(url_list, recovery=True, index_col=False, header=None, scheduler=s)
        self.assertTrue(module.table() is None)
        s.start()
        s.join()
        self.assertEqual(len(module.table()), 2000000)

    def test_07_read_multi_csv_file_no_crash(self):
        s=self.scheduler()
        module=CSVLoader([get_dataset('smallfile'), get_dataset('smallfile')], index_col=False, header=None, scheduler=s)
        self.assertTrue(module.table() is None)
        #decorate(s, Patch1("csv_loader_1"))
        s.start()
        s.join()
        self.assertEqual(len(module.table()), 60000)

    def _tst_08_read_multi_csv_file_compress_no_crash(self, files):
        s=self.scheduler()
        module=CSVLoader(files, index_col=False, header=None, scheduler=s)#, save_context=False)
        self.assertTrue(module.table() is None)
        #decorate(s, Patch1("csv_loader_1"))
        s.start()
        s.join()
        self.assertEqual(len(module.table()), 60000)

    def test_08_read_multi_csv_file_bz2_no_crash(self):
        files = [get_dataset_bz2('smallfile')]*2
        return self._tst_08_read_multi_csv_file_compress_no_crash(files)

    def test_08_read_multi_csv_file_gz_no_crash(self):
        files = [get_dataset_gz('smallfile')]*2
        return self._tst_08_read_multi_csv_file_compress_no_crash(files)
    
    @skip("Too slow ...")
    def test_08_read_multi_csv_file_lzma_no_crash(self):
        if six.PY2:
            return
        files = [get_dataset_lzma('smallfile')]*2
        return self._tst_08_read_multi_csv_file_compress_no_crash(files)

    def test_09_read_multi_csv_file_with_crash(self):
        s=self.scheduler()
        file_list = [get_dataset('bigfile'), get_dataset('bigfile')]
        module=CSVLoader(file_list, index_col=False, header=None, scheduler=s)
        self.assertTrue(module.table() is None)
        Patch1.max_steps = 1200000
        decorate(s, Patch1("csv_loader_1"))
        s.start()
        s.join()
        _close(module)
        s=self.scheduler()
        module=CSVLoader(file_list, recovery=True, index_col=False, header=None, scheduler=s)
        self.assertTrue(module.table() is None)
        s.start()
        s.join()
        self.assertEqual(len(module.table()), 2000000)

    def _tst_10_read_multi_csv_file_compress_with_crash(self, file_list):
        s=self.scheduler()
        module=CSVLoader(file_list, index_col=False, header=None, scheduler=s)
        self.assertTrue(module.table() is None)
        Patch1.max_steps = 1200000
        decorate(s, Patch1("csv_loader_1"))
        s.start()
        s.join()
        _close(module)
        s=self.scheduler()
        module=CSVLoader(file_list, recovery=True, index_col=False, header=None, scheduler=s)
        self.assertTrue(module.table() is None)
        s.start()
        s.join()
        self.assertEqual(len(module.table()), 2000000)

    def test_10_read_multi_csv_file_bz2_with_crash(self):
        file_list = [get_dataset_bz2('bigfile')]*2
        self._tst_10_read_multi_csv_file_compress_with_crash(file_list)

    def test_10_read_multi_csv_file_gzip_with_crash(self):
        file_list = [get_dataset_gz('bigfile')]*2
        self._tst_10_read_multi_csv_file_compress_with_crash(file_list)

    @skip("Too slow ...")
    def test_10_read_multi_csv_file_lzma_with_crash(self):
        if six.PY2:
            return
        file_list = [get_dataset_lzma('bigfile')]*2
        self._tst_10_read_multi_csv_file_compress_with_crash(file_list)

if __name__ == '__main__':
    ProgressiveTest.main()
