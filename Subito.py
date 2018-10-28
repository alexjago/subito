#! /usr/bin/python3

#################################################
# Rehearsal Files Generator                     #
# MIDI -> MIDI converter                        #
#################################################

import configparser
import argparse
import csv
import os.path
import os
import sys
import re
import subprocess


# First deal with the command line

argparser = argparse.ArgumentParser(description="Generate rehearsal part-files from source files. The default is MIDI to MIDI, but MuseScore input and MP3 output is also supported (if you have MuseScore installed).")
argparser.add_argument("--layout", action='store', help="choose a layout to disambiguate with")
argparser.add_argument("--version", action='version', version='0.2')
argparser.add_argument("--config", action='store', default="config.ini", help="path to the configuration file")
argparser.add_argument("--verbose", action='store_true', help="print debug messages")
argparser.add_argument("--musescore", action='store_true', help="begin by converting from .mscz format; requires MuseScore")
argparser.add_argument("--mp3", action='store_true', help="finish by rendering part-MIDIs to MP3; also requires MuseScore")
argparser.add_argument("--filter", action='store', default="*", help="filter files by name, not just extension; be sure to quote the pattern to prevent shell expansion")
argparser.add_argument("inpath", action='store', nargs='?', default='{}'.format(os.getcwd()), metavar="SOURCE", help="specify a file/directory for conversion input")
argparser.add_argument("outpath", action='store', nargs='?', default='{}'.format(os.getcwd()), metavar="DESTDIR", help="specify a directory for conversion output")

args = argparser.parse_args()


### Global settings ###
foregroundVolume = 127
backgroundVolume = 80
layoutPriority = "" # empty string here, if there's no priority defined in the file we want to prompt for it
markerText = "Generated By Subito"
verbose = args.verbose

dirmode = False # directory mode or file mode?
musescore = False

# handle arguments
if args.layout :
    layoutPriority = args.layout

# Just a little helper function
def printv(*args, **kwargs):
    if verbose:
        print(*args, **kwargs, file=sys.stderr)

printv(args)

# If the input is defined, first check it for existence
if not os.path.exists(args.inpath):
    print("Error: input path does not exist.")
    exit(1)
# We're still here, so assume the input does exist


# Now figure out if the config file is valid.
# Config file is valid if...
# all Parts are valid, and
# all Layouts are valid.

# Parts are valid if they match the regex
# ([\w]+)\s*=\s*(\d+)\s*,\s*(\d+)
# where {2} and {3} are integers between 0 and 127

# Layouts are valid if they match the regex
# (\w+)\s*=(\s*(([\w]+)(\s+[1-9]+)?)\s*,?)+
# and there is at least one {4}
# and every {4} is a valid Part Name
# and every {3} is unique

cfg = configparser.ConfigParser()

# set defaults here...

cfg.read(args.config)

printv(*cfg.sections())

# Handle config settings.
# Override defaults above, but not command-line arguments.

if "SETTINGS" in cfg:
    if "ForegroundVolume" in cfg["SETTINGS"]:
        foregroundVolume = int(cfg["SETTINGS"]["ForegroundVolume"])
    if "BackgroundVolume" in cfg["SETTINGS"]:
        backgroundVolume = int(cfg["SETTINGS"]["BackgroundVolume"])
    if ("LayoutPriority" in cfg["SETTINGS"]) and (not args.layout):
        layoutPriority = cfg["SETTINGS"]["LayoutPriority"].lower()
    if "MarkerText" in cfg["SETTINGS"]:
        markerText = cfg["SETTINGS"]["MarkerText"]

# Handle part descriptions

parts = {}

