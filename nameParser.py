import re, os
from utils import Utils

util = Utils()

class NameParser:
    def Scan(data,byLongest=True,allResults=False,anySequence=False):
        """Returns a dict of {'last_names':<list of strings>,'first_names':<list of strings>}
        :type data: string or list of strings
        :param byLongest: returns longest matches. Alternative is by Popularity: the most common names, as defined in the values of the JSON database (lower rank is more common).
        :param allResults: Limits best guesses from both categories, for each string if supplied a list.
        :param anySequence: =False discards all invalid orders of name types (eg. first,last,first). Use =True with allResults=True to get all possible names.
        """
        results = {'last_names':[],'first_names':[]}
        if type(data) is str: return _scanDatum(data,byLongest=byLongest,allResults=allResults,anySequence=anySequence)
        elif type(data) is list:
            for item in data:
                result = _scanDatum(item,byLongest=byLongest,allResults=allResults,anySequence=anySequence)
                results['last_names'] += result['last_names']
                results['first_names'] += result['first_names'] 
            return results
        else: raise TypeError("Scan() data needs to be a list or a string. Input type was "+str(type(data))) 

class _NameMatch:
    '''A string match with the name database'''
    def __init__(self,_isLname,_value,_popularity,_endIndex):
        assert(type(_popularity) is int)
        self.isLname, self.value, self.popularity, self.endIndex = _isLname, _value, _popularity, _endIndex
    @property
    def normalisedPopularity(self):
        if self.isLname: return (util.lenLast - self.popularity) /util.lenLast
        else: return (util.lenFirst - self.popularity) / util.lenFirst
    
class _NameMatchesGroup: #add variety checks and illegal order
    '''Multiple name matches derived from the same string'''
    def __init__(self, nameList,searchedLenString):
        self.searchedStringLength, self.names = searchedLenString, []
        self.addMatchesList(nameList)
        
    def addMatchesList(self,nameList):
        if type(nameList) is not list : raise TypeError("type is "+str(type(nameList)))
        for name in nameList: 
            if type(name) is not _NameMatch: raise TypeError("type is "+str(type(name)))
            self.names.append(name)
            
    def toDictionary(self): 
        dictionary = {'last_names':[],'first_names':[]}
        for name in self.names:
            if name.isLname: dictionary['last_names'].append(name.value)
            else: dictionary['first_names'].append(name.value)
        return dictionary
    
    ''' returns a _NameMatchesGroup
    Checks for [F,L,F] or [L,F,L] sequences in this nameGroup and takes the better group. '''
    def validatedOrder(self,popularityMode=False,longestMode=False):
        assert(popularityMode != longestMode) # pick a mode !
        prevWasFirst,firstExists,lastExists,splitSequencesMode = None, False, False,False        
        sequencesDB = _NameGroupsDatabase(self.searchedStringLength)
        currentSequence, previousSequence = _NameMatchesGroup([],self.searchedStringLength), _NameMatchesGroup([],self.searchedStringLength)
        currentUniformStreak = []
        firstStreak = []
        for i,name in enumerate(self.names):            
            if name.isLname:
                if prevWasFirst == True:
                    if lastExists: prevWasFirst,firstExists,splitSequencesMode= False,False,True  # invalid currentSequence [L,F,L] , splitSequencesMode
                    elif previousSequence.isEmpty: 
                        prevWasFirst = False
                        firstStreak = list(currentUniformStreak)
                        currentUniformStreak = []
                else:
                    currentUniformStreak.append(name)
                    prevWasFirst,lastExists = False,True
                    currentSequence.addMatchesList([name])
            else: #first name
                if prevWasFirst == False: 
                    if firstExists: prevWasFirst,lastExists,splitSequencesMode = True,False,True   # invalid currentSequence [F,L,F] , splitSequencesMode                     
                    elif previousSequence.isEmpty: 
                        prevWasFirst = True
                        firstStreak = list(currentUniformStreak)
                        currentUniformStreak = []
                else:
                    currentUniformStreak.append(name)
                    prevWasFirst,firstExists = True,True
                    currentSequence.addMatchesList([name])
            if splitSequencesMode:
                if previousSequence.isEmpty==False: #previous sequence needs the rest of current streak
                    previousSequence.addMatchesList(currentUniformStreak)
                    sequencesDB.addValue(previousSequence)
                else: sequencesDB.addValue( _NameMatchesGroup(firstStreak+currentUniformStreak,self.searchedStringLength) )
                if i == len(self.names)-1: #save current as well 
                    currentSequence.addMatchesList(currentUniformStreak)
                    sequencesDB.addValue(currentSequence)
                else:
                    previousSequence = _NameMatchesGroup(currentSequence.names,self.searchedStringLength) 
                    currentSequence = _NameMatchesGroup([name],self.searchedStringLength)
                currentUniformStreak = []
                splitSequencesMode = False        
        #process results                
        if len(sequencesDB.groups) > 1:
             if popularityMode: return sequencesDB.getPopularGuess()
             if longestMode: return sequencesDB.getLongestWords()
        else: return self #is valid
    
    @property
    def isEmpty(self): return True if len(self.names)==0 else False
    @property
    def lastnames(self): return [name for name in self.names if name.isLname == True]
    @property
    def firstnames(self): return [name for name in self.names if name.isLname == False]
    @property
    def longestLastAndFirst(self):
        fn, ln = self.firstnames, self.lastnames
        if len(fn)==0:
            if len(ln)==0:      return _NameMatchesGroup([],self.searchedStringLength)
            else:               return _NameMatchesGroup([max(ln, key=lambda x: len(x.value))],self.searchedStringLength) 
        if len(ln)==0:          return _NameMatchesGroup([max(fn, key=lambda x: len(x.value))],self.searchedStringLength)
        else:                   return _NameMatchesGroup([max(ln, key=lambda x: len(x.value)),
                                                         max(fn, key=lambda x: len(x.value))],self.searchedStringLength)    
    @property
    def mostPopularLastAndFirst(self): #doesn't handle empty lists well 
        fn, ln = self.firstnames, self.lastnames
        if len(fn)==0:
            if len(ln)==0:      return _NameMatchesGroup([],self.searchedStringLength)
            else:               return _NameMatchesGroup([max(ln, key=lambda x: x.normalisedPopularity)],self.searchedStringLength) 
        if len(ln)==0:          return _NameMatchesGroup([max(fn, key=lambda x: x.normalisedPopularity)],self.searchedStringLength)
        else:                   return _NameMatchesGroup([max(ln, key=lambda x: x.normalisedPopularity), 
                                                         max(fn, key=lambda x: x.normalisedPopularity)],self.searchedStringLength)    
    @property
    def longestWordsRank(self): return sum([len(name.value)**2 for name in self.names])
    @property
    def popularityRank(self): return sum([name.normalisedPopularity * len(name.value)**2 for name in self.names])
    @property
    def popularityRankValidatedSequence(self): return sum([name.normalisedPopularity * len(name.value)**2 for name in self.validatedOrder(popularityMode=True).names])
    @property
    def longestWordsRankValidatedSequence(self): return sum([len(name.value)**2 for name in self.validatedOrder(longestMode=True).names])
    
