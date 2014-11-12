
import yaml
import pprint
import requests
import urllib
import simplejson as json

from . import OktaConfig

global conf

conf = OktaConfig()

class OktaObjectNotFound(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
        
class OktaError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
        
class OktaInvalidArgs(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
        
class OktaApiGroup(object):
  def __init__(self):
    self.methods = []
  def register_method(self, mthname):
    self.methods.append(mthname)
    
class OktaApiMethod(OktaApiGroup):

  def __init__(self, apiobj, mthdata):
    self.mthdata = mthdata
    self.http_method = mthdata['method']
    
    if 'public' in mthdata:
      self.public = mthdata['public']
    else:
      self.public = False
      
    self.url = "https://%s%s%s" % (apiobj.host,
                                   apiobj.basepath,
                                   mthdata['path'])
    self.host = apiobj.host
    self.creds = apiobj.creds
    self.api = apiobj

  def __call__(self, **kwargs):
    
    # This is where we can put validations on the kwargs,
    # based off data in okta-api.yml (not there yet)
    
    url = self.url

    if 'uid' in kwargs:
      uid = kwargs['uid']
      url = url.replace(':uid',uid)

    if 'gid' in kwargs:
      uid = kwargs['gid']
      url = url.replace(':gid',uid)
      
    if 'params' in kwargs:
      params = kwargs['params']
      
    if 'data' in kwargs:
      data = kwargs['data']
    else:
      data = {}
    
    if 'args' in kwargs:
      if not isinstance(kwargs['args'], dict):
        raise OktaInvalidArgs("Invalid arguments. Should be a dict.")
      self.args = kwargs['args']
    else:
      self.args = {}
        
    if 'defargs' in self.mthdata:
      for arg,val in self.mthdata['defargs'].iteritems():
        if arg not in self.args:
          self.args[arg] = val
           
    # TODO: get rid of this shit 
    if len(self.args) > 0:
      encoded_args = urllib.urlencode(self.args)
      url = "%s?%s" % (url,encoded_args)

    try:

      resp = None
      while True:

        if self.http_method == "GET":
          r = requests.get(url, headers=self.creds)
        elif self.http_method == "POST":
          r = requests.post(url, data=json.dumps(data), headers=self.creds)
        elif self.http_method == "PUT":
          r = requests.put(url, data=json.dumps(data), headers=self.creds)
        elif self.http_method == "DELETE":
          r = requests.delete(url, data=json.dumps(data), headers=self.creds)

        # This is a valid return code for successful add/remove-user-to-group in Okta
        if r.status_code == 204:
          return True

        if r.status_code == 404:
          raise OktaObjectNotFound("Object not found. Tried: %s. Okta says: %s" % (url, r.json()))
        elif r.status_code != 200:
          print "ERROR: Return code", r.status_code
          raise OktaError("ERROR at %s. Okta says: %s" % (url, r.json()))

        thisresp = r.json()

        if isinstance(resp, list):
          resp.extend(thisresp)
        elif isinstance(resp, dict):
          resp.update(thisresp)
        else:
          resp = thisresp

        if not 'next' in r.links:
          break
        else:
          url = r.links['next']['url']

    except requests.exceptions.HTTPError, e:
      raise OktaError("ERROR: %s" % (e))
        
    return resp

  # later
  def validate_params(params):
    pass
    
  # later
  def validate_args(args):
    pass


class OktaApi(object):

  def __init__(self, **kwargs):
    
    fh = open(conf.apifile, "rb")
    self.apiconfig = yaml.load(fh.read())
    
    self.host = conf.host
    self.creds = conf.creds
    self.basepath = self.apiconfig['basepath']

    # loop through the classes in okta-api.yml
    for cls,mths in self.apiconfig['classes'].iteritems():
      
      # Each top level class name will be an OktaApiGroup
      new_type = type(cls,(OktaApiGroup,),{})
      new_cls = new_type()

      # For each defined method, add an OktaApiMethod as
      # an attribute in the OktaApiGroup instance
      for mth,data in mths.iteritems():
        setattr(new_cls, mth, OktaApiMethod(self,data))
        new_cls.register_method(mth)

      setattr(self,cls,new_cls)
      
  def methods(self):
    pass

    
