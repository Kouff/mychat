from django.urls import path
from .views import *

urlpatterns = [
    path('chat/', chat_chat, name='chat'),
    path('chat/dialog/<int:pk>/', dialog_chat, name='dialog'),
    path('chat/channel/<int:pk>/', channel_chat, name='channel'),
    path('chat/channel_create/', channel_create_chat, name='channel_create'),
    path('chat/channel_leave/<int:pk>/', channel_leave_chat, name='channel_leave'),
    path('chat/dialog_create/<slug:username>/', dialog_create_chat, name='dialog_create'),
    path('login/', login_chat, name='login'),
    path('logout/', logout_chat, name='logout'),
    path('registration/', registration_chat, name='registration'),
    path('people/', people_chat, name='people'),
    path('friends/<slug:username>/', friends_chat, name='friends'),
    path('friends/add/<slug:username>/', friends_add_chat, name='friends_add'),
    path('friends/del/<slug:username>/', friends_del_chat, name='friends_del'),
    path('person/<slug:username>/', person_chat, name='person'),
]
