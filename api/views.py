from django.shortcuts import render
from django.http import HttpResponse
import requests as session
from bs4 import BeautifulSoup
import datetime
import re
import json
import ast
import html
import lxml
import cchardet
from django.views.decorators.cache import cache_page
from .models import Token

# Create your views here.


def test(request):
	tokens=Token.objects.all()
	ltokens=[]
	for token in tokens:
		ltokens.append(token.token)
	headers=request.headers
	print(headers)
	if headers.get('token'):
		if headers['token'] in ltokens:
			return HttpResponse('Valid token')
	return HttpResponse('Check Console')


@cache_page(60*60)
def profile(response):
	tokens=Token.objects.all()
	ltokens=[]
	for token in tokens:
		ltokens.append(token.token)
	headers=response.headers
	print(headers)
	if 'Token' in headers:
		print(ltokens)
		if headers['Token'] in ltokens:
			u=response.GET.get('username', '')
			url=f'https://myanimelist.net/profile/{u}'
			#print(url)
			begin=datetime.datetime.now()

			resp = session.get(url)
			print(datetime.datetime.now()-begin)
			soup = BeautifulSoup(resp.content,features="lxml")
			#print(resp.content)
			tags = soup.find_all("title")
			for tag in tags:
				if tag.text.count('404')>0:
					return HttpResponse(json.dumps('{}'), content_type="application/json")
				else:
					title,grb = (tag.text).split("'s")

			#getting the profile bits
			RetProlist=[]
			Prolist=[]
			x=0
			for tag in soup.find_all('span'):
				if x==1:
					Prolist.append(tag.text)
					break
				if tag.text=='Clubs':
					x+=1
				Prolist.append(tag.text)
			Prolist=Prolist[Prolist.index('Last Online'):]
			for index in range(len(Prolist)):
				if index%2==0:
					RetProlist.append(f"{Prolist[index]}: {Prolist[index+1]}")
			RetProlist.pop(RetProlist.index('Statistics: History'))

			#gettings the stats
			for tag in soup.find_all('div', {'class':"user-statistics mb24"}, id=True):
				t=tag.text.replace('\n', '')
				m = re.search(f"{'Anime History'}(.+?){'Manga Stats'}", t)
				if m:
					m= m.group(1)
				t=t.replace(m, '')
				t,garb=t.split('Manga History')
				t=t.replace('StatisticsAnime Stats','').replace('Anime HistoryManga Stats', '').replace(' ', '').replace(':','').replace(',','')
				#now we have condensed info, time to make it into a dict?
				t="{"+t+"}"
				t=t.replace('Days', '''"ADays":''', 1)
				fields=['MeanScore', 'Watching', 'Completed', 'On-Hold', 'Dropped', 'PlantoWatch', 'TotalEntries', 'Rewatched', 'Episodes']
				for field in fields:
					t=t.replace(field, f''',"A{field}":''', 1)
				anime, manga=t.split(''',"AEpisodes":''')
				epival, manga1 = manga.split('Days')
				anime1=t.replace(manga, f"{epival}"+"}")
				manga1='''{"Days":'''+manga1
				fields=['MeanScore', 'Reading', 'Completed', 'On-Hold', 'Dropped', 'PlantoRead', 'TotalEntries', 'Reread', 'Chapters', 'Volumes']
				for field in fields:
					manga1=manga1.replace(field, f''',"M{field}":''')
				anime1=ast.literal_eval(anime1)
				manga1=ast.literal_eval(manga1)
			#getting favortie anime thingy
			fav_anime=[]
			for tag in soup.find_all('ul', {'class':"favorites-list anime"}):
				x=0
				for tags in tag:
					if str(type(tags))!="<class 'bs4.element.NavigableString'>":
						grb, t=str(tags).replace('</div>', 'splithere', 1).split('splithere')
						grb , t=t.split('<a href=')
						t ,grb=t.split("<br/>")
						t=t.replace('"https:', '{"url":"https:').replace('>', ',"name":"', 1).replace('</a>', '"}')
						#print(t)
						x+=1
						fav_anime.append(ast.literal_eval(t))
					if x==5:
						break
			#getting favorite maga thingy
			fav_manga=[]
			for tag in soup.find_all('ul', {'class':"favorites-list manga"}):
				x=0
				for tags in tag:
					if str(type(tags))!="<class 'bs4.element.NavigableString'>":
						grb, t=str(tags).replace('</div>', 'splithere', 1).split('splithere')
						grb , t=t.split('<a href=')
						t ,grb=t.split("<br/>")
						t=t.replace('"https:', '{"url":"https:').replace('>', ',"name":"', 1).replace('</a>', '"}')
						#print(t)
						x+=1
						fav_manga.append(ast.literal_eval(t))
					if x==5:
						break
			fav_chars=[]
			for tag in soup.find_all('ul', {'class':"favorites-list characters"}):
				x=0
				for tags in tag:
					if str(type(tags))!="<class 'bs4.element.NavigableString'>":
						grb, t=str(tags).replace('</div>', 'splithere', 1).split('splithere')
						grb , t=t.split('<a href=')
						t ,grb=t.split("<br/>")
						t=t.replace('"https:', '{"url":"https:').replace('>', ',"name":"', 1).replace('</a>', '"}')
						#print(t)
						x+=1
						fav_chars.append(ast.literal_eval(t))
					if x==5:
						break
			fav_peps=[]
			for tag in soup.find_all('ul', {'class':"favorites-list people"}):
				x=0
				for tags in tag:
					if str(type(tags))!="<class 'bs4.element.NavigableString'>":
						grb, t=str(tags).replace('</div>', 'splithere', 1).split('splithere')
						grb , t=t.split('<a href=')
						t ,grb=t.split("<br/>")
						x+=1
						t=t.replace('"https:', '{"url":"https:').replace('>', ',"name":"', 1).replace('</a>', '"}')
						#print(t)
						fav_peps.append(ast.literal_eval(t))
					if x==5:
						break
			tags=soup.find_all("img", {"class":"lazyload"})
			image_url=None
			for tag in tags:
				image_url,grb=tag['data-src'].split('?')
				break
			if image_url!=None:
				t={"image_url":image_url,"username":title,"Anime":anime1, "Manga":manga1, "favorites":{"Anime":fav_anime, "Manga":fav_manga, "Character":fav_chars, "People":fav_peps}}
			else:
				t={"image_url":None,"username":title,"Anime":anime1, "Manga":manga1, "favorites":{"Anime":fav_anime, "Manga":fav_manga, "Character":fav_chars, "People":fav_peps}}
			#print(t)
			print(datetime.datetime.now()-begin)
			t['Profile']=RetProlist
			return HttpResponse(json.dumps(t), content_type="application/json")
		else:
			return HttpResponse(json.dumps("{'error':'Invalid Token'}"), content_type="application/json")

	else:
		return HttpResponse(json.dumps("{'error':'No token provided'}"), content_type="application/json")

