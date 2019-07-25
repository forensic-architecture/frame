import pytest
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from ..frame import load_events


@pytest.fixture
def qapp(qtbot):
    """Pass the application to the test functions via a pytest fixture."""
    qapp = QApplication(sys.argv)
    qapp.setOverrideCursor(Qt.BlankCursor)
    # events = []
    # load_events("./settings.yaml", events)
    return qapp
