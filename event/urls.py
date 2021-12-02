from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.view_index, name='index'),
    re_path('^conference/(?P<cslug>.*)/new$', views.view_new_event, name='new_event'),
    re_path('^conference/(?P<cslug>.*)/(?P<eguid>.*)$', views.view_event, name='event'),
    re_path('^conference/(?P<cslug>.*)$', views.view_conference, name='conference'),
    re_path('^schedule/(?P<cslug>.*).json$', views.view_schedulejson, name='schedulejson'),
    re_path('^schedule/(?P<cslug>.*).xml$', views.view_schedulexml, name='schedulexml'),
]
