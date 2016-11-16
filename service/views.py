from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from .api import apiinit, apicalls, evalargs, ApiError
import json
import traceback
from workercrm.settings import DEBUG

class JsonErrorHttpResponse(JsonResponse):
  def __init__(self, status_code, message, **kwargs):
    data = { "status": False, "error": message, "code": status_code }
    super().__init__(status=status_code, data=data, **kwargs)
    

def index(request):
  return HttpResponse("Welcome to workercrm service")

def apicall(request, version, name):
  jdparams = {}
  if DEBUG:
    jdparams['indent'] = 2
  try:
    vapicalls = apicalls[version]
    try:
      apicall = vapicalls[name]
      if apicall['method'] == request.method:
        try:
          apiinit(request, version, name)
          args = evalargs(apicall, request, version, name)
          try:
            func = apicall['function']
          except KeyError:
            return JsonErrorHttpResponse(500, "apicall has no function", json_dumps_params=jdparams)
          r = func(**args)
          return JsonResponse({} if not r else r, json_dumps_params=jdparams)
        except ApiError as error:
          if DEBUG:
            traceback.print_exc()
          return JsonErrorHttpResponse(error.status, error.message, json_dumps_params=jdparams)
        except Exception as exception: # catch all exception
          # raise exception # for backtrace
          if DEBUG:
            traceback.print_exc()
          return JsonErrorHttpResponse(500, "%s: %s" % (type(exception).__name__, str(exception)), json_dumps_params=jdparams)
      else:
        return JsonErrorHttpResponse(400, "call with method `%s' expected" % apicall['method'], json_dumps_params=jdparams)
    except KeyError:
      return JsonErrorHttpResponse(400, "Unknown function: %s" % name, json_dumps_params=jdparams)
  except KeyError:
    return JsonErrorHttpResponse(400, "Unknown version: %s" % version, json_dumps_params=jdparams)

# csrf should get ignored for api view
setattr(apicall, 'csrf_exempt', True)
