from django.shortcuts import render, HttpResponse, HttpResponseRedirect, redirect, render_to_response
from .models import account_info
from .models import package_info
from django.contrib import messages
# Create your views here.

def login(request):	
	if request.POST:
		if 'login' in request.POST:
			name = request.POST.get("username", None)
			passwd = request.POST.get("password", None)
			temp = account_info.objects.filter(username = name, password = passwd)
			if len(temp) > 0:
				return redirect('home', username = name)
			else:
				return redirect('register')

		if 'register' in request.POST:
			return redirect('register')
		if 'reset' in request.POST:
			return render(request, "login.html")

		if 'track' in request.POST:
			package_id = request.POST.get("package_id", None)
			if not package_id:
				return render(request, "login.html")
			all_info = package_info.objects.filter(package_id = package_id)

			if len(all_info) > 0:
				return render(request, "login.html", {'all_info': all_info})
			else:
				return render(request, "login.html")

		if 'clear' in request.POST:
			return render(request, "login.html")

	else:
		return render(request, "login.html")


def register(request):
	if 'submit' in request.POST:
		name = request.POST.get("username", None)
		email = request.POST.get("email", None)
		passwd = request.POST.get("password", None)
		account_info.objects.create(username = name, email = email, password = passwd)
		return redirect('login')

	else:
	    return render(request, "register.html")

def home(request, username):
	all_info = package_info.objects.filter(username = username)
	if 'track' in request.POST:
		if len(all_info) > 0:
			return render(request, "home.html", {'all_info': all_info})

	if 'clear' in request.POST:
		return render(request, "home.html")

	if 'logout' in request.POST:
		return redirect('login')
	if 'upgrade' in request.POST:
		return redirect('upgrade', username1 = username)

	else:
		return render(request, "home.html")

def edit(request, package_id):
	item = package_info.objects.filter(package_id = package_id)
	temp = item.values()
	name = temp[0]['username']
	print(name)
	print(name)
	if 'change' in request.POST:
		x = request.POST.get("dest_x", None)
		y = request.POST.get("dest_y", None)
		if len(x) and len(y):
			item.update(dest_x=x, dest_y=y)
			messages.success(request, ('Destination Has Been Edited!'))
			return redirect('home', username = name)
		else:
			messages.success(request, ('Please enter a valid destination!'))
			return redirect('home', username = name)
	else:
		item = package_info.objects.filter(package_id = package_id) #query a database  
		return render(request, 'edit.html', {'item': item})


def upgrade(request, username1):
	if 'back' in request.POST:
		return redirect('home', username = username1)
	else:
		return render(request, "upgrade.html")
	



