from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('account', views.UserAccountViewSet, basename='user-account')
router.register('allUser', views.AllUserViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path('register/', views.UserRegistrationSerializerViewSet.as_view(), name='register'),
    path('active/<uid64>/<token>/', views.activate, name='active'),
    path('login/', views.UserLoginApiView.as_view(), name='login'),
    path('logout/', views.UserLogoutApiView.as_view(), name='logout'),
    path('deposit/',views.DepositApiView.as_view(), name='deposit-create'),
    path('successful-email-verified/',views.successful ,name='verified_success'),
    path('unsuccessful-email-verified/',views.unsuccessful ,name='verified_unsuccess'),
]
