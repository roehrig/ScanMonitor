'''
Created on Jun 10, 2013

@author: roehrig
'''
'''
Created on Oct 30, 2012

@author: roehrig
'''
import wx
import getpass
import time
import LocalClasses.DetectorError as DetectorError
from GUI_Classes.TextControlWithPVCheck import PVText
from GUI_Classes.GrowableSectionPanel import DynamicTextControlPanel
from Utils.PVTimer import PVTimer
from Utils.EmailSender import EmailSender
from epics import PV as PV
from epics.wx import DelayedEpicsCallback
from os.path import expanduser
        
########################################################################
class StatusPanel (wx.Panel):
    '''
    classdocs
    '''
    def __init__(self, emailAddressList, *args, **kwargs):
        '''
        Constructor
        '''
        wx.Panel.__init__(self, *args, **kwargs)
        
        self.emailAddressList = emailAddressList
        self.detectorHandler = DetectorError.DetectorErrorHandler(self.emailAddressList)
        self.sentScanDoneEmail = False # This indicates that an email has been sent at the completion of a scan.
        self.timer = None           # This will be a PVTimer object to monitor the progress of a scan
        self.updater = None         # This will be a PVTimer object that will simply update a scan status
        self.scanPaused = None      # This will be a PV object that checks to see if the scan is paused.
        self.scanExecuting = None   # This will be a PV object that checks to see if a scan is executing.
        self.scanWaiting = None     # This will be a PV object that checks to see if the scan is waiting.
        self.shutterStatus = None   # This will be a PV object that checks the shutter status
        self.scanWaitCount = None   # This will be a PV objcet that is used to change the .WCNT field of the scan record.
        self.monitorReady = False
        self.monitorStarted = False
        self.scanExecuting = False
        self.scanPaused = False
        self.scanWaiting = False
        self.paramSaveFile = "%s/scan_monitor_params.txt" % expanduser("~")
        
        self.pvLabel = wx.StaticText(self, -1, "PV To Monitor", style=wx.ALIGN_CENTER_VERTICAL | wx.SIMPLE_BORDER)
        self.timerLabel = wx.StaticText(self, -1, "Check error freq. (sec)", style=wx.ALIGN_CENTER_VERTICAL | wx.SIMPLE_BORDER)
        self.updateLabel = wx.StaticText(self, -1, "Update freq. (min)", style=wx.ALIGN_CENTER_VERTICAL | wx.SIMPLE_BORDER)
        self.resetsLabel = wx.StaticText(self, -1, "Number of reset tries", style=wx.ALIGN_CENTER_VERTICAL | wx.SIMPLE_BORDER)
        self.shutterLabel = wx.StaticText(self, -1, "Shutter PV", style=wx.ALIGN_CENTER_VERTICAL | wx.SIMPLE_BORDER)
        self.detectorPrefixLabel = wx.StaticText(self, -1, "Detector Prefix", style=wx.ALIGN_CENTER_VERTICAL | wx.SIMPLE_BORDER)
        self.innerScanLabel = wx.StaticText(self, -1, "Inner Scan", style=wx.ALIGN_CENTER_VERTICAL | wx.SIMPLE_BORDER)
        self.outerScanLabel = wx.StaticText(self, -1, "Outer Scan", style=wx.ALIGN_CENTER_VERTICAL | wx.SIMPLE_BORDER)
        self.pvStatusLabel = wx.StaticText(self, -1, "PV Status", style=wx.ALIGN_CENTER_VERTICAL | wx.SIMPLE_BORDER)
        self.senderLabel = wx.StaticText(self, -1, "Email sender", style=wx.ALIGN_CENTER_VERTICAL | wx.SIMPLE_BORDER)
        self.subjectLabel = wx.StaticText(self, -1, "Email subject", style=wx.ALIGN_CENTER_VERTICAL | wx.SIMPLE_BORDER)
        self.fileNameLabel = wx.StaticText(self, -1, "File name", style=wx.ALIGN_CENTER_VERTICAL | wx.SIMPLE_BORDER)
        
        self.pvTxtCtrl = PVText(self, -1, "", size=wx.Size(150,22), style=wx.SIMPLE_BORDER)
        self.timerTxtCtrl = wx.TextCtrl(self, -1, "", size=wx.Size(75,22), style=wx.SIMPLE_BORDER)
        self.updateTxtCtrl = wx.TextCtrl(self, -1, "", size=wx.Size(75,22), style=wx.SIMPLE_BORDER)
        self.resetsTxtCtrl = wx.TextCtrl(self, -1, "", size=wx.Size(75,22), style=wx.SIMPLE_BORDER)
        self.shutterTxtCtrl = wx.TextCtrl(self, -1, "", size=wx.Size(150,22), style=wx.SIMPLE_BORDER)
        self.detectorPrefixTxtCtrl = wx.TextCtrl(self, -1, "", size=wx.Size(150,22), style=wx.SIMPLE_BORDER)
        self.innerScanTxtCtrl = wx.TextCtrl(self, -1, "", size=wx.Size(150,22), style=wx.SIMPLE_BORDER)
        self.outerScanTxtCtrl = wx.TextCtrl(self, -1, "", size=wx.Size(150,22), style=wx.SIMPLE_BORDER)
        self.pvStatusTxtCtrl = wx.TextCtrl(self, -1, "Monitor Stopped", size=wx.Size(150,22), style=wx.SIMPLE_BORDER | wx.TE_READONLY | wx.TE_RICH2 | wx.BOLD)
        self.senderTxtCtrl = wx.TextCtrl(self, -1, "", size=wx.Size(200,22), style=wx.SIMPLE_BORDER)
        self.subjectTxtCtrl = wx.TextCtrl(self, -1, "", size=wx.Size(400,22), style=wx.SIMPLE_BORDER)
        self.fileNameTxtCtrl = wx.TextCtrl(self, -1, "", size=wx.Size(400,22), style=wx.SIMPLE_BORDER)
        
        # Set some properties of the status text
        currentFontSize = self.pvStatusTxtCtrl.GetFont().GetPointSize()
        currentFontStyle = self.pvStatusTxtCtrl.GetFont().GetStyle()
        currentFontFamily = self.pvStatusTxtCtrl.GetFont().GetFamily()
        self.newFont = wx.Font(currentFontSize, currentFontFamily, currentFontStyle, wx.BOLD, False)
        self.pvStatusTxtCtrl.SetFont(self.newFont)
        self.pvStatusTxtCtrl.SetForegroundColour(wx.RED)

        # Create some buttons
        self.stopMonitorButton = wx.Button(self, -1, "Stop",size=wx.Size(150,27))
        self.setValuesButton = wx.Button(self, -1, "Set Values",size=wx.Size(150,27))
        self.loadValuesButton = wx.Button(self, -1, "Load Values",size=wx.Size(150,27))
        self.saveValuesButton = wx.Button(self, -1, "Save Values",size=wx.Size(150,27))
        self.testResetFunctionButton = wx.Button(self, -1, "Test Reset",size=wx.Size(150,27))
        
        # The stop button begins disabled
        self.stopMonitorButton.Enable(False)
        self.testResetFunctionButton.Enable(False)
        
        # Set some tool tip strings
        self.pvTxtCtrl.SetToolTipString("The PV to monitor for value changes")
        self.timerTxtCtrl.SetToolTipString("The interval to check for scan errors")
        self.updateTxtCtrl.SetToolTipString("The interval to update scan status")
        self.resetsTxtCtrl.SetToolTipString("The number of times to reset the timer")
        self.shutterTxtCtrl.SetToolTipString("The PV for the shutter status")
        self.detectorPrefixTxtCtrl.SetToolTipString("The prefix of the detector ioc")
        self.innerScanTxtCtrl.SetToolTipString("The inner scan record name")
        self.outerScanTxtCtrl.SetToolTipString("The outer scan record name")
        self.senderTxtCtrl.SetToolTipString("The address that the email will come from")
        self.subjectTxtCtrl.SetToolTipString("The subject line of the update email")
        self.fileNameTxtCtrl.SetToolTipString("The file that the scan status will be written to")
        self.setValuesButton.SetToolTipString("Commit values entered and start monitor")
        self.loadValuesButton.SetToolTipString("Load last saved values")
        self.saveValuesButton.SetToolTipString("Save current values")
        self.stopMonitorButton.SetToolTipString("Stop Monitor")
        self.testResetFunctionButton.SetToolTipString("Test the detector reset function")
        
        # Bind events to their sources and the functions that need to be called.
        self.Bind(wx.EVT_BUTTON, self.OnStopButtonClick, self.stopMonitorButton)
        self.Bind(wx.EVT_BUTTON, self.OnSetButtonClick, self.setValuesButton)
        self.Bind(wx.EVT_BUTTON, self.OnLoadButtonClick, self.loadValuesButton)
        self.Bind(wx.EVT_BUTTON, self.OnSaveButtonClick, self.saveValuesButton)
        self.Bind(wx.EVT_TIMER, self.OnTimerExpired, self.timer)
        self.Bind(wx.EVT_BUTTON, self.ForceDetectorReset, self.testResetFunctionButton)
        
        # Set some initial values
        self.senderTxtCtrl.SetValue("%s@aps.anl.gov" % getpass.getuser())
        self.fileNameTxtCtrl.SetValue("%s/scan_monitor_status.txt" % expanduser("~"))

        panelSizer = wx.FlexGridSizer(rows=15, cols=2, hgap=5, vgap=5)
        panelSizer.Add(self.pvLabel, 0, wx.ALIGN_LEFT)
        panelSizer.Add(self.pvTxtCtrl, 0, wx.ALIGN_LEFT)
        panelSizer.Add(self.timerLabel, 0, wx.ALIGN_LEFT)
        panelSizer.Add(self.timerTxtCtrl, 0, wx.ALIGN_LEFT)
        panelSizer.Add(self.updateLabel, 0, wx.ALIGN_LEFT)
        panelSizer.Add(self.updateTxtCtrl, 0, wx.ALIGN_LEFT)
        panelSizer.Add(self.resetsLabel, 0, wx.ALIGN_LEFT)
        panelSizer.Add(self.resetsTxtCtrl, 0, wx.ALIGN_LEFT)
        panelSizer.Add(self.shutterLabel, 0, wx.ALIGN_LEFT)
        panelSizer.Add(self.shutterTxtCtrl, 0, wx.ALIGN_LEFT)
        panelSizer.Add(self.detectorPrefixLabel, 0, wx.ALIGN_LEFT)
        panelSizer.Add(self.detectorPrefixTxtCtrl, 0, wx.ALIGN_LEFT)
        panelSizer.Add(self.innerScanLabel, 0, wx.ALIGN_LEFT)
        panelSizer.Add(self.innerScanTxtCtrl, 0, wx.ALIGN_LEFT)
        panelSizer.Add(self.outerScanLabel, 0, wx.ALIGN_LEFT)
        panelSizer.Add(self.outerScanTxtCtrl, 0, wx.ALIGN_LEFT)
        panelSizer.Add(self.senderLabel, 0, wx.ALIGN_LEFT)
        panelSizer.Add(self.senderTxtCtrl, 0, wx.ALIGN_LEFT)
        panelSizer.Add(self.subjectLabel, 0, wx.ALIGN_LEFT)
        panelSizer.Add(self.subjectTxtCtrl, 0, wx.ALIGN_LEFT)
        panelSizer.Add(self.fileNameLabel, 0, wx.ALIGN_LEFT)
        panelSizer.Add(self.fileNameTxtCtrl, 0, wx.ALIGN_LEFT)
        panelSizer.Add(self.pvStatusLabel, 0, wx.ALIGN_LEFT)
        panelSizer.Add(self.pvStatusTxtCtrl, 0, wx.ALIGN_LEFT)
        panelSizer.Add(self.setValuesButton, 0, wx.ALIGN_LEFT)
        panelSizer.Add(self.stopMonitorButton, 0, wx.ALIGN_LEFT)
        panelSizer.Add(self.loadValuesButton, 0, wx.ALIGN_LEFT)
        panelSizer.Add(self.saveValuesButton, 0, wx.ALIGN_LEFT)
        panelSizer.Add(self.testResetFunctionButton, 0, wx.ALIGN_LEFT)
                
        self.SetSizer(panelSizer)
        self.Layout()
        self.Fit()
        
        return
    
    def ForceDetectorReset(self, event):
        # Set values in detectorHandler object to those that have ben entered in the GUI
        self.detectorHandler.SetDetectorPVs(self.detectorPrefixTxtCtrl.GetValue(), self.innerScanTxtCtrl.GetValue(), self.outerScanTxtCtrl.GetValue(),
                                                self.senderTxtCtrl.GetValue(), self.subjectTxtCtrl.GetValue(), self.fileNameTxtCtrl.GetValue())
        
        # Call the ResetDetector function
        self.detectorHandler.TestResetDetector()
        
        return
    
    def OnLoadButtonClick(self, event):
        
        try:
            fileHandle = open(self.paramSaveFile, 'r')
            
            line = fileHandle.readline()
            self.pvTxtCtrl.SetValue(line.rstrip("\n"))
                        
            line = fileHandle.readline()
            self.timerTxtCtrl.SetValue(line.rstrip("\n"))
                        
            line = fileHandle.readline()
            self.updateTxtCtrl.SetValue(line.rstrip("\n"))
                        
            line = fileHandle.readline()
            self.resetsTxtCtrl.SetValue(line.rstrip("\n"))
   
            line = fileHandle.readline()
            self.shutterTxtCtrl.SetValue(line.rstrip("\n"))
                        
            line = fileHandle.readline()
            self.detectorPrefixTxtCtrl.SetValue(line.rstrip("\n"))
                        
            line = fileHandle.readline()
            self.innerScanTxtCtrl.SetValue(line.rstrip("\n"))
                        
            line = fileHandle.readline()
            self.outerScanTxtCtrl.SetValue(line.rstrip("\n"))
                        
            line = fileHandle.readline()
            self.senderTxtCtrl.SetValue(line.rstrip("\n"))
                        
            line = fileHandle.readline()
            self.subjectTxtCtrl.SetValue(line.rstrip("\n"))
                        
            line = fileHandle.readline()
            self.fileNameTxtCtrl.SetValue(line.rstrip("\n"))
                        
            line = fileHandle.readline()
            numEmails = int(line.rstrip("\n"))
            
            for i in range(numEmails):
                line = fileHandle.readline()
                parent = self.GetParent()
                if len(self.emailAddressList) < (i + 1):
                    parent.emailSectionPanel.OnAddSection(wx.EVT_IDLE)
                self.emailAddressList[i].SetValue(line.rstrip("\n"))
                
            fileHandle.close()
            self.testResetFunctionButton.Enable(True)
            
        except IOError as e:
            for arg in e.args:
                print arg
                
            dialogBox = wx.MessageDialog(self, "Could not read from save file",
                                         caption="Load Error", style=wx.ICON_ERROR)
            dialogBox.ShowModal()
            dialogBox.Destroy()
            return
        return
    
    def OnSaveButtonClick(self, event):
        
        try:
            fileHandle = open(self.paramSaveFile, 'w+')
            
            fileHandle.write("%s\n" % self.pvTxtCtrl.GetValue())
            fileHandle.write("%s\n" % self.timerTxtCtrl.GetValue())
            fileHandle.write("%s\n" % self.updateTxtCtrl.GetValue())
            fileHandle.write("%s\n" % self.resetsTxtCtrl.GetValue())
            fileHandle.write("%s\n" % self.shutterTxtCtrl.GetValue())
            fileHandle.write("%s\n" % self.detectorPrefixTxtCtrl.GetValue())
            fileHandle.write("%s\n" % self.innerScanTxtCtrl.GetValue())
            fileHandle.write("%s\n" % self.outerScanTxtCtrl.GetValue())
            fileHandle.write("%s\n" % self.senderTxtCtrl.GetValue())
            fileHandle.write("%s\n" % self.subjectTxtCtrl.GetValue())
            fileHandle.write("%s\n" % self.fileNameTxtCtrl.GetValue())
            
            fileHandle.write("%s\n" % len(self.emailAddressList))
            for email in self.emailAddressList:
                fileHandle.write("%s\n" % email.GetValue())
           
            fileHandle.close()
        except IOError as e:
            for arg in e.args:
                print arg
                
            dialogBox = wx.MessageDialog(self, "Could not write to save file",
                                         caption="Save Error", style=wx.ICON_ERROR)
            dialogBox.ShowModal()
            dialogBox.Destroy()
            return
        
        return
    
    def OnSetButtonClick(self, event):
        
        try:
            self.detectorHandler.SetDetectorPVs(self.detectorPrefixTxtCtrl.GetValue(), self.innerScanTxtCtrl.GetValue(), self.outerScanTxtCtrl.GetValue(),
                                                self.senderTxtCtrl.GetValue(), self.subjectTxtCtrl.GetValue(), self.fileNameTxtCtrl.GetValue())
            self.timer = None
            self.updater = None
            self.scanPaused = None
            self.scanExecuting = None
            self.timer = PVTimer(self, self.detectorHandler.ResetDetector, self.pvTxtCtrl.GetValue(),True)
            self.updater = PVTimer(self, self.detectorHandler.WriteStatus)
            self.scanPaused = PV("%s.PAUS" % self.innerScanTxtCtrl.GetValue(),callback=self.ScanStateChange)
            self.scanExecuting = PV( "%s.EXSC" % self.outerScanTxtCtrl.GetValue(),callback=self.ScanStateChange)
            self.scanWaiting = PV( "%s.WCNT" % self.outerScanTxtCtrl.GetValue(),callback=self.ScanStateChange)
            self.shutterStatus = PV("%s" % self.shutterTxtCtrl.GetValue(), callback=self.ShutterChange)
            self.scanWaitCount = PV("%s.WAIT" % self.outerScanTxtCtrl.GetValue())
            self.monitorReady = True
            self.stopMonitorButton.Enable(True)
            
        except:
            dialogBox = wx.MessageDialog(self, "Could not create all data objects",
                                         caption="Data Error", style=wx.ICON_ERROR)
            dialogBox.ShowModal()
            dialogBox.Destroy()
            return
        
        return
    
    @DelayedEpicsCallback
    def ShutterChange(self, *args, **kwargs):
        '''
	    This is executed when the position of the shutter changes.  If the shutter is
	    closed, increment the outer scan record's wait count.  If the shutter is open
	    decrement the outer scan record's wait count.
	    '''

        pvValue = kwargs['value']  # This is the value of the PV that is running the callback

        if (pvValue == 0):
            self.scanWaitCount.put(1, False)
            self.shutterTxtCtrl.SetForegroundColour(wx.RED)
            print "%s Shutter is closed" % time.asctime(time.localtime())
        else:
            self.scanWaitCount.put(0, False)
            self.shutterTxtCtrl.SetForegroundColour(wx.GREEN)
            print "%s Shutter is open." % time.asctime(time.localtime())

        return

    
    @DelayedEpicsCallback
    def ScanStateChange(self, *args, **kwargs):
        '''
        This is executed when the scan record changes state from executing to not executing,
        from paused to running, or vice versa.  It is a callback function to a PV object
        created from PyEpics
        '''
        
        # Initialize some variables
        pvName = kwargs['pvname']  # This is the name of the PV that is running the callback
        pvValue = kwargs['value']  # This is the value of the PV that is running the callback
        
        waitChanged = False
        pauseChanged = False
        executeChanged = False
        
        # Determine which PV is executing this callback.
        if pvName == "%s.WCNT" % self.outerScanTxtCtrl.GetValue():
            waitChanged = True
            if (pvValue > 0):
                scanIsRunning = False
                self.scanWaiting = True
            else:
                scanIsRunning = True
                self.scanWaiting = False
                
        if pvName == "%s.PAUS" % self.innerScanTxtCtrl.GetValue():
            pauseChanged = True
            if pvValue == 1:
                scanIsRunning = False
                self.scanPaused = True
            else:
                scanIsRunning = True
                self.scanPaused = False
                
        if pvName == "%s.EXSC" % self.outerScanTxtCtrl.GetValue():
            executeChanged = True
            if pvValue == 0:
                scanIsRunning = False
                self.scanExecuting = False
            else:
                scanIsRunning = True
                self.scanExecuting = True

	print "%s Scan state changed." % time.asctime(time.localtime())
        print "Scan state has been changed by %s = %d" % (pvName,pvValue)
        # Since the wait count on the scan record is changed on purpose when
        # the detector handler is running, then don't take any action.
        resetting = self.detectorHandler.IsDetectorReset()
        print "Resetting status is %d" % resetting
        if (not resetting):
            # The monitor should be running if the scan is running.    
            if ((scanIsRunning) and (self.monitorReady) and (not self.monitorStarted) and (self.scanExecuting)
                and (not self.scanPaused) and (not self.scanWaiting)):
                self.StartMonitor()
                self.sentScanDoneEmail = False
                self.detectorHandler.WriteStatus(False)
                
            if ((scanIsRunning) and (self.monitorReady) and (not self.monitorStarted)):
                self.pvStatusTxtCtrl.SetValue("Monitor Ready")
                self.pvStatusTxtCtrl.SetForegroundColour(wx.BLUE)
        
            # If the scan is not running, don't run the monitor.  Further, if the scan record thinks it is done,
            # send a status update email.    
            if ((not scanIsRunning) and (self.monitorReady) and (self.monitorStarted)):
            
                #self.OnStopButtonClick(wx.EVT_IDLE)
                self.PauseMonitor()
                if ((self.sentScanDoneEmail == False) and (executeChanged) and (not scanIsRunning)):
                    self.detectorHandler.WriteStatus(False)
                    self.sentScanDoneEmail = True
        
        if (waitChanged) and (scanIsRunning):
            self.detectorHandler.SetResettingDetector(0)
                
        return
    
    def StartMonitor(self):
        if self.monitorReady:
            print "%s Starting monitor" % time.asctime(time.localtime())
            self.timer.PVTimerStart(float(self.timerTxtCtrl.GetValue()), int(self.resetsTxtCtrl.GetValue()))
            self.updater.Start(((float(self.updateTxtCtrl.GetValue())) * 1000 * 60), 0)
            self.pvStatusTxtCtrl.SetValue("Monitor Running")
            self.pvStatusTxtCtrl.SetForegroundColour(wx.GREEN)
            self.monitorStarted = True
        else:
            dialogBox = wx.MessageDialog(self, "Not all needed values have been entered",
                                         caption="", style=wx.ICON_ERROR)
            dialogBox.ShowModal()
            dialogBox.Destroy()
            
        return
    
    def PauseMonitor(self):
        print "%s Pausing Monitor" % time.asctime(time.localtime())
        self.updater.Stop()
        self.timer.Stop()
        self.pvStatusTxtCtrl.SetValue("Monitor Ready")
        self.pvStatusTxtCtrl.SetForegroundColour(wx.BLUE)
        self.monitorStarted = False
        return
    
    def OnStopButtonClick(self, event):
        print "%s Stopping monitor" % time.asctime(time.localtime())
        self.updater.Stop()
        self.timer.Stop()
        self.pvStatusTxtCtrl.SetValue("Monitor Stopped")
        self.pvStatusTxtCtrl.SetForegroundColour(wx.RED)
        self.monitorStarted = False
        return
    
    def OnTimerExpired(self, event):
        try:
            resets = self.timer.GetNumberOfResets()
            maxResets = int(self.resetsTxtCtrl.GetValue())
            
            print "Detector reset %d times" % resets
                        
            if (resets >= maxResets):
                print "Number of resets exceeded max"
                emailer = EmailSender(self.emailAddressList)
                emailer.SendEmail(self.senderTxtCtrl.GetValue(), "Scan problem",
                                  "The detector was reset too many times.  It requires user intervention", False)
                self.OnStopButtonClick(wx.EVT_IDLE)

        except:
            return
                
        return 

