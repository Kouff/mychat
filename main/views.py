from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from .permissions import MemberPermissionsMixin
from django.views.generic import DetailView, ListView
from django.views import View
from django.db.models import Q
from .models import *
from itertools import chain
from . import service


class LoginView(View):
    def get(self, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return render(self.request, 'main/login.html')
        else:
            return HttpResponseRedirect(reverse('person', kwargs={'slug': self.request.user.username}))

    def post(self, *args, **kwargs):
        username = self.request.POST['user_name']
        password = self.request.POST['user_password']
        user = authenticate(self.request, username=username.lower(), password=password)
        if user is not None:
            login(self.request, user)
            return HttpResponseRedirect(reverse('person', kwargs={'slug': user.username}))
        else:
            # Не правильное Имя или Пароль.
            return render(self.request, 'main/login.html', {'username': username, 'error_message': True})


class RegistrationView(View):
    def get(self, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return render(self.request, 'main/registration.html')
        else:
            return HttpResponseRedirect(reverse('person', kwargs={'slug': self.request.user.username}))

    def post(self, *args, **kwargs):
        if service.is_name_valid(self) and service.is_password_valid(self):
            user = service.create_user(self)
            return render(self.request, 'main/login.html', {'registration_username': user.username})
        contex = {'userfirstname': self.request.POST['user_first_name'],
                  'userlastname': self.request.POST['user_last_name']}
        if not service.is_name_valid(self):
            username = self.request.POST['user_name']
            contex['error_message_username'] = username.lower()
        if not service.is_password_valid(self):
            contex['error_message_password'] = True
        return render(self.request, 'main/registration.html', contex)


def logout_chat(request):
    logout(request)
    return HttpResponseRedirect(reverse('login'))


class ListPerson(LoginRequiredMixin, ListView):
    model = User
    template_name = 'main/people.html'

    def get_queryset(self):
        search = service.get_search(self)
        if search:
            return User.objects.exclude(username=self.request.user.username). \
                filter(Q(username__icontains=search) |
                       Q(first_name__icontains=search) |
                       Q(last_name__icontains=search))
        else:
            return User.objects.exclude(username=self.request.user.username)

    def get_context_data(self, **kwargs):
        mutual_friends = []
        for person in self.get_queryset():
            mutual_friends.append(len(self.request.user.ownerfriends.member.all() & person.ownerfriends.member.all()))
        context = super().get_context_data(**kwargs)
        context['current_user'] = self.request.user.username
        context['user_list'] = zip(self.get_queryset(), mutual_friends)
        context['friends'] = self.request.user.ownerfriends.member.all()
        context['search'] = service.get_search(self)
        return context


class DetailPerson(LoginRequiredMixin, DetailView):
    model = User
    slug_field = 'username'
    template_name = 'main/person.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_user'] = self.request.user.username
        context['online'] = service.get_online_text(self)
        context['friend_request'] = service.is_friend(self)
        return context


class ListFriends(LoginRequiredMixin, ListView):
    model = User
    template_name = 'main/friends.html'

    def get_queryset(self):
        return User.objects.get(username=self.kwargs['slug']).ownerfriends.member.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_user'] = self.request.user.username
        context['person_name'] = User.objects.get(username=self.kwargs['slug']).username
        context['user_is_owner'] = True
        if self.request.user.username != context['person_name']:
            context['user_is_owner'] = False
            context['my_friends'] = self.request.user.ownerfriends.member.all()
        return context


class UpdateFriendView(View):
    def post(self, *args, **kwargs):
        username = kwargs['username']
        if service.is_user_real(self, username):
            service.user_add_or_delete_to_friends(self, username)
        return HttpResponseRedirect(self.request.META['HTTP_REFERER'])


class ListChat(LoginRequiredMixin, ListView):
    context_object_name = 'chats'
    template_name = 'main/chat.html'

    def get_queryset(self):
        queryset = chain(self.request.user.channel_set.all(), self.request.user.firstopp.all(),
                         self.request.user.secondopp.all())
        return sorted(queryset, key=lambda chat: chat.date_update)[::-1]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        chats_type = []
        for chat in context['chats']:
            chats_type.append(str(type(chat)))
        context['current_user'] = self.request.user.username
        context['chats'] = zip(context['chats'], chats_type)
        return context


class DialogDetailView(MemberPermissionsMixin, DetailView):
    model = Dialog
    template_name = 'main/chat_dialog.html'

    def post(self, *args, **kwargs):
        service.create_message(self)
        return self.get(self)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_user'] = self.request.user.username
        context['opp'] = service.get_opponent(self)
        context['messages'] = self.get_object().message_set.all().order_by('-date_send')
        return context


class DialogChannelView(MemberPermissionsMixin, DetailView):
    model = Channel
    template_name = 'main/chat_channel.html'

    def post(self, *args, **kwargs):
        service.create_message(self, 'dialog')
        return self.get(self)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_user'] = self.request.user.username
        context['opps'] = self.get_object().opp.all()
        context['messages'] = self.get_object().message_set.all().order_by('-date_send')
        return context


class ChannelCreateView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        context = {'current_user': self.request.user.username, 'friends': self.request.user.ownerfriends.member.all()}
        return render(self.request, 'main/channel_create.html', context)

    def post(self, *args, **kwargs):
        channel = service.create_channel(self)
        return HttpResponseRedirect(reverse('channel', kwargs={'pk': channel.pk}))


class DialogCreateView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        username = kwargs['username']
        if service.is_user_real(self, username):
            dialog = service.get_or_create_dialog(self, username)
            return HttpResponseRedirect(reverse('dialog', kwargs={'pk': dialog.pk}))
        return HttpResponseRedirect(reverse('person', kwargs={'username': self.request.user.username}))


def channel_leave_chat(request, pk):
    if Channel.objects.filter(pk=pk).exists():
        channel = Channel.objects.get(pk=pk)
        try:
            channel.opp.remove(request.user)
        except:
            pass
        return HttpResponseRedirect(reverse('chat'))
