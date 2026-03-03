from controllers.controller import Controller
import socket
import json
import time
import os

from controllers.moonraker_controller import MoonrakerController
from runtime import Runtime

MESSAGE_ID_WEBHOOK_QUERY = 348894590
MESSAGE_ID_SUBSCRIBE = 84758249

class MoonrakerOnPropertyChangeController(MoonrakerController):
    def __init__(self, config: dict):
        super().__init__(config)
        self.runtime : Runtime
        self.track_object = str(config["track_object"])
        self.track_field = str(config["track_field"])
        self.get_index_from_field = str(config["get_index_from_field"])
        self.act_on_value = config.get("act_on_value", None)
        self.klippy_ready = False
        self.current_value = None

        # Array: Compare the arrays from old and new, all different indexes are taken as slots

        if self.get_index_from_field not in ["array"]:
            raise ValueError(f"Invalid field type: {self.get_index_from_field}")

    def on_connect(self):
        self.send_server_query()

    def on_message(self, message: dict):
        #self.logger.debug(f"Received message: {message}")
        if message is None:
            return
        
        if "id" in message:
            if message["id"] == MESSAGE_ID_WEBHOOK_QUERY:
                result = message.get("result", {})
                klippy_state = result.get("klippy_state", None)
                if klippy_state is not None:
                    self.klippy_ready = klippy_state == "ready"
                    if self.klippy_ready:
                        self.logger.debug("Klippy is ready, sending subscribe command...")
                        self.send_subscribe_command()
            elif message["id"] == MESSAGE_ID_SUBSCRIBE:
                result = message.get("result", {})
                status = result.get("status", {})
                tracked_object = status.get(self.track_object, {})
                tracked_field = tracked_object.get(self.track_field, None)
                if tracked_field is not None:
                    self.current_value = None
                    self.handle_diff(tracked_field)
                    self.current_value = tracked_field
                    self.logger.info(f"Initial value for tracked field set to: {self.current_value}")
        elif "method" in message:
            if message["method"] == "notify_klippy_disconnected" or message["method"] == "notify_klippy_shutdown":
                self.logger.warning("Klippy disconnected, resetting state")
                self.klippy_ready = False
                self.current_value = None
            elif message["method"] == "notify_klippy_ready":
                self.logger.debug("Klippy is ready, sending subscribe command...")
                self.klippy_ready = True
                self.send_subscribe_command()
            elif message["method"] == "notify_status_update":
                params = message.get("params", {})
                objects = params[0] if len(params) > 0 else {}
                tracked_object = objects.get(self.track_object, {})
                tracked_field = tracked_object.get(self.track_field, None)
                self.logger.debug(f"Received status update: {tracked_field}")
                self.handle_diff(tracked_field)

    def send_server_query(self):
        query_message = {
            "jsonrpc": "2.0",
            "method": "server.info",
            "id": MESSAGE_ID_WEBHOOK_QUERY
        }

        self.send_message(query_message)

    def send_subscribe_command(self):
        subscribe_message = {
            "jsonrpc": "2.0",
            "method": "printer.objects.subscribe",
            "params": {
                "objects": {
                    self.track_object: [self.track_field]
                }
            },
            "id": MESSAGE_ID_SUBSCRIBE
        }

        self.send_message(subscribe_message)

    def handle_diff(self, new):
        # TODO : This could be better
        if self.get_index_from_field == "array":
            if self.current_value is not None:
                if self.current_value == new and self.act_on_value is None:
                    return
                
                if not isinstance(new, list) or not isinstance(self.current_value, list):
                    self.logger.error("Expected array value for field but got non-array")
                    return
                
                if len(new) != len(self.current_value):
                    self.logger.warning("Array length changed, resetting state")
                    self.current_value = new
                    return
            
            changed_slots = []
            
            for i in range(len(new)):
                if (self.current_value is None or new[i] != self.current_value[i]) and (self.act_on_value is None or str(new[i]) == self.act_on_value):
                    changed_slots.append(i)

            for changed_slot in changed_slots:
                self.runtime.start_reading_tag(changed_slot)

        self.current_value = new