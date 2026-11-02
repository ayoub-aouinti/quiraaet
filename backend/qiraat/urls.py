from django.urls import path

from . import views

urlpatterns = [
    path('meta/', views.meta),
    path('suras/<int:n>/qalun/', views.qalun),
    path('suras/<int:n>/reads/', views.reads),
    path('mushafs/<str:mushaf>/<int:n>/', views.mushaf),
]
