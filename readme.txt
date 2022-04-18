1

From FLEx "Texts & Words" -> "Analyze" tab, select File -> Export Interlinear... and choose "Verifiable generic XML." If you are using FLEx 7.2 or later--which is highly, highly recommended--FLEx will then let you select which texts to export; everything you select will end up in the same XML file. This step may take several minutes. FLEx will not give you any indication that it is progressing but should become responsive again when it's done.

2

Save the file and run the "interlinearized.py" however you run a Python script on your system. PYTHON 2.7 IS REQUIRED. (On Mac OS X Lion, you can the file "interlinearized-mac.sh" can be dragged into a Terminal window and hit enter.) When prompted, select the XML file you just exported. The script will probably take a minute or two to run, depending on the size of the corpus and the CPU.

3

The output of the script will be a folder with a date and time stamp. Move your LaTeX master file to this output folder (an example file is provided) and be sure to include the line:

    \input{__inputs}

4

Compile the XeLaTeX document twice to be sure the Table of Contents shows up properly. This, too, may take some time.





Other notes:

This script works for Matsigenka. To use it with other languages, there is a Python variable called 'titlelang' that will need to be changed to the three-letter code of the language in FLEx. This specificity was built in because occasionally there were titles in alternate languages (Spanish or English), and only the Matsi ones were to be used.



Script written by Greg Finley, June 2013.
