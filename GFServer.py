import requests
from flask import request
from flask import Flask
import json
from bs4 import BeautifulSoup

GFServer = Flask(__name__)

GGkey=r"AIzaSyD9-4_5QUmogkjgvXdMGYVemsUEVVfy8tI"
PPkey=r"2PvUNGIQHTaDhSCa3E5WD1klEX67ajkM5eLGkgkO"

def fetchLL(address):
	URL=r'https://maps.googleapis.com/maps/api/geocode/json?address='+address+'&key='+GGkey
	LLReq = requests.get(URL)
	LLInfo=LLReq.text
	LLData=json.loads(LLInfo)
	LL=LLData['results'][0]['geometry']['location']
	return LL

def fetchS(address):
	URL=r'https://maps.googleapis.com/maps/api/geocode/json?address='+address+'&key='+GGkey
	SReq = requests.get(URL)
	SInfo=SReq.text
	SData=json.loads(SInfo)
	SInfo=SData['results'][0]['address_components']
	for component in SInfo:
		if component['types'][0]=='administrative_area_level_1':
			S=component['short_name']
			break
		else:
			continue
	return S

class state:
	def __init__(self,data):
		self.name=data['full_name']
		self.phone=[]
		for office in data['offices']:
			if office['name']=='Home Office':
				continue
			else:
				self.phone.append(office['phone'])
		self.picURL=data['photo_url']
		self.party=data['party']
		self.email=data['email']
		LOH=data['roles'][0]['chamber']
		if LOH=='lower':
			self.senOrRep=1
		else:
			self.senOrRep=0
		self.fedOrState=1
	def returnDict(self):
		dict={'name':self.name,'phone':self.phone,'picURL':self.picURL,'email':self.email,'party':self.party,'fedOrState':self.fedOrState,'senOrRep':self.senOrRep}
		return dict

def fetchState(lat,lng):
	URL=r"https://openstates.org/api/v1/legislators/geo/?lat="+str(lat)+"&long="+str(lng)
	stateReq=requests.get(URL)
	stateInfo=stateReq.text
	stateData=json.loads(stateInfo)
	return stateData

class federal:
	def __init__(self,data):
		self.name=data['first_name']+' '+data['last_name']
		self.phone=data['roles'][0]['phone']
		self.picURL=fetchPhoto(data['twitter_account'])
		#if data['current_party']=='R':
		#	self.party='Republican'
		#else:
		#	self.party='Democratic'
		#if data['roles'][0]['chamber']=='House':
		#	self.senOrRep=1
		#else:
		#	self.senOrRep=0
		#self.fedOrState=0
	def returnDict(self):
		dict={'name':self.name,'phone':self.phone,'picURL':self.picURL,'party':self.party,'fedOrState':self.fedOrState,'senOrRep':self.senOrRep}
		return dict


def fetchPhoto(twitter):
	URL=r'https://twitter.com/'+twitter
	source=requests.get(URL)
	picURL=""
	text=source.text
	soup=BeautifulSoup(text)
	#for photo in 
	soup.findALL('img')
	#	picURL=photo.get('src')
	return picURL

def fetchFederal(state):
	fed=[]
	key=""
	sURL=r"https://api.propublica.org/congress/v1/members/senate/"+state+r"/current.json"
	hURL=r"https://api.propublica.org/congress/v1/115/house/members.json"
	sReq=requests.get(sURL,headers={"X-API-Key":PPkey})
	sInfo=sReq.text
	sData=json.loads(sInfo)
	for s in sData['results']:
		URL=r"https://api.propublica.org/congress/v1/members/"+s['id']+".json"
		ssReq=requests.get(URL,headers={"X-API-Key":PPkey})
		ssInfo=ssReq.text
		ssData=json.loads(ssInfo)
		ss=ssData['results'][0]
		ssObject=federal(ss)
		#fed.append(ssObject.returnDict())
		fed.append(ss)
	hReq=requests.get(hURL,headers={"X-API-Key":PPkey})
	hInfo=hReq.text
	hData=json.loads(hInfo)
	for h in hData['results'][0]['members']:
		if state==h['state']:
			URL=r"https://api.propublica.org/congress/v1/members/"+h['id']+".json"
			hhReq=requests.get(URL,headers={"X-API-Key":PPkey})
			hhInfo=hhReq.text
			hhData=json.loads(hhInfo)
			hh=hhData['results'][0]
			#hhObject=federal(hh)
			#fed.append(hhObject.returnDict())
			#fed.append(hh)
		else:
			continue
	return fed

@GFServer.route('/state/',methods=['GET'])
def getState():
	address = str(request.args.get(key='address'))
	address.replace(' ','+')
	LL=fetchLL(address)
	ST=fetchState(LL['lat'],LL['lng'])
	stData=[]
	for st in ST:
		stObject=state(st)
		stData.append(stObject.returnDict())
	return json.dumps(stData,ensure_ascii=False)

@GFServer.route('/federal/',methods=['GET'])
def getFederal():
	address = str(request.args.get(key='address'))
	address.replace(' ','+')
	S=fetchS(address)
	FD=fetchFederal(S)
	return json.dumps(FD,ensure_ascii=False)

if __name__ == "__main__":
	GFServer.run()
