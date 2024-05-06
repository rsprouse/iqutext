# Script for converting interlinearized FLEx texts into LaTeX
# Greg Finley, March 2013

import sys, os, shutil, re
import xml.etree.ElementTree as ET
import datetime
import string
import tkinter
from tkinter import filedialog

encoding = 'utf-8'

# Note that upper/lower bar-i do not have precomposed acute forms.
vchars = 'àÀáÁaAèÈéÉeEìÌíÍiIƗɨòÒóÓoOùÙúÚuU'
vchars_not_i = 'àÀáÁaAèÈéÉeEƗɨòÒóÓoOùÙúÚuU'
cchars = 'bBcCdDfFgGhHjJkKlLmMnNpPqQrRsStTvVwWxXyYzZ'

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
    for idx, char in enumerate(word):
        try:
            # Don't convert first letter of capitalized words to small caps, e.g. Iquitos
            canlower = not word[idx+1] in 'abcdefghijklmnopqrstuvwxyz'
        except IndexError:
            canlower = True
        if canlower and char in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            if not incaps:
                newword += r'\D{'
                incaps = True
            newword += char.lower()
        elif char == '.':
            newword += char
        else:
            if incaps:
                incaps = False
                newword += '}'
            newword += char
    if incaps: newword += '}'
    return newword

# Encloses a (translation) line in single quotes

def enclose_single(x):
    # For future reference, double left/right quotes: “ , ”
    return f"‘{x}’" if len(x) and not x.startswith("‘") else x
#   if x[0] != "\xe2\x80\x98":
#    return "\xe2\x80\x98" + x + "\xe2\x80\x99"

def hash_escape(s):
    '''Escape hash character.'''
    return s.replace('#', r'\#')

def clean_firstline(w, community=False):
    '''
    Process text for first interlinear line.
    '''
    if re.match(r'^\s*\d+\s*$', w) and community is False:
        return ' {}'
    w = re.sub(r'\d', '', w)
    if community is False:
        w = w.replace('=', '')
    return w

def replace_tones(w):
    '''
    Replace H|L with latex replacements.
    '''
    return re.sub('(HH|LL|HL|H|L)', r'\\super{\1}', w)

def replace_nums(w):
    '''
    Replace numerals with latex replacements.
    '''
    mapdict = {
        '0': r'\super{HL}Ø',
        '1': r'Ø',
        '2': r'\super{HLL}Ø',
        '3': r'\super{H}Ø\super{LL}',
        '4': r'\super{H}Ø\super{LL}',
        '5': r'Ø',
        '6': r'\super{H}Ø\super{LL}',
        '7': r'Ø',
        '8': r'\super{H}Ø\super{LL}'
    }
    return w.translate(str.maketrans(mapdict))

def replace_spellings(w):
    '''
    Do spelling replacements.
    '''
    w = re.sub(rf'(k|K)w([{vchars}])', r'\1\ʷ\2', w)
    w = re.sub(r'[nN](ì|Ì|í|Í|i|I)(à|À|á|Á|a|A)', r'ɲ\2', w)

    # These must be ordered.
    w = re.sub(r'[sS]([ìÌíÍiI])([àÀáÁaAùÙúÚuU])', r'ʃ\1\2', w)
    w = re.sub(r'[sS]([ìÌíÍiI])', r'ʃ\1', w)
    w = w.translate(str.maketrans({'j': 'h', 'J': 'H'}))
    w = w.translate(str.maketrans({'y': 'j', 'Y': 'J'}))
    w = re.sub(rf'([{cchars}])i([{vchars_not_i}])', r'\1\ʲ\2', w)
    return w

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

# ~~~~~~~~~~~~~~~
# File operations
# ~~~~~~~~~~~~~~~

newpath = str(now.year) + "-" + str(now.month).zfill(2) + "-" + str(now.day).zfill(2) + "_" + str(now.hour).zfill(2) + str(now.minute).zfill(2)
newpath = os.path.join(thispath,newpath)
newcommpath = os.path.join(newpath, 'community')
defaultpath = os.path.join(thispath,"default")

if not os.path.exists(newpath):
    os.makedirs(newpath)
if not os.path.exists(newcommpath):
    os.makedirs(newcommpath)

masterfile = open(os.path.join(newpath, masterfilename),'w', encoding=encoding)
#masterfile.write("\\newcommand{\\texttitle}[1]{\chapter{#1}\setcounter{equation}{0}}\n")

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
    nextcommfilepath = os.path.join(newcommpath, titleascii + ".tex")
    while os.path.exists(nextcommfilepath):
        titleascii = title + "2"     # There's a better way to do this
        nextcommfilepath = os.path.join(newcommpath, titleascii + ".tex")

    # Open up a new output file for each text
    outfile = open(nextfilepath,'w', encoding=encoding)
    outcommfile = open(nextcommfilepath,'w', encoding=encoding)
    #outfile.write("\\texttitle{" + textitle + "}\n")
    #outcommfile.write("\\texttitle{" + textitle + "}\n")
    masterfile.write("\\input{" + title + "}\n")

    # Go through each "paragraph" and print the 4-line interlinearization for each

    for paragraph in text.iter('paragraph'):

        fullline = ''       # first line of text
        commfullline = ''   # first line of text, community text output
        linemorphs = []     # contains all morphemes in a given paragraph/line
        linecfs = []        # contains all cfs in a given paragraph/line
        lineglosses = []    # contains all glosses in a given paragraph/line
        translation = ''    # English free translation for each line
        sptranslation = ''    # Spanish free translation for each line

