import subprocess as sp
import tempfile
import threading
import time

class Feeder:
    #input Modes
    IM_CLASSIC = 0         #then input is a file path, which will be redirected to all programs
    IM_STRING = 1          #then input is the content of input file, which will be redirected as well
    IM_TIMED_STRING = 2    #then input is a list of tuple, which has the format of (time, content)

    #output Modes
    OM_CONSOLE = 0         #then output is None, and output will be displayed on the screen
    OM_CLASSIC = 1         #then output is a dict of name to file path, which will be redirected to for each programs
    OM_STRING = 2          #then output is None, and output will be stored inside the class

    #finish State
    FS_OK   = 0     #program ends normally
    FS_RE   = 1     #program ends with runtime error
    FS_TLE  = 2     #program couldn't end with in _timeOut
    def __init__(self, _names, _runningOption, _inputMode, _input, _outputMode, _output, _timeOut = 1.0):
        '''
        Feeder Constructor
        _names                      a list (or set) which contains all distinct participants
        _runningOption              a list of string, which will the argument for Popen()
        _inputMode
            IM_CLASSIC = 0          then _input is a file path, which will be redirected to all programs
            IM_STRING = 1           then _input is the content of input file, which will be redirected as well
            IM_TIMED_STRING = 2     then _input is a list of tuple, which has the format of (time, content)
        _outputMode
            OM_CONSOLE = 0          then _output is None, and output will be displayed on the screen
            OM_CLASSIC = 1          then _output is a dict of name to file path, which will be redirected to for each programs
            OM_STRING = 2           then _output is None, and output will be stored inside the class
        _timeOut = 1.0              longest time waiting for program to end (in sec)
        '''
        self.names = set(_names)
        self.runningOption = _runningOption
        self.inputMode = _inputMode
        self.input = _input
        self.outputMode = _outputMode
        self.output = _output
        self.timeOut = _timeOut

        self.programs = dict()
        self.returnCode = dict()
        self.finishState = dict()
        self.outputLines = dict()

        if _inputMode == Feeder.IM_CLASSIC:
            self.runningOption.append("<" + _input)

    def getStdin(self):
        '''
        return the parameter to Popen.stdin
        '''
        ipt = None
        if self.inputMode == Feeder.IM_STRING:
            ipt = tempfile.NamedTemporaryFile()
            ipt.write(self.input)
            ipt.flush()
            ipt.seek(0)
        elif self.inputMode == Feeder.IM_TIMED_STRING:
            ipt = sp.PIPE
        return ipt

    def getStdout(self):
        '''
        return the parameter to Popen.stdout
        '''
        opt = None
        if self.outputMode == Feeder.OM_STRING:
            opt = tempfile.NamedTemporaryFile()
        return opt

    def allFinished(self, lst = None):
        '''
        return true iff all programs have finished running (no matter how)
        '''
        if not lst:
            lst = self.names
        for name in lst:
            if self.programs[name].poll() == None:
                return False
        return True

    def killAll(self, lst = None):
        '''
        terminate each program in lst, if it is not finished yet;
        or record its return code, if it has already finished.
        '''
        if not lst:
            lst = self.names
        for name in lst:
            p = self.programs[name]
            if p.poll() == None:
                p.kill()
                self.finishState = Feeder.FS_TLE
            self.returnCode[name] = p.poll()
            if p.poll() == 0:
                self.finishState = Feeder.FS_OK
            else:
                self.finishState = Feeder.FS_RE

    def finishInput(self, lst = None):
        '''
        feed EOF to all programs in list `lst`
        '''
        if not lst:
            lst = self.names
        for name in lst:
            p = self.programs[name]
            if p.poll() == None:
                p.stdin.close()

    def feedAll(self, line, lst = None):
        '''
        feed the string `line` to programs in list `lst`
        '''
        if not lst:
            lst = self.names
        for name in lst:
            p = self.programs[name]
            if p.poll() == None:
                p.stdin.write((line+"\n").encode())
                p.stdin.flush()

    def getInputTimers(self, lst = None):
        '''
        return a list of timers of all timed input described in self.input
        '''
        ret = []
        maxtim = 0.0
        for pair in self.input:
            maxtim = max(maxtim, pair[0])
            timer = threading.Timer(pair[0], self.feedAll, [pair[1], lst])
            ret.append(timer)
        ret.append(threading.Timer(maxtim+1.0, self.finishInput, [lst]))
        return ret

    def startAll(self):
        '''
        start all programs at the same time, all programs will be running parallelly
        '''
        # print("startall")
        ro = self.runningOption
        ipt = self.getStdin()
        opt = self.getStdout()
        timers = []
        # initialize parameters for this IO mode
        if self.inputMode == Feeder.IM_TIMED_STRING:
            timers = self.getInputTimers()
        print("input timers got")
        # run all programs
        print(self.names)
        for name in self.names:
            print(name)
            if self.outputMode == Feeder.OM_CLASSIC:
                ro = self.runningOption[name]
                opt = open(self.output[name], "w")
            else:
                ro = self.runningOption[name]
            print(ro)
            p = sp.Popen(ro, stdin = ipt, stdout = opt)
            self.programs[name] = p
        startTime = time.time()
        
        # start all timers
        for timer in timers:
            timer.start()
        
        # wait until all programs are finished or time out
        while time.time()-startTime < self.timeOut:
            if self.allFinished():
                break
            time.sleep(min(1.0, self.timeOut/100.0))
        
        # now all programs are finished, or needs to be finished
        self.killAll()

    def runAll(self):
        '''
        run all programs one by one, each program will be running seperatedly
        '''
        ro = self.runningOption
        ipt = self.getStdin()
        opt = self.getStdout()
        timers = []

        # run all programs one by one
        for name in self.names:
            if self.outputMode == Feeder.OM_CLASSIC:
                ro = self.runningOption + ["1>" + self.output[name]]
            else:
                ro = self.runningOption
            # initialize parameters for this IO mode
            if self.inputMode == Feeder.IM_TIMED_STRING:
                timers = self.getInputTimers([name])
            p = sp.Popen(ro, stdin = ipt, stdout = opt)
            self.programs[name] = p
            start_time = time.time()
            # start all timers
            for timer in timers:
                timer.start()
            # wait until the program is finished or time out
            while time.time()-start_time < self.timeOut:
                if self.allFinished([name]):
                    break
                time.sleep(min(1.0, self.timeOut/100.0))
            self.killAll([name])
