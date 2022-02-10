from django.urls import path

from . import views

urlpatterns = [
    path('record', views.record, name='record'),
    path('upload', views.upload, name='upload'),
    path('analyzer', views.analyzer, name='analyzer'),
    path('analyze', views.analyze, name='analyze'),
    path('test-analyze', views.test_analyze, name='analyze'),
]