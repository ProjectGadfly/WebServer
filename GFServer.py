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
APIkey="v1key"

# Get both state and latitude/longitude in one call (saves hits on our Google API key, so it's
# worth a little extra trouble).
def addrToGeo(address):
	URL=r'https://maps.googleapis.com/maps/api/geocode/json?address='+address+'&key='+GGkey
	LLData=json.loads(requests.get(URL).text)
        if LLData['status'] != 'ok':
                raise Exception("Error return from Google geocode")
        result = dict()
	result['LL']=LLData['results'][0]['geometry']['location']
        for c in LLData['results'][0]['address_components']:
                if 'administrative_area_level_1' in c['types']:
                        result['state'] = c['short_name']
                        break

	return result
        

# GFServer = how flask gets inserted into the sequence of events
# @ invokes a python process called decoration, applies this function and these
# parameters to postScript,

@GFServer.route('/services/v1/representatives/', methods=['GET'])
def getRepresentatives():
	""" Description:
		Gets information on senators and representatives given an address.
		Returns:
				name: string,
		 		phone: integer,
		 		picURL: string,
		 		email: string,
		 		party: string,
		 		tag_names: [list of strings]
	"""
	# federal
	address = str(request.args.get(key = 'address'))
	# retreive lat and long
	coordinates = fetchLL(address)



# https://maps.googleapis.com/maps/api/geocode

@GFServer.route('/services/v1/script/', methods=['POST'])
def postScript():
	"""
	title: string,
    content: string,
    tags: [list of tag_ids],
    expiration date: string (MM/DD/YY, optional),
    email: string (optional)
	"""
	key = request.headers.get('key')
	if (key != APIkey):
		return json.dumps({'error':'Wrong API Key!'})
	title = request.form['title']
	content = request.form['content']
	tags = request.form['tags']
	email = request.form['email']
	dict = {'title':title, 'content':content, 'tags':tags, 'email':email}
	insert_new_script(dict)



def fetchLL(address):
	URL=r'https://maps.googleapis.com/maps/api/geocode/json?address='+address+'&key='+GGkey
	LLReq = requests.get(URL)
	LLInfo=LLReq.text
	LLData=json.loads(LLInfo)
	LL=LLData['results'][0]['geometry']['location']
	return LL



def fetchState(address):
	"""	Purpose:
		Returns
	"""
	URL = r'https://maps.googleapis.com/maps/api/geocode/json?address=' + address + '&key=' + GGkey
	SReq = requests.get(URL)
	SInfo = SReq.text
	SData = json.loads(SInfo)
	# Grabbing out of the first found result,
	SInfo = SData['results'][0]['address_components']
	for component in SInfo:
		if component['types'][0] == 'administrative_area_level_1':
			State = component['short_name']
			break
		else:
			continue
	return State



def fetchDistrict(ll):
	""" Purpose:
		Fetches federal district based upon the latitute and longitude passed as a parameter
	"""
	#ll = fetchLL(address)
	lat = ll['lat']
	lng = ll['lng']
	URL = r"https://congress.api.sunlightfoundation.com/districts/locate?latitude=" + str(lat) + "&longitude=" + str(lng)
	DReq = requests.get(URL)
	DInfo = DReq.text
	DData = json.loads(DInfo)
	D = DData['results'][0]['district']
	return D



class state:
	def __init__(self, data):
		self.name=data['full_name']
		self.APIkey=""
		for office in data['offices']:
			if office['name'] == 'Home Office':
				continue
			else:
				self.phone.append(office['phone'])
		self.picURL = data['photo_url']
		self.party = data['party']
		self.email = data['email']
		LOH = data['roles'][0]['chamber']
		if LOH == 'lower':
			self.senOrRep = 1
		else:
			self.senOrRep = 0
		self.fedOrState = 1

	def returnDict(self):
		dict = {'name':self.name,'phone':self.phone,'picURL':self.picURL,'email':self.email,'party':self.party,'fedOrState':self.fedOrState,'senOrRep':self.senOrRep}
		return dict

	def fetchStateRep(lat, lng):
		"""	Purpose:
			Returns the state representatives' data
		"""
		URL = r"https://openstates.org/api/v1/legislators/geo/?lat=" + str(lat) + "&long=" + str(lng)
		stateReq = requests.get(URL)
		stateInfo = stateReq.text
		stateData = json.loads(stateInfo)
		return stateData



class federal:
	def __init__(self, data):
		self.name = data['first_name'] + ' ' + data['last_name']
		self.phone = data['roles'][0]['phone']
		self.picURL = fetchPhoto(data['twitter_account'])
		if data['current_party'] == 'R':
			self.party = 'Republican'
		else:
			self.party = 'Democratic'
		if data['roles'][0]['chamber'] == 'House':
			self.senOrRep = 1
		else:
			self.senOrRep = 0
		self.fedOrState = 0

	def returnDict(self):
		dict = {'name':self.name, 'phone':self.phone, 'picURticketL':self.picURL,'email':'', 'party':self.party, 'fedOrState':self.fedOrState, 'senOrRep':self.senOrRep}
		return dict



def fetchPhoto(twitter):
	URL = r'https://twitter.com/' + twitter
	source = requests.get(URL)
	picURL = ""
	plain_text = source.text
	soup = BeautifulSoup(plain_text)
	for photo in soup.find_all('img', {'class':'ProfileAvatar-image '}):
		picURL = photo.get('src')
	return picURL
	federal

