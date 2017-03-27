import requests
from flask import request
from flask import Flask
import json
from bs4 import BeautifulSoup
import MySQLdb
import base64

from mysql.connector import MySQLConnection, Error
#from python_mysql_dbconfig import read_db_config

GFServer = Flask(__name__)


# Config info -- most of this should be *elsewhere*, not committed to public repos!
DBIP = "127.0.0.1"
DBUser = "gadfly_user"
DBName = "gadfly"
DBPasswd = "gadfly_pw"


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
    if LLData['status'] != 'ok':
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
    # store table in a variable
    GFServer.g[TagNames] = dict()
    GFServer.g[TagIDs] = dict()
    # store tag_names and id's into two dictionaries
    for (name, id) in cursor:
        GFServer.g[TagNames][name] = id
        GFServer.g[TagIDs][id] = name


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
    ticket = base64.b64encode(token_bytes(24))
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
    key = request.headers.get('key')
    if (key != APIkey):
        return json.dumps({'error':'Wrong API Key!'})
    title = request.form['title']
    content = request.form['content']
    tags = request.form['tags']
    email = request.form['email']
    dict = {'title':title, 'content':content, 'tags':tags, 'email':email}
    insert_new_script(dict)
    return ticket

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

@GFServer.route('/services/v1/script/', methods=['DELETE'])
def deleteScript(ticket):
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
    cnx = MySQLdb.connect(host = DBIP, user = DBUser, passwd = DBPasswd, db = DBName)
    cursor = cnx.cursor()
    # try to delete call script based on ticket number parameter
    try:
        query = "DELETE FROM call_scripts WHERE id = %s"
        cursor.execute(query, (ticket,))
        # success case
        success_resp = Response(js, status=200, mimetype='application/json')
        # save the changes
        cnx.commit()
        cursor.close()
        cnx.close()
        return success_resp
    except Error as error:
        # failure case
        failure_resp = Response(js, status=404, mimetype='application/json')
        cursor.close()
        cnx.close()
        return failure_resp


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

@GFServer.route('/services/v1/alltags/', methods = ['GET'])
def getAllTags():
    key = request.headers.get('key')
    if (key != APIkey):
        return json.dumps({'error':'Wrong API Key!'})

    tags = list()
    for t in GFServer.g.TagNames:
        entry = [t, GFServer.g.TagNames[t]]
        tags.append(entry)

    return json.dumps(tags);

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
        self.tags = list()
        self.name=data['full_name']
        for office in data['offices']:
            if office['name'] == 'Home Office':
                continue
            else:
                self.phone.append(office['phone'])
        self.picURL = data['photo_url']
        self.party = data['party']
        self.email = data['email']
        LOH = data['rolesGFServer'][0]['chamber']
        if LOH == 'lower':
            #self.senOrRep = 1
            self.tags.append(TagNames['representative'])
        else:
            self.tags.append(TagNames['senator'])
        self.tags.append(TagNames['state'])

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
            self.tags.append(GFServer.g[TagIDs]["representative"])
        else:
            self.tags.append(GFServer.g[TagIDs]["senator"])
        self.tags.append(GFServer.g[TagIDs]["federal"])

    def returnDict(self):
        """    Purpose:
            Puts all of the data from this federal object into a dictionary
        """
        dict = {'name':self.name, 'phone':self.phone, 'picURticketL':self.picURL,'email':'', 'party':self.party, 'tags':self.tags}
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
    key = request.headers.get('key')
    if (key != APIkey):
        return json.dumps({'error':'Wrong API Key!'})
    ticket = request.headers.get('ticket')
    cnx = MySQLdb.connect(host = DBIP, user = DBUser, passwd = DBPasswd, db = DBName)
    cursor = cnx.cursor()
    cursor.execute("SELECT unique_id FROM call_scripts WHERE ticket = %s", ticket,);
    if cursor.with_rows:
        row = cursor.fetchone()
        id = row[0]
        resp = Response(jason.dumps(id), status=200, mimetype='application/json')
        return resp
    else:
        resp = Response(None, status=404)
        return resp


if __name__ == "__main__":
    GFServer.run()
