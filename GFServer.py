import requests
from flask import request
from flask import Flask
from flask import Response
import json
from bs4 import BeautifulSoup
import MySQLdb 
import base64
from os import urandom
import pyqrcode

GFServer = Flask(__name__)

# Config info -- most of this should be *elsewhere*, not committed to public repos!
DBIP = "127.0.0.1"
DBUser = "gadfly_user"
DBName = "gadfly"
DBPasswd = "gadfly_PW123"


# Keys should be removed from GFServer.py
GGkey=r"AIzaSyD9-4_5QUmogkjgvXdMGYVemsUEVVfy8tI"
PPkey=r"2PvUNGIQHTaDhSCa3E5WD1klEX67ajkM5eLGkgkO"
APIkey="v1key"


#get geo~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def addrToGeo(LLData):
    """ Purpose:
        Get both state and latitude/longitude in one call (saves hits on our Google API key, so it's
        worth a little extra trouble).
        Returns:
        A dictionary
    """
    result = dict()
    result['LL'] = LLData['results'][0]['geometry']['location']
    for c in LLData['results'][0]['address_components']:
        if 'administrative_area_level_1' in c['types']:
            result['state'] = c['short_name']
            break
    return result

def fetchDistrict(ll):
    """ Purpose:
        Fetches federal district based upon the latitute and longitude passed as a parameter
    """
    lat = ll['lat']
    lng = ll['lng']
    URL = r"https://congress.api.sunlightfoundation.com/districts/locate?latitude=" + str(lat) + "&longitude=" + str(lng)
    DReq = requests.get(URL)
    DInfo = DReq.text
    DData = json.loads(DInfo)
    D = DData['results'][0]['district']
    return D

# end get geo~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


# support functions~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~`


def fetchPhoto(twitter):
    URL = r'https://twitter.com/' + twitter
    source = requests.get(URL)
    picURL = ""
    plain_text = source.text
    soup = BeautifulSoup(plain_text)
    for photo in soup.find_all('img', {'class':'ProfileAvatar-image '}):
        picURL = photo.get('src')
    return picURL



# end support functions~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~`


# classes~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

#end classes~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~``


#fetch functions~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

def fetchStateRep(lat, lng):
    """Purpose:
    Returns the state representatives' data
    """
    URL = r"https://openstates.org/api/v1/legislators/geo/?lat=" + str(lat) + "&long=" + str(lng)
    stateReq = requests.get(URL)
    stateInfo = stateReq.text
    stateData = json.loads(stateInfo)
    return stateData

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

#end fetch functions~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~``




#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# GFServer = how flask gets inserted into the sequence of events
# @ invokes a python process called decoration, applies this function and these
# parameters to postScript,

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def get_representatives_helper(LLData):
    """ Purpose:
        Retreive geocode location from address
        Retreive state and federal representatives from data providers
    """
    dict_coord_state = addrToGeo(LLData)
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



@GFServer.route('/services/v1/representatives', methods=['GET'])
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
        return Response('Error: Wrong API Key!', status=401)
    address = request.args['address']
    URL = r'https://maps.googleapis.com/maps/api/geocode/json?address=' + address + '&key=' + GGkey
    LLData = json.loads(requests.get(URL).text)
    if LLData['status'] != 'OK':
        resp = Response("{'Error':'invalid address'}", status=404, mimetype='application/json')
        return resp
    for c in LLData['results'][0]['address_components']:
        if 'country' in c['types']:
            if c['short_name'] != 'US':
                resp = Response("{'Error':'address should be in US'}", status=404, mimetype='application/json')
                return resp
            break
    if len(LLData['results'][0]['address_components'])<3:
        resp = Response("{'Error':'address too broad'}", status=404, mimetype='application/json')
        return resp
    # Retreive representative data from helper function
    all_reps = get_representatives_helper(LLData)
    js = json.dumps(all_reps)
    resp = Response(js, status=200, mimetype='application/json')
    return resp


# post new script~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def random_ticket_gen():
    """Description:
        Returns a ticket wich is a 32 byte base 64 random value in string form
    """
    ticket = base64.b64encode(urandom(24))
    return ticket



def insert_new_script(dict):
    """Purpose:

        Takes the fields provided in the dict parameter and adds a
        unique randomly generated ticket to the dict to create a new
        script.

        Returns:
        A dict, with ticket and id
    """

    # cnx is the connection to the database
    cnx = MySQLdb.connect(host = DBIP, user = DBUser, passwd = DBPasswd, db = DBName)
    cursor = cnx.cursor()
    no_success = True
    # Loop and transaction ensure ticket will be unique even though random
    cursor.execute("START TRANSACTION")
    while(no_success):
        ticket = str(random_ticket_gen())
        length=len(ticket)
        ticket=ticket[2:length-1]
        print(ticket)
        command="SELECT EXISTS(SELECT title FROM call_scripts WHERE ticket='{}')".format(ticket)
        print(command)
        cursor.execute(command)
        result=cursor.fetchone()[0]
        if result==0:
            no_success=False
    dict['ticket'] = ticket
    print("start to try")
    try:
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
        cnx.close()
        resp = Response("{'Error':'Post failed'}", status=404, mimetype='application/json')
        return resp

    cnx.close()
    result={'ticket':ticket,'id':new_id}
    resp = Response(json.dumps(result), status=200, mimetype='application/json')
    return resp


