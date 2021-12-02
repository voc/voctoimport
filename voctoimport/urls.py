from django.contrib import admin
from django.urls import include, path
from event import urls as event


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
]

urlpatterns += event.urlpatterns
