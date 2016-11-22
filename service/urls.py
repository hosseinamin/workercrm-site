from django.conf.urls import url

from . import views

app_name='service'
urlpatterns = [
  url(r'^$', views.index, name='index'),
  url(r'^(?P<version>[0-9.]+)/(?P<name>[^/]+)', views.apicallview, name='apicall')
]
