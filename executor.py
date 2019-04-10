import sys
import subprocess as sp
import tempfile
import manager

class Judge:
    # using what to compare
    FC  = 0         # using system file compare
    SPJ = 1         # using given SPJ
    # how to compare
    CROSS   = 0     # compare the output with each other
    STD     = 1     # only compare with std's output

    SYS_DIFF = ""

    @classmethod
    def initDiff(cls):
        if sys.platform.lower().find("win"):
            cls.SYS_DIFF = "FC"
        else:
            cls.SYS_DIFF = "diff"

    @staticmethod
    def fileCompare(stdin, filea, fileb):
        cmd = [Judge, filea, fileb]
        tmpf = tempfile.NamedTemporaryFile()
        p = sp.Popen(cmd, stdout=tmpf)
        p.wait()
        tmpf.seek(0)
        s = tmpf.read()
        tmpf.close()
        if p.poll() == 0:
            return (True, s)
        else:
            return (False, s)

    def __init__(self, compareTool, compareMode, spj=None):
        self.spj = spj
        self.compareTool = compareTool
        self.compareMode = compareMode
    
    def spjCompare(self, stdin, filea, fileb):
        cmd = [self.spj, stdin, filea, fileb]
        tmpf = tempfile.NamedTemporaryFile()
        p = sp.Popen(cmd, stdout=tmpf)
        p.wait()
        tmpf.seek(0)
        s = tmpf.read()
        tmpf.close()
        if p.poll() == 0:
            return (True, s)
        else:
            return (False, s)
    
    def crossCompare(self, names, stdin, partiOut, compareTool):
        namelist = list(names)
        N = len(namelist)
        for i in range(1, N):
            (ret, s) = compareTool(stdin, partiOut[names[0]], partiOut[names[i]])
            if not ret:
                return (ret, s)
        return (True, "all the same.")

    def stdCompare(self, names, stdin, stdout, partiOut, compareTool):
        ret = dict()
        for name in names:
            (ac, s) = compareTool(stdin, stdout, partiOut[name])
            if ac:
                ret[name] = manager.ResultManager.AC
            else:
                ret[name] = manager.ResultManager.WA
        return ret
    
    def judge(self, names, stdin, partiOut, stdout=None):
        if self.compareMode == Judge.CROSS:
            (res, s) = (False, "")
            if self.compareTool == Judge.SPJ:
                (res, s) = self.crossCompare(names, stdin, partiOut, self.spj)
            else:
                (res, s) = self.crossCompare(names, stdin, partiOut, Judge.fileCompare)
            stat = 0
            if not res:
                stat = manager.ResultManager.WA
                print(s)
            else:
                stat = manager.ResultManager.AC
            return {name: stat for name in names}
        elif self.compareMode == Judge.STD:
            jt = None
            if self.compareTool == Judge.SPJ:
                jt = Judge.fileCompare
            else:
                jt = self.spjCompare
            ret = self.stdCompare(names, stdin, stdout, partiOut, jt)
            return ret

