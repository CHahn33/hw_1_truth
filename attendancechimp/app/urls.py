from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path("index.html", views.index, name="index_html"),
    path('time', views.time_view, name='time'),
    path('sum', views.sum_view, name='sum'),
    path('createUser', views.createUser, name='create_user'),
    path('accounts/', include('django.contrib.auth.urls'))
]
