from flask import Flask


app = Flask(__name__)


@app.route("/")
def index():
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
