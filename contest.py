import feeder
import manager
import executor
import os

class Contest:
    def __init__(self, path):
        self.path = path
        self.participant = manager.ParticipantManager(os.path.join(self.path, "classes"))
        self.data = manager.DataManager(os.path.join(self.path, "data"), ["python", os.path.join(self.path, "gen.py")])
        self.result = manager.ResultManager(self.participant)
        self.judge = executor.Judge(executor.Judge.SPJ, executor.Judge.STD, os.path.join(self.path, "SPJ.exe"))
        self.runner = manager.Runner()

    def initialization(self):
        self.participant.detectParticipant()
        self.runner.addDependency(manager.Runner.JAVA, [r"C:\Users\qq567\Documents\OO\code\H6\duipai\lib\elevator-input-hw2-1.3-jar-with-dependencies.jar", r"C:\Users\qq567\Documents\OO\code\H6\duipai\lib\timable-output-1.0-raw-jar-with-dependencies.jar"])
        self.participant.getRunningOption(self.runner)
        
    def runOnce(self):
        data = self.data.generateData()[0]
        inputlist = manager.DataManager.parseTimedInput(data)
        outputname = manager.DataManager.formatOutputName(self.participant.names, self.path, os.path.basename(data))
        fdr = feeder.Feeder(
            self.participant.names,
            self.participant.runningOption,
            feeder.Feeder.IM_TIMED_STRING,
            inputlist,
            feeder.Feeder.OM_CLASSIC,
            outputname,
            200
        )
        fdr.startAll()
