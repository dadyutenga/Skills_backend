from django.urls import path
from . import views

urlpatterns = [
    path('auth-status/', views.get_auth_status, name='auth_status'),
    path('callback/', views.callback, name='callback'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('profile', views.get_profile, name='get_profile'),
    path('profile/update', views.update_profile, name='update_profile'),
]