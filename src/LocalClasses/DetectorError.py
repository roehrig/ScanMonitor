'''
Created on Jun 10, 2013

@author: roehrig
'''

import time
import epics
from epics import PV
from Utils.EmailSender import EmailSender
from epics.wx import DelayedEpicsCallback
from epics.wx import EpicsFunction

class DetectorErrorHandler(object):
    '''
    classdocs
    '''
    def __init__(self, email_list):
        '''
        Constructor
        '''
        self._detectorPrefix = ""
        self._innerScan = ""
        self._outerScan = ""
        self._sender = ""
        self._subject = ""
        self._file_name = ""
        self._mcs_prefix = ""
        self._savedata_prefix = ""
        self._fileCapturePV = None
        self._fileWritePV = None
        self._stopDetectorPV = None
        self._collectModePV = None
        self._scanWaitPV = None
        self._xmapPixelPV = None
        self._mcsPixelPV = None
        self._scalerResetPV = None
        self._usIonChamberPV = None
        self._dsIonChamberPV = None
        self._innerScanCurrentPointPV = None
        self._innerScanNumberPointsPV = None
        self._outerScanCurrentPointPV = None
        self._outerScanNumberPointsPV = None
        self._saveDataMessagePV = None
        self._ringCurrentPV = None
        self._emailList = email_list
        self._mailer = EmailSender(self._emailList)
        
        self._resettingDetector = 0
        self._xmapCurrentPixel = 0
        self._mcsCurrentPixel = 0
        
        return
        
    def SetDetectorPVs(self, detector_prefix, inner_scan, outer_scan, sender, subject, file_name, mcs_prefix,
                       savedata_prefix, us_ic, ds_ic):
        '''
        Create the PV objects that are used to correct the
        problem with the detector
        '''
        self._detectorPrefix = detector_prefix
        self._innerScan = inner_scan
        self._outerScan = outer_scan
        self._sender = sender
        self._subject = subject
        self._file_name = file_name
        self._mcs_prefix = mcs_prefix
        self._savedata_prefix = savedata_prefix
        
        self._scanWaitPV = PV(self._outerScan + '.WAIT')
        self._usIonChamberPV = PV(us_ic)
        self._dsIonChamberPV = PV(ds_ic)
        self._innerScanCurrentPointPV = PV(self._innerScan + '.CPT')
        self._innerScanNumberPointsPV = PV(self._innerScan + '.NPTS')
        self._outerScanCurrentPointPV = PV(self._outerScan + '.CPT')
        self._outerScanNumberPointsPV = PV(self._outerScan + '.NPTS')
        self._saveDataMessagePV = PV(self._savedata_prefix + "saveData_message")
        self._ringCurrentPV = PV("S:SRcurrentAI")
        self._fileCapturePV = PV(self._detectorPrefix + 'netCDF1:Capture.VAL')
        self._fileWritePV = PV(self._detectorPrefix + 'netCDF1:WriteFile.VAL')
        self._stopDetectorPV = PV(self._detectorPrefix + 'StopAll')
        self._collectModePV = PV(self._detectorPrefix + 'CollectMode')
        self._xmapPixelPV = PV(self._detectorPrefix + "dxp1:CurrentPixel")
        self._mcsPixelPV = PV(self._mcs_prefix + "CurrentChannel")
        self._scalerResetPV = PV(self._mcs_prefix + "StopAll")
        
        return        

    @DelayedEpicsCallback
    def ReportConnectionStatus(self, *args, **kwargs):

        # Initialize some variables
        pvName = kwargs['pvname']  # This is the name of the PV that is running the callback
        pvConnection = kwargs['conn']  # This is the connection status of the PV that is running the callback

        print "%s connection state is %s" % (pvName, pvConnection)
         
        return 
    
    @EpicsFunction
    def ResetDetector(self):
        self._resettingDetector = 1

        self._xmapCurrentPixel = self._xmapPixelPV.get(use_monitor=False)
        self._mcsCurrentPixel = self._mcsPixelPV.get(use_monitor=False)
        
        # Pause the scan.
        print "Pausing scan"
        self._scanWaitPV.put(1, False)
        time.sleep(1)
        # Reset the detector's file plugin and data acquisition
        #print "Stopping file save."
        #self._fileWritePV.put('Done', True, 5)
        print "Stopping data acquisition."
        self._stopDetectorPV.put(1, False)
        print "Stopping data acquisition."
        self._stopDetectorPV.put(1, False)
        print "Stopping data acquisition."
        self._stopDetectorPV.put(1, False)
        time.sleep(1)
        print "Stopping file capture."
        self._fileCapturePV.put(0, False)
        time.sleep(1)
        print "Setting MCS spectra mode."
        self._collectModePV.put(0, False)
        time.sleep(5)
        print "Setting MCA mapping mode."
        self._collectModePV.put(1, False)
        time.sleep(5)

        self._scalerResetPV.put(1,False)

        # Unpause the scan
        print "Resuming scan."
        self._scanWaitPV.put(0, False)

        ret_val = self.WriteStatus(reset=True)
         
        return ret_val

    @EpicsFunction
    def TestResetDetector(self):
        self._resettingDetector = 1
        
        # Pause the scan.
        print "Pausing scan"
        self._scanWaitPV.put(1, False)
        time.sleep(1)
        # Reset the detector's file plugin and data acquisition
        print "Stopping data acquisition."
        self._stopDetectorPV.put(1, False)
        print "Stopping data acquisition."
        self._stopDetectorPV.put(1, False)
        print "Stopping data acquisition."
        self._stopDetectorPV.put(1, False)
        time.sleep(1)
        print "Stopping file capture."
        self._fileCapturePV.put(0, False)
        time.sleep(1)
        print "Setting MCS spectra mode."
        self._collectModePV.put(0, False)
        time.sleep(5)
        print "Setting MCA mapping mode."
        self._collectModePV.put(1, False)
        time.sleep(5)
	
        # Unpause the scan
        print "Resuming scan."
        self._scanWaitPV.put(0, False)
        ret_val = 1
         
        return ret_val
	   
    def WriteStatus(self, reset=False):
        '''
        reset - Is this happening because the detectors was reset?
        '''
        try:
            fileHandle = open(self._file_name, 'w+')
            
            currentLine = int(self._outerScanCurrentPointPV.get(use_monitor=False))
            totalLines = int(self._outerScanNumberPointsPV.get(use_monitor=False))
            
            if reset:
                fileHandle.write("Scan error, attempting to reset detector.\n")
            else:
                self._xmapCurrentPixel = self._xmapPixelPV.get(use_monitor=False)
                self._mcsCurrentPixel = self._mcsPixelPV.get(use_monitor=False)
                if (currentLine == totalLines):
                    fileHandle.write("The scan reports that the scan is complete.\n")

            fileHandle.write("Experiment status at time %s \n" % time.strftime("%d %B %Y  %H:%M:%S", time.localtime()))
            fileHandle.write("Synchrotron current: %s \n" % self._ringCurrentPV.get(as_string=True))
            fileHandle.write("Upstream ion chamber reading: %s \n" % self._usIonChamberPV.get(as_string=True))
            fileHandle.write("Downstream ion chamber reading: %s \n" % self._dsIonChamberPV.get(as_string=True))
            fileHandle.write("SaveData message: %s \n" % self._saveDataMessagePV.get(as_string=True))
            fileHandle.write("Current point: %s \n" % self._innerScanCurrentPointPV.get(as_string=True))
            fileHandle.write("Current line: %s \n" % self._outerScanCurrentPointPV.get(as_string=True, use_monitor=False))
            fileHandle.write("Total number of pixels per line: %s \n" % self._innerScanNumberPointsPV.get(as_string=True))
            fileHandle.write("Total number of lines in the scan: %s \n" % self._outerScanNumberPointsPV.get(as_string=True))
            fileHandle.write("Current pixel of MCS: %d\n" % self._mcsCurrentPixel)
            fileHandle.write("Current pixel of XMAP: %d\n" % self._xmapCurrentPixel)
            
            fileHandle.close()
             
            if reset:
                self._mailer.SendEmail(self._sender, "Possible scan error", "",True, self._file_name)
            else:
                if (currentLine == totalLines):
                    self._mailer.SendEmail(self._sender, "Scan record reports completed scan", "", True, self._file_name)
                else:
                    self._mailer.SendEmail(self._sender, self._subject, "", True, self._file_name)
            
            return 1
        except IOError as e:
            for arg in e.args:
                print arg
            return -1
        
    def IsDetectorReset (self):
        return self._resettingDetector
    
    def SetResettingDetector(self, newVal):
        self._resettingDetector = newVal
        return
