import requests
from flask import request
from flask import Flask
import json
from bs4 import BeautifulSoup
import MySQLdb
import base64

GFServer = Flask(__name__)

GGkey=r"AIzaSyD9-4_5QUmogkjgvXdMGYVemsUEVVfy8tI"
PPkey=r"2PvUNGIQHTaDhSCa3E5WD1klEX67ajkM5eLGkgkO"
APIkey=""

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
ss=ssData['results'][0]
		ssObject=federal(ss)
		fed.append(ssObject.returnDict())
	hReq=requests.get(hURL,headers={"X-API-Key":PPkey})
	hI
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
		dict={'name':self.name,'phone':self.phone,'picURticketL':self.picURL,'email':'','party':self.party,'fedOrState':self.fedOrState,'senOrRep':self.senOrRep}
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

		fed.append(hhObject.returnDict())
	return fed

############################
#IP="127.0.0.1"
# Open database connection
#db = MySQLdb.connect(host=IP,user="gadfly_user",passwd="gadfly_pw",db="gadfly")
# prepare a cursor object using cursor() method
#cursor = db.cursor()
# execute SQL query using execute() method.
#cursor.execute("SELECT * FROM call_scripts")

# Fetch a single row using fetchone() method.
#data = cursor.fetchone()

#print("Call Script : " + str(data))

# disconnect from server
#db.close()

################################
# 32 byte base 64 random value
def random_ticket_gen():
	ticket = base64.b64encode(token_bytes(24))
	return ticket

IMPORTANT
NEED A TAGS TABLE AND A LINKS (RELATIONS, MANY TO MANY) TABLE


def insert_new_script(dict):
	ticket=random_ticket_gen()
	dict['ticket']=ticket
	IP="127.0.0.1"
	db = MySQLdb.connect(host=IP,user="gadfly_user",passwd="gadfly_pw",db="gadfly")
	cursor = db.cursor()
	# Look for reports of unique violation constraint for ticket
	# ticket col is indexed and labeled as unique (unique enforced by database)
	# check for error indicating ticket is not unique
	try:
		cursor.execute("INSERT INTO call_scripts (title, content, ticket, expiration_date) VALUES (%s, %s, %s, CURDATE() + INTERVAL 6 MONTH)",[dict['title'], dict['content'], dict['ticket']])
		db.commit()
	except:
		# revert back those changes completely if an error occurs
		db.rollback()
		insert_new_script(dict)
	db.close()


WHAT WE NEED TO DO FOR INSERT NEW SCRIPT
for tags in dict['tags']
go into tags table and figure out their tags id_
then insert arow in links table which contains the tags id and the ticket



@GFServer.route('/services/v1/postscript/',methods['POST'])
def postScript():
	key=request.headers.get('key')
	if (key != APIkey):
		return json.dumps({'error':'Wrong API Key!'})
	title=request.form['title']
	content=request.form['content']
	tags=request.form['tags']
	dict={'title':title,'content':content,'tags':tags,'ticket':""}
	insert_new_script(dict)

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
