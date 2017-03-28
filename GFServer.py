import requests
from flask import request
from flask import Flask
from flask import Response
import json
from bs4 import BeautifulSoup
import MySQLdb 
import base64
#import secrets

from mysql.connector import MySQLConnection, Error
#from python_mysql_dbconfig import read_db_config

GFServer = Flask(__name__)

# Config info -- most of this should be *elsewhere*, not committed to public repos!
DBIP = "127.0.0.1"
DBUser = "root"
DBName = "gadfly"
DBPasswd = "Czw100806918"


# Keys should be removed from GFServer.py
GGkey=r"AIzaSyD9-4_5QUmogkjgvXdMGYVemsUEVVfy8tI"
PPkey=r"2PvUNGIQHTaDhSCa3E5WD1klEX67ajkM5eLGkgkO"
APIkey="v1key"


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def addrToGeo(address):
    """ Purpose:
        Get both state and latitude/longitude in one call (saves hits on our Google API key, so it's
        worth a little extra trouble).
        Returns:
        A dictionary
    """
    URL = r'https://maps.googleapis.com/maps/api/geocode/json?address=' + address + '&key=' + GGkey
    LLData = json.loads(requests.get(URL).text)
    print(LLData)
    if LLData['status'] != 'OK':
        raise Exception("Error return from Google geocode")
    result = dict()
    result['LL'] = LLData['results'][0]['geometry']['location']
    for c in LLData['results'][0]['address_components']:
        if 'administrative_area_level_1' in c['types']:
            result['state'] = c['short_name']
            break

    return result


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# GFServer = how flask gets inserted into the sequence of events
# @ invokes a python process called decoration, applies this function and these
# parameters to postScript,

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def get_representatives_helper(address):
    """ Purpose:
        Retreive geocode location from address
        Retreive state and federal representatives from data providers
    """
    dict_coord_state = addrToGeo(address)
    ll = dict_coord_state['LL']
    district = fetchDistrict(ll)
    state = dict_coord_state['state']
    # retreive federal data
    federals = fetchFederal(state, district)
    # retreive state data
    states = fetchState(ll)
    # Merge and return federal and state
    results = federals
    results.extend(states)
    return results



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
    key = request.headers.get('APIKey')
    if (key != APIkey):
        return json.dumps({'error':'Wrong API Key!'})
    address = request.args['address']
    # Retreive representative data from helper function
    all_reps = get_representatives_helper(address)
    js = json.dumps(all_reps)
    resp = Response(js, status=200, mimetype='application/json')
    return resp




#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def random_ticket_gen():
    """Description:
        Returns a ticket wich is a 32 byte base 64 random value in string form
    """
	#ticket = base64.b64encode(secrets.token_bytes(24))
	#ticket="12313123"
    ticket="12313"
    return ticket



def insert_new_script(dict):
    """ Purpose:
        Takes the fields provided in the dict parameter and adds a unique randomly generated ticket to
        the dict to create a new script.
        Returns:
        A string, ticket OR an exception
    """
    IP = "127.0.0.1"
    # cnx is the connection to the database
    cnx = MySQLdb.connect(host = DBIP, user = DBUser, passwd = DBPasswd, db = DBName)
    cursor = cnx.cursor()
    no_success = True
    # Loop ensues ticket to be randomly generated will be unique
    while(no_success):
        ticket = random_ticket_gen()
        command="SELECT EXISTS(SELECT title FROM call_scripts WHERE ticket={})".format(ticket)
        cursor.execute(command)
        result=cursor.fetchone()[0]
        if result==0:
            no_success=False
    dict['ticket'] = ticket
    print("start to try")
    try:
	#cnx.start_transaction()
        print("start to execute")
        # creates a row in the call script table
        command="INSERT INTO call_scripts (title, content, ticket, expiration_date) VALUES ('{}', '{}', '{}', CURDATE() + INTERVAL 6 MONTH)".format(dict['title'], dict['content'], dict['ticket'])
        print(command)
        cursor.execute(command)
        print('start ot get id')
        new_id = cnx.insert_id()
        print("new id is "+str(new_id))
        no_success = False
        print("start to insert tags")
        # Create new entries in table to associate scripts and tags
        for tag_id in dict['tags']:
            command="INSERT INTO link_callscripts_tags (call_script_id, tag_id) VALUES ({}, {})".format(new_id, tag_id)
            print(command)
            cursor.execute(command)
        cnx.commit()
        """
            If email sending is added it will be added here
        """
		#except MySqlException as e:
            # 1062 is a unique column value exception, the ticket has a match in the table
            # the second condition determines which column failed
			#if e.Number == 1062 and "key 'ticket'" in e.Message:
			#    cnx.rollback()
			#else:
                # Some other error was encountered and rollback will happen automatically
			#    raise
    except:
        return "break"

    cnx.close()
    return ticket


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

