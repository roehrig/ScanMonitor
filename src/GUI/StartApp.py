'''
Created on Jun 10, 2013

@author: roehrig
'''

import sys
import os

filePath = os.path.split(__file__)
sys.path.append(filePath[0] + '/..')
sys.path.append(filePath[0] + '/../../../GenericClasses/src')

import wx
import MainWindow

class MyApp(wx.App):
    def __init__(self, redirect=False, filename=None, useBestVisual=False, clearSigInt=False):
        wx.App.__init__(self, redirect, filename, useBestVisual, clearSigInt)
        
    def OnInit(self):
        startWindow = MainWindow.MainFrame(None, "Scan Monitor")
        startWindow.Show(True)
        return True

app = MyApp(False)
app.MainLoop()