def validPartDef(partDef, prompt=False):
    '''Returns either an empty or a valid Part Definition.
       If `prompt = True` it will prompt you for a valid Definition and recurse
        to ensure that it is valid.
    '''
    try:
        pp = [int(x.strip()) for x in partDef.split(',')]
        if len(pp) != 2:
            raise RuntimeError("Expected 2 parameters, got {}.".format(len(pp)))
        for x in pp:
            if (x < 0) or (x > 127):
                 raise ValueError("Parameter outside the range 0-127.")
        return pp
    except (ValueError, TypeError, RuntimeError) as error:
        if prompt:
            print("Problem with definition `{}` of potential Part".format(partDef))
            print('(' + "\n".join(error.args) + ')')
            potentialPartDef = input("Please enter a valid Part definition: ").strip()
            return validPartDef(potentialPartDef, prompt=True)
        else:
            printv("Problem with definition `{}` of potential Part".format(partStr))
            printv("\n".join(error.args))
            return []

# end of validPartDef function definition

def validPart(partKey, partDef, prompt=False):
    '''Returns either an empty or a valid Part.
       If `prompt = True` it will prompt you for a valid Name and/or
        Definition and recurse to ensure that it is valid.
    '''

    printv('partKey: {:20}\tpartDef: {:^8}'.format(partKey, partDef))
    
    word = re.compile("^\w+")
    if word.match(partKey.strip()):
        kk = partKey.strip()
        dd = validPartDef(partDef, prompt=prompt)
        return {kk: dd}
    elif prompt:
        print("Problem with name {} of potential Part".format(partKey))
        potentialPartName = input("Please enter a valid Part name: ").strip()
        validPart(potentialPartName, partDef, prompt=True)
    else:
         printv("Problem with name {} of potential Part".format(partKey))
         return {}

# end of validPart function definition

if "PARTS" in cfg:
    # get keys

    for key in cfg["PARTS"]:
        parts = {**parts, **validPart(key, cfg["PARTS"][key])}

# Handle layout descriptions

# printv("PARTS: ", parts)

layouts = {}

def validLayoutDef(layoutDef, prompt=False):
    '''Returns either an empty or a valid Layout Definition.
       If a Part Name would be valid but is missing and `prompt = True`
        it will prompt you for a valid Definition
        and recurse to ensure that it is valid.
    '''
    lp = [p.strip().split() for p in layoutDef.split(',')]

    #printv("lp:", lp)

    if lp == [[]]:
        printv("Note: layout contains no Parts.")
        return []

    word = re.compile("^\w+")
    for p in lp:
        
        name = p[0]
        if not word.match(name):
            printv("Error: {} cannot be a valid Part name.".format(p))
            return []
        elif (not name in parts):
            if prompt:
                print("Error: Part {} not found when processing layout".format(p))
                newpart = validPart(''.join(p), '', prompt=True)
                npk = sorted(newpart.keys())[0]
                parts[npk] = newpart[npk]
                return validLayoutDef(layoutDef, prompt=True) # recurse
            else:
                return []
    else:   # loop ended normally
        return lp   # we made it



def validLayout(layoutKey, layoutDef, prompt=False):
    '''Returns either an empty or a valid Layout.
       If `prompt = True` it will prompt you for a valid Name and/or
        Definition and recurse to ensure that it is valid.
    '''
    word = re.compile("^\w+")
    if word.match(layoutKey.strip()):
        kk = layoutKey.strip()
        dd = validLayoutDef(layoutDef, prompt=prompt)
        printv("layoutKey: {}\nlayoutDef: {}".format(layoutKey, layoutDef))
        return {kk: dd}
    elif prompt:
        print("Problem with name {} of potential Layout".format(layoutKey))
        potentialLayoutName = input("Please enter a valid Layout name").strip()
        validLayout(potentialLayoutName, layoutDef, prompt=True)
    else:
         printv("Problem with name {} of potential Layout".format(layoutKey))
         return {}

def reprLayout(layout):
    ret = ""
    for i in layout:
        ret += ', '
        subret = ""
        for j in i:
            subret += str(j) + ' '
        ret += subret[:-1]
    return ret[2:]

if "LAYOUTS" in cfg:
    for layout in cfg["LAYOUTS"]:
        printv(layout, cfg["LAYOUTS"][layout].strip())
        layouts = {**layouts, **validLayout(layout, cfg["LAYOUTS"][layout].strip().lower(), parts)}

