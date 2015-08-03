#!/usr/bin/env python

from progressive.server.protocol import *
from progressive.server.scheduler_server import run_scheduler_server

import tornado.httpserver
import tornado.ioloop
import tornado.web
import functools
import multiprocessing
import random
import time

class ProgressiveRequestHandler(tornado.web.RequestHandler):
    def initialize(self, hub):
        self.hub = hub

    @tornado.web.asynchronous
    def get(self):
        path = self.request.path
        print "Sending a request for %s"%path
        arg = self.get_query_arguments('arg')
        if arg:
            arg = arg[0]
            print "Argument is '%s'"%(arg)
        else:
            arg = None
        req = Request(path, value=arg)
        self.hub.send(req, self._finish)
    
    def _finish(self, res):
        print "Entering ProgressiveRequestHandler._finish"
        self.write(res.value)
        print "Finishing the request."
        self.finish()

class MainHandler(tornado.web.RequestHandler):    
    def get(self):
        self.write("Welcome to the Progressive server")

class Hub(object):
    def __init__(self, pipe):
        self.pipe = pipe
        self.reqs = {}
        self.serial = 0

    def send(self, req, callback):
        self.serial += 1
        req.serial = self.serial
        self.reqs[self.serial] = callback
        print "Sending serial %d for %s to pipe"%(self.serial, req.path)
        self.pipe.send(req)

    def recv(self, fd, event):
        res = self.pipe.recv()
        print "Receiving serial %d for %s from pipe"%(res.serial, res.path)
        callback = self.reqs[res.serial]
        del self.reqs[res.serial]
        if res.path==Messages.WORKFLOW_STOP:
            tornado.ioloop.IOLoop.instance().remove_handler(self.pipe.fileno())
            tornado.ioloop.IOLoop.instance().stop()
        callback(res)


def server():
    fd1, fd2 = multiprocessing.Pipe()
    pipe = fd1
    fno = fd1.fileno()
    # Create a process for the sleepy function. Provide one pipe end.
    p = multiprocessing.Process(target=run_scheduler_server, args=(fd2,))
    p.start()
    hub = Hub(pipe)
    iol = tornado.ioloop.IOLoop.instance()
    iol.add_handler(fno, hub.recv, iol.READ)
    
    handlers = [(req, ProgressiveRequestHandler, {'hub': hub}) for req in Messages.ALL]
    application = tornado.web.Application([
        (r"/", MainHandler),
    ] + handlers)
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8888)
    print 'The HTTP server is listening on port 8888.'
    iol.start()
    http_server.stop()
    p.join()
    

if __name__ == '__main__':
    application = tornado.web.Application([
        (r"/", MainHandler),
        (r"/async", AsyncHandler),
    ])
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8888)
    print 'The HTTP server is listening on port 8888.'
    tornado.ioloop.IOLoop.instance().start()
    
