from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from django.db.models import Q
from .models import *
from itertools import chain


def deltatime(time):
    delta = timezone.now() - time
    delta = int(delta.total_seconds())

    def text(t, t2=''):
        return 'Бил в сети ' + str(t) + str(t2) + ' назад...'

    if delta < 45:
        return 'online'
    elif delta < 60:
        return text('меньше минуты')
    elif delta < 3600:
        return text(delta // 60, ' минут')
    elif delta < 86400:
        return text(delta // 3600, ' часов')
    else:
        return text(delta // 86400, ' дней')


def login_chat(request):
    if request.method == 'POST':
        username = request.POST['user_name']
        password = request.POST['user_password']
        user = authenticate(request, username=username.lower(), password=password)
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse('person', kwargs={'username': user.username}))
        else:
            request.error_message = "Не правильное Имя или Пароль."
            return render(request, 'main/login.html', {
                'username': username,
                'error_message': True,
            })
    else:
        if not request.user.is_authenticated:
            return render(request, 'main/login.html')
        else:
            return HttpResponseRedirect(reverse('person', kwargs={'username': request.user.username}))


def registration_chat(request):
    if request.method == 'POST':
        username = request.POST['user_name']
        userfirstname = request.POST['user_first_name']
        userlastname = request.POST['user_last_name']
        if User.objects.filter(username=username.lower()).exists():
            return render(request, 'main/registration.html', {
                'userfirstname': userfirstname,
                'userlastname': userlastname,
                'error_message_username': username.lower(),
            })
        if request.POST['user_password'] == request.POST['user_password2']:
            password = request.POST['user_password']
            user = User.objects.create_user(username=username.lower(), first_name=userfirstname,
                                     last_name=userlastname, password=password)
            Friends.objects.create(owner=user)
            return render(request, 'main/login.html', {'registration_username': username})
        else:
            return render(request, 'main/registration.html', {
                'username': username,
                'userfirstname': userfirstname,
                'userlastname': userlastname,
                'error_message_password': True,
            })
    else:
        if not request.user.is_authenticated:
            return render(request, 'main/registration.html')
        else:
            return HttpResponseRedirect(reverse('person', kwargs={'username': request.user.username}))


def logout_chat(request):
    logout(request)
    return HttpResponseRedirect(reverse('login'))


def people_chat(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            search = request.POST['search']
            people = User.objects.exclude(username=request.user.username).filter(Q(username__icontains=search) |
                                                                                 Q(first_name__icontains=search) |
                                                                                 Q(last_name__icontains=search))
            people = people.order_by('first_name')
        else:
            search = ''
            people = User.objects.exclude(username=request.user.username).order_by('first_name')
        try:
            friends = request.user.ownerfriends.member.all()
        except User.ownerfriends.RelatedObjectDoesNotExist:
            Friends.objects.create(owner=request.user)
            friends = request.user.ownerfriends.member.all()
        mutual_friends = []
        for person in people:
            try:
                mutual_friends.append(len(request.user.ownerfriends.member.all() & person.ownerfriends.member.all()))
            except User.ownerfriends.RelatedObjectDoesNotExist:
                mutual_friends.append(0)
        context = {'user': request.user.username, 'people': zip(people, mutual_friends), 'friends': friends,
                   'search': search}
        return render(request, 'main/people.html', context)
    else:
        return HttpResponseRedirect(reverse('login'))


def person_chat(request, username):
    if request.user.is_authenticated:
        if User.objects.filter(username=username).exists():
            person = User.objects.get(username=username)
        else:
            return HttpResponseRedirect(reverse('person', kwargs={'username': request.user.username}))
        if request.user.username == username:
            online = 'online'
            friend_request = False
        else:
            try:
                is_friend = request.user.ownerfriends.member.filter(username=username).exists()
            except User.ownerfriends.RelatedObjectDoesNotExist:
                Friends.objects.create(owner=request.user)
                is_friend = True
            if is_friend:
                friend_request = 1
            else:
                friend_request = 2
            try:
                online = deltatime(person.last_login)
            except TypeError:
                online = 'Пользователь еще не заходил в учетную запись...'
        context = {'user': request.user.username, 'person': person, 'online': online, 'friend_request': friend_request}
        return render(request, 'main/person.html', context)
    else:
        return HttpResponseRedirect(reverse('login'))


def friends_chat(request, username):
    if request.user.is_authenticated:
        if not User.objects.filter(username=username).exists():
            return HttpResponseRedirect(reverse('person', kwargs={'username': request.user.username}))
        else:
            context = {'user': request.user.username,
                       'person': User.objects.get(username=username),
                       'user_is_owner': True}
            if request.user.username != username:
                context['user_is_owner'] = False
                context['my_friends'] = request.user.ownerfriends.member.all()
            return render(request, 'main/friends.html', context)
    else:
        return HttpResponseRedirect(reverse('login'))


def friends_add_chat(request, username):
    if request.user.is_authenticated:
        if request.user.username == username or not User.objects.filter(username=username).exists():
            return HttpResponseRedirect(reverse('person', kwargs={'username': request.user.username}))
        else:
            try:
                request.user.ownerfriends.member.add(User.objects.get(username=username))
            except User.ownerfriends.RelatedObjectDoesNotExist:
                Friends.objects.create(owner=request.user)
                request.user.ownerfriends.member.add(User.objects.get(username=username))
            try:
                User.objects.get(username=username).ownerfriends.member.add(request.user)
            except User.ownerfriends.RelatedObjectDoesNotExist:
                Friends.objects.create(owner=User.objects.get(username=username))
                User.objects.get(username=username).ownerfriends.member.add(request.user)
            return HttpResponseRedirect(request.META['HTTP_REFERER'])
    else:
        return HttpResponseRedirect(reverse('login'))


def friends_del_chat(request, username):
    if request.user.is_authenticated:
        if request.user.username == username or not User.objects.filter(username=username).exists():
            return HttpResponseRedirect(reverse('person', kwargs={'username': request.user.username}))
        else:
            try:
                request.user.ownerfriends.member.remove(User.objects.get(username=username))
                User.objects.get(username=username).ownerfriends.member.remove(request.user)
            except User.ownerfriends.RelatedObjectDoesNotExist:
                pass
            return HttpResponseRedirect(request.META['HTTP_REFERER'])
    else:
        return HttpResponseRedirect(reverse('login'))


def chat_chat(request):
    if request.user.is_authenticated:
        chats = chain(request.user.channel_set.all(), request.user.firstopp.all(), request.user.secondopp.all())
        chats = sorted(chats, key=lambda chat: chat.date_update)[::-1]
        chats_type = []
        for chat in chats:
            chats_type.append(str(type(chat)))
        context = {'user': request.user.username, 'chats': zip(chats, chats_type)}
        return render(request, 'main/chat.html', context)
    else:
        return HttpResponseRedirect(reverse('login'))


def dialog_chat(request, pk):
    if not Dialog.objects.filter(pk=pk).exists():
        return HttpResponseRedirect(reverse('chat'))
    dialog = Dialog.objects.get(pk=pk)
    if request.method == 'POST':
        Message.objects.create(text=request.POST['message_text'], author=request.user, dialog=dialog)
        dialog.date_update = timezone.now()
        dialog.save()
    if request.user.is_authenticated:
        if request.user in [dialog.firstopp, dialog.secondopp]:
            if request.user == dialog.firstopp:
                opp = dialog.secondopp
            else:
                opp = dialog.firstopp
            context = {'user': request.user.username, 'opp': opp,
                       'messages': dialog.message_set.all().order_by('-date_send')}
            return render(request, 'main/chat_dialog.html', context)
        else:
            return HttpResponseRedirect(reverse('chat'))
    else:
        return HttpResponseRedirect(reverse('login'))


def channel_chat(request, pk):
    if not Channel.objects.filter(pk=pk).exists():
        return HttpResponseRedirect(reverse('chat'))
    channel = Channel.objects.get(pk=pk)
    if request.method == 'POST':
        Message.objects.create(text=request.POST['message_text'], author=request.user, channel=channel)
        channel.date_update = timezone.now()
        channel.save()
    if request.user.is_authenticated:
        if request.user in channel.opp.all():
            context = {'user': request.user.username, 'channel': channel,
                       'messages': channel.message_set.all().order_by('-date_send'),
                       'opps': channel.opp.all()}
            return render(request, 'main/chat_channel.html', context)
        else:
            return HttpResponseRedirect(reverse('chat'))
    else:
        return HttpResponseRedirect(reverse('login'))


def channel_create_chat(request):
    if request.method == 'POST':
        new_channel = Channel.objects.create(name=request.POST['channel_name'], owner=request.user)
        new_channel.opp.set(User.objects.filter(pk__in=request.POST.getlist('opps')))
        new_channel.opp.add(request.user)
        new_channel.save()
        return HttpResponseRedirect(reverse('channel', kwargs={'pk': new_channel.pk}))
    if request.user.is_authenticated:
        select_size = 10
        try:
            if len(request.user.ownerfriends.member.all()) < 10:
                select_size = len(request.user.ownerfriends.member.all())
        except User.ownerfriends.RelatedObjectDoesNotExist:
            Friends.objects.create(owner=request.user)
            select_size = 0
        context = {'user': request.user.username, 'friends': request.user.ownerfriends.member.all(),
                   'select_size': select_size}
        return render(request, 'main/channel_create.html', context)
    else:
        return HttpResponseRedirect(reverse('login'))


def dialog_create_chat(request, username):
    if request.user.is_authenticated:
        if not User.objects.filter(username=username).exists():
            return HttpResponseRedirect(reverse('person', kwargs={'username': request.user.username}))
        opp1, opp2 = User.objects.get(username=username), request.user
        try:
            dialog = Dialog.objects.get(Q(firstopp=opp2, secondopp=opp1) | Q(firstopp=opp1, secondopp=opp2))
        except Dialog.DoesNotExist:
            dialog = Dialog.objects.create(firstopp=opp2, secondopp=opp1)
        return HttpResponseRedirect(reverse('dialog', kwargs={'pk': dialog.pk}))
    else:
        return HttpResponseRedirect(reverse('login'))


def channel_leave_chat(request, pk):
    if request.user.is_authenticated:
        if not Channel.objects.filter(pk=pk).exists():
            return HttpResponseRedirect(reverse('chat'))
        channel = Channel.objects.get(pk=pk)
        channel.opp.remove(request.user)
        return HttpResponseRedirect(reverse('chat'))
    else:
        return HttpResponseRedirect(reverse('login'))
