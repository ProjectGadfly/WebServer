import requests
from flask import request
from flask import Flask
import json
from bs4 import BeautifulSoup

GFServer = Flask(__name__)

GGkey=r"AIzaSyD9-4_5QUmogkjgvXdMGYVemsUEVVfy8tI"
PPkey=r"2PvUNGIQHTaDhSCa3E5WD1klEX67ajkM5eLGkgkO"
APIkey=r"b9ae3e78eb1c94ee7d7c4cb0cfa0bd889e900f2abefdf75f418c79f133aee28f468f18194b3ce1cd54f1850c332d7b6fd096ee50068cc5cb542efd0bd07cd6f3"

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

def fetchD(address):
	ll=fetchLL(address)
	lat=ll['lat']
	lng=ll['lng']
	URL=r"https://congress.api.sunlightfoundation.com/districts/locate?latitude="+str(lat)+"&longitude="+str(lng)
	DReq=requests.get(URL)
	DInfo=DReq.text
	DData=json.loads(DInfo)
	D=DData['results'][0]['district']
	return D

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
		if data['current_party']=='R':
			self.party='Republican'
		else:
			self.party='Democratic'
		if data['roles'][0]['chamber']=='House':
			self.senOrRep=1
		else:
			self.senOrRep=0
		self.fedOrState=0
	def returnDict(self):
		dict={'name':self.name,'phone':self.phone,'picURL':self.picURL,'email':'','party':self.party,'fedOrState':self.fedOrState,'senOrRep':self.senOrRep}
		return dict


def fetchPhoto(twitter):
	URL=r'https://twitter.com/'+twitter
	source=requests.get(URL)
	picURL=""
	plain_text=source.text
	soup=BeautifulSoup(plain_text)
	for photo in soup.find_all('img',{'class':'ProfileAvatar-image '}):
		picURL=photo.get('src')
	return picURL

def fetchFederal(state,district):
	fed=[]
	key=""
	sURL=r"https://api.propublica.org/congress/v1/members/senate/"+state+r"/current.json"
	hURL=r"https://api.propublica.org/congress/v1/members/house/"+state+"/"+str(district)+r"/current.json"
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
		fed.append(ssObject.returnDict())
	hReq=requests.get(hURL,headers={"X-API-Key":PPkey})
	hInfo=hReq.text
	hData=json.loads(hInfo)
	for h in hData['results']:
		URL=r"https://api.propublica.org/congress/v1/members/"+h['id']+".json"
		hhReq=requests.get(URL,headers={"X-API-Key":PPkey})
		hhInfo=hhReq.text
		hhData=json.loads(hhInfo)
		hh=hhData['results'][0]
		hhObject=federal(hh)
		fed.append(hhObject.returnDict())
	return fed

@GFServer.route('/services/v1/getstate/',methods=['GET'])
def getState():
	key=request.headers.get('key')
	if (key != APIkey):
		return json.dumps({'error':'Wrong API Key!'})
	address = str(request.args.get(key='address'))
	address.replace(' ','+')
	LL=fetchLL(address)
	ST=fetchState(LL['lat'],LL['lng'])
	stData=[]
	for st in ST:
		stObject=state(st)
		stData.append(stObject.returnDict())
	return json.dumps(stData,ensure_ascii=False)

@GFServer.route('/services/v1/getfederal/',methods=['GET'])
def getFederal():
	key=request.headers.get('key')
	if (key != APIkey):
		return json.dumps({'error':'Wrong API Key!'})
	address = str(request.args.get(key='address'))
	address.replace(' ','+')
	S=fetchS(address)
	D=fetchD(address)
	FD=fetchFederal(S,D)
	return json.dumps(FD,ensure_ascii=False)

if __name__ == "__main__":
	GFServer.run()
