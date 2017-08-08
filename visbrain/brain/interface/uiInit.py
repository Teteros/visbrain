"""This script group the diffrent graphical components.

Grouped components :
    * PyQt elements (window, Pyqt functions...)
    * Vispy canvas functions
    * User shortcuts
"""

from PyQt5 import QtWidgets

from vispy import app, scene
import vispy.scene.visuals as visu
import vispy.visuals.transforms as vist

from .gui import Ui_MainWindow
from ...utils import color2vb

__all__ = ('uiInit')


class vbShortcuts(object):
    """This class add some shortcuts to the main canvas of Brain.

    It's also use to initialize to panel of shortcuts.

    Args:
        canvas: vispy canvas
            Vispy canvas to add the shortcuts.
    """

    def __init__(self, canvas):
        """Init."""
        self.sh = [('<space>', 'Brain transparency'),
                   ('0', 'Top view'),
                   ('1', 'Bottom view'),
                   ('2', 'Left view'),
                   ('3', 'Right view'),
                   ('4', 'Front view'),
                   ('5', 'Back view'),
                   ('b', 'Display / hide brain'),
                   ('s', 'Display / hide sources'),
                   ('t', 'Display / hide connectivity'),
                   ('r', 'Display / hide ROI'),
                   ('c', 'Display / hide colorbar'),
                   ('a', 'Auto-scale the colormap'),
                   ('+', 'Increase brain opacity'),
                   ('-', 'Decrease brain opacity'),
                   ('CTRL + p', 'Run the cortical projection'),
                   ('CTRL + r', 'Run the cortical repartition'),
                   ('CTRL + d', 'Display / hide setting panel'),
                   ('CTRL + e', 'Show the documentation'),
                   ('CTRL + t', 'Display shortcuts'),
                   ('CTRL + n', 'Take a screenshot'),
                   ('CTRL + q', 'Exit'),
                   ]

        # Add shortcuts to vbCanvas :
        @canvas.events.key_press.connect
        def on_key_press(event):
            """Executed function when a key is pressed on a keyboard over Brain canvas.

            :event: the trigger event
            """
            # Internal / external view :
            if event.text == ' ':
                viz = self._brainTransp.isChecked()
                self._brainTransp.setChecked(not viz)
                self._light_reflection()
                self._light_Atlas2Ui()

            # Increase / decrease brain opacity :
            elif event.text in ['+', '-']:
                # Get slider value :
                sl = self.OpacitySlider.value()
                step = 10 if (event.text == '+') else -10
                self.OpacitySlider.setValue(sl + step)
                self._fcn_opacity()
                self._light_Atlas2Ui()

                # Colormap :
            elif event.text == 'a':
                self.cbqt._fcn_cbAutoscale()

        @canvas.events.mouse_release.connect
        def on_mouse_release(event):
            """Executed function when the mouse is pressed over Brain canvas.

            :event: the trigger event
            """
            # Hide the rotation panel :
            self.userRotationPanel.setVisible(False)

        @canvas.events.mouse_double_click.connect
        def on_mouse_double_click(event):
            """Executed function when double click mouse over Brain canvas.

            :event: the trigger event
            """
            pass

        @canvas.events.mouse_move.connect
        def on_mouse_move(event):
            """Executed function when the mouse move over Brain canvas.

            :event: the trigger event
            """
            if self.view.wc.camera.name == 'turntable':
                # Display the rotation panel and set informations :
                self._fcn_userRotation()

        @canvas.events.mouse_press.connect
        def on_mouse_press(event):
            """Executed function when single click mouse over Brain canvas.

            :event: the trigger event
            """
            if self.view.wc.camera.name == 'turntable':
                # Display the rotation panel :
                self._fcn_userRotation()
                self.userRotationPanel.setVisible(True)


