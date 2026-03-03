from controllers.controller import Controller
import socket
from abc import abstractmethod
import json
from typing import Any
import os
import time

class MoonrakerController(Controller):
    def __init__(self, config: dict):
        super().__init__(config)
        self.moonraker_socket_path = str(config["moonraker_socket_path"])
        self.socket : socket.socket|None = None
        self.buffer = b""
    
    def __loop_inner(self):
        if self.socket is not None:
            self.socket.close()

        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        if not os.path.exists(self.moonraker_socket_path):
            self.logger.warning(f"Moonraker socket not found at {self.moonraker_socket_path}")
            return

        self.socket.connect(self.moonraker_socket_path)
        time.sleep(0.1)
        self.on_connect()
        
        while True:
            data = self.socket.recv(4096)
            if not data:
                raise Exception("Moonraker socket connection closed")
            
            self.buffer += data

            while b'\x03' in self.buffer:
                message_data, self.buffer = self.buffer.split(b'\x03', 1)
                try:
                    message = json.loads(message_data.decode("utf-8").strip())
                    self.on_message(message)
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to decode JSON message: {e}")
                    continue

    def loop(self):
        while True:
            try:
                self.__loop_inner()
            except Exception as e:
                self.logger.error(f"Error in MoonrakerController loop: {e}")

            self.logger.info("Retrying connection in 5 seconds...")
            time.sleep(5)

    def send_message(self, message: Any):
        message_str = json.dumps(message)
        self.socket.sendall(message_str.encode("utf-8") + b'\x03')

    def on_connect(self):
        """Called when the socket connection is established."""
        pass

    @abstractmethod
    def on_message(self, message: Any):
        """Handle a message received from the Moonraker socket."""
        raise NotImplementedError("Subclasses must implement this method")