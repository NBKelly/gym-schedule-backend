#!/bin/python3

import json
import sys

f = open("images/allowed.json", "r", encoding="utf-8")

allowedImages = json.load(f)
f.close()

output = open("images/allowed.json", "w", encoding="utf-8")
num_args = len(sys.argv)

for i in range (1, num_args):
    image = sys.argv[i]
    if not image in allowedImages['allowed']:
        allowedImages['allowed'].append(image)
    #print(image)

output.write(json.dumps(allowedImages))
output.close()
print(json.dumps(allowedImages))
#print(allowedImages)
