from django.shortcuts import render, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
import json
from django.http import JsonResponse
from .models import Users
import pyrebase


config = {
  "apiKey": "AIzaSyD_4OQ0_9mXYstUMrwPW974cVAfmMFvQ4M",
  "authDomain": "igatimust-4bfb0.firebaseapp.com",
  "databaseURL": "https://igatimust-4bfb0-default-rtdb.firebaseio.com/",
  "projectId": "igatimust-4bfb0",
  "storageBucket": "igatimust-4bfb0.firebasestorage.app",
  "messagingSenderId": "101983045275",
  "appId": "1:101983045275:web:1868cec617b28b674e683e",
  "measurementId": "G-6MGK9SPFYM"
}
firebase = pyrebase.initialize_app(config)
authe = firebase.auth() 
database = firebase.database()

def index(request):
    return HttpResponse("Welcome to Igati!")

#start of register endpoint

@csrf_exempt
@api_view(['POST'])
def register(request):
    try:
        data = json.loads(request.body)  # Convert request body to JSON
        
        # Extract data
        firstName = data.get("firstName")  # Define email first 
        lastName = data.get("lastName")  
        email = data.get("email")  
        password = data.get("password")
        phoneNumber = data.get("phoneNumber")
       

        # Check if email already exists
        if Users.objects.filter(email=email).exists():
            return JsonResponse({"message": "Email already exists"}, status=400)

        # Create user
        user = authe.create_user_with_email_and_password(email, password)
        uid = user['localId']

        # Save member
        user = Users(email=email,firstName=firstName,lastName=lastName ,password=uid ,phoneNumber=phoneNumber)
        user.save()

        return JsonResponse({"message": "Successfully registered"}, status=201)

    except Exception as e:
        print("Error:", str(e))
        return JsonResponse({"error":str(e)})

        

        #start of login endpoint
def login(request, email, password):
    try:
        user = authe.sign_in_with_email_and_password(email,password)
        if Users.objects.filter(email=email).exists() and user:
            session_id = user['idToken']
            print ( session_id)
            request.session['uid'] = str(session_id)
            return JsonResponse({"message": "Successfully logged in"})
        elif not Users.objects.filter(email=email).exists():
            return JsonResponse({"message": "No user found with this email,please register"})
        elif not user:
            return JsonResponse({"message": "Invalid email"})
        else:
            return JsonResponse({"message": "please register"})
    except:
        message = "Invalid Credentials!! Please Check your data"
        return JsonResponse({"message": message})
    

