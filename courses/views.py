from django.shortcuts import render
from .models import Course
from .serializers import CoursesSerializer, UserSerializer, CurrentUserSerializer
from rest_framework import generics, permissions
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, IsAdminUser
from django.contrib.auth.models import User

class CoursesAPIView(generics.ListAPIView):
    queryset = Course.objects.all()
    serializer_class = CoursesSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, )

class CoursesCreateAPIView(generics.ListCreateAPIView):
    queryset = Course.objects.all()
    serializer_class = CoursesSerializer
    permission_classes = (IsAdminUser, )

class CoursesAPIUpdate(generics.RetrieveUpdateAPIView):
    queryset = Course.objects.all()
    serializer_class = CoursesSerializer
    permission_classes = (IsAdminUser, )

class CoursesAPIDestroy(generics.RetrieveDestroyAPIView):
    queryset = Course.objects.all()
    serializer_class = CoursesSerializer
    permission_classes = (IsAdminUser, )

#USERS
class CurrentUserView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated, )

class UserView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = CurrentUserSerializer
    permission_classes = (IsAuthenticated, )

    def get_object(self):
        return self.request.user