@GFServer.route('/services/v1/script/', methods=['POST'])
def postScript():
    """
    Purpose:
    Posts a new script given information inputted by a user and returns a unique ticket.
    This ticket will be in the unique URL to that script for the user to access if they want to delete the script in the future.
    Returns:
    Ticket, a 32 character string in base64
    """
    key = request.headers.get('APIKey')
    if (key != APIkey):
        return json.dumps({'error':'Wrong API Key!'})
    request.get_json(force=True)
    script_dict=request.json
    print("json: "+str(script_dict['tags']))
    ticket = insert_new_script(script_dict)
    return ticket

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

@GFServer.route('/services/v1/script/', methods=['DELETE'])
def deleteScript():
    """ Purpose:
        Deletes script given a ticket.
        The ticket is internally tied to the script ID.
        This will allow script-writers to "edit" or delete their script.

        Parameter:
        ticket, a string list

        Returns:
        On success, 200 error
        On failure, 400 error

        Useful Source:
        http://www.mysqltutorial.org/python-mysql-delete-data/
    """
    # not touching tags table
    # connection to database
    IP = "127.0.0.1"
    key = request.headers.get('APIKey')
    if (key != APIkey):
        return json.dumps({'error':'Wrong API Key!'})
    ticket=request.args['ticket']
    cnx = MySQLdb.connect(host = DBIP, user = DBUser, passwd = DBPasswd, db = DBName)
    cursor = cnx.cursor()
    # try to delete call script based on ticket number parameter
    try:
        print("start delete script")
        query = "DELETE FROM call_scripts WHERE ticket = '{}'".format(ticket)
        print(query)
        cursor.execute(query)
        # success case
		#success_resp = Response(js, status=200, mimetype='application/json')
        # save the changes
        cnx.commit()
        cnx.close()
        return "200"
    except Error as error:
        # failure case
		#ifailure_resp = Response(js, status=404, mimetype='application/json')
        cnx.close()
        return "400"


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

TagNames = dict()
TagIDs = dict()

def init_tagnames():
    """Purpose:
        Read in the tags table and cache it into memory
        Returns:
        Void
    """
    # establish database connection
    cnx = MySQLdb.connect(host = DBIP, user = DBUser, passwd = DBPasswd, db = DBName)
    cursor = cnx.cursor()
    # execute SQL
    cursor.execute("SELECT tag_name, unique_id FROM tags")
    thetags = cursor.fetchall()
    # store table in a variable
    # store tag_names and id's into two dictionaries
    for row in thetags:
        TagIDs[row[0]] = row[1]
        TagNames[row[1]] = row[0]

init_tagnames()

@GFServer.route('/services/v1/alltags/', methods = ['GET'])
def getAllTags():
    key = request.headers.get('APIKey')
    if (key != APIkey):
        print ("point b")
        failure_resp = Response('Wrong API Key!', status=404)
        return failure_resp
    return Response (json.dumps(TagIDs), status=200, mimetype='application/json')

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def fetchLL(address):
    URL=r'https://maps.googleapis.com/maps/api/geocode/json?address='+address+'&key='+GGkey
    LLReq = requests.get(URL)
    LLInfo=LLReq.text
    LLData=json.loads(LLInfo)
    LL=LLData['results'][0]['geometry']['location']
    return LL


