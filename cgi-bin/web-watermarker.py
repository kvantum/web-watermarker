#!/usr/bin/env python3
# This script allows optional resizing of a picture, making text and image watermarks.

import cgi
import cgitb
import html
import os
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFont
from shutil import copyfile

def resize_image(filename, width, height, outfolder):
    """
    Resizes the image to width x height box size and saves the
    image to outfolder in PNG format.
    :filename: path to the input image
    :width: desired width of output image, an integer number
    :height: desired height of output image, an integer number
    :outfolder: path to the folder for the output image saving
    """
    image = Image.open(filename)
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    image_width, image_height = image.size
    if width <= image_width and height <= image_height:
        image_width = width
        image_height = height
    elif width < image_width and height > image_height:
        image_height = (image_height * width) / image_width
        image_width = width
    elif width > image_width and height < image_height:
        image_width = (image_width * height) / image_height
        image_height = height

    layer = Image.new('RGBA', (width, height), (0,0,0,0))
    resized_image = image.resize((int(image_width), int(image_height)))
    position = (int((width - image_width)/2), int((height - image_height)/2))
    layer.paste(resized_image, position)
    new_filename = os.path.split(filename.rsplit('.')[0]+".png")[1]
    layer.save(os.path.join(outfolder, new_filename),'PNG')
    return new_filename

def text_watermark(filename, text, outfolder, angle=25, opacity=0.25):
    """
    Adds a text watermark to the image.
    :filename: path to the input image
    :text: text of a watermark
    :outfolder: path to the folder for the output image saving
    :angle: angle of the watermark text, a float number
    :opacity: watermark opacity, a float number from 0 to 1
    """
    # Font of the text watermark
    font = 'Verdana.ttf'
    # Path to the font. There is a problem of using MS fonts in Linux platforms,
    # so the path to the font should be set manually.
    font_path = "/usr/share/fonts/truetype/msttcorefonts"

    img = Image.open(filename).convert('RGBA')
    watermark = Image.new('RGBA', img.size, (0,0,0,0))
    size = 2

    if sys.platform == "linux" or sys.platform == "linux2":
        font = os.path.join(font_path, font)

    # return watermark TruTypeFont(filename, size, index, encoding)
    wm_font = ImageFont.truetype(font, size)
    # Width and height of the watermark text in pixels
    wm_width, wm_height = wm_font.getsize(text)
    while wm_width + wm_height + 10 < watermark.size[0]:
        size += 2
        wm_font = ImageFont.truetype(font, size)
        wm_width, wm_height = wm_font.getsize(text)
    draw = ImageDraw.Draw(watermark, 'RGBA')
    draw.text(((watermark.size[0] - wm_width) / 2,
              (watermark.size[1] - wm_height) / 2),
              text, font=wm_font)
    watermark = watermark.rotate(float(angle), Image.BICUBIC)
    alpha = watermark.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
    watermark.putalpha(alpha)
    Image.composite(watermark, img, watermark).save(os.path.join(outfolder, \
                    filename), 'PNG')

def image_watermark(filename, watermark, outfolder, opacity=0.25):
    """
    Adds a watermark image to the input picture.
    :filename: path to the input image
    :watermark: path to the watermark image
    :outfolder: path to the folder for the output image saving
    :opacity: watermark opacity, a float number from 0 to 1
    """
    watermark = Image.open(watermark)
    if watermark.mode != 'RGBA':
        watermark = watermark.convert('RGBA')
    alpha = watermark.split()[3]
    #reduce the brightness or the 'alpha' band
    alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
    watermark.putalpha(alpha)
    image = Image.open(filename)
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    if watermark.size[0] > image.size[0] or watermark.size[1] > image.size[1]:
        watermark = watermark.resize(image.size[0],image.size[1])
    layer = Image.new('RGBA', image.size, (0,0,0,0))
    position = (image.size[0]-watermark.size[0], image.size[1]-watermark.size[1])
    layer.paste(watermark, position)
    Image.composite(layer, image, layer).save(os.path.join(outfolder, filename),'PNG')


def main():
    cgitb.enable()

    form = cgi.FieldStorage()
    # Get image filename here.
    image = form['filename']
    width = (form.getfirst("width"))
    height = (form.getfirst("height"))
    # Get watermark image filename here.
    imagewatermark = form['watermark_image']
    text_wm = form.getlist("text_watermark")
    text_wm = " ".join(text_wm)
    angle = form.getfirst("angle")
    # There is a problem with a default parameter, i.e. default='0.3'
    opacity = form.getfirst('opacity','0.3')

    # Test if the image file was uploaded
    if image.filename:
       fn = os.path.basename(image.filename)
       open(fn, 'wb').write(image.file.read())
       message = 'The file "' + fn + '" was uploaded successfully.'
    else:
       message = 'No image file was uploaded.'

    if imagewatermark.filename:
       wm_file = os.path.basename(imagewatermark.filename)
       open(wm_file, 'wb').write(imagewatermark.file.read())
       message = 'The file "' + wm_file + '" was uploaded successfully'
    else:
       message = 'No watermark file was uploaded.'
    # Path to the project folder on the local machine.
    path = os.path.split(os.path.abspath(image.filename))[0]

    output_folder_name = 'output_folder'
    # Path to the folder with processed images.
    outfolder = os.path.join(path, output_folder_name)

    # Change directory to the input folder.
    os.chdir(path)
    # Check the image extension.
    if len(width) > 0 and len(height) > 0:
        new_filename = resize_image(os.path.abspath(image.filename), \
                                    int(width), int(height), outfolder)
    else:
        copyfile(os.path.abspath(image.filename), os.path.join(outfolder, fn))
        new_filename = fn

    # Change directory to the output folder.
    os.chdir(outfolder)
    if len(text_wm) > 0:
        if len(angle) > 0 and len(opacity) > 0:
            text_watermark(new_filename, text_wm, outfolder, float(angle), opacity)
        elif len(angle) > 0 and len(opacity) == 0:
            # Add a watermark with the default opacity
            text_watermark(new_filename, text_wm, outfolder, float(angle))
        elif len(angle) == 0 and len(opacity) > 0:
            # Add a watermark text with the 0 angle and  default opacity
            text_watermark(new_filename, text_wm, outfolder, 0, opacity)
        else:
            # Add a watermark with the default opacity
            text_watermark(new_filename, text_wm, outfolder, 0)

    if len(imagewatermark.filename) > 0:
        if len(opacity) > 0:
            image_watermark(new_filename, os.path.join(path, \
                            imagewatermark.filename), outfolder, opacity)
        else:
            # Add a watermark with the default opacity
            image_watermark(new_filename, os.path.join(path, \
                            imagewatermark.filename), outfolder)

    print("""\
    Content-Type: text/html\n
    <html>
    <body>
       <p></p>
       <p>
       Input image: </p>
       <img src="%s" alt="image"></img>
       """ % ("../"+os.path.basename(image.filename),))
    print(""" <p> Watermark image:</p>
       <img src="%s" alt="watermark"></img>
       """ % ("../"+os.path.basename(imagewatermark.filename),))
    print(""" <p> Processed image: </p>
     <img src="%s" alt="processed image"></img>
    </body>
    </html>
    """ % ("../" + output_folder_name + "/" + new_filename))

if __name__ == '__main__':
    main()