########################################################################
class CollectiveGUIPanel(wx.Panel):
    """
    """
    #----------------------------------------------------------------------
    def __init__(self, parent, emailAddressList):
        """
        """
 
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
 
        self.emailAddressList = emailAddressList           # This is a list of email addresses
 
        self.emailSectionPanel = DynamicTextControlPanel(self, "Email Address", emailAddressList)
        self.statusPanel = StatusPanel(emailAddressList, self)
        
        #!self.sectionList = [self.emailSectionPanel]    # This is a list of panels that each contain an email address.
                        
        self.sectionSizer = wx.BoxSizer(wx.VERTICAL)
        self.sectionSizer.Add(self.emailSectionPanel, 0, wx.EXPAND)
        
        self.panelSizer = wx.BoxSizer(wx.VERTICAL)
        self.panelSizer.Add(self.statusPanel, 0, wx.EXPAND)
        self.panelSizer.Add(self.sectionSizer, 0, wx.EXPAND)
 
        self.SetSizer(self.panelSizer)
        self.Layout()
        self.Fit()
        
        return
    
    def OnCloseButtonClick(self,event):
        parent = self.GetParent()
        parent.OnCloseButtonClick(event)
        return
            
    def Redraw(self):
        parent = self.GetParent()
        parent.Redraw()
        
########################################################################

class MainFrame(wx.Frame):
    '''
    classdocs
    '''

    def __init__(self, parent, title):
        '''
        Constructor
        '''
        wx.Frame.__init__(self, parent, title=title, pos=(200,200), size=(600,600))
        
        self.emailAddressList = []
        
        mainPanel = CollectiveGUIPanel(self, self.emailAddressList)
        
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        
        self.frameSizer = wx.BoxSizer(wx.VERTICAL)
        
        self.frameSizer.Add(mainPanel, 0, wx.EXPAND)
        
        self.SetSizer(self.frameSizer)
        self.SetAutoLayout(True)
        self.frameSizer.Fit(self)

        self.Layout()
        
        return
    
    def Redraw(self):
        self.frameSizer.Layout()
        self.frameSizer.Fit(self)
        return
    
    def OnCloseButtonClick(self, event):
        self.Close(True)

    def OnCloseWindow(self, event):
        self.Destroy()
        