class _NameGroupsDatabase:
    '''Contains all name match groups for a specific string (or substring)'''
    def __init__(self, stringLength):  self.groups, self.strLen = [], stringLength
    def addValue(self, nameMatchesGroup):
        if type(nameMatchesGroup) is not _NameMatchesGroup: raise TypeError("type = "+str(type(nameMatchesGroup)))
        assert(nameMatchesGroup.searchedStringLength == self.strLen) #making sure the group are derived from the same string
        self.groups.append(nameMatchesGroup)
    
    '''Inserts all groups from another database into this database, and inserts the same group/match in front of them'''
    def expandInputDatabase(self, aGroupOrMatch,aDatabase):
        matchesList = []
        if type(aGroupOrMatch) == _NameMatch:  matchesList = [aGroupOrMatch]
        elif type(aGroupOrMatch) == _NameMatchesGroup: matchesList = aGroupOrMatch.names
        else: raise TypeError("aGroupOrMatch type is: "+str(type(aGroupOrMatch))+"value: "+str(aGroupOrMatch))
        for group in aDatabase.groups: self.addValue(_NameMatchesGroup(matchesList + group.names,self.strLen))
    
    def envelopName(self, aName):
        if type(aName) is not _NameMatch: raise TypeError("type = "+str(type(aName)))
        if len(self.groups) == 0: self.addValue(_NameMatchesGroup([aName],self.strLen))
        else: 
            for group in self.groups: group.addMatchesList([aName])
    
    def envelopGroup(self,aMatchGroup):    
        if type(aMatchGroup) is not _NameMatchesGroup: raise TypeError("type = "+str(type(aName)))
        if len(self.groups) == 0 : self.addValue(_NameMatchesGroup(aMatchGroup,self.strLen))
        else: 
            for group in self.groups: group.addMatchesList(aMatchGroup.names)
    
    """Caution: merges regardless of databases' searched string lengths, should be used for merging a database into a larger one. """
    def envelopDatabase(self, aDatabase):
        if type(aDatabase) is not _NameGroupsDatabase: raise TypeError("type = "+str(type(aName)))
        if len(self.groups) == 0:
                for inputGroup in aDatabase.groups: self.addValue(_NameMatchesGroup(inputGroup.names,self.strLen))
        else:
            oldGroups = self.groups
            self.groups = []
            while len(oldGroups) > 0:
                currentGroup = oldGroups.pop()
                for inputGroup in aDatabase.groups: self.addValue(_NameMatchesGroup(currentGroup.names+inputGroup.names,self.strLen))

    def isEmpty(self): return True if len(self.groups)==0 else False              
    def getLongestWords(self): return _NameMatchesGroup([],self.strLen) if len(self.groups)==0 else max(self.groups,key=lambda x: x.longestWordsRank)
    def getPopularGuess(self): return _NameMatchesGroup([],self.strLen) if len(self.groups)==0 else max(self.groups,key=lambda x: x.popularityRank)
    """validated guesses don't contain [F,L,F] or [L,F,L] sequences"""
    def getValidatedPopularGuess(self): return _NameMatchesGroup([],self.strLen) if len(self.groups)==0 else max(self.groups,key=lambda x: x.popularityRankValidatedSequence)
    def getValidatedLongestWords(self):  return _NameMatchesGroup([],self.strLen) if len(self.groups)==0 else max(self.groups,key=lambda x: x.longestWordsRankValidatedSequence)

  
        
