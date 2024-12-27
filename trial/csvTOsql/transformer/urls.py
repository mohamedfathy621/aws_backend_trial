from django.urls import path
from . import views

urlpatterns = [
    path('hello', views.sayHI, name='home'),
    path('file', views.csv_col,name='data frame'),
    path('query',views.get_Data,name='querying')
]
