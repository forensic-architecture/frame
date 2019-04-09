import sys

import pkg_resources
import os.path
import schedule
import time
import yaml
import logging
import argparse

from PyQt5.QtCore import Qt, QUrl, QRect, QTimer
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QAction, QApplication, QDesktopWidget, QDialog, QFileDialog,
                             QHBoxLayout, QLabel, QMainWindow, QToolBar, QVBoxLayout, QWidget, QPushButton)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaPlaylist, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget

def string_to_job(schedule_str):
    schedule_str = 'schedule.' + str(schedule_str) + '.do(lambda t: print())'
    try:
        return eval(schedule_str)
    except Exception:
        import traceback
        logging.error('Error while evaluating schedule string: ' + schedule_str)
        logging.error(traceback.format_exc())
        return None

class Event:
    def __init__(self, settings):
        self.running = False
        self.name = settings.get('name')
        self.tags = settings.get('tags', [])
        self.type = settings.get('type')
        self.job = string_to_job(settings.get('schedule'))
        self.cancel_on_error = settings.get('cancel_on_error', False)

        if self.tags:
            self.job.tags(*self.tags)
    
    def start(self):
        if self.running:
            self.stop()

        self.running = True
        self.on_start()
        self.job.do(self.safe_run)

    def stop(self):
        self.on_stop()

    def cancel(self):
        schedule.cancel_job(self.job)
        self.running = False
        self.on_cancel()

    def safe_run(self):
        logging.debug("Running task %s" % (self.name))
        try:
            return self.run()
        except:
            import traceback
            logging.error(traceback.format_exc())
            if self.cancel_on_error:
                self.cancel()

    def run(self):
        pass

class PlayVideo(Event):
    def __init__(self, parent, settings):
        super().__init__(settings)

        self.url = QUrl(settings.get('url'))
        self.start_time = settings.get('start', 0)
        self.end_time = settings.get('end')
        self.loop = settings.get('loop', True)
        self.fullscreen = settings.get('fullscreen', True)
        self.geometry = settings.get('geometry', [0, 0, 100, 100])
        self.volume = settings.get('volume', 100)
        self.playbackRate = settings.get('playbackRate', 1.0)

        if (self.geometry):
            self.geometry = QRect(self.geometry[0], self.geometry[1], self.geometry[2], self.geometry[3])

        self.video = QVideoWidget(parent)

        self.media = QMediaContent(self.url)
        self.playlist = QMediaPlaylist(self.video)
        self.playlist.addMedia(self.media)
        self.playlist.setPlaybackMode(QMediaPlaylist.Loop if self.loop else QMediaPlaylist.Sequential)

        self.player = QMediaPlayer()
        self.player.setVideoOutput(self.video)
        self.player.setVolume(self.volume)
        self.player.setPlaybackRate(self.playbackRate)
    
    def on_start(self):
        pass

    def on_stop(self):
        self.video.hide()
        self.player.stop()

    def run(self):
        self.video.move(self.geometry.left(), self.geometry.top())
        self.video.resize(self.geometry.width(), self.geometry.height())

        if self.fullscreen:
            self.video.setFullScreen(True)

        self.player.setPlaylist(self.playlist)
        self.player.setPosition(self.start_time)
        self.video.show()
        self.player.play()

def create_event(parent, settings):
    event_types = {
        'PlayVideo': PlayVideo
    }
    logging.info("Creating an event: " + str(settings))
    event_class = event_types.get(settings.get('type'))
    event = event_class(parent, settings)
    event.start()
    return event

    
class frame(QMainWindow):
    """Create the main window that stores all of the widgets necessary for the application."""

    def __init__(self, args):
        """Initialize the components of the main window."""
        super(frame, self).__init__(None)
        self.resize(1024, 768)
        self.setWindowTitle('Event Manager')
        window_icon = pkg_resources.resource_filename('frame.images',
                                                      'ic_insert_drive_file_black_48dp_1x.png')
        self.setWindowIcon(QIcon(window_icon))

        self.menu_bar = self.menuBar()
        self.file_menu()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(1000)

        self.events = []
        self.load_events(args.settings_yaml)

        for e in self.events:
            e.start()

    def load_events(self, path):
        settings_file = open(path, 'r')

        try:
            from yaml import Loader, Dumper
            import yaml
            self.settings = yaml.load(settings_file, Loader=Loader)
            logging.info("Loaded settings: " + str(self.settings))
        except ImportError:
            import traceback
            logging.error(traceback.format_exc())
            return

        events = self.settings.get('events')
        for name, event in events.items():
            event['name'] = name
            self.events.append(
                create_event(self, event)
            )

    def tick(self):
        logging.info("Tick")
        schedule.run_pending()

    def stop_all(self):
        for e in self.events:
            e.cancel()
    
    def file_menu(self):
        """Create a file submenu with an Open File item that opens a file dialog."""
        self.file_sub_menu = self.menu_bar.addMenu('File')

        self.play_action = QAction("Stop All", self)
        self.play_action.triggered.connect(self.stop_all)

        self.exit_action = QAction('Exit Application', self)
        self.exit_action.setStatusTip('Exit the application.')
        self.exit_action.setShortcut('CTRL+Q')
        self.exit_action.triggered.connect(lambda: QApplication.quit())

        self.file_sub_menu.addAction(self.exit_action)
        self.file_sub_menu.addAction(self.play_action)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    sys.exit(app.exec_())

def main():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('settings_yaml', help='Path to a yaml file with settings')
    args = parser.parse_args()

    logging.root.setLevel(logging.DEBUG)

    application = QApplication(sys.argv)

    window = frame(args)
    window.move(200, 200)
    window.show()
    


    sys.exit(application.exec_())
