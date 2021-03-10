from rest_framework import serializers
from django.contrib.auth import authenticate, login, logout
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_200_OK,
    HTTP_401_UNAUTHORIZED
)
class SignUpSerializer(serializers.Serializer):
    """
    For serialize signup data request
    """
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)
    country = serializers.CharField(required=True)

    def validate(self, data):
        """ Validates If user already exist or not """

        username = data.get("email").split("@")[0]
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None
        if user:
            raise serializers.ValidationError({"error": "User email already exists",
                                                           "status": HTTP_400_BAD_REQUEST})
        else:
            return data

class LoginSerializer(serializers.Serializer):
    """
    For serialize login data request
    """

    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)

    def validate(self, data):
        """ Validates the request data for POST Login API """
        username = data.get("username")
        password = data.get("password")
        try:
            # import pdb;pdb.set_trace()
            user = authenticate(username=username, password=password)
        except Exception as e:
            print(e)
        if not user:
            msg = "Unable to login with given credentials."
            raise serializers.ValidationError({"error": msg, "status": HTTP_400_BAD_REQUEST})

        
        # data.update({"token":"xyz"})
        return data


        
class GetCovidDataParamsSerializer(serializers.Serializer):
    """
    For serialize query params of get_covid_data request
    """

    country = serializers.CharField(required=False)
    days = serializers.IntegerField(required=False,default=15)     