printv("Layout Priority: ", layoutPriority)

# Prompt for layout
def promptLayout(layoutPriority):
    while layoutPriority and ((layoutPriority not in layouts) or (not layouts[layoutPriority])):
    ##while layoutPriority not in layouts:
        print("'{}' is set as the layout priority, but is not defined.".format(layoutPriority))
        choice = input("Would you like to [S]et it now, view available [L]ayouts, or view available [P]arts?\n").strip().upper()
        if(choice.startswith('S')):
            if not layoutPriority:
                layoutPriority = input("Enter Layout Name: ").strip().lower()
            if (layoutPriority not in layouts) or (not layouts[layoutPriority]): # it might be that we entered a defined layout name
                potentialDef = input("Enter Layout Definition for {}: ".format(layoutPriority)).strip().lower()
                nl = validLayout(layoutPriority, potentialDef, prompt=True)
                npl = sorted(nl.keys())[0]
                layouts[npl] = nl[npl]
            else:
                print("Layout Priority set to existing layout:", layoutPriority, ':', reprLayout(layouts[layoutPriority]))
        elif(choice.startswith('L')):
            for l in layouts: print(l, ':', reprLayout(layouts[l]))
        elif(choice.startswith('P')):
            for p in parts: print(p, ':', *[t for t in parts[p]])
        #else:
        #    layoutPriority = ''
    return layoutPriority

layoutPriority = promptLayout(layoutPriority)

printv("PARTS: ", parts)
printv("LAYOUTS: ", layouts)

# the meat of the script

out_midis = [] # just a list of paths

