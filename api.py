import io
import tarfile
import requests

from flask import Flask, request, jsonify, make_response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def packFile(content, name, archive):
    s = io.StringIO(content)
    s.seek(0)

    tarinfo = tarfile.TarInfo(name="main.tex")
    tarinfo.size = len(s.getvalue())
    archive.addfile(tarinfo=tarinfo, fileobj=io.BytesIO(s.getvalue().encode('utf-8')))

def tarMe(latex, tarname):
    archive = tarfile.open(tarname, mode='w')

    packFile(latex, "main.tex", archive)

    archive.close()

def requestPDF(tarname):
    params = {
        'target': 'main.tex',
        'force': 'true'
    }

    files = {
        'file': open(tarname, 'rb')
    }

    response = requests.post('https://texlive2020.latexonline.cc/data', params=params, files=files)

    return response;

@app.route('/compile/', methods=['POST'])
def respond():
    #get name from url
    latex = request.json.get("latex", None)
    latexLen = "latex size: " + str(len(latex)) + " characters "

    print(f"Received: {latexLen}")

    tarname = "test.tar"
    tarMe(latex, tarname)

    # send a post request to the latexonline.cc server

    response2 = requestPDF(tarname)
    #

    #response = {}
    #response["MESSAGE"] = f"sneed {latex}"
    #response["PDF"] = response2.content;

    # IF SUCCESSFUL
    response = make_response(response2.content)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'filename=schedule.pdf'
    return response


#return response2.content #jsonify(response)

@app.route('/')
def index():
    # A welcome message to test our server
    return "<h1>Welcome to our medium-greeting-api!</h1>"

if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)
