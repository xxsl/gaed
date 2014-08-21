#coding:utf-8
import wsgiref.handlers
import os,re
from functools import wraps
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api import users
from django.utils import simplejson
from models import FileList,File,Folder,Setting
import logging

class AdminControl(webapp.RequestHandler):
    def render(self,template_file,template_value):
        path=os.path.join(os.path.dirname(__file__),template_file)
        self.response.out.write(template.render(path, template_value))
    def returnjson(self,dit):
        self.response.headers['Content-Type'] = "application/json"
        self.response.out.write(simplejson.dumps(dit))
    
def requires_admin(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if not users.is_current_user_admin():
            self.redirect(users.create_login_url(self.request.uri))
        else:
            return method(self, *args, **kwargs)
    return wrapper

class Admin_Upload(AdminControl):
    @requires_admin
    def get(self):
        self.render('views/admin/upload.html', {})
        
    @requires_admin
    def post(self):
        bf=self.request.get("file")
        if not bf:
            return self.redirect('/admin/upload/')

        name=unicode(self.request.body_file.vars['file'].filename,'utf-8')
        mime = self.request.body_file.vars['file'].headers['content-type']
        
        #handle file than 10M 
        if len(bf)>10*1000*1000:
            self.redirect('/admin/upload/')
            
        FileList.add(name, mime, bf)
        self.redirect('/admin/')
        
class Admin_Login(AdminControl):
    @requires_admin
    def get(self):
        PAGESIZE = 20
        next=None
        prev=None
        
        page = self.request.get('page')
        page = int(page) if page else 1
        
        filelists=FileList.all().order('-created_at').fetch(PAGESIZE+1, PAGESIZE*(page-1))
        
        if page>1:
            prev=page-1
        
        if len(filelists)==PAGESIZE+1:
            next=page+1

        filelists=filelists[0:PAGESIZE]
        template_value={"filelists":filelists,'prev':prev,'next':next}
        self.render('views/admin/file.html', template_value)


class Admin_Del(AdminControl):
    @requires_admin
    def get(self,key):
        filelist=FileList.get(key)
        filelist.delete()
        self.redirect('/admin/')
        
class Admin_Edit(AdminControl):
    @requires_admin
    def get(self,key):
        filelist=FileList.get(key)
        folders=Folder.all().order('count')
        self.render('views/admin/fileedit.html', {'filelist':filelist,'folders':folders})
    
    @requires_admin
    def post(self,key):
        slug=self.request.get("slug")
        path_key = self.request.get("path")
        FileList.modify(key, slug, path_key)
        self.redirect('/admin/', '304')
        
class Admin_Folder(AdminControl):
    @requires_admin
    def get(self):
        folders = Folder.all().order('-last_modified')
        self.render('views/admin/folder.html', {'folders':folders})

class Admin_FolderAdd(AdminControl):
    @requires_admin
    def get(self):
        self.render('views/admin/folderadd.html',{})
        
    @requires_admin
    def post(self):
        name=self.request.get("name")
        slug=self.request.get("slug")
        Folder.add(name, slug)
        self.redirect('/admin/folder/', '302')

class Admin_FolderDel(AdminControl):
    @requires_admin
    def get(self,key):
        folder = Folder.get(key)
        folder.delete()
        self.redirect('/admin/folder/', '302')
        
class Admin_FolderEdit(AdminControl):
    @requires_admin
    def get(self,key):
        folder=Folder.get(key)
        self.render('views/admin/folderedit.html', {'folder':folder,'key':key})
        
    @requires_admin
    def post(self,key):
        name=self.request.get("name")
        slug=self.request.get("slug")
        Folder.modify(key, name, slug)
        
        self.redirect('/admin/folder/', '302')
        
class Admin_Setting(AdminControl):
    @requires_admin
    def get(self):
        setting=Setting.getsetting()
        self.render('views/admin/setting.html',{'setting':setting})
    
    @requires_admin
    def post(self):
        rpcupload=self.request.get('rpcupload')
        rpcuser=self.request.get('rpcuser')
        rpcpwd=self.request.get('rpcpwd')
        
        logging.info(rpcupload)
        setting=Setting.getsetting()
        setting.rpcupload=(rpcupload=='1')
        setting.rpcuser=rpcuser
        setting.rpcpwd=rpcpwd
        setting.put()
        self.redirect('/admin/', '302')
        
    
def main():
    application = webapp.WSGIApplication(
                                       [(r'/admin/upload/', Admin_Upload),
                                        (r'/admin/', Admin_Login),
                                        (r'/admin/del/(?P<key>.+)',Admin_Del),
                                        (r'/admin/edit/(?P<key>.+)',Admin_Edit),
                                        
                                        #folder
                                        (r'/admin/folder/',Admin_Folder),
                                        (r'/admin/folder/add/',Admin_FolderAdd),
                                        (r'/admin/folder/del/(?P<key>.+)',Admin_FolderDel),
                                        (r'/admin/folder/edit/(?P<key>.+)',Admin_FolderEdit),
                                        
                                        #setting
                                        (r'/admin/setting/',Admin_Setting),
                                       ], debug=True)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
    main()