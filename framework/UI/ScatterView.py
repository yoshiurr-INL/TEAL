#!/usr/bin/env python

from PySide import QtCore as qtc
from PySide import QtGui as qtg

from BaseView import BaseView

from mpl_toolkits.mplot3d import Axes3D
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import mpl_toolkits
import matplotlib.pyplot
import matplotlib.ticker


import numpy as np
import colors

class ScatterView(BaseView):
  """
    A view widget for visualizing scatterplots of data utilizing matplotlib.
  """
  def __init__(self, mainWindow=None):
    """
      Constructor for the Scatter plot view
      @ In, mainWindow, MainWindow, the main window associated to this dependent
        view
    """
    BaseView.__init__(self, mainWindow)

    self.setLayout(qtg.QVBoxLayout())
    layout = self.layout()
    self.clearLayout(layout)

    mySplitter = qtg.QSplitter()
    mySplitter.setOrientation(qtc.Qt.Vertical)
    layout.addWidget(mySplitter)

    self.fig = Figure(facecolor='white')
    self.mplCanvas = FigureCanvas(self.fig)
    self.mplCanvas.axes = self.fig.add_subplot(111)

    # We want the axes cleared every time plot() is called
    self.mplCanvas.axes.hold(False)
    self.colorbar = None

    mySplitter.addWidget(self.mplCanvas)

    controls = qtg.QGroupBox()
    controls.setLayout(qtg.QGridLayout())
    subLayout = controls.layout()
    row = 0
    col = 0

    self.rightClickMenu = qtg.QMenu()
    self.axesLabelAction = self.rightClickMenu.addAction('Show Axis Labels')
    self.axesLabelAction.setCheckable(True)
    self.axesLabelAction.setChecked(True)
    self.axesLabelAction.triggered.connect(self.updateScene)

    self.cmbVars = {}

    for i,name in enumerate(['X','Y','Z','Color']):
      varLabel = name + ' variable:'
      self.cmbVars[name] = qtg.QComboBox()

      if name == 'Z':
        self.cmbVars[name].addItem('Off')
      elif name == 'Color':
        self.cmbVars[name].addItem('Cluster')

      dimNames = self.mainWindow.getDimensions()
      self.cmbVars[name].addItems(dimNames)

      if i < len(dimNames):
        self.cmbVars[name].setCurrentIndex(i)
      else:
        self.cmbVars[name].setCurrentIndex(len(dimNames)-1)

      self.cmbVars[name].currentIndexChanged.connect(self.updateScene)

      subLayout.addWidget(qtg.QLabel(varLabel),row,col)
      col += 1
      subLayout.addWidget(self.cmbVars[name],row,col)
      row += 1
      col = 0

    self.lblColorMaps = qtg.QLabel('Colormap')
    self.cmbColorMaps = qtg.QComboBox()
    self.cmbColorMaps.addItems(matplotlib.pyplot.colormaps())
    self.cmbColorMaps.setCurrentIndex(self.cmbColorMaps.findText('coolwarm'))
    self.cmbColorMaps.currentIndexChanged.connect(self.updateScene)
    subLayout.addWidget(self.lblColorMaps,row,col)
    col += 1
    subLayout.addWidget(self.cmbColorMaps,row,col)
    mySplitter.addWidget(controls)

    self.cmbVars['Z'].setCurrentIndex(0)
    self.updateScene()

  def sizeHint(self):
    """
      This property holds the recommended size for the widget. If the value of
      this property is an invalid size, no size is recommended. The default
      implementation of PySide.QtGui.QWidget.sizeHint() returns an invalid
      size if there is no layout for this widget, and returns the layout's
      preferred size otherwise. (Copied from base class text)
      @ In, None
      @ Out, QSize, the recommended size of this widget
    """
    return qtc.QSize(300,600)

  def selectionChanged(self):
    """
      An event handler triggered when the user changes the selection of the
      data.
      @ In, None
      @ Out, None
    """
    self.updateScene()

  def updateScene(self):
    """
      A method for drawing the scene of this view.
      @ In, None
      @ Out, None
    """
    fontSize=16
    smallFontSize=12
    rows = self.mainWindow.getSelectedIndices()
    names = self.mainWindow.getDimensions()
    data = self.mainWindow.getData()

    # self.fig = Figure(facecolor='white')
    # self.mplCanvas = FigureCanvas(self.fig)

    self.fig.clear()

    if self.cmbVars['Z'].currentIndex() == 0:
      dimensionality = 2
      self.mplCanvas.axes = self.fig.add_subplot(111)
    else:
      dimensionality = 3
      self.mplCanvas.axes = self.fig.add_subplot(111, projection='3d')

    # We want the axes cleared every time plot() is called
    self.mplCanvas.axes.hold(False)

    myColormap = colors.cm.get_cmap(self.cmbColorMaps.currentText())

    if len(rows) == 0:
      rows = list(xrange(data.shape[0]))

    allValues = {}
    values = {}
    mins = {}
    maxs = {}

    specialColorKeywords = ['Cluster']

    for key,cmb in self.cmbVars.iteritems():
      if dimensionality == 2 and key == 'Z':
        continue
      if cmb.currentText() == 'Cluster':
        labels = self.mainWindow.getLabels()
        allValues[key] = np.array([self.mainWindow.getColor(label).name() for label in labels], dtype='|S7')
        values[key] = allValues[key][rows]
        self.lblColorMaps.setEnabled(False)
        self.cmbColorMaps.setEnabled(False)
        self.lblColorMaps.setVisible(False)
        self.cmbColorMaps.setVisible(False)
      else:
        col = names.index(cmb.currentText())
        allValues[key] = data[:,col]
        mins[key] = min(allValues[key])
        maxs[key] = max(allValues[key])
        values[key] = allValues[key][rows]
        self.lblColorMaps.setEnabled(True)
        self.cmbColorMaps.setEnabled(True)
        self.lblColorMaps.setVisible(True)
        self.cmbColorMaps.setVisible(True)

      self.mplCanvas.axes.hold(True)

    kwargs = {'edgecolors': 'none', 'c': values['Color']}

    if dimensionality == 2:
      kwargs['x'] = values['X']
      kwargs['y'] = values['Y']
    else:
      kwargs['xs'] = values['X']
      kwargs['ys'] = values['Y']
      kwargs['zs'] = values['Z']

    if self.cmbVars['Color'].currentText() not in specialColorKeywords:
      kwargs['c'] = values['Color']
      kwargs['cmap'] = myColormap
      kwargs['vmin'] = mins['Color']
      kwargs['vmax'] = maxs['Color']

    myPlot = self.mplCanvas.axes.scatter(**kwargs)
    self.mplCanvas.axes.hold(True)

    if self.axesLabelAction.isChecked():
      self.mplCanvas.axes.set_xlabel(self.cmbVars['X'].currentText(),size=fontSize,labelpad=10)
      self.mplCanvas.axes.set_ylabel(self.cmbVars['Y'].currentText(),size=fontSize,labelpad=10)
      if dimensionality == 3:
        self.mplCanvas.axes.set_zlabel(self.cmbVars['Z'].currentText(),size=fontSize,labelpad=10)

    ticks = np.linspace(mins['X'],maxs['X'],5)
    self.mplCanvas.axes.set_xticks(ticks)
    self.mplCanvas.axes.set_xlim([ticks[0],ticks[-1]])
    self.mplCanvas.axes.xaxis.set_ticklabels([])
    self.mplCanvas.axes.yaxis.set_ticklabels([])
    self.mplCanvas.axes.xaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter('%.2g'))

    ticks = np.linspace(mins['Y'],maxs['Y'],5)
    self.mplCanvas.axes.set_yticks(ticks)
    self.mplCanvas.axes.set_ylim([ticks[0],ticks[-1]])
    self.mplCanvas.axes.yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter('%.2g'))

    if dimensionality == 3:
      ticks = np.linspace(mins['Z'],maxs['Z'],3)
      self.mplCanvas.axes.set_zticks(ticks)
      self.mplCanvas.axes.set_zlim([ticks[0],ticks[-1]])
      self.mplCanvas.axes.zaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter('%.2g'))

    for label in  (self.mplCanvas.axes.get_xticklabels()+self.mplCanvas.axes.get_yticklabels()):
      label.set_fontsize(smallFontSize)

    self.mplCanvas.axes.hold(False)
    self.mplCanvas.draw()
