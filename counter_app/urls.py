from django.urls import path
from .views import counter


urlpatterns = [
    path('', counter, name='counter'),
]