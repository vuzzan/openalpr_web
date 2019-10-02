from openalpr import Alpr
import locale

import os, uuid
import sys
import logging
import signal

import tornado.web
import tornado.template
import tornado.ioloop
import tornado.httpserver

import json
import tornado.ioloop
import tornado.web
locale.setlocale(locale.LC_ALL, 'C')

__UPLOADS__ = "img/"


alpr = Alpr("vn", "/etc/openalpr/openalpr.conf", "/usr/share/openalpr/runtime_data")
alpr.set_top_n(20)
alpr.set_default_region("vn")


class IndexHandler(tornado.web.RequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self, path):
        """ GET method to list contents of directory or
        write index page if index.html exists."""

        # remove heading slash
        path = path[1:]

        for index in ['index.html', 'index.htm']:
            index = os.path.join(path, index)
            if os.path.exists(index):
                with open(index, 'rb') as f:
                    self.write(f.read())
                    self.finish()
                    return
        html = self.generate_index(path)
        self.write(html)
        self.finish()

    def generate_index(self, path):
        """ generate index html page, list all files and dirs.
        """
        if path:
            files = os.listdir(path)
        else:
            files = os.listdir('.')
        files = [filename + '/'
                if os.path.isdir(os.path.join(path, filename))
                else filename
                for filename in files]
        html_template = """
        <!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN"><html>
        <title>Directory listing for /{{ path }}</title>
        <body>
        <h2>Directory listing for /{{ path }}</h2>
        <hr>
        <ul>
        {% for filename in files %}
        <li><a href="{{ filename }}">{{ filename }}</a>
        {% end %}
        </ul>
        <hr>
        </body>
        </html>
        """
        t = tornado.template.Template(html_template)
        return t.generate(files=files, path=path)
        
class MainHandler(tornado.web.RequestHandler):
    def post(self):

        if 'image' not in self.request.files:
            self.finish('Image parameter not provided')

        fileinfo = self.request.files['image'][0]
        jpeg_bytes = fileinfo['body']

        if len(jpeg_bytes) <= 0:
            return False
            
        fname = fileinfo['filename']
        extn = os.path.splitext(fname)[1]
        extn0 = os.path.splitext(fname)[0]
        cname = extn0+"_"+str(uuid.uuid4()) + extn
        fh = open(__UPLOADS__ + cname, 'wb')
        fh.write(fileinfo['body'])

        results = alpr.recognize_array(jpeg_bytes)

        self.finish(json.dumps(results))
        
        


application = tornado.web.Application([
    (r"/alpr", MainHandler),
    (r'(.*)/$', IndexHandler,),
    (r"/(.*)", tornado.web.StaticFileHandler, {"path": "./", "default_filename": "index.html"},),
])

if __name__ == "__main__":
    application.listen(8080)
    tornado.ioloop.IOLoop.current().start()