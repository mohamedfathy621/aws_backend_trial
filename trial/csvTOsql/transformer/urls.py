from django.urls import path
from . import views

urlpatterns = [
    path('hello', views.sayHI, name='home'),
    path('file', views.csv_col,name='data frame'),
    path('query',views.get_Data,name='querying'),
    path('login',views.login,name='login'),
    path('regist',views.regist,name="regist"),
    path('download',views.download_sheet,name="download excel"),
    path('refresh',views.refresh_sheet,name="refresh data"),
    path('logout',views.logout,name="log out")
]
