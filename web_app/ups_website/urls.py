from . import views
from django.urls import path
from django.contrib import admin

urlpatterns = [
	path('', views.login, name = 'login'),
	path('register/', views.register, name='register'),
	path('home/<username>', views.home, name='home'),
	path('edit/<package_id>', views.edit, name='edit'),
	path('/upgrade/<username1>', views.upgrade, name = 'upgrade')
]