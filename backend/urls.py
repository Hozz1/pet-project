"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from courses.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/courses/', CoursesAPIView.as_view()), #all courses
    path("api/v1/courses/top/", TopCoursesView.as_view(), name="courses-top"),
    path('api/v1/courses/create/', CoursesCreateAPIView.as_view()), #create a new course
    path("api/v1/courses/<int:pk>/", CourseDetailView.as_view(), name="course-detail"),
    path('api/v1/courses/update/<int:pk>/', CoursesAPIUpdate.as_view()), # edit current course
    path('api/v1/course/delete/<int:pk>/', CoursesAPIDestroy.as_view()), # delete current course
    path('api/v1/user/<int:pk>/', CurrentUserView.as_view()), #public user data
    path('api/v1/me/', UserView.as_view()), #current user data
    path('api/v1/redis/items', RedisTestView.manage_items, name="items"),
    path('api/v1/redis/item/<slug:key>', RedisTestView.manage_item),
]
urlpatterns = format_suffix_patterns(urlpatterns)

