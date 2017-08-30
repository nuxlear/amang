from django.conf.urls import url

from . import views

app_name = 'timetable'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^new/$', views.new, name='new'),
    url(r'^add/$', views.add, name='add'),
    url(r'^changeweek/$', views.changeweek, name='changeweek'),
    url(r'^(?P<schedule_id>[0-9]+)/$', views.info, name='info'),
    url(r'^(?P<schedule_id>[0-9]+)/delete/$', views.delete, name='delete'),
    url(r'^(?P<schedule_id>[0-9]+)/modify/$', views.modify, name='modify'),
    # url(r'^report/$', views.report, name='report'),
]
