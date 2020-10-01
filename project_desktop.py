#!/usr/bin/env python
# coding: utf-8

# Import required packages
from zipfile import ZipFile, ZipInfo
from PIL import Image, ImageDraw, ImageFont
import pytesseract
import cv2 as cv
import numpy as np
import math
import os
from pathlib import Path

# *** FUNCTIONS *** #

# Function to open each image file in a zip folder, and create a dictionary
# with a key for each filename, and a subdictionary containing the image
def extractImgs(zfn):
    # Create a zipfile object
    zfile = ZipFile(zfn)

    # Extract the zip file info into a list
    sourcelist = zfile.infolist()

    # Create a dictionary to store output
    output = {}

    # Loop over the zip files in the folder
    for source in sourcelist:
        # Filename variable for convenience
        fn = source.filename
        # Print out the file we're processing so we can keep track of progress
        print('Extracting image from {}'.format(fn))
        # Create a subdictionary for this file
        output[fn] = {}
        # Extract the image
        img = Image.open(zfile.extract(source, "temp"))
        # Add the image to the subdictionary
        output[fn]['img'] = img
    
    # Close the zip file
    zfile.close()

    # Return the dictionary
    return output

# Function to extract text from each image contained in a dictionary
def extractText(dict):
    # Loop throught the filenames in the dictionary
    for fn in dict.keys():
        # Print a message to display progress
        print('Extracting text from {}'.format(fn))
        # Convert the image to grayscale
        img_gs = dict[fn]['img'].convert('L')
        # Extract text using tesseract OCR
        text = pytesseract.image_to_string(img_gs)
        # Save text string to subdictionary
        dict[fn]['text'] = text
    # Return the dictionary
    return dict

# Function to search and save faces, if text of relevant file contains name passed to function
def searchFaces(dict, name):
    # Load the face detection classifier
    face_cascade = cv.CascadeClassifier("faceclassifier/haarcascade_frontalface_default.xml")

    for fn in dict.keys():
        # Create a list to save the extracted (cropped) face images
        facekey = 'faces-' + name
        dict[fn][facekey] = []

        # Boolean indicator whether search string was found in text
        dict[fn]['found-' + name] = False

        # If the name searched for occurs in the relevant image, we extract the faces
        if name in dict[fn]['text']:
            dict[fn]['found-' + name] = True
            # Print out the file we're processing so we can keep track of progress
            print('Searching {} for faces'.format(fn))

            # Read in the image for OpenCV
            cv_img = cv.imread("temp/" + fn)
            # Convert the image to greyscale for better face detection
            cv_img = cv.cvtColor(cv_img, cv.COLOR_BGR2GRAY)
            # Detect the faces and save the coordinates 
            faces = face_cascade.detectMultiScale(cv_img, 1.35)

            # Loop over the coordinates for all the faces detected
            img = dict[fn]['img']
            for x, y, w, h in faces:
                # Crop out the face
                cropimg = img.crop((x, y, x+w, y+h))
                # Resize the face if it's larger than the size we need
                if (cropimg.width > cropsize) or (cropimg.height > cropsize):
                    cropimg = cropimg.resize((cropsize, cropsize))
                # Add the face to the list
                dict[fn][facekey].append(cropimg)

    # Return the dictionary
    return dict

# Function to create a contact sheet for the results of the face search
# for a given zip folder
def resultsSheet(dict, name):
    # Key variable for convenience
    facekey = "faces-" + name

    # Set the mode for creating new images
    mode = "RGB"
    # Create a list for the midi size contact sheets
    midis = []

    # Loop over the keys in the subdictionary for the relevant name (i.e. the files with matches)
    for fn in dict.keys():
        if dict[fn]["found-" + name] == False:
            continue
        # Calculate the number of rows we'll need in the mini contact sheet
        rows = math.ceil(len(dict[fn][facekey])/5)
        # Create a mini contact sheet in which to paste the cropped faces
        cs_mini = Image.new(mode, (cropsize*5, rows*cropsize))
        
        # If the list for the relevant file is empty, it means no faces were detected
        if dict[fn][facekey] == []:
            # Create a midi size contact sheet with the text from the example
            cs_midi = Image.new(mode, (cs_mini.width+10, 90), (255,255,255))
            text = """Results found in file {}\n
But there were no faces in that file!""".format(fn)

            draw = ImageDraw.Draw(cs_midi)
            draw.text((5,10), text, fill = (0,0,0), font = font)
        # Else (if the list isn't empty) it means we can paste the faces into the mini contact sheet
        else:
            # Paste the faces into the mini contact sheet with the right coordinates
            x, y = 0, 0
            for img in dict[fn][facekey]:
                if x == cropsize*5:
                    x = 0
                    y = y + cropsize
                cs_mini.paste(img, (x, y))
                x = x + cropsize
            
            # Create a midi size contact sheet to paste the mini contact sheet into
            cs_midi = Image.new(mode, (cs_mini.width+10, cs_mini.height+40), (255,255,255))
            # Add the text description at the top
            text = 'Results found in file {}'.format(fn)
            draw = ImageDraw.Draw(cs_midi)
            draw.text((5,10), text, fill = (0,0,0), font = font)
            # Paste on the mini contact sheet
            cs_midi.paste(cs_mini, (5,40))
        
        # append the midi size contact sheet we just created to the list
        midis.append(cs_midi)
    # Create a variable to calculate the total height for the final contact sheet
    totalheight = 0
    # Create an empty list to store the y-coordinates where the midi size contact sheets will be pasted
    ycoords = []
    
    # Run a loop over the midi contact sheets to calculate total height and y-coordinates
    for img in midis:
        ycoords.append(totalheight)
        totalheight = totalheight + img.height
    
    # Create an empty image for the final contact sheet
    cs_maxi = Image.new(mode, (510,totalheight), (255,255,255))
    
    # Run a loop to paste the midi contact sheets onto the final contact sheet
    counter = 0
    for img in midis:
        y = ycoords[counter]
        cs_maxi.paste(img,(0,y))
        counter = counter + 1
    
    # Return the contact sheet for the relevant name
    return cs_maxi

# *** PROGRAM *** #

# Set some variables required for the functions to run
font = ImageFont.truetype('fonts/FanwoodText-Regular.ttf', 20)
cropsize = 100

# Create the required output for the images in the small zip folder,
# searching for the name "Chris"

# Extract the images
smallChris = extractImgs("input/small_img.zip")
# Extract text from the images
smallChris = extractText(smallChris)
# Search the images for faces, in files that contain the name "Chris"
smallChris = searchFaces(smallChris, 'Chris')
# Create a results sheet with the output
sheetSmallChris = resultsSheet(smallChris, "Chris")
# Show and save the results sheet
sheetSmallChris.show()
sheetSmallChris.save("output/small-Chris.png")

# Create the required output for the images in the large zip folder,
# searching for the name "Mark"

# Extract the images
largeMark = extractImgs("input/images.zip")
# Extract text from the images
largeMark = extractText(largeMark)
# Search the images for faces, in files that contain the name "Mark"
largeMark = searchFaces(largeMark, 'Mark')
# Create a results sheet with the output
sheetLargeMark = resultsSheet(largeMark, "Mark")
# Show and save the results sheet
sheetLargeMark.show()
sheetLargeMark.save("output/large-Mark.png")

# Clear the temp folder
tempPath = Path(Path.cwd(), 'temp')
for filename in tempPath.glob("*"):
    os.unlink(filename)



