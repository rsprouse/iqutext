# Script for converting interlinearized FLEx texts into LaTeX
# Greg Finley, March 2013

import sys, os, shutil
import xml.etree.ElementTree as ET
import datetime
import string
import tkinter
from tkinter import filedialog

encoding = 'utf-8'

class Application(tkinter.Frame):

    def createWidgets(self):
        self.msg = tkinter.Message(self)
        self.msg["text"] = """
Give me an XML file of interlinearized text output from FLEx and I'll do the rest.
        """
        self.msg.pack()

        self.go = tkinter.Button(self)
        self.go["text"] = "Begin!"
        self.go["command"] = self.letsgo
        self.go.pack()

        self.morph = tkinter.Checkbutton(self)
        self.morphbox = tkinter.IntVar()
        self.morph["variable"] = self.morphbox
        self.morph["text"] = "4-line output?"
        self.morph.select()
        self.morph.pack()

    def letsgo(self):
        self.makedic=True
        self.quit()

    def __init__(self, master=None):
        tkinter.Frame.__init__(self, master)
        self.pack()
        self.master.title("FLEx-TeX")
        self.createWidgets()
        self.makedic = False

app = Application()
app.mainloop()
if not app.makedic: os._exit(0)

xmlfilemsg = "XML file from FLEx?"
xmlfile = filedialog.askopenfilename(title = xmlfilemsg)

if not xmlfile: os._exit(0)

fourline = app.morphbox.get()       # Are we doing a 4-line interlinearization?

app.master.destroy()

# ~~~~~~~~~
# Functions
# ~~~~~~~~~

# To strip whitespace, using periods for spaces in morpheme glosses

def killspace(line) :
    if line == None: line = ""
    line = line.replace("\r",'')
    line = line.replace("\n",'')
    line = line.replace(' ','.')
    line = line.replace("\t",'')
    return line

# Also for morpheme glosses: replace caps with LaTeX small caps

def toSmallCaps(word):
    newword = ''
    incaps = False          # Are we in a \textsc{} environment already?
    for char in word:
        if char in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            if not incaps:
                newword += r'\textsc{'
                incaps = True
            newword += char.lower()
        else:
            if incaps:
                incaps = False
                newword += '}'
            newword += char
    if incaps: newword += '}'
    return newword

# Encloses a (translation) line in single quotes

def enclose_single(x):
    if not len(x): return x
#   if x[0] != "\xe2\x80\x98":
#    return "\xe2\x80\x98" + x + "\xe2\x80\x99"
    return f"`{x}'"

# ~~~~~~~~~~~~~~
# Variable setup
# ~~~~~~~~~~~~~~

now = datetime.datetime.now()
thispath = os.path.dirname(sys.argv[0])
if len(sys.argv) > 1:
    xmlargument = sys.argv[1]
title = ""
masterfilename = "__inputs.tex"

# THIS will have to be changed to reflect the language used!
# It is set up now for Matsigenka.
titlelang = 'iqu'

# Get rid of characters disliked by Windows...
badwin = r':"%/<>^|\?*'
# ...and LaTeX.
badtex = "()# "
illegalchars = badwin + badtex

# Also: characters that are bad for the text title in LaTeX
badtitle = "_#"

def hash_escape(s):
    '''Escape hash character.'''
    return s.replace('#', r'\#')

# ~~~~~~~~~~~~~~~
# File operations
# ~~~~~~~~~~~~~~~

newpath = str(now.year) + "-" + str(now.month).zfill(2) + "-" + str(now.day).zfill(2) + "_" + str(now.hour).zfill(2) + str(now.minute).zfill(2)
newpath = os.path.join(thispath,newpath)
defaultpath = os.path.join(thispath,"default")

if not os.path.exists(newpath):
    os.makedirs(newpath)

masterfile = open(os.path.join(newpath, masterfilename),'w', encoding=encoding)
masterfile.write("\\newcommand{\\texttitle}[1]{\chapter{#1}\setcounter{equation}{0}}\n")

# Get the XML. This is where most of the processing happens.

try:
    tree = ET.parse(xmlfile)
except:
    print("No XML file found. Exiting.")
    os._exit(0)
root = tree.getroot()

# ~~~~~~~~~~~~~~~~~~~~
# Go through each text
# ~~~~~~~~~~~~~~~~~~~~

for text in root.findall('interlinear-text'):

    # Get the title and format it into three different versions

    for titleitem in text.findall('item'):
        if 'type' in titleitem.attrib and titleitem.attrib['type'] == 'title':
            #rawtitle = titleitem.text.encode('utf-8')
            rawtitle = titleitem.text
            # Only break once we've gotten the title in the language we want
            if 'lang' in titleitem.attrib and titleitem.attrib['lang'] == titlelang:
                break

    title = rawtitle        # title to use for filenames and \include{}
    for char in illegalchars:
        try:
            title = title.replace(char,"_")
        except:
            print(char)
            print(f'type(char) {type(char)}')
            print(f'type(title) {type(title)}')
    textitle = rawtitle     # title to use for heading in LaTeX file
    for char in badtitle:
        try:
            textitle = textitle.replace(char,'')
        except:
            print(f'type(title) {type(title)}')
    #titleascii = title.decode(encoding)
    titleascii = title

    nextfilepath = os.path.join(newpath, titleascii + ".tex")
    while os.path.exists(nextfilepath):
        titleascii = title + "2"     # There's a better way to do this
        nextfilepath = os.path.join(newpath, titleascii + ".tex")

    # Open up a new output file for each text
    outfile = open(nextfilepath,'w', encoding=encoding)
    outfile.write("\\texttitle{" + textitle + "}\n")
    masterfile.write("\\input{" + title + "}\n")

    # Go through each "paragraph" and print the 4-line interlinearization for each

    for paragraph in text.iter('paragraph'):

        fullline = ''       # first line of text
        linemorphs = []     # contains all morphemes in a given paragraph/line
        linecfs = []        # contains all cfs in a given paragraph/line
        lineglosses = []    # contains all glosses in a given paragraph/line
        translation = ''    # free translation for each line

