import json
from django.shortcuts import render
from .models import Course
from .serializers import CoursesSerializer, UserSerializer, CurrentUserSerializer
from rest_framework import generics, permissions, status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, IsAdminUser
from django.contrib.auth.models import User
import redis
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.throttling import ScopedRateThrottle

# TTL можно сделать короче, чтобы реже ловить «устаревшие» списки
LIST_TTL = 120
@method_decorator(cache_page(LIST_TTL, key_prefix="v1:courses:list"), name="dispatch")
class CoursesAPIView(generics.ListAPIView):
    queryset = Course.objects.all()
    serializer_class = CoursesSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, )

TOP_TTL = 60
DETAIL_TTL = 300
class CourseDetailView(generics.RetrieveAPIView):
    queryset = Course.objects.all()
    serializer_class = CoursesSerializer

    def retrieve(self, request, *args, **kwargs):
        pk = kwargs["pk"]
        key = f"v1:courses:detail:{pk}"
        data = cache.get(key)
        if data is not None:
            resp = Response(data)
            resp["X-Cache"] = "HIT detail"
            return resp

        resp = super().retrieve(request, *args, **kwargs)
        cache.set(key, resp.data, timeout=DETAIL_TTL)
        resp["X-Cache"] = "MISS detail"
        return resp

class TopCoursesView(APIView):
    throttle_scope = "courses-top"
    throttle_classes = [ScopedRateThrottle]

    def get(self, request):
        limit = int(request.query_params.get("limit", 10))
        key = f"v1:courses:top:{limit}"
        data = cache.get(key)
        if data is not None:
            resp = Response(data)
            resp["X-Cache"] = "HIT top"
            return resp

        qs = Course.objects.order_by("-title")[:limit]
        data = CoursesSerializer(qs, many=True).data
        cache.set(key, data, timeout=60)
        resp = Response(data)
        resp["X-Cache"] = "MISS top"
        return resp

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


redis_instance = redis.StrictRedis(host=settings.REDIS_HOST,
                                    port=settings.REDIS_PORT, db=0)
class RedisTestView():
    @api_view(['GET', 'POST'])
    def manage_items(request, *args, **kwargs):
        if request.method == 'GET':
            items = {}
            count = 0
            for key in redis_instance.keys('*'):
                items[key.decode("utf-8")] = redis_instance.get(key)
                count += 1

            response = {
                'count': count,
                'msg': f"Found {count} items.",
                'items': items
            }
            return Response(response, status=200)
        elif request.method == 'POST':
            item = json.loads(request.body)
            key = list(item.keys())[0]
            value = item[key]
            redis_instance.set(key, value)
            response = {
                'msg': f"{key} successfully set to {value}"
            }
            return Response(response, status=201)

    @api_view(['GET', 'PUT', 'DELETE'])
    def manage_item(request, *args, **kwargs):
        if request.method == 'GET':
            if kwargs['key']:
                value = redis_instance.get(kwargs['key'])
                if value:
                    response = {
                        'key': kwargs['key'],
                        'value': value,
                        'msg': 'success'
                    }
                    return Response(response, status=200)
                else:
                    response = {
                        'key': kwargs['key'],
                        'value': value,
                        'msg': 'Not found'
                    }
                    return Response(response, status=404)
        elif request.method == 'PUT':
            if kwargs['key']:
                request_data = json.loads(request.body)
                new_value = request_data['new_value']
                value = redis_instance.get(kwargs['key'])
                if value:
                    redis_instance.set(kwargs['key'], new_value)
                    response = {
                        'key': kwargs['key'],
                        'value': value,
                        'msg': f"Successfully updated {kwargs['key']}"
                    }
                    return Response(response, status=200)
                else:
                    response = {
                        'key': kwargs['key'],
                        'value': None,
                        'msg': 'Not found'
                    }
                    return Response(response, status=404)

        elif request.method == 'DELETE':
            if kwargs['key']:
                result = redis_instance.delete(kwargs['key'])
                if result == 1:
                    response = {
                        'msg': f"{kwargs['key']} successfully deleted"
                    }
                    return Response(response, status=404)
                else:
                    response = {
                        'key': kwargs['key'],
                        'value': None,
                        'msg': 'Not found'
                    }
                    return Response(response, status=404)
