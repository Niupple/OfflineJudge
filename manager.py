import os
import glob
import copy
import subprocess as sp
import tempfile
import re
import time
import random

def allFilesUnder(path, pattern=".*"):
    ret = []
    for i in os.walk(path):
        for j in i[2]:
            s = os.path.basename(j)
            if re.fullmatch(pattern, s, re.IGNORECASE):
                ret += [os.path.join(i[0], j)]
    return ret

class Runner:
    '''
    Class Runner
    in charge of detecting, compiling and generate execution option out of runnable files 
    '''
    C       = 0
    CPP     = 1
    JAVA    = 2
    PYTHON  = 3

    extensions  = {"c": C, "cpp": CPP, "java": JAVA, "py": PYTHON, "class": JAVA}
    compilers   = {
        C       : "gcc -o {filename}.o {filename}",
        CPP     : "g++ -o {filename}.o {filename}",
        JAVA    : "javac -cp {classpath} {filename}",
        PYTHON  : ""
        }

    JAVA_MC_PAT = "public static void main(java.lang.String[])"

    STDERR = ["2>" + os.path.devnull]

    @staticmethod
    def execute(cmd):
        tmpf = tempfile.NamedTemporaryFile()
        p = sp.Popen(cmd.split(), stdout=tmpf)
        p.wait()
        tmpf.seek(0)
        if p.poll() == 0:
            s = tmpf.read()
            tmpf.close()
            return s.decode("utf8")
        else:
            # print(tmpf.read())
            tmpf.close()
            return None

    @staticmethod
    def getMainclassFromSource(partiPath):
        files = allFilesUnder(partiPath, r".*\.java")
        for fi in files:
            # print("in file", fi)
            with open(fi, "r", encoding="utf-8") as f:
                content = f.read()
                # print(content)
                if content.find(Runner.JAVA_MC_PAT) != -1:
                    path = os.path.splitext(os.path.relpath(fi, partiPath))[0]
                    return path.replace(os.path.sep, ".")
        return None
    
    @staticmethod
    def getMainclassFromBytes(partiPath):
        files = allFilesUnder(partiPath, r".*\.class")
        for fi in files:
            cmd = " ".join(["javap", fi])
            s = Runner.execute(cmd)
            if s and s.find(Runner.JAVA_MC_PAT) != -1:
                path = os.path.splitext(os.path.relpath(fi, partiPath))[0]
                print(partiPath, fi, path)
                return path.replace(os.path.sep, ".")
        return None

    @staticmethod
    def autoType(partiPath):
        '''
        automatically detect the file types, pariPath should be the directory of participant
        function is based on extension of all files under partiPath, if multiple types are possible,
            exception raises
        '''
        possible = set()
        # print("in", partiPath)
        for d in allFilesUnder(partiPath):
            # print("got", d)
            ext = os.path.splitext(d)[1].lower()[1:]
            if ext in Runner.extensions:
                possible.add(Runner.extensions[ext])
        if len(possible) != 1:
            print(possible)
            print("Multiple possible types, auto detection failed.")
            return None
        else:
            ext = list(possible)[0]
            return ext

    @staticmethod
    def getMainFile(partiPath, language):
        if language == Runner.JAVA:
            mc = Runner.getMainclassFromBytes(partiPath)
            if mc == None:
                mc = Runner.getMainclassFromSource(partiPath)
            return mc
        return None

    def __init__(self):
        self.compilers = copy.deepcopy(Runner.compilers)
        self.dependencies = {Runner.JAVA: []}
    
    def addDependency(self, language, deps):
        self.dependencies[language] += deps
        print(self.dependencies[language])

    def setCompiler(self, language, newOption):
        self.compilers[language] = newOption

    def appendCompiler(self, language, newOption):
        self.compilers[language] += newOption

    def compile(self, language, partiPath, name = "*"):
        if language == Runner.C or language == Runner.CPP:
            cmd = self.compilers[language]
            cmd = cmd.format(filename = name)
            return Runner.execute(cmd) != None
        elif language == Runner.JAVA:
            mainclass = Runner.getMainclassFromSource(partiPath)
            cmd = self.compilers[language].format(filename = mainclass, classpath = ";".join(self.dependencies[language] + [partiPath]))
            return Runner.execute(cmd) != None
        elif language == Runner.PYTHON:     # python doesn't need compiliation
            return True

    def getRunningOption(self, language, partiPath, mainFile):
        "getting running option"
        cmd = None
        if language == Runner.C or language == Runner.CPP:
            cmd = [mainFile] + Runner.STDERR
        elif language == Runner.JAVA:
            cmd = ["java", "-cp", ";".join(self.dependencies[language] + [partiPath]), mainFile]
        elif language == Runner.PYTHON:
            cmd = ["python", mainFile]
        return cmd