@GFServer.route('/services/v1/script', methods=['POST'])
def postScript():
    """
    Purpose:
    Posts a new script given information inputted by a user and returns a unique ticket.
    This ticket will be in the unique URL to that script for the user to access if they want to delete the script in the future.
    Returns:
    A dict with a ticket and a id
    """
    key = request.headers.get('APIKey')
    if (key != APIkey):
        return Response('Error: Wrong API Key!', status=401)
    request.get_json(force=True)
    script_dict=request.json
    print("json: "+str(script_dict['tags']))
    resp = insert_new_script(script_dict)
    return resp

# end post new script~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# delete script~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

@GFServer.route('/services/v1/script', methods=['DELETE'])
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
    key = request.headers.get('APIKey')
    if (key != APIkey):
        return Response('Error: Wrong API Key!', status=401)
    ticket=request.args['ticket']
    ticket=ticket.replace(" ","+")
    cnx = MySQLdb.connect(host = DBIP, user = DBUser, passwd = DBPasswd, db = DBName)
    cursor = cnx.cursor()
    print("ticketttttttt"+ticket)
    command="SELECT EXISTS(SELECT title FROM call_scripts WHERE ticket='{}')".format(ticket)
    cursor.execute(command)
    result=cursor.fetchone()[0]
    print("resultttttt"+str(result))
    if result==0:
        resp = Response("{'Error':'No such ticket'}", status=404, mimetype='application/json')
        return resp
    # try to delete call script based on ticket number parameter
    try:
        print("start delete script")
        query = "SELECT unique_id FROM call_scripts WHERE ticket = '{}'".format(ticket)
        print(query)
        cursor.execute(query)
        id=cursor.fetchone()[0]
        print("idddddddddd"+str(id))
        query = "DELETE FROM link_callscripts_tags WHERE call_script_id = {}".format(id)
        print(query)
        cursor.execute(query)
        query = "DELETE FROM call_scripts WHERE ticket = '{}'".format(ticket)
        print(query)
        cursor.execute(query)
        success_resp = Response("{'Result':'Deletion Succeeded'}", status=200, mimetype='application/json')
        cnx.commit()
        cnx.close()
        return success_resp
    except:
        failure_resp = Response("{'Error':'Deletion Failed'}", status=404, mimetype='application/json')
        cnx.close()
        return failure_resp


# end delete script~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# alltags~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

TagNames = dict()
TagIDs = dict()

def init_tagnames():
    """
		Purpose:
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

#automatically load all tags when application start
init_tagnames()

@GFServer.route('/services/v1/alltags', methods = ['GET'])
def getAllTags():
    key = request.headers.get('APIKey')
    if (key != APIkey):
        return Response('Error: Wrong API Key!', status=401)

    return Response (json.dumps(TagNames), status=200, mimetype='application/json')

# end alltags~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


# get id and script~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


@GFServer.route('/services/v1/id', methods=['GET'])
def getID():
    """ Purpose:
        Given a ticket, find and return the script id
    """
    key = request.headers.get('APIKey')
    if (key != APIkey):
        return Response('Error: Wrong API Key!', status=401)

    ticket = request.args['ticket']
    ticket=ticket.replace(" ","+")
    cnx = MySQLdb.connect(host = DBIP, user = DBUser, passwd = DBPasswd, db = DBName)
    cursor = cnx.cursor()
    command="SELECT EXISTS(SELECT title FROM call_scripts WHERE ticket='{}')".format(ticket)
    cursor.execute(command)
    result=cursor.fetchone()[0]
    if result==0:
        resp = Response("{'Error':'No such ticket'}", status=404, mimetype='application/json')
        return resp
    try:
        command = "SELECT unique_id FROM call_scripts WHERE ticket = '{}'".format(ticket)
        print(command)
        cursor.execute(command)
        print("finish getting id")
        row = cursor.fetchone()
        id = row[0]
        resp = Response("{'id':"+str(id)+"}", status=200, mimetype='application/json')
        return resp
    except:
        resp = Response("{'id':null}", status=404, mimetype='application/json')
        return resp



@GFServer.route('/services/v1/script', methods=['GET'])
def getScript():
    """ Purpose:
        Given a id, find and return the script
    """
    key = request.headers.get('APIKey')
    if (key != APIkey):
        return Response('Error: Wrong API Key!', status=401)

    id = request.args['id']
    cnx = MySQLdb.connect(host = DBIP, user = DBUser, passwd = DBPasswd, db = DBName)
    cursor = cnx.cursor()
    command="SELECT EXISTS(SELECT title FROM call_scripts WHERE unique_id={})".format(id)
    cursor.execute(command)
    result=cursor.fetchone()[0]
    if result==0:
        resp = Response("{'Error':'No such id'}", status=404, mimetype='application/json')
        return resp
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
        resp = Response(json.dumps(script), status=200, mimetype='application/json')
        return resp
    except:
        resp = Response("{'Script':null}", status=404, mimetype='application/json')
        return resp


# end get id and script~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

if __name__ == "__main__":
    GFServer.run()
