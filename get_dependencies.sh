#!/usr/bin/bash
#Replace /py file path with your own
echo "Reading from file $1"
while read -r widget
do
	echo "Now finding image dependencies for $widget"
	widget_file=$(echo /usr/lib/python3.6/site-packages/kivy/uix/$widget.py)
	echo $widget >> requirements.txt
	grep "atlas://data/images/defaulttheme" $widget_file >> requirements.txt
	echo "-----" >> requirements.txt
	echo "Done finding images for $widget"
done < "$1"
