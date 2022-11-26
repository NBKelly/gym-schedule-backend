import io
import re
import json
import os
import tarfile
import requests
import random

from flask import Flask, request, jsonify, make_response
from flask_cors import CORS

# CORS allow - for now take anything, later I will nuke it down to just the github page
app = Flask(__name__)
CORS(app)

approvedList = set(json.load(open("images/allowed.json"))['allowed'])
approvedFolders = set(json.load(open("images/allowed.json"))['folders'])

## checks that every supplied image is on the approved images list
def verifyImages(images):
    for image in images:
        if image in approvedList:
            if not os.path.exists(image):
                return "bad image (file doesn't exist): " + image
            continue
        else:
            return "bad image (image not on allowed list - malformed name or type): " + image

    return True

## this is predicated on the images being on the approved list/existing already
def replaceImages(images, imagePrefs, latex):
    new_images = []
    for image in images:
        #all images are prefased with "image/"
        # we want to change it to "image/[pref]"
        found = False;
        for pref in imagePrefs:
            if(pref == ""):
                #new_images.append(image)
                #found = True
                break
            ## see if a new image exists to replace the old one
            new_image = image.replace("images/", "images/" + pref)
            if os.path.exists(new_image):
                latex.replace(image, new_image)
                new_images.append(new_image)
                found = True
                break

        if not found:
            new_images.append(image)


    images.clear()
    images.extend(new_images)

    return latex

## packs the latex file into the tar (without actually making a new file)
def packFile(content, name, archive):
    s = io.StringIO(content)
    s.seek(0)

    tarinfo = tarfile.TarInfo(name="main.tex")
    tarinfo.size = len(s.getvalue())
    archive.addfile(tarinfo=tarinfo, fileobj=io.BytesIO(s.getvalue().encode('utf-8')))

## packs the image into the tar
def packImage(_name, archive):
    archive.add(_name)

## creates a tar archive with the latex file and all included images
def tarMe(latex, tarname, images):
    archive = tarfile.open(tarname, mode='w')

    packFile(latex, "main.tex", archive)

    for image in images:
        packImage(image, archive)

    archive.close()

## requests a pdf from the server
def requestPDF(tarname):
    params = {
        'target': 'main.tex',
        'force': 'true'
    }

    files = {
        'file': open(tarname, 'rb')
    }

    response = requests.post('https://texlive2020.latexonline.cc/data', params=params, files=files)

    ## remove the created tar file (so we don't run out of space)
    os.remove(tarname)

    return response;

def generateTarName():
    return str(random.randint(0, 99999)) + "-collected.tar"

@app.route('/compile/', methods=['POST'])
def respond():
    #get name from url
    latex = request.json.get("latex", None)
    images = request.json.get("images", None)
    prefs = request.json.get("imageprefs", None)

    latexLen = "latex size: " + str(len(latex)) + " characters "

    print(f"Received: {latexLen}")

    ## The image set doesn't add up - simply abort

    imageStr = verifyImages(images)
    if (imageStr != True):
        response = make_response("image list contains an illegal expression or form. The supplied images were: " + str(images) + "\n the image checker reported: " + imageStr)
        response.headers['Content-Type'] = 'text/plain'
        response.status_code = 400
        return response

    ## replace the images if we can
    latex = replaceImages(images, prefs, latex)

    ## tarname should be unique for each client
    ## on the chance it clashes, who cares, they can just run it back
    tarname = generateTarName()

    ## create tar
    tarMe(latex, tarname, images)

    # send a post request to the latexonline.cc server
    latex_response = requestPDF(tarname)

    if latex_response.status_code == 200:
        response = make_response(latex_response.content)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'filename=schedule.pdf'
        return response

    else:
        response = make_response(latex_response.content)
        response.headers['Content-Type'] = 'text/plain'
        response.status_code = latex_response.status_code
        return response

@app.route('/')
def index():
    # A welcome message to test our server
    return "<h1>Whoops! Can't show this to a christain internet!</h1><br><p>To see what this is actually about, please visit <a href=\"https://nbkelly.github.io/GymSchedule/\">the workout templar service</a></p>"

if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)