class ParticipantManager:
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
        self.runnable = dict()
        self.mainFile = dict()
        self.runningOption = dict()

    def detectParticipant(self):
        '''
        detect all directory under self.path, each child directory will be regarded as a participant
        '''
        # detect all files under path
        for d in glob.glob(os.path.join(self.path, "*")):
            # if it is a name
            if os.path.isdir(d):
                name = os.path.basename(d)
                self.names.append(name)
                partiPath = os.path.join(self.path, name)
                tp = Runner.autoType(partiPath)
                if tp != None:
                    self.types[name] = tp
                    self.mainFile[name] = Runner.getMainFile(partiPath, tp)
        print(self.mainFile)
        return len(self.names)

    def getRunningOption(self, runner):
        for name in self.names:
            self.runningOption[name] = runner.getRunningOption(self.types[name], os.path.join(self.path, name), self.mainFile[name])

class DataManager:
    @staticmethod
    def parseTimedInput(filepath, pattern=r"\[{time}\]{data}"):
        pat = pattern.format(time=r"(.*)", data=r"(.*)")
        with open(filepath, "r") as f:
            lines = f.readlines()
            ret = []
            for line in lines:
                #print(pat, line)
                group = re.match(pat, line).groups()
                ret.append((float(group[0]), group[1]))
            return ret
        return None
    
    @staticmethod
    def formatOutputName(names, outputPath, inputfile, pattern="{names}_{inputfile}.out"):
        ret = dict()
        for name in names:
            ret[name] = os.path.join(outputPath, pattern.format(names=name, inputfile=inputfile))
        return ret

    def __init__(self, _path, _maker = None):
        self.path = _path
        self.maker = _maker
        self.counter = 0
        self.data = []
        self.prefix = time.strftime("%Y-%m-%d-%H-%M-%S-", time.localtime())
        self.suffix = ".in"

    def generateData(self, number = 1):
        ret = []
        for i in range(number):
            name = os.path.join(self.path, self.prefix+str(self.counter)+self.suffix)
            with open(name, "w") as of:
                self.counter += 1
                cmd = self.maker + [ str(random.randint(1, 1000000000))]
                #print(cmd)
                p = sp.Popen(cmd, stdout=of)
                p.wait(60)
                self.data.append(name)
                ret.append(name)
        return ret

    def resetCounter(self):
        self.prefix = time.strftime("%Y-%m-%d-%H-%M-%S-", time.localtime())
        self.counter = 0

    def getRealPath(self, name):
        return os.path.realpath(os.path.join(self.path, name))

    def clearBuffer(self):
        for i in range(len(self.data)):
            os.remove(self.getRealPath(self.data[i]))
        self.data = []

    def removeData(self, name):
        if name in self.data:
            os.remove(self.getRealPath(name))

class ResultManager:
    AC  = 0
    WA  = 1
    RE  = 2
    TLE = 3
    PE  = 4
    def __init__(self, pm):
        self.names = pm.names
        self.result = dict()
    
    def addRow(self, data, result):
        self.result[data] = dict()
        for name in self.names:
            self.result[data][name] = result[name]
    
    def getRow(self, data):
        return self.result[data]
