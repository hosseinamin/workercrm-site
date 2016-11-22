from ..models import ConfigData
from ..apimod import ApiError, mk_readsingle_call, mk_readmulti_call
import json

configdataColumns = ('id', 'inherits_id', 'data')
configdataRelatedKeys = [ ]

def gcCheckAConfigData(configdata):
  for key in configdataRelatedKeys:
    if getattr(configdata,key).count() > 0: # has references
      return False
  configdata.delete()
  return True

def updateConfigData(user, id, data, inherits_id):
  if id == inherits_id:
    raise ApiError(406, "ConfigData and its inherits cannot be the same")
  configdata = ConfigData.objects.get(owner=user, id=id)
  if data != None:
    data = json.loads(data)
    configdata.data = data
  if inherits_id != None:
    if inherits_id == '': # set to null
      configdata.inherits = None
    else:
      iconfigdata = ConfigData.objects.get(owner=user, id=inherits_id)
      configdata.inherits = iconfigdata
  configdata.save()
  return { }

def createConfigData(user, data, inherits_id):
  data = json.loads(data)
  configdata = ConfigData(owner=user, data=data)
  if inherits_id != None:
    iconfigdata = ConfigData.objects.get(owner=user, id=inherits_id)
    configdata.inherits = iconfigdata
  else:
    configdata.inherits = None
  configdata.save()
  return { 'id': str(configdata.id) }

getConfigData = mk_readsingle_call( \
  lambda user, id: \
    (configdataColumns, ConfigData.objects.get(id=id, owner=user)))

def deleteConfigData(user, id):
  configdata = ConfigData.objects.get(owner=user, id=id)
  inherits = configdata.inherits
  configdata.delete()
  # configdata inherits is experimental and there's no gc for it
  #if inherits != None:
  #  gcCheckAConfigData(inherits)
  return { }