#       This is how it used to work. Then FLEx started putting 'word' under each 'phrases' XML tag for some reason.
#        phrases = paragraph.iter('phrase')
        
#       This is how it works now. Goes into <phrases> and then finds all the <word> tags (which used to be <phrase>) immediately under that.
        phrasesblock = paragraph.find('phrases')
        if not phrasesblock == None:
            phrases = phrasesblock.findall('word') + phrasesblock.findall('phrase')

        for phrase in phrases:

            # String together all the words for the first line

            words = phrase.iter('word')

            in_single_quote = False
            in_double_quote = False
            for widx, word in enumerate(words):
                for item in word:
                    if item.tag == "item" and 'type' in item.attrib:

                        # Encode the word to add to the string.
                        # Add a leading space if it's not punctuation.

                        if item.attrib['type'] == 'txt' or item.attrib['type'] == 'cf':
                            if in_single_quote or in_double_quote:
                                txt = item.text #.encode('utf-8')
                            else:
                                txt = " " + item.text #.encode('utf-8')
                            fullline += clean_firstline(txt)
                            commfullline += clean_firstline(txt, community=True)
                        if item.attrib['type'] == 'punct':
                            if item.text in ("'", '"'):
                                txt = f' {item.text}'
                                if item.text == "'":
                                    in_single_quote = not in_single_quote
                                if item.text == '"':
                                    in_double_quote = not in_double_quote
                            else:
                                txt = item.text or '' #.encode('utf-8')
                            if item.text is None:
                                sys.stderr.write('Empty punctuation found\n')
                                ET.dump(item)
                            if txt == "\\": txt = ''    # Kill weird backslashes
                            fullline += clean_firstline(txt)
                            commfullline += clean_firstline(txt, community=True)

            # Post-processing:
            # Punctuation that should not behave like other punctuation:
            leftsidepunc = ["“", "``", "`", "«", "\xe2\x80\x98", "(", "[", "{", "\xe2\x80\x9c"]
            for punc in leftsidepunc:
                fullline = fullline.replace(punc + " ", " " + punc)
                commfullline = commfullline.replace(punc + " ", " " + punc)
            nospacepunc = ["-", "\xe2\x80\x94", "\xe2\x80\x93"]
            for punc in nospacepunc:
                fullline = fullline.replace(punc + " ", punc)
            # Add space before emdash
            commfullline = commfullline.replace('—', ' —')
            # Remove leading space (necessary?)
            if fullline[0] == ' ': fullline = fullline[1:]
            fullline = replace_spellings(fullline)
            if commfullline[0] == ' ': commfullline = commfullline[1:]

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
                                cf = replace_tones(cf)
                                cf = replace_spellings(cf)
                                cf = replace_nums(cf)
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
                    if item.tag == 'item' and 'type' in item.attrib and item.attrib['type'] == 'gls' and item.attrib['lang'] == 'en':
                        translation = item.text
                        if translation == None: translation = ""
                        break
                for item in phrase:
                    if item.tag == 'item' and 'type' in item.attrib and item.attrib['type'] == 'gls' and item.attrib['lang'] == 'es':
                        sptranslation = item.text
                        if sptranslation == None: sptranslation = ""
                        break

        outfile.write("\\begin{exe}\n")
        if fourline:
            outfile.write("\\glll \n")
        outfile.write(hash_escape(fullline) + r"\\" + "\n")
        if fourline:
#            for morph in linemorphs:
#                outfile.write(hash_escape(morph))
#            outfile.write(r'\\' + "\n")
            for cf in linecfs:
                outfile.write(hash_escape(cf))
            outfile.write(r'\\' + "\n")
            for gls in lineglosses:
                if gls == '':
                    gls = "{}"
                #outfile.write(gls+" ")
                outfile.write(hash_escape(gls))
            outfile.write(r'\\' + "\n")
        outfile.write("\\glt " + hash_escape(enclose_single(translation)) + "\n")
        outfile.write("\\glts " + hash_escape(enclose_single(sptranslation)) + "\n")
        outfile.write("\\glend\n\\end{exe}\n\n")

        # Community texts
        outcommfile.write("\\begin{exe}\n")
        outcommfile.write("\\iqu{" + hash_escape(commfullline) + r"}\\" + "\n")
#        for cf in linecfs:
#            outcommfile.write(hash_escape(cf))
#        outcommfile.write(r'\\' + "\n")
#        for gls in lineglosses:
#            if gls == '':
#                gls = "{}"
#            #outcommfile.write(gls+" ")
#            outcommfile.write(hash_escape(gls))
        outcommfile.write("\\spq{" + hash_escape(sptranslation) + r"}\\" + "\n")
        outcommfile.write("\\eng{" + hash_escape(translation) + "}\n")
        outcommfile.write("\\end{exe}\n\\vspace{-0.20in}\n")

    outfile.close()
    outcommfile.close()

masterfile.close()
