from django.contrib import admin
from django.urls import path
from calculator import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/calculate/', views.calculate_bid_services, name='calculate-services'),
    path('api/health/', views.health_check, name='health-check'),
    path('', views.calculate_bid_services, name='default-calculate'),
]