#       This is how it used to work. Then FLEx started putting 'word' under each 'phrases' XML tag for some reason.
#        phrases = paragraph.iter('phrase')
        
#       This is how it works now. Goes into <phrases> and then finds all the <word> tags (which used to be <phrase>) immediately under that.
        phrasesblock = paragraph.find('phrases')
        if not phrasesblock == None:
            phrases = phrasesblock.findall('word') + phrasesblock.findall('phrase')

        for phrase in phrases:

            # String together all the words for the first line

            words = phrase.iter('word')

            for word in words:
                for item in word:
                    if item.tag == "item" and 'type' in item.attrib:

                        # Encode the word to add to the string.
                        # Add a leading space if it's not punctuation.

                        if item.attrib['type'] == 'txt' or item.attrib['type'] == 'cf':
                            txt = " " + item.text #.encode('utf-8')
                            fullline += txt
                        if item.attrib['type'] == 'punct':
                            txt = item.text or '' #.encode('utf-8')
                            if item.text is None:
                                sys.stderr.write('Empty punctuation found\n')
                                ET.dump(item)
                            if txt == "\\": txt = ''    # Kill weird backslashes
                            fullline += txt

            # Post-processing:
            # Punctuation that should not behave like other punctuation:
            leftsidepunc = ["`", "\xe2\x80\x98", "(", "[", "{", "\xe2\x80\x9c"]
            for punc in leftsidepunc:
                fullline = fullline.replace(punc + " ", " " + punc)
            nospacepunc = ["-", "\xe2\x80\x94", "\xe2\x80\x93"]
            for punc in nospacepunc:
                fullline = fullline.replace(punc + " ", punc)
            # Remove leading space (necessary?)
            if fullline[0] == ' ': fullline = fullline[1:]

            # Go through morphemes for second and third lines

            for morphword in paragraph.iter('morphemes'):
                for morpheme in morphword.iter('morph'):
                    txt = ""    # text for each morpheme
                    cf = ""     # cf for each morpheme
                    gls = ""    # gloss for each morpheme
                    for item in morpheme.iter('item'):
                        if 'type' in item.attrib:
                            if item.attrib['type'] == 'txt':
                                txt = killspace(item.text) #.encode("utf-8")
                                # TODO: escape badtex chars here, e.g. #
                            if item.attrib['type'] == 'cf':
                                cf = killspace(item.text) #.encode("utf-8")
                            if item.attrib['type'] == 'gls':
                                gls = killspace(item.text) #.encode("utf-8")
                                gls = toSmallCaps(gls)
    
                    # Add a hyphen to the beginning or end of a gloss morpheme if the corresponding text has it.
                    if len(txt) and len(gls):
                        if txt[0] == '-' and gls[0] != '-':
                            gls = '-' + gls
                        if txt[-1] == '-' and gls[-1] != '-':
                            gls = gls + '-'
    
                    linemorphs.append(txt)
                    linecfs.append(cf)
                    lineglosses.append(gls)
                linemorphs.append(' ')
                linecfs.append(' ')
                lineglosses.append(' ')

                # Get free translation (held within <phrase>) for the last line

                for item in phrase:
                    if item.tag == 'item' and 'type' in item.attrib and item.attrib['type'] == 'gls':
                        translation = item.text
                        if translation == None: translation = ""
                        translation = translation #.encode("utf-8")
                        # Enclose in single quotes:
                        translation = enclose_single(translation)
                        break

        label = title       # This may end up being something different

        outfile.write("\\begin{exe}\n")
        outfile.write("\\label{ex:" + label + "} \\ex\n")
        if fourline:
            outfile.write("\\glll \n")
        outfile.write(hash_escape(fullline) + r"\\" + "\n")
        if fourline:
            for morph in linemorphs:
                outfile.write(hash_escape(morph))
            outfile.write(r'\\' + "\n")
            for cf in linecfs:
                outfile.write(hash_escape(cf))
            outfile.write(r'\\' + "\n")
            for gls in lineglosses:
                if gls == '':
                    gls = "{}"
                #outfile.write(gls+" ")
                outfile.write(hash_escape(gls))
            outfile.write(r'\\' + "\n")
        outfile.write("\\glt " + hash_escape(translation) + "\n")
        outfile.write("\\glend\n\\end{exe}\n\n")

    outfile.close()

masterfile.close()
