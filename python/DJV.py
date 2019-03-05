# DJV.py version 2.3
# N Carroll 2014-08-14 fixed disk cache value

import os.path
import re
import nuke
import subprocess
from nukescripts import flipbooking

class DJVFlipbook(flipbooking.FlipbookApplication):

  def __init__(self):
    self._djvPath = os.environ["DJV_VIEW_EXECUTABLE"]

  def name(self):
    return "DJV"

  def path(self):
    return self._djvPath

  def cacheDir(self):
    return nuke.value("preferences.DiskCachePath")

  def convertPadding(self, filename):
    pattern = re.compile("%([0-9]*)d")
    match = re.search(pattern, filename)
    if match:
      return re.sub(pattern, '#'*int(match.group(1)), filename)
    else:
      return filename

  def run(self, imagePath, frameRanges, views, options):
    args = []
    args.append( self.path() )
    imageFile = os.path.basename(imagePath)
    imageFile = self.convertPadding(imageFile)
    imageFile = imageFile[::-1]
    pattern = re.compile("\.###+") 
    match = re.search(pattern, imageFile)
    if match:
      imageSeqLength = match.end() - match.start() - 1
      imageSeq = str(frameRanges.minFrame()).zfill(imageSeqLength) + '-' + str(frameRanges.maxFrame()).zfill(imageSeqLength) + '.'
      imageSeq = imageSeq[::-1]
      imageFile = re.sub(pattern, imageSeq, imageFile)
    imageFile = imageFile[::-1]
    imagePath = os.path.join(os.path.dirname(imagePath), imageFile)
    args.append(imagePath)
    subprocess.Popen( args )

  def capabilities(self):
    return { 
      'proxyScale': True,
      'crop': False,
      'canPreLaunch': False, 
      'supportsArbitraryChannels': False, 
      'maximumViews' : 1,
      'fileTypes' : ['cin', 'dpx', 'iff', 'mov','avi','mp4', 'z', 'ifl', 'jpeg', 'jpg', 'JPG', 'jfif', 'lut', '1dl', 'exr', 'pic', 'png', 'PNG','ppm', 'pnm', 'pgm', 'pbm', 'rla', 'rpf', 'sgi', 'rgb', 'rgba', 'bw', 'tiff', 'tif']
    }
  
flipbooking.register( DJVFlipbook() )



