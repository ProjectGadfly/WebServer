from flask import Flask

"""
server html page that takes information
connect to data api
assemble data and drop html page back to browser
website is where people enter (nonprogramming) scripts"
"""


"""
    getlabwiki
"""
"""
html character
-> when you create a script, go with plaintext, plaintext sends stream of chars to server
what looks like chars is eaten in html, use non-breaking space char in html



get:

post:
"""


# creation and storing of documents

app = Flask(__name__)


@app.route("/")
def index():
    """
    Description:
        Gets the index page of the web server, returns a from for entering address
        when you get data back, it returns rep data formtml

        I need to put An's html page

        use location tag as input for put operation

        address = page name
        use querry to alter uri = address


        rest comes down to way u structured urleach object gets unique url
         """
         return "Index!"
    # return render('index.html')
    pass


@app.route("/", method=['POST'])
def search():

    # return render('results.html' .... )
    pass


@app.route("/new_script", method=['GET'])
def new_script():
    # return a form for the user to enter a new script
    pass


@app.route("/new_script", method=['POST'])
def save_script():
    # save the script the user uploaded, and return the saved script information
    pass


@app.route("/edit_script", method=['GET'])
def edit_script():
    # return a form with the existing script for editing
    pass


@app.route("/update_script", method=['POST'])
def update_script():
    # take the updated script and save it, and return the script information
    pass


@app.route("/show_script", method=['GET'])
def show_script():
    # display the script and it's information
    pass
