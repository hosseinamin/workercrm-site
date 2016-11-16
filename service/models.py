from django.db import models
import json
from django.contrib.auth.models import User

NAME_LIMIT = 200
TYPE_CHAR_LIMIT = 10
DIGITAL_KEY_LENGTH = 40
JSON_DATA_ENCODING = 'UTF-8'

class JSONDataField(models.TextField):
  def get_prep_value(self, value):
    return json.dumps(value)

  def __parse(self, value):
    try:
      data = json.loads(value, JSON_DATA_ENCODING)
      if type(data) == str:
        data = None
        # raise ValueError("Invalid JSONData value of type string")
    except:
      data = None
    return data
    
  def from_db_value(self, value, expression, connection, context):
    if value is None:
      return value
    return self.__parse(value)

  def to_python(self, value):
    if type(value) is not str:
      return value
    if value is None:
      return value
    return self.__parse(value)

class ConfigData(models.Model):
  owner = models.ForeignKey(User, db_index=True, on_delete=models.CASCADE)
  inherits = models.ForeignKey("self", null=True, blank=True,
                               on_delete=models.SET_NULL)
  data = JSONDataField('Config content stored in json format')

class Config(models.Model):
  owner = models.ForeignKey(User, db_index=True, on_delete=models.CASCADE)
  name = models.CharField(max_length=NAME_LIMIT, db_index=True)
  configdata = models.ForeignKey(ConfigData, on_delete=models.DO_NOTHING)

class Worker(models.Model):
  owner = models.ForeignKey(User, db_index=True, on_delete=models.CASCADE)
  name = models.CharField(max_length=NAME_LIMIT, db_index=True)
  key = models.CharField(max_length=DIGITAL_KEY_LENGTH)
  baseconfig = models.ForeignKey(Config, null=True, blank=True,
                                 on_delete=models.SET_NULL)
  configdata = models.ForeignKey(ConfigData, on_delete=models.DO_NOTHING)
