#coding:utf-8
import wsgiref.handlers
import os
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api import users
import logging
from models import FileList,File,Folder
def format_date(dt):
    return dt.strftime('%a, %d %b %Y %H:%M:%S GMT')

class PublicPage(webapp.RequestHandler):
    def render(self, template_file, template_value):
        path = os.path.join(os.path.dirname(__file__), template_file)
        self.response.out.write(template.render(path, template_value))
    
    def error(self,code):
        if code==404:
            self.response.set_status(code)
            self.response.out.write("404")
        else:
            self.response.set_status(code)
            
    def is_admin(self):
        return users.is_current_user_admin()
    
    def head(self, *args):
        return self.get(*args) 
    
class MainPage(PublicPage):
    def get(self):
        folders = Folder.all().order('-slug')
        filelists = FileList.getnone()
        template_value={"folders":folders,'filelists':filelists,'path':'/'}
        self.render('views/index.html', template_value)

class Download(PublicPage):
    def get(self,id):
        id=int(id)
        filelist = FileList.get_by_id(id)
        if filelist:
            self.response.headers['Content-Type'] = str(filelist.mime)            
            self.response.out.write(filelist.bf)

class FolderPage(PublicPage):
    def get(self,path):
        folder=Folder.get_by_slug(path)
        if folder:
            self.render('views/folder.html',{'folder':folder})
        else:
            self.error(404)
    
class Error(PublicPage):
    def get(self):
        return self.error(404)

def main():
    application = webapp.WSGIApplication(
                                       [('/', MainPage),
                                        (r'/[a-z,0-9,-]+/(?P<id>[0-9]+)-.+',Download),
                                        (r'/(?P<id>[0-9]+)-.+',Download),
                                        (r'/(?P<path>[a-z,0-9,-]+)/',FolderPage),
                                        ('.*',Error),
                                       ], debug=True)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
    main()