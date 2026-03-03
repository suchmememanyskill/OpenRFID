import requests
import jinja2
from exporters.exporter import Exporter
from filament.generic import GenericFilament
from reader.scan_result import ScanResult
import json
from reader.rfid_reader import RfidReader

class WebhookExporter(Exporter):
    def __init__(self, config : dict):
        super().__init__(config)
        self.env = jinja2.Environment()
        self.url = config.get("url", None)
        url_template = config.get("url_template", None)
        self.url_template = self.env.from_string(url_template) if url_template else None
        self.method = str(config.get("method", "POST")).upper()
        self.headers = config.get("headers", {})
        self.body_json = config.get("body_json", None)
        body_json_template = config.get("body_json_template", None)
        self.body_json_template = self.env.from_string(body_json_template) if body_json_template else None
        self.timeout = float(config.get("timeout", 5.0))

        if not self.url and not self.url_template:
            raise ValueError("WebhookExporter requires either a 'url' or 'url_template' in the configuration")

    def export_data(self, scan: ScanResult|None, filament: GenericFilament|None, reader : RfidReader):
        context = {
            "scan": scan.to_dict() if scan else None,
            "filament": filament.to_dict() if filament else None,
            "reader": {
                "name": reader.name,
                "slot": reader.slot
            }
        }

        try:
            if self.url_template:
                url = str(self.url_template.render(context))
            elif self.url:
                url = self.url
            else:
                raise ValueError("No URL or URL template provided for webhook export")

            if self.body_json:
                json_data = self.body_json
            elif self.body_json_template:
                body_str = self.body_json_template.render(context)
                json_data = json.loads(body_str)
            else:
                json_data = None

            response = requests.request(
                method=self.method,
                url=url,
                json=json_data,
                headers=self.headers,
                timeout=self.timeout
            )

            response.raise_for_status()
        except Exception as e:
            self.logger.exception(f"Failed to export data via webhook: {e}")