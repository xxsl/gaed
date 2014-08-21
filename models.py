#coding:utf-8
import re,logging,os
from google.appengine.ext import db
import urllib,datetime,random,string

class Folder(db.Model):
    name = db.StringProperty()
    slug = db.StringProperty()
    last_modified = db.DateTimeProperty(auto_now_add=True)
    count = db.IntegerProperty(default=0)
    
    def put(self):
        self.slug =urllib.quote(re.sub(r'-+', '-', re.sub(r'\s', '-', re.sub(r'[:/?#\[\]\'*.,&]', '', self.slug).strip())).lower().encode('utf8'))
        
        if self.slug == "" or self.name == "":
            return
        super(Folder,self).put()
    
    def delete(self):
        #make ture all files path change to '/'
        for filelist in self.filelists:
            filelist.folder=None
            filelist.put()
        super(Folder,self).delete()

    @property
    def path(self):
        return "/%s/" % self.slug
    
    @property
    def sort_filelists(self):
        return self.filelists.order('-created_at')

    @classmethod
    def add(cls,name,slug):
        folder=Folder(name=name,slug=slug)
        folder.put()
        
    @classmethod
    def modify(cls,key,name,slug):
        folder=Folder.get(key)
        folder.name = name
        folder.slug = slug
        folder.put()
    
    @classmethod 
    def get_by_slug(cls,slug):
        return Folder.gql('WHERE slug = :1',slug).get()

class FileList(db.Model):
    name = db.StringProperty()
    mime = db.StringProperty()
    created_at = db.DateTimeProperty(auto_now_add=True)
    size = db.IntegerProperty()
    slug = db.StringProperty()
    
    count = db.IntegerProperty(default=0)
    folder = db.ReferenceProperty(Folder,collection_name='filelists')

    def put(self):
        if not self.slug:
            self.slug = self.name
        if self.folder:
            self.folder.count+=1
            self.folder.last_modified=datetime.datetime.now()
            self.folder.put()
        super(FileList,self).put()
        
    def delete(self):
        for file in self.files:
            file.delete()
        super(FileList,self).delete()
        
    @property
    def url(self):
        return '%s%s-%s' % (self.path,self.key().id(),self.slug)
    
    @property
    def path(self):
        return '/' if self.folder is None else self.folder.path

    @property
    def bf(self):
        bflist=[]
        [bflist.append(file.bf) for file in self.files]
        self.count+=1
        self.put()
        return ''.join(bflist)
    

    @classmethod
    def add(cls,name,mime,bf):
        filelist=FileList(name=name,mime=mime)
        filelist.size = len(bf)
        filelist.put()
        
        start =0
        splitelen=1000*1000 # 1M limit
        while start<filelist.size:
            file=File(bf=bf[start:start+splitelen],fileList=filelist)
            file.put()
            start+=splitelen

    @classmethod
    def modify(cls,key,slug,path_key):
        filelist = FileList.get(key)
        filelist.slug = slug
        filelist.folder=None if path_key =="" else Folder.get(path_key)
        filelist.put()
    
    @classmethod
    def getnone(cls):
        return FileList.all().filter("folder =", None).order('-created_at')

class File(db.Model):
    bf = db.BlobProperty() #binary file
    fileList = db.ReferenceProperty(FileList,collection_name='files')

class Setting(db.Model):
    rpcupload=db.BooleanProperty(default=False)
    rpcuser=db.StringProperty(default='admin')
    rpcpwd=db.StringProperty()
    enable_memorycache=db.BooleanProperty(default=False)
    
    @classmethod
    def getsetting(cls):
        setting = Setting.get_by_key_name('setting')
        if setting is None:
            setting=Setting(key_name = 'setting')
            #random pwd
            setting.rpcpwd=''.join(random.sample(string.letters+string.digits,8))
            setting.put()
        return setting
    