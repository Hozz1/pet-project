from .models import Course
from rest_framework import serializers
from django.contrib.auth.models import User

class CoursesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = "__all__"


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', "date_joined", "is_staff", "last_login")
        read_only_fields = fields #no changes from frontend

class CurrentUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', "last_login")

