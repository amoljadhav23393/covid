from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_200_OK,
    HTTP_401_UNAUTHORIZED
)
from authentication.serializer import *
import requests
from django_countries import countries
import json
import plotly.express as px
import pandas as pd
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email import encoders
# Create your views here.
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@api_view(['POST'])
@permission_classes((AllowAny,))
def sign_up(request):
    """
    
    """
    validated_data = SignUpSerializer(data=request.data)
    if validated_data is None or not validated_data.is_valid():
            return Response({'errors': validated_data.errors,
                            'status': HTTP_400_BAD_REQUEST
                            }, status=HTTP_400_BAD_REQUEST)
    create_user(validated_data.data)
    return Response({"data": validated_data.data})


@api_view(['POST'])
@permission_classes((AllowAny,))
def log_in(request):
    """
    
    """
    validated_data = LoginSerializer(data=request.data)
    if validated_data is None or not validated_data.is_valid():
            return Response({'errors': validated_data.errors,
                            'status': HTTP_400_BAD_REQUEST
                            }, status=HTTP_400_BAD_REQUEST)
    data = validated_data.data
    
    try:
        user = authenticate(username=data.get("username"), password=data.get("password"))
    except Exception as e:
        print(e)

    login(request, user)
        
    token, created = Token.objects.get_or_create(user=user)

    data.update({"token": token.key})

    return Response({"data": data})


def create_user(data):
    try:
        # import pdb;pdb.set_trace()
        password = data.pop('password')
        user = User.objects.create(**data)
        user.set_password(password)
        user.username = data.get("email").split("@")[0]
        user.save()
    
    except Exception as e:
        print(e)


@api_view(['GET'])
def get_covid_data(request):
    """
    
    """
    # import pdb;pdb.set_trace()

    validated_data = GetCovidDataParamsSerializer(data=request.GET)
    if validated_data is None or not validated_data.is_valid():
            return Response({'errors': validated_data.errors,
                            'status': HTTP_400_BAD_REQUEST
                            }, status=HTTP_400_BAD_REQUEST)
    
    data = validated_data.data
    user = get_logged_user(request.META.get("HTTP_AUTHORIZATION"))
    country = data.get("country")
    mail_id = user.email
    if not country:
        country = user.country

    country_code = get_country_code(country)
    
    covid_data = dict()
    try:
        
        covid_data_response = requests.get('https://corona-api.com/countries/'+country_code)

    except Exception as e:
        print(e)
    else:
        covid_data = covid_data_response.json()
        covid_data = get_timeline_data_by_days(covid_data, data.get("days"))

    plot_bar_chart(covid_data)
    send_email_attachment(mail_id, data.get("country"), data.get("days"))
    return Response(covid_data)
 


def get_country_code(country_name):
    """
        
    """
    try:
        countries_dict = dict(countries)
        for key, value in countries_dict.items():
         if country_name.lower() == value.lower():
             return key
    except Exception as e:
        print(e)


def get_timeline_data_by_days(covid_data, days):
    """
    """
    timeline = covid_data.get("data").get("timeline") if covid_data and covid_data.get("data") else None
    if timeline:
        timeline = timeline[:days]
        covid_data.get("data").update({"timeline":timeline})


    return covid_data



def plot_bar_chart(covid_data):
    """
        
    """
    try:
        df = pd.DataFrame.from_dict(covid_data.get("data").get("timeline"))
        fig = px.bar(df, x='date', y='confirmed',title=covid_data.get("data").get("name"))

        if 'images' not in os.listdir(project_dir):
            os.mkdir(project_dir+'/images')
        fig.write_image(project_dir+"/images/"+covid_data.get("data").get("name").lower()+".png")
        # fig.show()
    except Exception as e:
        print(e)


def get_logged_user(token):
    """
        return country code by identifying user by token in header
    """

    print(token)
    if token:
        token = token.split(" ")[1] if len(token.split(" ")) > 1 else None

    try:
        user = Token.objects.get(key=token).user
    except Exception as e:
        return None
    else:
        return user

    
def send_email_attachment(user_email,country,days):
    try:
        
        mail_content = '''Hello,

        This is a COVID-DATA of last {} days for {}.

        Thank You'''.format(days, country)
        #The mail addresses and password
        sender_address = ''
        sender_pass = ''
        receiver_address = user_email
        #Setup the MIME
        message = MIMEMultipart()
        message['From'] = sender_address
        message['To'] = receiver_address
        message['Subject'] = 'COVID-DATA for {}. It has an attachment.'.format(country)

        #The subject line
        #The body and the attachments for the mail
        message.attach(MIMEText(mail_content, 'plain'))
        attach_file_name = project_dir+"/images/"+country.lower()+".png"
        img_data = open(attach_file_name, 'rb').read()
        image = MIMEImage(img_data, name=os.path.basename(attach_file_name))
        message.attach(image)
        
        #Create SMTP session for sending the mail
        session = smtplib.SMTP('smtp.gmail.com', 587) #use gmail with port
        session.starttls() #enable security
        session.login(sender_address, sender_pass) #login with mail_id and password
        text = message.as_string()
        session.sendmail(sender_address, receiver_address, text)
        session.quit()
        print('Mail Sent')
    except Exception as e:
        print(e)