# vestigial, name conflict
"""
def fetchState(address):
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
"""


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


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class state:
    def __init__(self, data):
        self.name=data['full_name']
        for office in data['offices']:
            if office['name'] == 'Home Office':
                self.phone=None
                continue
            else:
                self.phone=office['phone']
        self.picURL = data['photo_url']
        self.party = data['party']
        self.email = data['email']
        self.tags = list()
        LOH = data['roles'][0]['chamber']
        if LOH == 'lower':
            #self.senOrRep = 1
            self.tags.append(TagIDs['representative'])
        else:
            self.tags.append(TagIDs['senator'])
        self.tags.append(TagIDs['state'])

    def returnDict(self):
        dict = {'name':self.name,'phone':self.phone,'picURL':self.picURL,'email':self.email,'party':self.party,'tags':self.tags}
        return dict


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def fetchStateRep(lat, lng):
    """Purpose:
        Returns the state representatives' data
    """
    URL = r"https://openstates.org/api/v1/legislators/geo/?lat=" + str(lat) + "&long=" + str(lng)
    stateReq = requests.get(URL)
    stateInfo = stateReq.text
    stateData = json.loads(stateInfo)
    return stateData


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class federal:
    def __init__(self, data):
        self.tags = list()
        self.name = data['first_name'] + ' ' + data['last_name']
        self.phone = data['roles'][0]['phone']
        self.picURL = fetchPhoto(data['twitter_account'])
        if data['current_party'] == 'R':
            self.party = 'Republican'
        else:
            self.party = 'Democratic'
        if data['roles'][0]['chamber'] == 'House':
            # array of tag id's
            self.tags.append(TagIDs["representative"])
        else:
            self.tags.append(TagIDs["senator"])
        self.tags.append(TagIDs["federal"])

    def returnDict(self):
        """    Purpose:
            Puts all of the data from this federal object into a dictionary
        """
        dict = {'name':self.name, 'phone':self.phone, 'picURL':self.picURL,'email':'', 'party':self.party, 'tags':self.tags}
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


def fetchFederal(state, district):
    """    Purpose:
        Returns the list of federal objects
    """
    fed = []
    key = ""
    sURL = r"https://api.propublica.org/congress/v1/members/senate/" + state + r"/current.json"
    hURL = r"https://api.propublica.org/congress/v1/members/house/" + state + "/" + str(district) + r"/current.json"
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
        hh=hhData['results'][0]
        hhObject=federal(hh)
        fed.append(hhObject.returnDict())
    return fed



def generate_QR_code():
    """ Description:
        Generates QR Code
    """
    # since the avialability of api is everyones blocking factor
    # and in the long run the qr code is vital, but in the short term we
    # dont need the qr code




def fetchState(LL):
    """Purpose:
        Fetch all state reps matching the latitude and longitude
    """
    ST = fetchStateRep(LL['lat'], LL['lng'])
    stData = []
    for st in ST:
        stObject = state(st)
        stData.append(stObject.returnDict())
    return stData




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

@GFServer.route('/services/v1/id/', methods=['GET'])
def getID():
    """ Purpose:
        Given a ticket, find and return the script id
    """
    key = request.headers.get('APIKey')
    if (key != APIkey):
        return json.dumps({'error':'Wrong API Key!'})
    ticket = request.args['ticket']
    cnx = MySQLdb.connect(host = DBIP, user = DBUser, passwd = DBPasswd, db = DBName)
    cursor = cnx.cursor()
    try:
        cursor.execute("SELECT unique_id FROM call_scripts WHERE ticket = {}".format(ticket));
        row = cursor.fetchone()
        id = row[0]
        resp = Response(json.dumps(id), status=200, mimetype='application/json')
        return resp
    except:
        return "failed"



@GFServer.route('/services/v1/script/', methods=['GET'])
def getScript():
    """ Purpose:
        Given a id, find and return the script
    """
    key = request.headers.get('APIKey')
    if (key != APIkey):
        return json.dumps({'error':'Wrong API Key!'})
    id = request.args['id']
    cnx = MySQLdb.connect(host = DBIP, user = DBUser, passwd = DBPasswd, db = DBName)
    cursor = cnx.cursor()
    try:
        print("start to get script")
        cursor.execute("SELECT title,content FROM call_scripts WHERE unique_id = {}".format(id));
        row = cursor.fetchone()
        script=dict()
        script['title'] = row[0]
        script['content'] = row[1]
        script['tags'] = list()
        print(str(script))
        print("start to get tags")
        cursor.execute("SELECT tag_id FROM link_callscripts_tags WHERE call_script_id = {}".format(id));
        rows = cursor.fetchall()
        for row in rows:
            print(str(row[0]))
            print("start to get tagnames")
            command="SELECT tag_name FROM tags WHERE unique_id = {}".format(int(row[0]));
            print(command)
            cursor.execute(command);
            tag_name=cursor.fetchone()[0]
            print(tag_name)
            script['tags'].append(tag_name)
		#resp = Response(json.dumps(script), status=200, mimetype='application/json')
		#return resp
        print(str(script))
        return json.dumps(script)
    except:
        return "failed"



if __name__ == "__main__":
    GFServer.run()
