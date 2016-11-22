from ..models import Config, ConfigData
import json
from ..apimod import ApiError, mk_readsingle_call, mk_readmulti_call
from .configdata import configdataColumns, configdataRelatedKeys, \
  gcCheckAConfigData

configdataRelatedKeys.append("config_set")

configColumns = ('id', 'name', 'configdata_id')


def updateConfig(user, id, name, configdata):
  config = Config.objects.get(owner=user, id=id)
  if name != None:
    config.name = name
  if configdata != None:
    data = json.loads(configdata)
    try:
      config.configdata.data = data
    except ConfigData.DoesNotExist:
      config.configdata = ConfigData(data=data, inherits=None)
    config.configdata.save()
  config.save()
  return { }

def createConfig(user, name, configdata):
  # make new configdata
  data = json.loads(configdata)
  configdata = ConfigData(owner=user, inherits=None, data=data)
  configdata.save()
  config = Config(owner=user, name=name, configdata=configdata)
  config.save()
  return { 'id': str(config.id) }

_ccdColumn = ({
  'name': "configdata",
  'type': "onerel",
  'columns': configdataColumns
},)

def _getConfigsFunc(user, offset, limit, query):
  records = Config.objects.filter(owner=user) \
     if query == "" or query == None \
     else Config.objects.filter(owner=user, name__icontains=query)
  return (configColumns, records[offset:offset+limit], records.count())
getConfigs = mk_readmulti_call(_getConfigsFunc)

getConfig = mk_readsingle_call( \
  lambda user, id, with_configdata: \
    (configColumns + (_ccdColumn if with_configdata else ()), \
     Config.objects.get(id=id, owner=user)))

def deleteConfig(user, id):
  config = Config.objects.get(owner=user, id=id)
  configdata = config.configdata
  config.delete()
  gcCheckAConfigData(configdata)
  return { }
