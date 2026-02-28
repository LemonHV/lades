from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from chat import views
from router.api import BaseAPI


api = BaseAPI()
api.auto_discover_controllers()

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
    path("chat/<uuid:user_uid>/", views.private_chat, name="private_chat"),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)  # type: ignore