class vbCanvas(object):
    """This class is responsible of cannvas creation.

    The main canvas in which the brain is displayed.

    Kargs:
        bgcolor: tuple, optional, (def: (0, 0, 0))
            Set the background color for both canvas (main canvas in
            which the brain is displayed and the canvas for the colorbar)
    """

    def __init__(self, title='', bgcolor=(0, 0, 0)):
        """Init."""
        # Initialize main canvas:
        self.canvas = scene.SceneCanvas(keys='interactive', show=False,
                                        dpi=600, bgcolor=bgcolor,
                                        fullscreen=True, resizable=True,
                                        title=title)
        self.wc = self.canvas.central_widget.add_view()
        # Visualization settings. The min/maxOpacity attributes are defined
        # because it seems that OpenGL have trouble with small opacity (usually
        # between 0 and 1). Defining min and max far away from 0 / 1 solve this
        # problem.
        self.minOpacity = -10000
        self.maxOpacity = 10000


class uiInit(QtWidgets.QMainWindow, Ui_MainWindow, app.Canvas, vbShortcuts):
    """Group and initialize the graphical elements and interactions.

    Kargs:
        bgcolor: tuple, optional, (def: (0.1, 0.1, 0.1))
            Background color of the main window. The same background
            will be used for the colorbar panel so that future figures
            can be uniform.
    """

    def __init__(self, bgcolor=(0.1, 0.1, 0.1)):
        """Init."""
        # Create the main window :
        super(uiInit, self).__init__(None)
        self.setupUi(self)
        if self._savename is not None:
            self.setWindowTitle('Brain - ' + self._savename)

        #######################################################################
        #                            BRAIN CANVAS
        #######################################################################
        self.view = vbCanvas('MainCanvas', bgcolor)
        self.vBrain.addWidget(self.view.canvas.native)

        #######################################################################
        #                         CROSS-SECTIONS CANVAS
        #######################################################################
        # Create one canvas per view and respectively attach to layout :
        self._csView = [vbCanvas('AxialCanvas', bgcolor),
                        vbCanvas('CoronalCanvas', bgcolor),
                        vbCanvas('SagittalCanvas', bgcolor)]
        self._axialLayout.addWidget(self._csView[0].canvas.native)
        self._coronLayout.addWidget(self._csView[1].canvas.native)
        self._sagitLayout.addWidget(self._csView[2].canvas.native)
        # Create one node per view :
        self._csNode = [scene.Node(name='AxialNode'),
                        scene.Node(name='CoronalNode'),
                        scene.Node(name='SagittalNode')]
        self._csNode[0].parent = self._csView[0].wc.scene
        self._csNode[1].parent = self._csView[1].wc.scene
        self._csNode[2].parent = self._csView[2].wc.scene
        # Add one image per node :
        self._csImg = [visu.Image(name='AxialSplit', parent=self._csNode[0]),
                       visu.Image(name='CoronalSplit', parent=self._csNode[1]),
                       visu.Image(name='SagittalSplit', parent=self._csNode[2])
                       ]
        # Add one PanZoom camera per canvas :
        self._csView[0].wc.camera = 'panzoom'
        self._csView[1].wc.camera = 'panzoom'
        self._csView[2].wc.camera = 'panzoom'
        # Finally add transformations to each node :
        r90 = vist.MatrixTransform()
        r90.rotate(90, (0, 0, 1))
        r180 = vist.MatrixTransform()
        r180.rotate(180, (0, 0, 1))
        self._csImg[0].transform = r180
        self._csImg[1].transform = r90
        self._csImg[2].transform = r90

        # Set background color and hide quick settings panel :
        self.bgcolor = tuple(color2vb(color=bgcolor, length=1)[0, 0:3])

        # Set background elements :
        self.bgd_red.setValue(self.bgcolor[0])
        self.bgd_green.setValue(self.bgcolor[1])
        self.bgd_blue.setValue(self.bgcolor[2])

        # Initialize shortcuts :
        vbShortcuts.__init__(self, self.view.canvas)
