import os
import glob
import copy

class Runner:
    '''
    Class Runner
    in charge of detecting, compiling and generate execution option out of runnable files 
    '''
    C       = 0
    CPP     = 1
    JAVA    = 2
    PYTHON  = 3

    extensions  = {"c": C, "cpp": CPP, "java": JAVA, "py": PYTHON}
    compilers   = {
        C       : "gcc -o {filename}.o {filename}",
        CPP     : "g++ -o {filename}.o {filename}",
        JAVA    : "javac -cp {classpath} {filename}",
        PYTHON  : ""
        }
    def __init__(self):
        self.compilers = copy.deepcopy(Runner.compilers)

    def autoType(self, partiPath):
        '''
        automatically detect the file types, pariPath should be the directory of participant
        function is based on extension of all files under partiPath, if multiple types are possible,
            exception raises
        '''
        possible = set()
        for d in glob.glob(os.path.join(partiPath, "*"), recursive=True):
            ext = os.path.splitext(d)[1].lower()
            if ext in Runner.extensions:
                possible.add(ext)
        if len(possible) != 1:
            print("Multiple possible types, auto detection failed.")
            return None
        else:
            ext = list(possible)[0]
            return Runner.extensions[ext]

    def setCompiler(self, language, newOption):
        self.compilers[language] = newOption

    def appendCompiler(self, language, newOption):
        self.compilers[language] += newOption

    #def compile(self, )

class Manager:
    '''
    Class Manager
    in charge of manage all participants' scorce codes and programs, uncompiled and compiled
    '''
    def __init__(self, _path):
        '''
        _path is the directory of participants. Each participant should be contained in a single 
        directory in _path, and each child directory of _path will be regarded as a participant
        '''
        self.path = os.path.abspath(_path)
        self.names = []
        self.types = dict()
        self.status = dict()

    def detect(self):
        '''
        detect all directory under self.path, each child directory will be regarded as a participant
        '''
        # detect all files under path
        for d in glob.glob(os.path.join(self.path, "*")):
            # if it is a name
            if os.path.isdir(d):
                self.names.append(os.path.basename(d))
        return len(self.names)

    def autoType(self, name):
        files = glob.glob(os.path.join(self.path, "*"))
