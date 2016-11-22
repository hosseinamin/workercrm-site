from .auth import token_parse, token_new, sign, verify, VerificationExpired
from django.contrib.auth.models import User

class ApiError(Exception):
  def __init__(self, status, message):
    self.status = status
    self.message = message

def _readitem_for_mk(columns, item, appendix_id_tostr):
  if item == None:
    return None
  record = {}
  for column in columns:
    try:
      if type(column) == dict:
        column_def = column
        column_name = column_def['name']
        column_type = column_def['type']
        if column_type == 'onerel':
          record[column_name] = \
            _readitem_for_mk(column_def['columns'], getattr(item, column_name),
                             appendix_id_tostr)
      else:
        if appendix_id_tostr and \
           (column == 'id' or \
            column.index('_id') == len(column) - len('_id')):
          record[column] = None if getattr(item, column) == None \
                           else str(getattr(item, column))
        else:
          record[column] = getattr(item, column)
    except ValueError:
      record[column] = getattr(item, column)
  return record

def mk_readmulti_call(readmultifunc, appendix_id_tostr=True):
  def readmulti(**kwargs):
    (columns, items, count) = readmultifunc(**kwargs)
    return {
      "status": True,
      "records": [ _readitem_for_mk(columns, item, appendix_id_tostr) \
                   for item in items ],
      "count": count
    }
  return readmulti
  
def mk_readsingle_call(readsinglefunc, appendix_id_tostr=True):
  def readsingle(**kwargs):
    (columns, item) = readsinglefunc(**kwargs)
    return {
      "status": True,
      "record": _readitem_for_mk(columns, item, appendix_id_tostr)
    }
  return readsingle

apiglobals = {}

def apiinit(request, version, name):
  if 'HTTP_X_USER_TOKEN' in request.META:
    token = request.META['HTTP_X_USER_TOKEN']
    (data, start_time, expire_time, signature) = token_parse(token)
    if verify(data, start_time, expire_time, signature):
      (user_id, loginrand) = data.decode('UTF-8').split(',')
      apiglobals['user'] = User.objects.get(id=user_id)
    else:
      raise ApiError(403,"ValueError: X-USER-TOKEN Could not verify signature")
    
_evalargs_truevalues = frozenset(('yes','true','1',''))

def evalargs(apicall, request, version, name):
  method = request.method
  if method == 'GET' or method == 'DELETE':
    query = request.GET if request.GET != None else {}
  elif method == 'POST':
    query = request.POST if request.POST != None else {}
  else:
    query = None
  retargs = {}
  if query == None:
    return retargs
  xor_required={}
  def keyerror_handle(arg):
    name = arg['name']
    if 'required' in arg and  arg['required']:
      if 'xor' in arg:
        xor_name = arg['xor']
        if xor_name not in retargs:
          if xor_name not in xor_required:
            xor_required[xor_name] = []
          xor_required[xor_name].append(name)
      else:
        raise ApiError(406, "Required field `%s' does not exits" % name)
    if 'xor' in arg:
      return False
    return True
  for arg in apicall['args']:
    name = arg['name']
    if 'global' in arg and arg['global']:
      gname = arg['gname'] if 'gname' in arg else name
      if gname in apiglobals:
        retargs[name] = apiglobals[gname]
      else:
        if 'required' in arg and arg['required']:
          raise ApiError(406, "global is not defined `%s'" % gname)
        retargs[name] = None
      continue
    atype = arg['type']
    val = None
    if 'default' in arg:
      val = arg['default']
    if atype  == int:
      try:
        val = int(query[name])
        if 'max' in arg and arg['max'] < val:
          val = arg['max']
        if 'min' in arg and arg['min'] > val:
          val = arg['min']
      except KeyError:
        if not keyerror_handle(arg):
          continue
    elif atype == str:
      try:
        val = query[name]
      except KeyError:
        if not keyerror_handle(arg):
          continue
    elif atype == bool:
      try:
        val = query[name]
        if type(val) == str:
          val = val in _evalargs_truevalues
        val = not not val
      except KeyError:
        if not keyerror_handle(arg):
          continue
    if 'xor' in arg:
      if name in xor_required:
        del xor_required[name]
      if arg['xor'] in retargs:
        raise ApiError(406, "One of the following is required (%s), "
                         "both are given" % ",".join((name,arg['xor'])))
    if 'validate' in arg:
      arg['validate'](val)
    retargs[name] = val
    
  for arg in apicall['args']:
    name = arg['name']
    if name in retargs and 'validateAfter' in arg:
      arg['validateAfter'](retargs[name])
  if len(xor_required) > 0:
    for (name, others) in xor_required.items():
      raise ApiError(406, "One of the following is required " +
                     ",".join([name]+others))
  return retargs
