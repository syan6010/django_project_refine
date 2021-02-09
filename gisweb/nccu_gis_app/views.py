from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib import auth
from nccu_gis_app.models import imgData
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.contrib.auth.models import User
import os
import logging
from PIL import Image
import exifread

imgWidthId = 256
imgLengthId = 257
pixelDix = 40962
pixelDiy = 40963
imgTimeId = 306
orientationId = 274
gpsTagId = 34853

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)




def index(request):
	user_name = request.user.username
	return render(request, "index.html", locals())

def add(request):
	# all=maplist.objects.all()  #取得所有景點
	if('title' in request.POST):
		try:
			aTitle = request.POST['title']
			aContent = request.POST['content']
			aType = request.POST['type']
			apurl = request.FILES.get('purl', False)
			user_name = request.user.username		
			logger.debug(apurl)		
			fs = FileSystemStorage()
			filename = fs.save(apurl.name , apurl)
			path_name = "media/{}".format(apurl)
			basename = apurl.name
			exif = get_exif(path_name)	
			try:
				width = exif[imgWidthId]
				height = exif[imgLengthId]          
			except:
				width = exif[pixelDix]
				height = exif[pixelDiy]
			
			new_w = int(width / 10)
			new_h = int(height / 10)
			img = Image.open(path_name)
			rsize_img = img.resize((new_w, new_h))
			orientation = exif[orientationId]
			if(orientation == 6):
				ori_img = rsize_img.transpose(Image.ROTATE_270)
				ori_img.save('media/reImg/re_{}'.format(basename), 'JPEG')
				new_h , new_w = new_w, new_h
				print('90')
			elif(orientation == 8):
				ori_img = rsize_img.transpose(Image.ROTATE_90)
				ori_img.save('media/reImg/re_{}'.format(basename), 'JPEG')
				new_h , new_w = new_w, new_h
				print('270')
			elif(orientation == 2):
				ori_img = rsize_img.transpose(Image.FLIP_LEFT_RIGHT)
				ori_img.save('media/reImg/re_{}'.format(basename), 'JPEG')
				print('180')
			elif(orientation == 4):
				ori_img = rsize_img.transpose(Image.FLIP_TOP_BOTTOM)
				ori_img.save('media/reImg/re_{}'.format(basename), 'JPEG')
				print('180')
			elif(orientation == 5):
				ori_img = rsize_img.transpose(Image.FLIP_LEFT_RIGHT)
				ori_img_f = rsize_img.transpose(Image.ROTATE_90)
				ori_img_f.save('media/reImg/re_{}'.format(basename), 'JPEG')
				print('180')
			elif(orientation == 7):
				ori_img = rsize_img.transpose(Image.FLIP_LEFT_RIGHT)
				ori_img_f = rsize_img.transpose(Image.ROTATE_270)
				ori_img_f.save('media/reImg/re_{}'.format(basename), 'JPEG')
				print('180')
			elif(orientation == 3):
				ori_img = rsize_img.transpose(Image.ROTATE_180)
				ori_img.save('media/reImg/re_{}'.format(basename), 'JPEG')
				print('180')		
			else:
				rsize_img.save('media/reImg/re_{}'.format(basename), 'JPEG')
				print('else')
			gpsInfo = exif[gpsTagId]
			lat_str = gpsInfo[2]
			lat = format_lat_lon(lat_str)
			lon_str = gpsInfo[4]
			lon = format_lat_lon(lon_str)   
			rec = imgData(title = aTitle, content = aContent, type = aType, purl = apurl, lon = lon, lat = lat, username = user_name)
			rec.save()
			return render(request, "index.html")
		except:
			return redirect('/error/')			
	else:
	    return render(request, "add.html")

def map(request):		
	user_name = request.user.username
	if request.method == "POST":
		getTitle = request.POST['title']
		getType = request.POST['type']		
		all = imgData.objects.filter(title__contains = "{}".format(getTitle), type = "{}".format(getType))
		return render(request, "map.html", locals())
	else:
		if request.user.is_authenticated:
			all = imgData.objects.filter(username = "{}".format(user_name))	
		else:
			all = imgData.objects.all()  #取得所有景點
		return render(request, "map.html", locals())


def login(request):
	# messages = ''  #初始時清除訊息，依照判斷結果決定秀出那些訊息
	if request.method == 'POST':  #如果是以POST方式才處理
		name = request.POST['username'].strip()  #取得輸入帳號
		password = request.POST['password']  #取得輸入密碼
		user1 = authenticate(username=name, password=password)  #驗證
		if user1 is not None:  #驗證通過
			if user1.is_active:  #帳號有效
				auth.login(request, user1)  #登入
				return redirect('/index/')  #開啟管理頁面
			else:  #帳號無效
				message = '帳號尚未啟用！'
		else:  #驗證未通過
			message = '登入失敗！'	
	return render(request, "login.html", locals())

def logout(request):  #登出
	auth.logout(request)
	return redirect('/index/')



def profileUpdate(request):
	if request.method == "POST":
		try:
			name = request.POST['username'].strip()  #取得輸入帳號
			password = request.POST['password']  #取得輸入密碼
			email = request.POST['email']  #取得輸入密碼		
			user= User.objects.create_user(name , email, password)
			user.save()
			return redirect('/login/')
		except:
			return redirect('/error/')			
	else:
		return render(request, "profileUpdate.html")

def error(request):
		return render(request, "error.html")

def map_refine(request):
	user_name = request.user.username
	if request.method == "POST":
		getTitle = request.POST['title']
		getType = request.POST['type']		
		all = imgData.objects.filter(title__contains = "{}".format(getTitle), type = "{}".format(getType))
		return render(request, "map_refine.html", locals())
	else:
		if request.user.is_authenticated:
			all = imgData.objects.filter(username = "{}".format(user_name))	
		else:
			all = imgData.objects.all()  #取得所有景點
		return render(request, "map_refine.html", locals())

def modify(request,editid=None, deletetype=None):  #修改景點資料
	user_name = request.user.username
	item = imgData.objects.get(id = editid)
	if request.method == 'POST':
		item.title = request.POST['title']
		item.content = request.POST['content']
		item.lat = request.POST['lat']
		item.lon = request.POST['lon']
		item.type = request.POST['type']
		item.save()
		return redirect('/blog/')
	else:
		if deletetype=='delete':  #刪除相片
			item.delete()  #從資料庫移除
			return redirect('/blog/')
		return render(request, "modify.html", locals())

def blog(request):
	all = imgData.objects.all()  #取得所有景點
	return render(request, "blog.html", locals())

def blog_detail(request, pk):
	item = imgData.objects.get(id = pk)
	return render(request, "blog-detail.html", locals())


def user_blog(request):
	user_name = request.user.username
	all = imgData.objects.filter(username = "{}".format(user_name))
	return render(request, "user_blog.html", locals())

# Create your views here.
def get_exif(filename):
    image = Image.open(filename)
    image.verify()
    return image._getexif()

def format_lat_lon(data):
    dd = float(data[0])
    mm = float(data[1]) / 60
    ss = float(data[2]) / 3600
    
    result = dd + mm + ss
    return result


