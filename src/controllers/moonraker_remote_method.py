from controllers.controller import Controller
import socket
import json
import time
import os

from controllers.moonraker_controller import MoonrakerController
from runtime import Runtime

MESSAGE_REGISTER_AGENT = {
    "jsonrpc": "2.0",
    "method": "server.connection.identify",
    "params": {
        "client_name": "filament-detect",
        "version": "0.0.1",
        "type": "agent",
        "url": "https://github.com/suchmememanyskill/filament-detect"
    },
    "id": 4656
}

class MoonrakerRemoteMethodController(MoonrakerController):
    def __init__(self, config: dict):
        super().__init__(config)
        self.remote_method_name = str(config["remote_method_name"])
        self.runtime : Runtime

    def on_connect(self):
        self.send_register_agent()
        time.sleep(0.1)
        self.send_register_remote_command()
        time.sleep(0.1)

    def on_message(self, message: dict):
        if "method" in message and message["method"] == self.remote_method_name:
            params = message.get("params", {})
            slot = params.get("slot", None)
            if slot is not None:
                self.runtime.start_reading_tag(slot)

    def send_register_agent(self):
        self.send_message(MESSAGE_REGISTER_AGENT)

    def send_register_remote_command(self):
        message = {
            "jsonrpc": "2.0",
            "method": "connection.register_remote_method",
            "params": {
                "method_name": self.remote_method_name
            }
        }

        self.send_message(message)