def mainboi(infile, outdir, layoutPriority):
    '''The meat of this script. Converts a single file.'''

    # Step one: figure out what/where

    name = os.path.splitext(os.path.basename(infile))[0]
    score_midi = os.path.join(outdir, name + os.path.extsep + 'mid')

    printv("name: `{}`".format(name), "score_midi: `{}`".format(score_midi))

    

    if musescore:
        subprocess.run(["mscore",
                        "-o", score_midi,
                        infile], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        subprocess.run(["cp",
                        infile,
                        score_midi])

    # now we use csvmidi

    csv = subprocess.run(["midicsv", score_midi],
                          stdout=subprocess.PIPE).stdout.decode('ascii').split('\n')

    #printv("*** CSV OUTPUT ***")
    #printv(csv)

    # now we do a bunch of string processing


    ###########################################################
    # first step is to build a set of instrumentation candidates

    
    #instr = re.compile("(\d+), [\d]+, ")

    patches = {}

    for i in range(len(csv)):
        lsp = csv[i].split(', ')
        #printv(lsp)
        if len(lsp)==5 and lsp[2] == "Program_c":
            # this line has a synth set
            tracknum = int(lsp[0])
            patches[tracknum] = int(lsp[-1])
            printv(lsp)

        # neutralise volumes
        if len(lsp)>5 and lsp[2] == "Control_c" and lsp[4] == '7':
            lsp[5] = str(backgroundVolume)
            printv(lsp)

        if len(lsp)==4 and lsp[2] == "Text_t" and lsp[3] == markerText:
            printv("File already processed!")
            # this file has already been processed!
            return

        csv[i] = ', '.join(lsp)
        
    printv("Patches: ", patches)
    
    candidates = []
    chosen_layout = ''
    
    for layout in layouts:
        if len(layouts[layout]) == len(patches):
            for i in range(len(layouts[layout])):
                    partname = layouts[layout][i][0]
                    if parts[partname][0] != patches[i+1]:
                        break
            else:
                candidates.append(layout)


    printv("Candidates: ", candidates)

    if len(candidates) > 1:
        if layoutPriority in candidates:
            chosen_layout = layoutPriority
        else:
            print("Please select a layout for "+name+" or else describe a new one.")
            optstr = ' '.join(["[{}]: {},".format(i+1, candidates[i]) for i in range(len(candidates))])
            opt = input(optstr + ' [N]ew layout: ').upper().strip()

            if opt.startswith('N'):
                layoutPriority = input("Enter Layout Name: ").strip().lower()
                potentialDef = input("Enter Layout Definition for {}: ".format(layoutPriority)).strip().lower()
                nl = validLayout(layoutPriority, potentialDef, prompt=True)
                npl = sorted(nl.keys())[0]
                layouts[npl] = nl[npl]
                chosen_layout = npl
            elif opt.strip().isdigit():
                chosen_layout = candidates[int(opt)]
            else:
                print("Selecting option [1]")
                chosen_layout = candidates[0]
                
    elif len(candidates) == 1:
        chosen_layout = candidates[0]
    else:
        print("Error: no candidate layouts for {}.".format(infile))
        layoutPriority = input("Enter a new Layout Name: ").strip().lower()
        potentialDef = input("Enter Layout Definition for {}: ".format(layoutPriority)).strip().lower()
        nl = validLayout(layoutPriority, potentialDef, prompt=True)
        npl = sorted(nl.keys())[0]
        layouts[npl] = nl[npl]
        chosen_layout = layoutPriority
            
    
    #########################################################################
    # We have a layout now, in `chosen_layout`

    printv(chosen_layout)

    # now for the real fun... iterating over everything
    
    

    for p in layouts[chosen_layout]:
        partname = p[0]
        partid = 0
        for i in range(len(layouts[chosen_layout])):
            if partname == layouts[chosen_layout][i][0]:
                partid = i+1

        printv(partname, partid)
        number = ''
        if len(p) > 1:
            number = p[1]
        partlabel = ''.join(p)
        filename = os.path.join(outdir, name + "_" + partlabel + os.path.extsep + 'mid')

        this_csv = csv.copy()

        this_csv = ["0, 0, Text_t, "+markerText] + this_csv

        for i in range(len(this_csv)):
            lsp = this_csv[i].split(', ')
            # foreground volumes
            #if "Control_c" in this_csv[i]:
            #    printv(lsp)
            if (len(lsp)==6) and lsp[0] == str(partid) and lsp[2] == "Control_c" and lsp[4] == '7':
                lsp[5] = str(foregroundVolume)
                printv(lsp)

            # instrument swapsies
            if (len(lsp)==5) and lsp[0] == str(partid) and lsp[2] == "Program_c" and lsp[4] == str(parts[partname][0]):
                lsp[4] = str(parts[partname][1])
                printv(lsp)
                
            this_csv[i] = ', '.join(lsp)            

        subprocess.run(['csvmidi', '-', filename],
                       input='\n'.join(this_csv).encode())

        if args.mp3:
            mp3_name = filename[0:-3] + "mp3"
            subprocess.run(['mscore',
                            '-o', mp3_name,
                            filename],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    


### OK, now we should have some valid layouts and valid parts
### Our next step is to figure out what we're being run on

# already demonstrated that input path exists. But what is it?

if args.musescore or os.path.splitext(args.inpath)[1].lower() == ".mscz":
    musescore = True

if not os.path.isdir(args.outpath):
    os.mkdir(args.outpath) # go ahead and make the output directory if it doesn't already exist

if os.path.isdir(args.inpath):
    dirmode = True # we shall need to iterate over everything in a directory
    # find all the things
    sourcetype = ".mid"
    if musescore:
        sourcetype = ".mscz"
        
    sources = subprocess.run(["find", args.inpath, "-type", "f", "-name", args.filter+sourcetype],
                       stdout=subprocess.PIPE,
                       universal_newlines=True)\
        .stdout.strip().split(sep="\n")

    for s in sources:

        # we should respect the subdirectory structure if there is one

        subdir = os.path.join(args.outpath, os.path.dirname(os.path.relpath(s, args.inpath)))
        printv(subdir)
        if not os.path.isdir(subdir):
            os.mkdir(subdir)
        
        mainboi(s, subdir, layoutPriority)
else:
    mainboi(args.inpath, args.outpath, layoutPriority)
    

    

    