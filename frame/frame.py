import sys

import pkg_resources
import os.path
import schedule
import time
import yaml
import logging, logging.handlers
import argparse
import server

from queue import Queue

from PyQt5.QtCore import Qt, QUrl, QRect, QTimer
from PyQt5.QtGui import QIcon, QColor, QPalette
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QDesktopWidget,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QToolBar,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QStackedWidget,
)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaPlaylist, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget

app_logging = logging.getLogger("frame")
event_logging = logging.getLogger("frame.event")


def string_to_job(schedule_str):
    schedule_str = "schedule." + str(schedule_str) + ""
    try:
        return eval(schedule_str)
    except Exception:
        import traceback

        logging.error("Error while evaluating schedule string: " + schedule_str)
        logging.error(traceback.format_exc())
        return None


class Event:
    def __init__(self, settings):
        self.__init_logging__(settings)

        self.name = settings.get("name")
        self.logging.debug(("Creating event %s: " % self.name) + str(settings))

        self.tags = settings.get("tags", [])
        self.type = settings.get("type")
        self.schedule_string = settings.get("schedule")
        self.job = string_to_job(settings.get("schedule"))
        self.cancel_on_error = settings.get("cancel_on_error", False)

        if self.job:
            if self.tags:
                self.job.tags(*self.tags)
            self.job.do(self.run)

        self.__state = "uninitialized"

    def __init_logging__(self, settings):
        self.logging = logging.getLogger("frame.event.%s" % str(settings.get("name")))

    def protect(self, func, *args, **kwargs):
        try:
            self.logging.debug(
                "Running '%s.%s()'" % (self.__class__.__name__, func.__name__)
            )
            func()
            return True
        except Exception:
            import traceback

            self.logging.error(traceback.format_exc())
            if self.cancel_on_error:
                self.cancel()
            return False

    @property
    def state(self):
        return self.__state

    @state.setter
    def state(self, value):
        if self.__state != value:
            self.logging.debug("Changed from %s -> %s" % (self.__state, value))
            self.__state = value

    def initialize(self):
        if self.state == "uninitialized":
            if self.protect(self.do_initialize):
                self.state = "initialized"
        elif self.state == "playing":
            self.stop()

    def run(self):
        if self.state == "uninitialized":
            self.initialize()
        if self.state == "running":
            self.stop()
        if self.state == "initialized":
            if self.protect(self.do_run):
                self.state = "running"

    def stop(self):
        if self.state == "running":
            if self.protect(self.do_stop):
                self.state = "initialized"

    def reset(self):
        self.stop()
        if self.protect(self.do_reset):
            self.state = "uninitialized"

    def cancel(self):
        self.reset()
        self.state = "cancelled"

    def tick(self):
        if self.state == "running":
            self.do_tick()

    def do_initialize(self):
        pass

    def do_run(self):
        pass

    def do_stop(self):
        pass

    def do_reset(self):
        pass

    def do_tick(self):
        pass


class DisplayEvent(Event):
    def __init__(self, frame, settings):
        super().__init__(settings)
        self.frame = frame
        self.widget = frame.create_widget()
        self.widget.setLayout(QVBoxLayout())
        self.widget.layout().setContentsMargins(0, 0, 0, 0)
        self.widget.layout().setSpacing(0)

        self.fullscreen = settings.get("fullscreen", True)
        self.geometry = settings.get("geometry")

        if self.geometry:
            self.geometry = QRect(
                self.geometry[0], self.geometry[1], self.geometry[2], self.geometry[3]
            )

    def add_widget(self, widget):
        if self.geometry:
            widget.setParent(self.widget)
            widget.setGeometry(self.geometry)
        else:
            self.widget.layout().addWidget(widget)

    def do_run(self):
        self.widget.show()
        self.frame.push(self.widget)

    def do_stop(self):
        self.frame.pop(self.widget)

    def tick(self):
        super().tick()
        if self.state == "running":
            cur_widget = self.frame.currentWidget()
            if cur_widget is not self.widget:
                self.stop()


