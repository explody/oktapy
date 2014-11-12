import os
import sys
import yaml
import pprint

from .version import VERSION

__version__ = VERSION

global confpaths

# Paths to check, in order
#   calling script directory
#   module directory
#   user home directory
confpaths = ['/etc/oktapy',
             os.path.dirname(os.path.realpath(sys.argv[0])),
             os.path.dirname(os.path.realpath(__file__)),
             os.path.expanduser('~')]

class PivotalOktaException(Exception):
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)

class OktaConfigNotFound(Exception):
    def __init__(self, filename, paths):
        self.value = "Not found: [" + filename + "] I looked here:" + " ".join(paths)
    def __str__(self):
        return self.value

class OktaConfig(object):
  
  def __init__(self, conffile=None):
    
    oktaenv = os.environ['OKTA_ENV']
    
    if conffile is None:
      fname = 'okta.yml'
    else:
      fname = conffile

    try:
      confpath = find_config(fname)
    except OktaConfigNotFound, e:
      print "Could not find my config file: %s" % fname
      print "I checked these paths:"
      for path in confpaths:
        print "\t" + os.path.join(path, fname)
      sys.exit()
    
    self.confpath = confpath
    try:
      fh = open(confpath, "rb")
    except Exception, e:
      print "Error opening config: ", e
      
    conf = yaml.load(fh.read())

    if not oktaenv in conf['environments']:
      raise PivotalOktaException("No such environment is configured: %s" % oktaenv)

    for k,v in conf['environments'][oktaenv].iteritems():
      setattr(self,k,v)
      
    try:
      self.creds = creds_header(find_config(self.credfile))
    except OktaConfigNotFound, e:
      print "Credentials file error -", e
      sys.exit()
    
    objfile = find_config(self.objfile)
    ofh = open(objfile, "rb")
    self.objdata = yaml.load(ofh.read())
    
    apifile = find_config(self.apifile)
    afh = open(apifile, "rb")
    self.apidata = yaml.load(afh.read())

def find_config(filename):
  
  # expanduser here in case some passed a "~" path
  filename = os.path.expanduser(filename)
  
  if os.path.isfile(filename):
    return os.path.abspath(filename)
    
  for path in confpaths:
    confpath = os.path.join(path,filename)
    if os.path.isfile(confpath):
      return confpath
      
  raise OktaConfigNotFound(filename,confpaths)

def read_credentials(credfile):

  fh = open(credfile, "rb")
  creds = fh.read().rstrip()
  return creds
  
def creds_header(credfile):

  creds = read_credentials(credfile)
  
  hd = {
     'Authorization': creds,
     'Content-type': 'application/json',
     'Accept': 'application/json'
     }
     
  return hd
  
  
