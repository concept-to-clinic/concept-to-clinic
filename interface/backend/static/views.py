from django.shortcuts import render


def home(request):
    current_hash = open('/HEAD', 'r').readlines()[-1].split(' ')[1]
    short_hash = current_hash[:7]
    return render(request, '../frontend/index.html', {'short_hash': short_hash})