class Frame(QStackedWidget):
    def __init__(self, parent, settings):
        super().__init__(parent)
        self.null = QWidget()
        self.stack = [self.null]
        self.addWidget(self.null)

        self.setAutoFillBackground(True)
        self.background_color = settings.get("background_color", [0.0, 0.0, 0.0])
        self.background_color = QColor(
            self.background_color[0] * 255,
            self.background_color[1] * 255,
            self.background_color[2] * 255,
            255,
        )
        self.set_background_color(self.background_color)

        self.set_current()
        self.showFullScreen()

    def set_background_color(self, color):
        palette = self.palette()
        palette.setColor(QPalette.Background, self.background_color)
        self.setPalette(palette)

    def create_widget(self):
        widget = QWidget()
        self.addWidget(widget)
        return widget

    def push(self, widget):
        self.stack.append(widget)
        self.set_current()

    def pop(self, widget):
        try:
            self.stack.remove(widget)
        except Exception:
            pass
        self.set_current()

    def set_current(self):
        self.setCurrentWidget(self.stack[-1])


class PlayVideo(DisplayEvent):
    def __init__(self, frame, settings):
        super().__init__(frame, settings)

        self.url = QUrl(settings.get("url"))
        self.start_time = settings.get("start", 0) * 1000
        self.duration = settings.get("duration")
        self.loop = settings.get("loop", True)
        self.volume = settings.get("volume", 100)
        self.playback_rate = settings.get("playbackRate", 1.0)

    def do_tick(self):
        if self.player:
            self.logging.info(
                "position: %s/%s status: %s error: %s"
                % (
                    self.player.position(),
                    self.player.duration(),
                    self.player.mediaStatus(),
                    self.player.errorString(),
                )
            )
            if self.player.errorString():
                self.logging.error(self.player.errorString())
                self.cancel()

    def do_initialize(self):
        super().do_initialize()
        self.video = QVideoWidget(self.widget)
        self.add_widget(self.video)
        self.video.show()

        self.media = QMediaContent(self.url)
        self.playlist = QMediaPlaylist(self.video)
        self.playlist.addMedia(self.media)
        self.playlist.setPlaybackMode(
            QMediaPlaylist.Loop if self.loop else QMediaPlaylist.Sequential
        )

        self.player = QMediaPlayer(self.widget)
        self.player.setVideoOutput(self.video)
        self.player.setVolume(self.volume)
        self.player.setPlaybackRate(self.playback_rate)

    def do_run(self):
        super().do_run()
        self.player.setPlaylist(self.playlist)
        self.player.setPosition(self.start_time)
        self.player.play()

        if self.player.errorString():
            self.logging.error(self.player.errorString())
            self.cancel()

    def do_stop(self):
        super().do_stop()
        self.player.stop()

    def do_reset(self):
        self.player = None
        self.video = None


def create_event(parent, settings):
    event_types = {"PlayVideo": PlayVideo}
    event_class = event_types.get(settings.get("type"))
    event = event_class(parent, settings)
    return event


def load_events(path, events_list):
    settings_file = open(path, "r")

    try:
        from yaml import Loader, Dumper
        import yaml

        settings = yaml.load(settings_file, Loader=Loader)
        logging.info("Loaded settings: " + str(settings))
    except ImportError:
        import traceback

        logging.error(traceback.format_exc())
        return

    events = settings.get("events")
    frame = Frame(None, settings)
    for name, event in events.items():
        event["name"] = name
        events_list.append(create_event(frame, event))


def tick(events):
    event_logging.info("Tick")
    schedule.run_pending()
    for event in events:
        event.tick()


def main():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("settings_yaml", help="Path to a yaml file with settings")
    args = parser.parse_args()

    logging.root.setLevel(logging.DEBUG)
    event_logging.setLevel(logging.DEBUG)

    event_logging_queue = Queue()  # no limit on size
    event_logging_handler = logging.handlers.QueueHandler(event_logging_queue)
    event_logging.addHandler(event_logging_handler)

    events = []

    app = server.run_server(event_logging_queue, events)

    application = QApplication(sys.argv)
    application.setOverrideCursor(Qt.BlankCursor)

    load_events(args.settings_yaml, events)

    timer = QTimer()
    timer.timeout.connect(lambda: tick(events))
    timer.start(1000)

    for e in events:
        e.initialize()

    sys.exit(application.exec_())


if __name__ == "__main__":
    main()
