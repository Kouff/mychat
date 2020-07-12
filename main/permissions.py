from django.http import HttpResponseRedirect
from django.urls import reverse




class MemberPermissionsMixin:
    """ Права доступа к диалогу или каналу владеют только участники диалога """

    def has_permissions(self):
        try:
            permissions = self.request.user in [self.get_object().firstopp, self.get_object().secondopp]
        except:
            permissions = self.request.user in self.get_object().opp.all()
        return permissions

    def dispatch(self, request, *args, **kwargs):
        if not self.has_permissions():
            return HttpResponseRedirect(reverse('chat'))
        return super().dispatch(request, *args, **kwargs)


