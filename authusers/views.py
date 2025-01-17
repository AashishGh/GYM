from django.shortcuts import render
from rest_framework.generics import GenericAPIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import CustomUser
from rest_framework.decorators import api_view
from rest_framework.reverse import reverse
from django.contrib.auth import  logout
from rest_framework import generics
from .serializers import *
from rest_framework.permissions import IsAuthenticated 
from rest_framework.views import APIView
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from members.views import BasicPagination
from .permissions import IsAdminOrReadOnly
from rest_framework_simplejwt.tokens import RefreshToken  


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    default_error_messages = {
        "no_active_account": ("Invalid username or password")
    }
    def validate(self, attrs):
        try:
            data = super().validate(attrs)
            refresh = self.get_token(self.user)
            data['refresh'] = str(refresh)
            data['access'] = str(refresh.access_token)

            # Add extra responses here
            data['user_type'] = self.user.user_type
            data['username']=self.user.username
        
        except ValidationError:
            # raise serializers.ValidationError(default_error_messages)
            data["message"]=default_error_messages
            return data
        return data
    


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
    
# change password
class ChangePasswordView(generics.UpdateAPIView):
    """
    An endpoint for changing password.
    """
    serializer_class = ChangePasswordSerializer
    model = CustomUser
    permission_classes = (IsAuthenticated,)

    def get_object(self, queryset=None):
        obj = self.request.user
        # print(obj)
        return obj

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Check old password
            if not self.object.check_password(serializer.data.get("old_password")):
                return Response({"detail": "Current password didnot match."}, status=status.HTTP_400_BAD_REQUEST)
            # set_password also hashes the password that the user will get
            if serializer.data.get("new_password")!=serializer.data.get("new_password2"):
                # return Response({"detail":"New passwords donot match."},status=status.HTTP_400_BAD_REQUEST)
                raise serializers.ValidationError({"detail":"Password fields didn't match."})

            self.object.set_password(serializer.data.get("new_password"))
            self.object.save()
            response = {
                'status': 'success',
                'code': status.HTTP_200_OK,
                'message': 'Password updated successfully',
                'data': []
            }
            return Response(response)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.ListAPIView):
    serializer_class = UserSerializer
    model = CustomUser
    def get(self,request,*args, **kwargs):
        
        obj=self.request.user
        
        if obj.username is not None:
            context = {
                    'username': obj.username,
                    'firstname': obj.first_name,
                    'lastname': obj.last_name,
                    'created_at':obj.created_at.year,
                    'user_type':obj.user_type
                    
                }
            return Response(context,status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)
    
# class LogoutAPIView(APIView):
#     def get(self, request):
#         # request.user.auth_token.delete()
#         logout(request)
#         return Response(status=status.HTTP_200_OK)
    
# class LogoutAPIView(GenericAPIView):
#     serializer_class = LogoutSerializer

#     def post(self, request):
#         serializer = self.serializer_class(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()

#         return Response(status=status.HTTP_204_NO_CONTENT)    
    
class LogoutAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST) 
           
class UsersView(generics.ListCreateAPIView):
    permission_classes=[IsAdminOrReadOnly]
    serializer_class=RegisterSerializer
    
    def get_queryset(self):
        if self.request.user.user_type=='AD':
            queryset=CustomUser.objects.all()
        else:
            queryset=CustomUser.objects.filter(user_type='ST')
        return queryset

class UserDetailsView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserSerializer
    lookup_field='id'
    def get_queryset(self):
        if self.request.user.user_type=='AD':
            queryset=CustomUser.objects.all()
        else:
            queryset=CustomUser.objects.filter(user_type='ST')
        return queryset
