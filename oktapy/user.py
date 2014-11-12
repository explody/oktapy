import os
import sys
import pprint

from . import OktaConfig
from api import OktaApi, OktaObjectNotFound, OktaError, OktaInvalidArgs

global conf

conf = OktaConfig()
api = OktaApi()

class OktaException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
        
class OktaUserNoProfile(OktaException):
    def __init__(self, value):
        super(OktaUserNoProfile, self).__init__('OktaUserNoProfile: ' + value)
        
class OktaInvalidProfile(OktaException):
    def __init__(self, value):
        super(OktaInvalidProfile, self).__init__('OktaInvalidProfile: ' + value)

class OktaUserProfile(dict):
  
  def __init__(self, profile={}, **kwargs):
    self.mustf = conf.objdata['user']['profile']['must']
    super(OktaUserProfile, self).__init__(profile, **kwargs)
    self.__dict__ = self
    
    if profile:
      for k,v in profile.iteritems():
        setattr(self, k, v)
    if kwargs:
      for k,v in kwargs.iteritems():
        setattr(self,k,v)

  def add(self,key,value):
    setattr(self,key,value)
    
  def get(self,key):
    return self[key]
    
  def fields(self):
    return self.keys()
    
  def must(self):
    return conf.objdata['user']['profile']['must']
    
  def may(self):
    return conf.objdata['user']['profile']['may']
    
  def validfields(self):
    return self.must()+self.may()

  def validate(self, strict=False):

    if strict:
      invalids = []
      for k in self.keys():
        if k not in self.validfields():
          invalids.append(k)
      if invalids:
        raise OktaInvalidProfile('Invalid profile fields (strict checking enabled): ' + str(invalids) )
    
    missing = []
    for k in self.must():
      if k not in self:
        missing.append(k)
    if missing:
      raise OktaInvalidProfile('Required profile fields missing: ' + str(missing))
        
    return True

class OktaUserCredentials(dict):
  def __init__(self):
    super(OktaUserCredentials, self).__init__(profile, **kwargs)
    self.__dict__ = self

'''
'uid' can be any valid Okta unique key. e.g.
   login (user@domain.com)
   okta uid (string like "00ub0oNGTSWTBKOLGLNR")
'''
class OktaUser(object):
  
  def __init__(self, uid=None, strict=False):

    self.api = api.user
    self.strict = strict

    #for mth in self.api.methods:
    #  setattr(self, mth, getattr(self.api, mth))
    
    if uid is not None:
      self.uid = uid
      self._sync()
    else:
      self._userinit()
        
  def _userinit(self):
    self._new = True
    self.profile = OktaUserProfile()
    
  def _sync(self):
  
    try:
      userdata = self.api.get(uid=self.uid)
      for k,v in userdata.iteritems():
        if k == "profile":
          self.profile = OktaUserProfile(v)
        else:
          setattr(self,k,v)
      self.raw = userdata
      self.uuid = userdata['id']
      self._new = False
    except OktaObjectNotFound, e:
      self._userinit()

  def is_new(self):
    return self._new

  def save(self, strict=False):
    
    try:
      self.validate(strict=strict)
    except OktaException, e:
      print "Pre-save validation failed, cannot save: ", e
      return False

    return self._save()

    
  def _save(self):
    
    try:
      if self._new:
        ujson = self.api.create(data={'profile': self.profile})
      else:
        ujson = self.api.update(uid=self.id,data={'profile': self.profile})
      
      self._sync()

      return ujson
    
    except Exception, e:
      print "Error adding/updating user: ", e
    
  def validate(self,strict=False):
    
    if not hasattr(self, 'profile'):
      raise OktaUserNoProfile("User has no profile defined")
    
    if not isinstance(self.profile, OktaUserProfile):
      raise OktaInvalidProfile("Profile is not an OktaUserProfile")
    else:
      self.profile.validate(strict=strict)
    
    return True
      
      
      
class OktaUserList(dict):
  
  def __init__(self,filter=None):
    
    self.api = api
    if filter:
      userlist = api.user.list(args={ 'filter': filter })
    else:
      userlist = api.user.list()
      
    for user in userlist:
      self[user['id']] = user
      

def fetch(uid):
  pass

