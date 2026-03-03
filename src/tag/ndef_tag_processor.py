
from filament import GenericFilament
from reader.scan_result import ScanResult
from tag.mifare_ultralight_tag_processor import MifareUltralightTagProcessor
from abc import abstractmethod
import io

from tag.tag_types import TagType

# Adapted from https://github.com/paxx12/SnapmakerU1-Extended-Firmware/blob/3c97d1d80309d817ad37f2daac8e436712cc7865/overlays/firmware-extended/13-rfid-support/root/home/lava/klipper/klippy/extras/filament_protocol_ndef.py

NDEF_OK = 0
NDEF_ERR = -1
NDEF_PARAMETER_ERR = -2
NDEF_NOT_FOUND_ERR = -3

class NdefRecord:
    def __init__(self, mime_type: str, payload: bytes):
        self.mime_type = mime_type
        self.payload = payload

class NdefTagProcessor(MifareUltralightTagProcessor):
    def __init__(self, config : dict):
        super().__init__(config)

    def process_tag(self, scan_result: ScanResult, data: bytes) -> GenericFilament | None:
        if scan_result.tag_type != TagType.MifareUltralight:
            raise ValueError("NdefTagProcessor can only process Mifare Ultralight tags")
        
        error, ndef_records = self.__ndef_parse(data)

        if error != NDEF_OK:
            self.logger.error(f"NDEF parse failed: NDEF parsing error (code: {error})")
            return None
        
        return self.process_ndef(scan_result, ndef_records)
    
    @abstractmethod
    def process_ndef(self, scan_result: ScanResult, ndef_records : list[NdefRecord]) -> GenericFilament | None:
        """Process NDEF data from the tag and return a GenericFilament if recognized, else None."""
        raise NotImplementedError("Subclasses must implement this method")
    
    def __xxd_dump(self, data : bytes|list, max_lines=16):
        if isinstance(data, list):
            data = bytes(data)
        if not isinstance(data, (bytes, bytearray)):
            return ""

        lines = []
        for i in range(0, min(len(data), max_lines * 16), 16):
            hex_part = ' '.join(f'{b:02x}' for b in data[i:i+16])
            ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
            lines.append(f'{i:08x}: {hex_part:<48}  {ascii_part}')

        if len(data) > max_lines * 16:
            lines.append(f'... ({len(data)} bytes total)')

        return '\n'.join(lines)

    def __ndef_parse(self, data_buf : bytes|list) -> tuple[int, list[NdefRecord]]:
        if None == data_buf or isinstance(data_buf, (list, bytes, bytearray)) == False:
            return NDEF_PARAMETER_ERR, []

        try:
            data = bytes(data_buf) if isinstance(data_buf, list) else data_buf

            self.logger.debug("NDEF RFID data:")
            self.logger.debug("\n" + self.__xxd_dump(data))

            data_io = io.BytesIO(data)

            start_offset = 0
            if len(data) > 12 and data[0] != 0xE1:
                for i in range(min(16, len(data) - 4)):
                    if data[i] == 0xE1 and (data[i+1] == 0x10 or data[i+1] == 0x11 or data[i+1] == 0x40):
                        start_offset = i
                        break

            if start_offset > 0:
                data_io.seek(start_offset)

            cc = data_io.read(4)
            if len(cc) < 4 or cc[0] != 0xE1:
                return NDEF_PARAMETER_ERR, []

            records = []

            while True:
                base_tlv = data_io.read(2)
                if len(base_tlv) < 2:
                    break

                tag = base_tlv[0]
                if tag == 0xFE:
                    break

                tlv_len = base_tlv[1]
                if tlv_len == 0xFF:
                    ext_len = data_io.read(2)
                    if len(ext_len) < 2:
                        break
                    tlv_len = (ext_len[0] << 8) | ext_len[1]

                if tag == 0x03:
                    ndef_data = data_io.read(tlv_len)
                    ndef_offset = 0

                    while ndef_offset < len(ndef_data) - 2:
                        header = ndef_data[ndef_offset]
                        ndef_offset += 1

                        tnf = header & 0x07
                        sr_flag = (header >> 4) & 0x01
                        il_flag = (header >> 3) & 0x01

                        type_len = ndef_data[ndef_offset]
                        ndef_offset += 1

                        if sr_flag:
                            payload_len = ndef_data[ndef_offset]
                            ndef_offset += 1
                        else:
                            if ndef_offset + 4 > len(ndef_data):
                                break
                            payload_len = (ndef_data[ndef_offset] << 24) | (ndef_data[ndef_offset + 1] << 16) | (ndef_data[ndef_offset + 2] << 8) | ndef_data[ndef_offset + 3]
                            ndef_offset += 4

                        id_len = 0
                        if il_flag:
                            id_len = ndef_data[ndef_offset]
                            ndef_offset += 1

                        if ndef_offset + type_len + id_len + payload_len > len(ndef_data):
                            break

                        mime_type = ndef_data[ndef_offset:ndef_offset + type_len].decode('ascii', errors='ignore')
                        ndef_offset += type_len

                        if id_len > 0:
                            ndef_offset += id_len

                        payload = bytes(ndef_data[ndef_offset:ndef_offset + payload_len])
                        ndef_offset += payload_len

                        if tnf == 0x02:
                            records.append(NdefRecord(mime_type, payload))
                            self.logger.debug(f"NDEF record found: mime_type='{mime_type}', payload_len={len(payload)}")
                else:
                    data_io.seek(tlv_len, 1)

            if not records:
                return NDEF_NOT_FOUND_ERR, []

            return NDEF_OK, records

        except Exception as e:
            self.logger.exception("NDEF parsing failed: %s", str(e))
            return NDEF_ERR, []