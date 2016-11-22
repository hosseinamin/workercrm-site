from .models import Worker, ConfigData
from django.contrib.auth.models import User
from .auth import token_parse, token_new, sign, verify, VerificationExpired
from time import time
import random
import sys
import json
from .apimod import apiinit, evalargs, ApiError, mk_readsingle_call
from .api_1_0.worker import updateWorker, createWorker, getWorker, getWorkers,\
  deleteWorker
from .api_1_0.config import updateConfig, createConfig, getConfig, getConfigs,\
  deleteConfig
from .api_1_0.configdata import updateConfigData, createConfigData, \
  getConfigData, deleteConfigData
import re

def login(username, password, expires):
  try:
    user = User.objects.get_by_natural_key(username)
    if user.check_password(password):
      # verified login, make a token
      start_time = int(time())
      expire_time = start_time + expires
      user_id = str(user.id)
      data = (user_id + "," + \
              str(random.randint(0, sys.maxsize))).encode('UTF-8')
      signature = sign(data, start_time, expire_time)
      return {
        "token": token_new(data, start_time, expire_time, signature).decode('UTF-8')
      }
  except User.DoesNotExist:
    pass
  raise ApiError(403, "Failed! (Username/Password does not match))")

def register(username, email, password):
  user = User.objects.create_user(username, email, password)
  return {
    "id": str(user.id)
  }

def registerValidateUser(v):
  try:
    User.objects.get_by_natural_key(v)
    raise ApiError(406, "username unavailable!")
  except User.DoesNotExist:
    pass

myInfoColumns = ['username','first_name','last_name','email']
myInfo = mk_readsingle_call(lambda user: (myInfoColumns, user))

email_pttrn = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")
def emailValidate(v):
  if email_pttrn.match(v) == None:
    raise ApiError(406, "Invalid email has given")

