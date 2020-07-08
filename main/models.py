from django.db import models
from django.contrib.auth.models import User


class Dialog(models.Model):
    firstopp = models.ForeignKey(User, related_name="firstopp", on_delete=models.DO_NOTHING)
    secondopp = models.ForeignKey(User, related_name="secondopp", on_delete=models.DO_NOTHING)
    date_update = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "Chat with " + self.firstopp.username + ' and ' + self.secondopp.username


class Channel(models.Model):
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(User, related_name='ownerchannel', on_delete=models.DO_NOTHING)
    opp = models.ManyToManyField(User)
    date_update = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '(' + self.owner.username + ') Channel name: ' + self.name[:40]


class Message(models.Model):
    text = models.TextField(max_length=500)
    dialog = models.ForeignKey(Dialog, on_delete=models.CASCADE, blank=True, null=True)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, blank=True, null=True)
    author = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    date_send = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.dialog:
            return self.author.username + ' (' + str(self.dialog.pk) + ' dialog) ' + self.text[:40]
        else:
            return self.author.username + ' (' + str(self.channel.pk) + ' channel) ' + self.text[:40]


class Friends(models.Model):
    owner = models.OneToOneField(User, related_name='ownerfriends', on_delete=models.CASCADE)
    member = models.ManyToManyField(User)

    def __str__(self):
        return self.owner.username + ' friends'
