import cv2
import json
import os

main_image = cv2.imread("/usr/lib/python3.6/site-packages/kivy/data/images/defaulttheme-0.png", -1)

with open('/usr/lib/python3.6/site-packages/kivy/data/images/defaulttheme.atlas') as atlas:
	atlas = json.loads(atlas.read())
	for (filename, indices) in atlas["defaulttheme-0.png"].items():
		x_begin = indices[0]
		x_end = x_begin + indices[2]
		y_begin = 512 - indices[1]
		y_end = y_begin - indices[3]
		cv2.imwrite(os.path.join("images", filename + ".png"),
		            main_image[y_end:y_begin, x_begin:x_end])

'''
To recompile images back to an atlas file, run
$ python -m kivy.atlas/path/to/custom/atlas/file 512 /path/to/images/folder
'''