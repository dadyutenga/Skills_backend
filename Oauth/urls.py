from django.urls import path
from . import views

urlpatterns = [
    path('auth-status/', views.get_auth_status, name='auth_status'),
    path('callback/', views.callback, name='callback'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
]