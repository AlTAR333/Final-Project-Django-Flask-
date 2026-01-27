from django.shortcuts import render
from django.http import HttpResponse
import requests
from django.http import JsonResponse

def home(request):
    return HttpResponse("NAHB – Django Web App OK")

def api_test(request):
    r = requests.get("http://127.0.0.1:5000/ping")
    return JsonResponse(r.json())
