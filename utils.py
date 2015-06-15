import json, os,time

def loadJson(path):
    if os.path.isfile(path)==False: raise FileNotFoundError( 'Missing file at: '+os.getcwd()+'\\'+path)
    f = open(path,mode='r')
    output = json.JSONDecoder().decode(f.read())
    f.close()
    return json.load(open(path,mode='r'))

class Utils:
    def __init__(self):
        self.fnames, self.lnames = loadJson('data\\first_names.json'), loadJson('data\\last_names.json')
        self.lenFirst, self.lenLast = len(self.fnames), len(self.lnames)
       