def fetchFederal(state, district):
	fed = []
	key = ""
	sURL = r"https://api.propublica.org/congress/v1/members/senate/"+ state + r"/current.json"
	hURL = r"https://api.propublica.org/congress/v1/members/house/"+ state + "/" + str(district) + r"/current.json"
	sReq = requests.get(sURL,headers = {"X-API-Key":PPkey})
	sInfo = sReq.text
	sData = json.loads(sInfo)
	for s in sData['results']:
		URL = r"https://api.propublica.org/congress/v1/members/"+s['id']+".json"
		ssReq = requests.get(URL,headers={"X-API-Key":PPkey})
		ssInfo = ssReq.text
		ssData = json.loads(ssInfo)
		ss = ssData['results'][0]
		# new federal class
		ssObject = federal(ss)
		fed.append(ssObject.returnDict())
	hReq = requests.get(hURL,headers = {"X-API-Key":PPkey})
	hInfo = hReq.text
	hData = json.loads(hInfo)
	for h in hData['results']:
		URL = r"https://api.propublica.org/congress/v1/members/" + h['id'] + ".json"
		hhReq = requests.get(URL,headers = {"X-API-Key":PPkey})
		hhInfo = hhReq.text
		hhData = json.loads(hhInfo)

def fetchFederal(state, district):
	fed = []
	key = ""
	sURL = r"https://api.propublica.org/congress/v1/members/senate/" + state + r"/current.json"
	hURL = r"https://api.propublica.org/congress/v1/members/house/" + state + "/" + str(district) + r"/current.json"
	sReq = requests.get(sURL,headers={"X-API-Key":PPkey})
	sInfo = sReq.text
	sData = json.loads(sInfo)
	for s in sData['results']:
		URL = r"https://api.propublica.org/congress/v1/members/" + s['id'] + ".json"
		ssReq = requests.get(URL,headers = {"X-API-Key":PPkey})
		ssInfo = ssReq.text
		ssData = json.loads(ssInfo)
		ss = ssData['results'][0]
		ssObject = federal(ss)

		fed.append(hhObject.returnDict())
	return fed



def generate_QR_code():
	""" Description:
		Generates QR Code
	"""
	# since the avialability of api is everyones blocking factor
	# and in the long run the qr code is vital, but in the short term we
	# dont need the qr code



def random_ticket_gen():
	"""	Description:
		Returns a ticket wich is a 32 byte base 64 random value
	"""
	ticket = base64.b64encode(token_bytes(24))
	return ticket



def insert_new_script(dict):
	""" Description:
		Takes the fields provided in the dict parameter and adds a unique randomly generated ticket to
		the dict to create a new script.
	"""
	IP = "127.0.0.1"
	# cnx is the connection to the database
	cnx = MySQLdb.connect(host = IP, user = "gadfly_user", passwd = "gadfly_pw", db = "gadfly")
	cursor = cnx.cursor()
	no_success = True
	while(no_success):
		ticket = random_ticket_gen()
		dict['ticket'] = ticket
		try:
			cnx.start_transaction()
			# creates a row in the call script table
			cursor.execute("INSERT INTO call_scripts (title, content, ticket, expiration_date) VALUES (%s, %s, %s, CURDATE() + INTERVAL 6 MONTH)", [dict['title'], dict['content'], dict['ticket']])
			new_id = cnx.insert_id()
			no_success = False
			# Create new entries in table to associate scripts and tags
			for tag_id in dict['tags']:
				cursor.execute("INSERT INTO link_callscripts_tags (call_script_id, tag_id) VALUES (%d, %d)", new_id, tag_id)
			cnx.commit()
			"""
				If email sending is added it will be added here
			"""
		except MySqlException as e:
			# 1062 is a unique column value exception, the ticket has a match in the table
			# the second condition determines which column failed
			if e.Number == 1062 and "key 'ticket'" in e.Message:
				cnx.rollback()
			else:
				# Some other error was encountered and rollback will happen automatically
				raise

	# for each ticket id, insert a new row for each tag id in the link_callscripts_tags table
	cnx.close()

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
WHAT WE NEED TO DO FOR INSERT NEW SCRIPT
for tags in dict['tags']
go into tags table and figure out their tags id_
then insert arow in links table which contains the tags id and the ticket
"""





"""
@GFServer.route('/services/v1/getstate/', methods=['GET'])
def getState():
	key = request.headers.get('key')
	if (key != APIkey):
		return json.dumps({'error':'Wrong API Key!'})
	address = str(request.args.get(key = 'address'))
	address.replace(' ', '+')
	LL = fetchLL(address)
	ST = fetchStateRep(LL['lat'], LL['lng'])
	stData = []
	for st in ST:
		stObject = state(st)
		stData.append(stObject.returnDict())
	return json.dumps(stData, ensure_ascii=False)
"""



"""
@GFServer.route('/services/v1/getfederal/', methods=['GET'])
def getFederal():
	key = request.headers.get('key')
	if (key != APIkey):
		return json.dumps({'error':'Wrong API Key!'})
	address = str(request.args.get(key = 'address'))
	address.replace(' ','+')
	S = fetchState(address)
	D = fetchD(address)
	FD = fetchFederal(S,D)
	return json.dumps(FD,ensure_ascii=False)
"""



if __name__ == "__main__":
	GFServer.run()