def _searchSubtrings(string,substringLen):
    '''
    Extracts names by checking for substrings of a specified length.
    Returns list of _NameMatch objects
    '''
    matches = {} #dict to avoid the same name saved, also prefers the earlier occurrence of multiple names
    for i in range(len(string)-substringLen+1):
        check = str.title(string[i:i+substringLen])
        if check in util.fnames: 
            if check not in matches: matches[check] = _NameMatch(False,check,int(util.fnames[check]),i+substringLen)
        elif check in util.lnames: 
            if check not in matches: matches[check] = _NameMatch(True,check,int(util.lnames[check]),i+substringLen)
    if len(matches) > 0: return list(matches.values())

def _findNames(string):
    '''
    Returns either a _NameMatch  or a NameGroupDatabase
    '''        
    #quick check block
    check = str.title(string)
    if check in util.fnames: return _NameMatch(False,check,int(util.fnames[check]),len(string))
    if check in util.lnames: return _NameMatch(True,check,int(util.lnames[check]),len(string))
    
    database = _NameGroupsDatabase(len(string))
    floored, topped, sign, i, stringLenToCheck, ceil = False, False, 1, 1, 7, min(len(string), 15)
    if len(string) < 7:
        topped, stringLenToCheck, sign = True, len(string)-1, -1
        
    while not floored or not topped:
        if stringLenToCheck <= 2: floored = True
        elif stringLenToCheck >= ceil: topped = True
        nameMatches = _searchSubtrings(string,stringLenToCheck)
        if nameMatches:
            for nameMatch in nameMatches:
                if nameMatch.endIndex < len(string) -1: #possibility of further names matches in remaining string, recurse
                    nextNameMatches = _findNames(string[nameMatch.endIndex:])
                    if nextNameMatches:
                        if type(nextNameMatches) is _NameMatch: 
                            database.addValue( _NameMatchesGroup([nameMatch,nextNameMatches],len(string)))
                        if type(nextNameMatches) is _NameGroupsDatabase: database.expandInputDatabase(nameMatch,nextNameMatches)
                    else: 
                        database.addValue(_NameMatchesGroup([nameMatch],len(string)))
                else:
                    database.addValue(_NameMatchesGroup([nameMatch],len(string)))        
        if floored: i, sign = 1,1
        elif topped: i, sign = 1,-1
        else: #alternating one up one down
            sign = sign*(-1)
            i +=1
        stringLenToCheck += i*sign
    if database.isEmpty() == False: return database
       
       
       
def _nameMatchString(string,byLongest=True,allResults=False,anySequence=False): 
    '''Handles _findNames() output.'''
    
    words = re.findall('[a-z]+',str.lower(string))
    database = _NameGroupsDatabase(sum([len(word) for word in words]))
    returnDict = {'last_names':[],'first_names':[]}
    if len(words)==0: return returnDict
    elif len(words)==1:
        result = _findNames(words[0])
        if type(result) is _NameMatch:
            returnDict['last_names' if result.isLname else 'first_names' ] = [result.value]
            return returnDict
        if type(result) is _NameGroupsDatabase: database = result
    else:
        results = []
        for word in words: 
            results.append(_findNames(word))
        for result in results: 
            if type(result) is _NameMatch: database.envelopName(result)
            elif type(result) is _NameMatchesGroup: database.envelopGroup(result)
            elif type(result) is _NameGroupsDatabase: database.envelopDatabase(result)
            else: raise TypeError("type = "+str(type(result)))
            
    #process results
    if anySequence:
        if byLongest: finalGroup = database.getPopularGuess()
        else: finalGroup = database.getLongestWords()        
    else: #only validated sequences        
        if byLongest: finalGroup = database.getValidatedPopularGuess()
        else: finalGroup = database.getValidatedLongestWords()
    #output results as dictionaries
    if allResults: return finalGroup.toDictionary()  #all resutls
    else:
        if byLongest: return finalGroup.longestLastAndFirst.toDictionary()
        else: return finalGroup.mostPopularLastAndFirst.toDictionary()



def _scanDatum(datum,byLongest=True,allResults=False,anySequence=False):
    '''breaks up input for _nameMatchString'''
    if type(datum) is not str: datum = str(datum)
    words = re.findall('[a-z]+',str.lower(datum))
    if len(words) > 7 or len(words)> 1 and sum([len(word) for word in words])>20: #long input, split to avoid memory hog.
        results = {'last_names':[],'first_names':[]}
        for word in words:
            result = _nameMatchString(word,byLongest=byLongest,allResults=allResults,anySequence=anySequence)
            results['last_names'] += result['last_names']
            results['first_names'] += result['first_names']
        return results
    else: 
        return _nameMatchString(datum,byLongest=byLongest,allResults=allResults,anySequence=anySequence)
        