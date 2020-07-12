from django.utils import timezone
from django.db.models import Q
from .models import *


def is_name_valid(self):
    username = self.request.POST['user_name']
    return not User.objects.filter(username=username.lower()).exists()


def is_password_valid(self):
    return self.request.POST['user_password'] == self.request.POST['user_password2']


def create_user(self):
    username = self.request.POST['user_name']
    userfirstname = self.request.POST['user_first_name']
    userlastname = self.request.POST['user_last_name']
    password = self.request.POST['user_password']
    user = User.objects.create_user(username=username.lower(), first_name=userfirstname,
                                    last_name=userlastname, password=password)
    Friends.objects.create(owner=user)
    return user


def get_online_text(self):
    def text(t, t2=''):
        return 'Бил в сети ' + str(t) + str(t2) + ' назад...'

    if self.request.user == self.get_object():
        return 'online'
    delta = timezone.now() - self.get_object().last_login
    delta = int(delta.total_seconds())
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


def get_search(self):
    try:
        return self.request.GET['search']
    except:
        return ''


def is_friend(self):
    if self.get_object() == self.request.user:
        return 0
    elif self.get_object() in self.request.user.ownerfriends.member.all():
        return 1
    else:
        return 2


def is_user_real(self, username):
    return self.request.user.username != username and User.objects.filter(username=username).exists()


def user_add_or_delete_to_friends(self, username):
    if User.objects.get(username=username) in self.request.user.ownerfriends.member.all():
        self.request.user.ownerfriends.member.remove(User.objects.get(username=username))
        User.objects.get(username=username).ownerfriends.member.remove(self.request.user)
    else:
        self.request.user.ownerfriends.member.add(User.objects.get(username=username))
        User.objects.get(username=username).ownerfriends.member.add(self.request.user)


def get_or_create_dialog(self, username):
    opp1, opp2 = User.objects.get(username=username), self.request.user
    try:
        dialog = Dialog.objects.get(Q(firstopp=opp2, secondopp=opp1) | Q(firstopp=opp1, secondopp=opp2))
    except Dialog.DoesNotExist:
        dialog = Dialog.objects.create(firstopp=opp2, secondopp=opp1)
    return dialog


def get_opponent(self):
    dialog = self.get_object()
    if self.request.user == dialog.firstopp:
        return dialog.secondopp
    else:
        return dialog.firstopp


def create_message(self, type):
    chat = self.get_object()
    if type == 'dialog':
        Message.objects.create(text=self.request.POST['message_text'], author=self.request.user, dialog=chat)
    else:
        Message.objects.create(text=self.request.POST['message_text'], author=self.request.user, dialog=chat)
    chat.date_update = timezone.now()
    chat.save()


def create_channel(self):
    new_channel = Channel.objects.create(name=self.request.POST['channel_name'], owner=self.request.user)
    new_channel.opp.set(User.objects.filter(pk__in=self.request.POST.getlist('opps')))
    new_channel.opp.add(self.request.user)
    new_channel.save()
    return new_channel
