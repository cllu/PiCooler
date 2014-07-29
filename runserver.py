#!/usr/bin/env python
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from cooler import app

http_server = HTTPServer(WSGIContainer(app))
http_server.listen(31415)
IOLoop.instance().start()

#from autodorm import app
#app.run(debug=True, host="0.0.0.0", port=80)