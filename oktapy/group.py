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
        
class OktaGroupNoProfile(OktaException):
    def __init__(self, value):
        super(OktaGroupNoProfile, self).__init__('OktaGroupNoProfile: ' + value)
        
class OktaInvalidProfile(OktaException):
    def __init__(self, value):
        super(OktaInvalidProfile, self).__init__('OktaInvalidProfile: ' + value)

class OktaGroupProfile(dict):
  
  def __init__(self, profile={}, **kwargs):
    self.mustf = conf.objdata['group']['profile']['must']
    super(OktaGroupProfile, self).__init__(profile, **kwargs)
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
    return conf.objdata['group']['profile']['must']
    
  def may(self):
    return conf.objdata['group']['profile']['may']
    
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

'''
OktaGroup
Takes either a group name or group ID
'''
class OktaGroup(object):
  
  def __init__(self, name=None, gid=None, strict=False):
    
    self.api = api.group
    self.strict = strict
    self._gid = None
    self._name = None
    
    if gid is not None:
      self._gid = gid
      self._sync()
    elif name is not None:
      self._name = name
      self._sync()
    else:
      self._groupinit()
        
  def _groupinit(self):
    self._new = True
    self.profile = OktaGroupProfile()
    
  # TODO: change the name of this to _pull or _fetch or something
  # Unlike OktaUser, _sync does a search() here rather than a get() because okta only supports doing a group get() using the GID
  # We want to support grabbing a group by name as well so we have to search()
  def _sync(self):

    groupdata = None

    if self._gid:
      try:
        groupdata = self.api.get(gid=self._gid)
      except OktaObjectNotFound, e:
        raise OktaObjectNotFound("Found no group with GID %s" % self._gid)
    elif self._name:
      group_result = self.api.search(args={'q': self._name, 'limit': 1})
      if len(group_result) == 1:
        groupdata = group_result[0]

    if groupdata:
      for k,v in groupdata.iteritems():
        if k == "profile":
          self.profile = OktaGroupProfile(v)
        else:
          setattr(self,k,v)
      self.raw = groupdata
      self.uuid = groupdata['id']
      self._new = False
    else:
      print "NO GROUPDATA"
      self._groupinit()

  def is_new(self):
    return self._new
    
  def adduser(self,uid):
    self.api._adduser(gid=self._gid,uid=uid)

  def deluser(self,uid):
    self.api.deluser(gid=self._gid,uid=uid)

  def members(self):
    return self.api.members(gid=self._gid)
    
  def save(self, strict=False):
    
    try:
      self.validate(strict=strict)
    except OktaException, e:
      print "Pre-save validation failed, cannot save: ", e
      return False

    self._save()   
    
  def _save(self):
    
    try:
      if self._new:
        self.api.create(data={'profile': self.profile})
      else:
        self.api.update(gid=self.id,data={'profile': self.profile})
      
      self._sync()
    
    except Exception, e:
      print "Error adding/updating group: ", e
    
  def validate(self,strict=False):
    
    if not hasattr(self, 'profile'):
      raise OktaGroupNoProfile("Group has no profile defined")
    
    if not isinstance(self.profile, OktaGroupProfile):
      raise OktaInvalidProfile("Profile is not an OktaGroupProfile")
    else:
      self.profile.validate(strict=strict)
    
    return True
      
class OktaGroupList(dict):

  def __init__(self,query=None,limit=None):

    self.api = api

    args = {}

    if limit:
      args['limit'] = limit

    if query:
      args['q'] = query

    grouplist = api.group.list(args=args)

    for group in grouplist:
      self[group['id']] = group