apicalls = {
'1.0': {
  # User apicalls 
  'login': {
    'POST': {
      'function': login,
      'args': [
        {
          'name': 'username',
          'type': str,
          'required': True
        },
        {
          'name': 'password',
          'type': str,
          'required': True
        },
        {
          'name': 'expires',
          'default': 60 * 60 * 24,
          'max': 60 * 60 * 24 * 30 * 3,
          'type': int
        }
      ]
    }
  },
  'register': {
    'POST': {
      'function': register,
      'args': [
        {
          'name': 'username',
          'type': str,
          'required': True,
          'validateAfter': registerValidateUser
        },
        {
          'name': 'password',
          'type': str,
          'required': True
        },
        {
          'name': 'email',
          'type': str,
          'validate': emailValidate,
          'required': True
        }
      ]
    }
  },
  'myInfo': {
    'GET': {
      'function': myInfo,
      'method': 'GET',
      'args': [
        { 'name': 'user', 'gname': 'user', 'global': True, 'required': True },
      ]
    }
  },
  # Worker apicalls
  'workers': {
    'GET': {
      'function': getWorkers,
      'args': [
        { 'name': 'user', 'gname': 'user', 'global': True, 'required': True },
        {
          'name': 'query',
          'type': str
        },
        {
          'name': 'offset',
          'default': 0,
          'type': int
        },
        {
          'name': 'limit',
          'default': 10,
          'min': 0,
          'max': 1000,
          'type': int
        }
      ]
    }
  },
  'workerCreate': {
    'POST': {
      'function': createWorker,
      'args': [
        { 'name': 'user', 'gname': 'user', 'global': True, 'required': True },
        {
          'name': 'name',
          'type': str,
          'required': True
        },
        {
          'name': 'key',
          'type': str,
          'required': True
        },
        {
          'name': 'configdata_id',
          'type': str,
          'xor': 'configdata',
          'required': True
        },
        {
          # json data
          'name': 'configdata',
          'type': str,
          'xor': 'configdata_id',
          'required': True
        },
        {
          'name': 'baseconfig_id',
          'type': str
        }
      ]
    }
  },
  'workerUpdate': {
    'POST': {
      'function': updateWorker,
      'args': [
        { 'name': 'user', 'gname': 'user', 'global': True, 'required': True },
        {
          'name': 'id',
          'type': str,
          'required': True
        },
        {
          'name': 'name',
          'type': str
        },
        {
          'name': 'key',
          'type': str
        },
        {
          'name': 'configdata_id',
          'type': str,
          'xor': 'configdata'
        },
        {
          # json data
          'name': 'configdata',
          'type': str,
          'xor': 'configdata_id'
        },
        {
          'name': 'baseconfig_id',
          'type': str
        }
      ]
    }
  },
  'worker': {
    'GET': {
      'function': getWorker,
      'args': [
        { 'name': 'user', 'gname': 'user', 'global': True, 'required': True },
        {
          'name': 'id',
          'type': str,
          'required': True
        },
        {
          'name': 'with_configdata',
          'type': bool,
          'default': False
        },
        {
          'name': 'with_baseconfig',
          'type': bool,
          'default': False
        },
      ]
    },
    'DELETE': {
      'function': deleteWorker,
      'args': [
        { 'name': 'user', 'gname': 'user', 'global': True, 'required': True },
        {
          'name': 'id',
          'type': str,
          'required': True
        },
      ]
    },
  },
  # Config apicalls
  'configs': {
    'GET': {
      'function': getConfigs,
      'args': [
        { 'name': 'user', 'gname': 'user', 'global': True, 'required': True },
        {
          'name': 'query',
          'type': str
        },
        {
          'name': 'offset',
          'default': 0,
          'type': int
        },
        {
          'name': 'limit',
          'default': 10,
          'min': 0,
          'max': 1000,
          'type': int
        }
      ]
    }
  },
  'configCreate': {
    'POST': {
      'function': createConfig,
      'method': 'POST',
      'args': [
        { 'name': 'user', 'gname': 'user', 'global': True, 'required': True },
        {
          'name': 'name',
          'type': str,
          'required': True
        },
        {
          # json data
          'name': 'configdata',
          'type': str,
          'required': True
        }
      ]
    },
  },
  'configUpdate': {
    'POST': {
      'function': updateConfig,
      'args': [
        { 'name': 'user', 'gname': 'user', 'global': True, 'required': True },
        {
          'name': 'id',
          'type': str,
          'required': True
        },
        {
          'name': 'name',
          'type': str
        },
        {
          # json data
          'name': 'configdata',
          'type': str
        }
      ]
    },
  },
  'config': {
    'GET': {
      'function': getConfig,
      'args': [
        { 'name': 'user', 'gname': 'user', 'global': True, 'required': True },
        {
          'name': 'id',
          'type': str,
          'required': True
        },
        {
          'name': 'with_configdata',
          'type': bool,
          'default': False
        }
      ]
    },
    'DELETE': {
      'function': deleteConfig,
      'args': [
        { 'name': 'user', 'gname': 'user', 'global': True, 'required': True },
        {
          'name': 'id',
          'type': str,
          'required': True
        },
      ]
    },
  },
  # ConfigData apicalls
  'configDataCreate': {
    'POST': {
      'function': createConfigData,
      'args': [
        { 'name': 'user', 'gname': 'user', 'global': True, 'required': True },
        {
          # json data
          'name': 'data',
          'type': str,
          'required': True
        },
        {
          # json data
          'name': 'inherits_id',
          'type': str
        }
      ]
    },
  },
  'configDataUpdate': {
    'POST': {
      'function': updateConfigData,
      'args': [
        { 'name': 'user', 'gname': 'user', 'global': True, 'required': True },
        {
          'name': 'id',
          'type': str,
          'required': True
        },
        {
          # json data
          'name': 'configdata',
          'type': str,
          'required': True
        },
        {
          # json data
          'name': 'inherits_id',
          'type': str
        }
      ]
    },
  },
  'configData': {
    'GET': {
      'function': getConfigData,
      'args': [
        { 'name': 'user', 'gname': 'user', 'global': True, 'required': True },
        {
          'name': 'id',
          'type': str,
          'required': True
        }
      ]
    },
    'DELETE': {
      'function': deleteConfigData,
      'args': [
        { 'name': 'user', 'gname': 'user', 'global': True, 'required': True },
        {
          'name': 'id',
          'type': str,
          'required': True
        },
      ]
    },
  }
} }
