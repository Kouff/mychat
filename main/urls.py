from django.urls import path
from .views import *

urlpatterns = [
    path('chat/', ListChat.as_view(), name='chat'),
    path('chat/dialog/<int:pk>/', DialogDetailView.as_view(), name='dialog'),
    path('chat/channel/<int:pk>/', ChannelDetailView.as_view(), name='channel'),
    path('chat/channel_create/', ChannelCreateView.as_view(), name='channel_create'),
    path('chat/channel_leave/<int:pk>/', channel_leave_chat, name='channel_leave'),
    path('chat/dialog_create/<slug:username>/', DialogCreateView.as_view(), name='dialog_create'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', logout_chat, name='logout'),
    path('registration/', RegistrationView.as_view(), name='registration'),
    path('people/', ListPerson.as_view(), name='people'),
    path('friends/<slug:slug>/', ListFriends.as_view(), name='friends'),
    path('friends/update/<slug:username>/', UpdateFriendView.as_view(), name='friends_update'),
    path('person/<slug:slug>/', DetailPerson.as_view(), name='person'),
]
