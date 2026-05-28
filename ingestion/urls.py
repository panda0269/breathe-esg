from django.urls import path
from .views import (
    UploadFileView,
    RecordsListView,
    ReviewRecordView,
    DashboardStatsView,
    ClientListView,
)

urlpatterns = [
    path('upload/', UploadFileView.as_view(), name='upload'),
    path('records/', RecordsListView.as_view(), name='records'),
    path('records/<int:pk>/review/', ReviewRecordView.as_view(), name='review'),
    path('dashboard/', DashboardStatsView.as_view(), name='dashboard'),
    path('clients/', ClientListView.as_view(), name='clients'),
]