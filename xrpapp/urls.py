"""xrptransactions URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
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
from django.conf.urls.static import static
from django.conf import settings
from . import views

urlpatterns = [
    path('',views.index,name='index'),
    path('newwallet/',views.newwallet,name='newwallet'),
    path('maketransactions/',views.maketransactions,name='maketransactions'),
    path('chain/',views.fullchain,name='fullchain'),
    path('viewtransactions/',views.viewtransactions,name='viewtransactions'),
    path('transactions/new/',views.newtransaction,name='newtransaction'),
    path('transactions/get/', views.getransactions,name='getransactions' ),
    path('generatetransactions/',views.generatetransactions,name='generatetransactions'),
    path('mine/',views.mine,name='mine'),
]


