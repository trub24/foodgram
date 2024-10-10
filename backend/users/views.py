from djoser import views as djoser_views
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth import get_user_model
from recipe.models import Follow
from users.serializers import (
    UserSerializer,
    AvatarSerializer,
    UserListSerializer,
    SubscriptionsSerializer
)


User = get_user_model()


class UserViewSet(djoser_views.UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(methods=['get'],
            permission_classes=[IsAuthenticated],
            detail=False)
    def me(self, request):
        user = self.request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @action(methods=['put', 'delete'],
            url_path='me/avatar',
            url_name='avatar',
            permission_classes=[IsAuthenticated],
            detail=False)
    def avatar(self, request):
        user = self.request.user
        if request.method == 'PUT':
            serializer = AvatarSerializer(
                user,
                data=request.data
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        if request.method == 'DELETE':
            user.avatar.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    def list(self, request):
        queryset = User.objects.all()
        paginator = LimitOffsetPagination()
        paginator.page_size = 5
        result_page = paginator.paginate_queryset(queryset, request)
        serializer = UserListSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @action(methods=['get'],
            url_path='subscriptions',
            url_name='subscriptions',
            permission_classes=[IsAuthenticated],
            detail=False)
    def subscriptions(self, request):
        user = self.request.user
        following = Follow.objects.filter(user=user)
        paginator = LimitOffsetPagination()
        paginator.page_size = 5
        result_page = paginator.paginate_queryset(following, request)
        serializer = SubscriptionsSerializer(
            result_page, many=True, context={'request': request}
        )
        return paginator.get_paginated_response(serializer.data)

    @action(methods=['post', 'delete'],
            url_path=r'(?P<user_id>\d+)/subscribe',
            url_name='subscribe',
            permission_classes=[IsAuthenticated],
            detail=False)
    def subscribe(self, request, user_id):
        user = self.request.user
        following = get_object_or_404(User, id=user_id)
        if request.method == 'POST':
            if Follow.objects.filter(user=user, following=following).exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            if user == following:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            serializer = SubscriptionsSerializer(
                data=request.data,
                context={'request': request, 'following': following}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(user=user, following=following)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            if Follow.objects.filter(user=user, following=following).exists():
                follow = Follow.objects.get(user=user, following=following)
                follow.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(status=status.HTTP_400_BAD_REQUEST)
