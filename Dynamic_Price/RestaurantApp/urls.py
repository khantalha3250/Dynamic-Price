from django.urls import path
from . import views

urlpatterns = [
    path('details/', views.restaurant_details, name='restaurant_details'),
    path('top-restaurants/', views.top_restaurants, name='top_restaurants'),
    path('menu-prices/', views.menu_prices, name='menu_prices'),
    path('lowest-prices/', views.lowest_prices, name='lowest_prices'),
     path('consolidated-prices/', views.consolidated_prices, name='consolidated_prices'),
]
