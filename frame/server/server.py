import os.path
import logging
import json
import datetime
import asyncio

from queue import Queue
from logging.handlers import QueueHandler
from threading import Thread

import tornado
from tornado import web, gen, template
from tornado.iostream import StreamClosedError

event_logging_listener = None

class Server(tornado.web.Application):
    def __init__(self, event_list, event_logging_listener):
        handlers = [
            (r"/events", Events, dict(event_list=event_list)),
            (r"/events/{name}", Events, dict(event_list=event_list)),
            (r'/events/log', EventsLog, dict(listener=event_logging_listener))
        ]
        settings = {'debug': True}
        super().__init__(handlers, **settings)

    def run(self, port=8886):
        self.listen(port)
        tornado.ioloop.IOLoop.instance().start()

class Events(tornado.web.RequestHandler):
    SUPPORTED_METHODS = ["GET"]

    def initialize(self, event_list):
        self.template = template.Loader("frame/server/templates").load("events.html")
        self.event_list = event_list

    def prepare(self):
        pass

    def get(self, event_id=None):
        event_id = None
        if event_id == None:
            page = self.template.generate(
                events=self.event_list
            )
            self.write(page)
        else:
            self.write('')

class EventsLog(tornado.web.RequestHandler):
    SUPPORTED_METHODS = ["GET"]

    def initialize(self, listener):
        self.queue = Queue()
        self.handler = QueueHandler(self.queue)
        self.listener = listener
        listener.handlers = listener.handlers = (self.handler,)

    def prepare(self):
        self.set_header('content-type', 'text/event-stream')
        self.set_header('cache-control', 'no-cache')

    @gen.coroutine
    def get(self):
        while True:
            if self.queue.empty():
                yield gen.sleep(0.005)
            else:
                record = self.queue.get(False)
                record_json = {
                    'time': datetime.datetime.fromtimestamp(record.created).strftime('%H:%M:%S'),
                    'name': record.name,
                    'level': record.levelname,
                    'message': record.getMessage()
                }
                try:
                    self.write('data: %s\n\n' % json.dumps(record_json))
                    yield self.flush()
                except StreamClosedError:
                    return

    def on_finish(self):
        handlers = list(self.listener.handlers)
        handlers.remove(self.handler)
        self.listener.handlers = tuple(handlers)

def run_server(event_logging_queue, event_list):
    event_logging_listener = logging.handlers.QueueListener(event_logging_queue)
    event_logging_listener.start()

    # SUBTLE: We need an event loop running on the thread that owns the server.
    # Since the main thread is owned by QT, we need another thread to own the
    # server event loop.
    def start_server():
        asyncio.set_event_loop(asyncio.new_event_loop())

        ws = Server(
            event_list=event_list,
            event_logging_listener=event_logging_listener)
        ws.run()

    t = Thread(target=start_server, args=())
    t.daemon = True
    t.start()

    return {}
