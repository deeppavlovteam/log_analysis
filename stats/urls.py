from django.urls import path

from . import views

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('chart/<int:config_id>/', views.StatsChartView.as_view(), name='chart'),
    path('<int:pk>/', views.DetailView.as_view(), name='detail'),
]
