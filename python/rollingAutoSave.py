import nuke
import glob
import time
import os
import datetime
import re

def onAutoSave(filename):

  fileNo = 1
  files = getAutoSaveFiles(filename)

  if len(files) > 0 :
    lastFile = files[-1]
    # get the last file number

    if len(lastFile) > 0:
      try:
        fileNo = int(lastFile[-3:])
      except:
        pass

      fileNo = fileNo + 1

  filename = filename + str(time.strftime("__%m-%d-%Y__%I-%M-%p"))

  if ( len(files) > 50 ):
    os.remove(files[0])

  return filename


def onAutoSaveRestore(filename):

  files = getAutoSaveFiles(filename)

  if len(files) > 0:
    filename = files[-1]

  return filename, re.IGNORECASE


def onAutoSaveDelete(filename):

  return None


def getAutoSaveFiles(filename):
  date_file_list = []
  files = glob.glob(filename + '*')
  files.extend( glob.glob(filename) )

  for file in files:
      stats = os.stat(file)
      lastmod_date = time.localtime(stats[8])
      date_file_tuple = lastmod_date, file
      date_file_list.append(date_file_tuple)

  date_file_list.sort()
  return [ filename for _, filename in date_file_list ]


nuke.addAutoSaveFilter( onAutoSave )
nuke.addAutoSaveRestoreFilter( onAutoSaveRestore )
nuke.addAutoSaveDeleteFilter( onAutoSaveDelete )
