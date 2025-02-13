# importing required modules 
import PyPDF2 
import pdf2image
import numpy as np
import os
from os import listdir
import cv2
from PIL import Image
import subprocess
import pytesseract

# converts pdf to images
PDFTOPPMPATH = r"C:\Users\monamoe\Downloads\poppler-0.68.0_x86\poppler-0.68.0\bin\pdftoppm.exe"
PDFFILE = "pdf_file.pdf"
path_to_tesseract = r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
subprocess.Popen('"%s" -png "%s" out' % (PDFTOPPMPATH, PDFFILE))

# Opening the image & storing it in an image object
img = Image.open("out-1.png")

for images in os.listdir(r'..\output'):
 
    # check if the image ends with png
    if (images.endswith(".png")):
        print(images)
pytesseract.tesseract_cmd = path_to_tesseract
  
# Passing the image object to image_to_string() function
# This function will extract the text from the image
text = pytesseract.image_to_string(img)
  
# Displaying the extracted text
print(text[:-1])


