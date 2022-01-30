import datetime
import json
import os
from logging import getLogger
from typing import List, Optional

import kombu
from requests import Session
from urwid import (AttrMap, AttrWrap, Columns, Edit, ExitMainLoop, Filler, Frame, LineBox, ListBox,
                   MainLoop, Pile, SimpleFocusListWalker, Text,
                   WidgetWrap, connect_signal, disconnect_signal, emit_signal, raw_display,
                   register_signal)

from commands import CreateGroup, JoinGroup
from worker import ClientWorker

logger = getLogger(__name__)

USERNAME = os.getenv("USERNAME", "Anonymous")
RABBITMQ_API_URL = os.getenv("RABBITMQ_API_URL")
RABBITMQ_USER = os.getenv("RABBITMQ_USER")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD")
RABBITMQ_URI = os.getenv("RABBITMQ_URI")


class ListItem(WidgetWrap):

    def __init__(self, group):
        self.content = group
        name = group["name"]

        t = AttrWrap(Text(name), "group", "group_selected")
        WidgetWrap.__init__(self, t)

    def selectable(self):
        return True

    def keypress(self, size, key):
        return key


class CommandItem(WidgetWrap):

    def __init__(self, command):
        self.content = command
        t = AttrWrap(Text(command), "command", "command_selected")
        WidgetWrap.__init__(self, t)

    def selectable(self):
        return False

    def keypress(self, size, key):
        return key


class GroupsList(WidgetWrap):

    def __init__(self):
        register_signal(self.__class__, ['open_group'])
        self.walker = SimpleFocusListWalker([])
        lb = ListBox(self.walker)
        WidgetWrap.__init__(self, lb)

    def modified(self):
        focus_w, _ = self.walker.get_focus()
        if focus_w is not None:
            emit_signal(self, 'open_group', focus_w.content)

    def set_data(self, groups):
        groups_widgets = [ListItem(g) for g in groups]
        disconnect_signal(self.walker, 'modified', self.modified)

        while len(self.walker) > 0:
            self.walker.pop()

        self.walker.extend(groups_widgets)
        connect_signal(self.walker, "modified", self.modified)
        self.walker.set_focus(0)


class ChatMessages(ListBox):

    def __init__(self, chat):
        self.chat = chat
        self.walker = SimpleFocusListWalker([])

        super(ChatMessages, self).__init__(self.walker)

    def fill(self, messages: List[str]):
        self.walker.clear()
        widgets = [Text(m) for m in messages]
        self.walker.extend(widgets)

    def add(self, message: str):
        logger.info(f"Display message {message}")
        self.walker.append(Text(message))
        self.set_focus(len(self.walker) - 1)

    def clear(self):
        self.walker.clear()


class CommandsList(WidgetWrap):

    def __init__(self):
        self.walker = SimpleFocusListWalker([
            CommandItem(f"/{CreateGroup.name} <group_name> - create new group"),
            CommandItem(f"/{JoinGroup.name} <group_name> - join to existed group")
        ])
        lb = ListBox(self.walker)
        WidgetWrap.__init__(self, lb)


class ChatInput(Edit):

    def __init__(self, chat):
        self.chat = chat
        super(ChatInput, self).__init__(caption='>>>')

    def keypress(self, size, key):
        message = self.get_edit_text()

        if key == 'enter':
            if message == '':
                return
            if message[0] == '/':
                self.chat.execute_command(message[1:])
            else:
                self.chat.send_message(message)
            self.set_edit_text('')

        super(ChatInput, self).keypress(size, key)


class Chat(object):

    def __init__(self, username: str, session: Session):
        self.username = username
        self.session = session
        self.selected_group = None
        self.client_worker: Optional[ClientWorker] = None
        self.palette = {
            ("bg", "black", "white"),
            ("group", "black", "white"),
            ("group_selected", "black", "yellow"),
            ("footer", "white, bold", "dark red"),
            ("message_input", "white, bold", "black")
        }
        self.output = ChatMessages(self)
        self.message_input = AttrWrap(ChatInput(self), "message_input")

        self.groups_list = GroupsList()

        connect_signal(self.groups_list, 'open_group', self.open_group)

        footer = AttrWrap(Text(" Q to exit"), "footer")

        col_rows = raw_display.Screen().get_cols_rows()
        h = col_rows[0] - 2

        f1 = Filler(self.groups_list, valign='top', height=h)
        commands_list = Filler(CommandsList(), valign="top", height=h)

        c_list = Pile([
            ('weight', 60, LineBox(f1, title="Groups")),
            ('weight', 40, LineBox(commands_list, title="Commands"))
        ])
        c_chat = LineBox(self.output, title="Chat")

        columns = Columns([('weight', 30, c_list), ('weight', 70, c_chat)])
        content = Frame(body=columns, footer=self.message_input)

        frame = AttrMap(Frame(body=content, footer=footer), 'bg')

        self.loop = MainLoop(frame, self.palette, unhandled_input=self.unhandled_input)

    def open_group(self, group: dict):
        self.output.clear()
        self.selected_group = group["name"]

        def drain_events(loop, user_data):
            with kombu.Connection(RABBITMQ_URI) as conn:
                name = f"username.{self.username}"
                group_name = user_data["group_name"]
                queue = kombu.Queue(
                    name,
                    exchange=kombu.Exchange(f"group.{group_name}"),
                    routing_key=f"group.{group_name}"
                )
                client_worker = ClientWorker(conn, queue, group_name, callback=self.output.add)
                self.output.clear()
                try:
                    next(client_worker.consume(limit=1))
                except StopIteration:
                    pass

            if self.selected_group == group_name:
                self.loop.set_alarm_in(1, drain_events, user_data=user_data)

        self.loop.set_alarm_in(1, drain_events, user_data={"group_name": group["name"]})

    def send_message(self, message: str):
        if self.selected_group is None:
            return
        now = datetime.datetime.now().strftime("%H:%M:%S")
        message = {
            "sender_username": self.username,
            "timestamp": now,
            "group_name": self.selected_group,
            "message": message
        }
        with kombu.Connection(RABBITMQ_URI) as conn:
            conn.Producer().publish(
                json.dumps(message),
                exchange=kombu.Exchange("hub"),
                content_type="application/json",
                serializer="json"
            )

    def fetch_groups(self, *args, **kwargs):
        result = self.session.get(f"{RABBITMQ_API_URL}api/bindings")
        groups = []
        for binding in result.json():
            destination = binding["destination"].split(".")
            if not len(destination) > 1 or not destination[0] == "username":
                continue
            source = binding["source"].split(".")
            if not len(source) > 1 or not source[0] == "group":
                continue
            if destination[1] == self.username:
                groups.append({"name": source[1]})

        self.groups_list.set_data(groups)

    def execute_command(self, message: str):
        command_name, *args = message.split()
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.output.add(f"[{now}] Command {command_name} executed with args {args}")
        if CreateGroup.name == command_name:
            CreateGroup()(username=self.username, group_name=args[0])
            self.loop.set_alarm_in(1, self.fetch_groups)
        elif JoinGroup.name == command_name:
            JoinGroup()(username=self.username, group_name=args[0])
            self.loop.set_alarm_in(1, self.fetch_groups)

    def unhandled_input(self, key):
        if key in ('q',):
            raise ExitMainLoop()

    def start(self):
        self.fetch_groups()
        self.loop.run()


if __name__ == '__main__':
    with Session() as sess:
        sess.auth = (RABBITMQ_USER, RABBITMQ_PASSWORD)
        app = Chat(USERNAME, sess)
        app.start()
