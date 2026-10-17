from time import sleep

from django.contrib.auth.models import Group, User
from django.http import HttpResponse
from rest_framework.viewsets import ReadOnlyModelViewSet

from .serializers import GroupSerializer, UserSerializer


def sleepy_view(request):
    sleep(3)
    return HttpResponse('OK')


class UserViewSet(ReadOnlyModelViewSet):
    """
    API endpoint that allows users to be viewed.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer


class GroupViewSet(ReadOnlyModelViewSet):
    """
    API endpoint that allows groups to be viewed.
    """

    queryset = Group.objects.all()
    serializer_class = GroupSerializer
