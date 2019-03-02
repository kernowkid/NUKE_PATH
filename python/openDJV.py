### open read file in djv
import nuke
import subprocess
import os
import os.path


def openReadInDJV():

	### create list of all nuke Write nodes a
	nodes = [n for n in nuke.selectedNodes() if n.Class() == 'Read']

	### if nodes list is not empty
	if nodes != []:

		for r in nodes:
			##get the path and directory
		
			##get and set path
			path = r['file'].value()
			##get and set directory
			spl = path.split('/')[:-1]
			dir = '/'.join(spl)
	  

		##getting framerange from the directory
		if path:
			imgDir = os.path.dirname(path)
			if os.path.exists(imgDir):
				imgFiles = os.listdir(imgDir)
				sortList = sorted(imgFiles)
				firstFile = sortList[0]
				lastFile = sortList[-1]
				imgPath = dir + '/' + firstFile
				print imgPath

					
				subprocess.call('C:/Program Files/DJV-1.2.5-win64/bin/djv_view.exe %s' % imgPath)