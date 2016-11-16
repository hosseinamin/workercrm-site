from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Util.number import long_to_bytes, bytes_to_long
from base64 import b64encode, b64decode
from time import time
from workercrm.settings import USER_AUTH_PUBKEY, USER_AUTH_KEY

def token_parse(token):
  try:
    if type(token) == str:
      token = token.encode("UTF-8")
    first_sep = token.index(b'|')
    second_sep = token.index(b'|', first_sep+1)
    third_sep = token.index(b'|', second_sep+1)
    data = token[0:first_sep]
    # ValueError will raise if it's not int
    start_time = int(token[first_sep+1:second_sep])
    expire_time = int(token[second_sep+1:third_sep])
    signature = token[third_sep+1:]
    if len(data) == 0 or len(signature) == 0:
      raise ValueError()
    return (data, start_time, expire_time, b64decode(signature))
  except ValueError:
    raise ValueError("Unexpected token format")

def token_new(data, start_time, expire_time, signature):
  """
    data should not contain character `|'
  """
  return data + b'|' + str(start_time).encode('UTF-8') + b'|' + \
    str(expire_time).encode('UTF-8') + b'|' + \
    b64encode(signature)

def _readpubkey():
  with open(USER_AUTH_PUBKEY) as f:
    return RSA.importKey(f.read())

def _readprivkey():
  with open(USER_AUTH_KEY) as f:
    return RSA.importKey(f.read())

def verify(data, start_time, expire_time, signature):
  time_int = int(time())
  if time_int < start_time:
    raise VerificationNotValidYet()
  if time_int > expire_time:
    raise VerificationExpired()
  pubkey = _readpubkey()
  content = b','.join([ data, str(start_time).encode('UTF-8'),
                        str(expire_time).encode('UTF-8') ])
  sigval = (bytes_to_long(signature),)
  return pubkey.verify(SHA256.new(content).digest(), sigval)

def sign(data, start_time, expire_time):
  expire_time = int(expire_time)
  start_time = int(start_time)
  privkey = _readprivkey()
  content = b','.join([ data, str(start_time).encode('UTF-8'),
                        str(expire_time).encode('UTF-8') ])
  sigval = privkey.sign(SHA256.new(content).digest(), '')
  return long_to_bytes(sigval[0])

class VerificationNotValidYet(Exception):
  pass
class VerificationExpired(Exception):
  pass

__all__ = [ 'token_parse', 'token_new', 'sign', 'verify', 'VerificationExpired' ]

