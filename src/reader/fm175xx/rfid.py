from tag.mifare_classic_tag_processor import TagAuthentication
from tag.tag_types import tag_type_from_sak
from . import constants as Constants
from bus import SoftwareSPI, OutputPin
from reader.mifare_classic_reader import MifareClassicReader
from reader.mifare_ultralight_reader import MifareUltralightReader
from reader.scan_result import ScanResult
from config import get_required_configurable_entity_by_name, TYPE_SOFTWARE_SPI, TYPE_OUTPUT_PIN
from typing import cast
import time

# Reader command
class Fm175xxCmdMetaData:
    def __init__(self) -> None:
        self.cmd : int
        self.send_crc_en : int
        self.recv_crc_en : int
        self.bits_to_send : int
        self.bytes_to_send : int
        self.bits_to_recv : int
        self.bytes_to_recv : int
        self.bits_recved : int
        self.bytes_recved : int
        self.send_buff : list
        self.recv_buff : list
        self.coll_pos : int
        self.error : int
        self.timeout : int

# Return value
class Fm175xxReturnVal:
    def __init__(self) -> None:
        self.err_code : int = 0
        self.out_data : list[int] = []

class Fm175xx(MifareClassicReader, MifareUltralightReader):
    def __init__(self, config : dict):
        super().__init__(config)
        self.spi = cast(SoftwareSPI, get_required_configurable_entity_by_name(config["spi"], TYPE_SOFTWARE_SPI))
        self.reset_pin = cast(OutputPin, get_required_configurable_entity_by_name(config["reset_pin"], TYPE_OUTPUT_PIN))
        self.hard_reset()

    def hard_reset(self):
        self.reset_pin.set_low()
        time.sleep(0.3)
        self.reset_pin.set_high()
        time.sleep(0.3)

    def start_session(self):
        self.__reader_a_init()
        self.__set_carrier_wave(Constants.FM175XX_CW_ENABLE)

    def end_session(self):
        self.__reader_a_halt()
        self.__set_carrier_wave(Constants.FM175XX_CW_DISABLE)

    def scan(self) -> ScanResult | None:
        (ret, UID, ATQA, BCC, SAK) = self.__reader_a_activate()
        if (ret != Constants.FM175XX_OK):
            self.logger.error("Scan error: %d", ret)
            return None

        return ScanResult(tag_type_from_sak(bytes(SAK)), bytes(UID), bytes(ATQA), bytes(BCC), bytes(SAK))

    def read_mifare_classic(self, scan_result: ScanResult, keys: TagAuthentication) -> bytes | None:
        data = self.__reader_a_m1_read_all_data(list(scan_result.uid), Constants.FM175XX_M1_CARD_AUTH_MODE_A, keys)

        if data.err_code != Constants.FM175XX_OK:
            self.logger.error("Mifare Classic read error: %d", data.err_code)
            return None

        return bytes(data.out_data)
    
    def read_mifare_ultralight(self, scan_result: ScanResult) -> bytes | None:
        data = self.__reader_a_ultralight_read_all_data()

        if data.err_code != Constants.FM175XX_OK:
            self.logger.error("Mifare Classic read error: %d", data.err_code)
            return None

        return bytes(data.out_data)

    # read register
    def __register_read(self, addr:int) -> int:
        addr = (addr << 1) | 0x80
        to_send = [addr, 0x00]
        reg_data = self.spi.transfer(to_send)
        return reg_data[1]
    
    # write register
    def __register_write(self, addr:int, reg_data:int) -> None:
        addr = (addr << 1) & 0x7E
        to_send = [addr, reg_data]
        self.spi.transfer(to_send)

    # modify register
    def __register_modify(self, addr:int, mask:int, is_set:int) -> None:
        reg_data = self.__register_read(addr)
        if (is_set):
            reg_data |= mask
        else:
            reg_data &= ~mask
        self.__register_write(addr, reg_data)

    # read FIFO
    def __fifo_read(self, len:int) -> list[int]:
        addr = [0x92] * len + [0x00]
        buff = self.spi.transfer(addr)
        return buff[1 : len + 1]

    # write FIFO
    def __fifo_write(self, len:int, buff:list) -> None:
        to_write = [0x12]
        to_write += buff[0:len]
        self.spi.transfer(to_write)

    # Enable/Disable CRC check generation during data transmission.
    def __set_send_crc(self, mode:int) -> None:
        if (mode):
            self.__register_modify(Constants.FM175XX_TX_MODE_REG, 0x80, Constants.FM175XX_SET)
        else:
            self.__register_modify(Constants.FM175XX_TX_MODE_REG, 0x80, Constants.FM175XX_RESET)

    # Enable/Disable CRC check generation during data reception.
    def __set_recv_crc(self, mode:int) -> None:
        if (mode):
            self.__register_modify(Constants.FM175XX_RX_MODE_REG, 0x80, Constants.FM175XX_SET)
        else:
            self.__register_modify(Constants.FM175XX_RX_MODE_REG, 0x80, Constants.FM175XX_RESET)

    # Set the timeout period for communication
    def __set_timeout(self, microseconds:int) -> None:
        prescaler = 0
        time_reload = 0

        if microseconds < 1 :
            microseconds = 1

        while( prescaler < 0xFFF ):
            time_reload = int((( microseconds * 13560 ) -1 ) / ( prescaler * 2 + 1))
            if (time_reload < 0xFFFF):
                break
            prescaler += 1

        time_reload &=  0xFFFF
        self.__register_write(Constants.FM175XX_T_MODE_REG, 0x80 | ((prescaler >> 8) & 0x0F) )
        self.__register_write(Constants.FM175XX_T_PRESCALER_REG, prescaler & 0xFF)
        self.__register_write(Constants.FM175XX_T_RELOAD_MSB_REG, time_reload >> 8 )
        self.__register_write(Constants.FM175XX_T_RELOAD_LSB_REG, time_reload & 0xFF )

    # set carrier wave
    def __set_carrier_wave(self, mode:int) -> None:
        if (Constants.FM175XX_CW1_ENABLE == mode):
            self.__register_modify(Constants.FM175XX_TX_CONTROL_REG, 0x01, Constants.FM175XX_SET)
            self.__register_modify(Constants.FM175XX_TX_CONTROL_REG, 0x02, Constants.FM175XX_RESET)
        elif (Constants.FM175XX_CW2_ENABLE == mode):
            self.__register_modify(Constants.FM175XX_TX_CONTROL_REG, 0x01, Constants.FM175XX_RESET)
            self.__register_modify(Constants.FM175XX_TX_CONTROL_REG, 0x02, Constants.FM175XX_SET)
        elif (Constants.FM175XX_CW_ENABLE == mode):
            self.__register_modify(Constants.FM175XX_TX_CONTROL_REG, 0x03, Constants.FM175XX_SET)
        else: # FM175XX_CW_DISABLE == mode
            self.__register_modify(Constants.FM175XX_TX_CONTROL_REG, 0x03, Constants.FM175XX_RESET)


    # Execute Command
    def __command_exe(self, cmd:Fm175xxCmdMetaData) -> Fm175xxReturnVal:
        reg_data = 0
        irq = 0
        result = Constants.FM175XX_ERR
        send_length = cmd.bytes_to_send
        receive_length = 0
        send_finish = 0
        cmd.bits_recved = 0
        cmd.bytes_recved = 0
        cmd.coll_pos = 0
        cmd.error = 0
        fifo_water_level  = 32
        last_time = time.time()

        self.__register_write(Constants.FM175XX_COMMAND_REG, Constants.FM175XX_CMD_IDLE)
        self.__register_write(Constants.FM175XX_FIFO_LEVEL_REG, 0x80)
        self.__register_write(Constants.FM175XX_COM_IRQ_REG, 0x7F)
        self.__register_write(Constants.FM175XX_DIV_IRQ_REG, 0x7F)
        self.__register_write(Constants.FM175XX_COM_I_EN_REG, 0x80)
        self.__register_write(Constants.FM175XX_DIV_I_EN_REG, 0x00)
        self.__register_write(Constants.FM175XX_WATER_LEVEL_REG, fifo_water_level)

        self.__set_send_crc(cmd.send_crc_en)
        self.__set_recv_crc(cmd.recv_crc_en)
        self.__set_timeout(cmd.timeout)

        # authentication
        if (cmd.cmd == Constants.FM175XX_CMD_MF_AUTHENT) :
            self.__fifo_write(send_length, cmd.send_buff)
            send_length = 0
            self.__register_write(Constants.FM175XX_COMMAND_REG, cmd.cmd)
            self.__register_write(Constants.FM175XX_BIT_FRAMING_REG, 0x80 | cmd.bits_to_send)

        if (cmd.cmd == Constants.FM175XX_CMD_TRANSCEIVE):
            self.__register_write(Constants.FM175XX_COMMAND_REG, cmd.cmd)
            self.__register_write(Constants.FM175XX_BIT_FRAMING_REG, (cmd.bits_to_recv << 4) | cmd.bits_to_send)

        last_time = time.time() * 1000
        while 1:
            # timeout
            new_time = time.time() * 1000
            if (new_time - last_time > 50 + cmd.timeout):
                result = Constants.FM175XX_CARD_TIMER_ERR
                break
            irq = self.__register_read(Constants.FM175XX_COM_IRQ_REG)

            # timeout
            if (irq & 0x01):
                self.__register_write(Constants.FM175XX_COM_IRQ_REG, 0x01)
                result = Constants.FM175XX_CARD_TIMER_ERR
                break

            # errors occurred
            if (irq & 0x02):
                reg_data = self.__register_read(Constants.FM175XX_ERROR_REG)
                cmd.error = reg_data

                if (cmd.error & 0x08):
                    reg_data = self.__register_read(Constants.FM175XX_COLL_REG)
                    cmd.coll_pos = reg_data & 0x1F
                    result = Constants.FM175XX_CARD_COLL_ERR
                    break

                result = Constants.FM175XX_CARD_COMM_ERR
                self.__register_write(Constants.FM175XX_COM_IRQ_REG, 0x02)
                break

            # low level alert
            if (irq & 0x04):
                # send data
                if (send_length > 0):
                    if (send_length > fifo_water_level):
                        self.__fifo_write(fifo_water_level, cmd.send_buff)
                        del cmd.send_buff[0:fifo_water_level]
                        send_length = send_length - fifo_water_level
                    else:
                        self.__fifo_write(send_length, cmd.send_buff)
                        send_length = 0
                    self.__register_modify(Constants.FM175XX_BIT_FRAMING_REG, 0x80, Constants.FM175XX_SET)
                self.__register_write(Constants.FM175XX_COM_IRQ_REG, 0x04)

            # high level alert
            if (irq & 0x08):
                # Waiting for data transmission to complete
                if (send_finish == 1):
                    cmd.recv_buff[cmd.bytes_recved:cmd.bytes_recved + fifo_water_level] = self.__fifo_read(fifo_water_level)
                    cmd.bytes_recved += fifo_water_level
                self.__register_write(Constants.FM175XX_COM_IRQ_REG, 0x08)

            # idle status
            if ((irq & 0x10) and (cmd.cmd == Constants.FM175XX_CMD_MF_AUTHENT)):
                self.__register_write(Constants.FM175XX_COM_IRQ_REG, 0x10)
                result = Constants.FM175XX_OK
                break

            # receice data
            if ((irq & 0x20) and (cmd.cmd == Constants.FM175XX_CMD_TRANSCEIVE)):
                reg_data = self.__register_read(Constants.FM175XX_CONTROL_REG)
                cmd.bits_recved = reg_data & 0x07
                reg_data = self.__register_read(Constants.FM175XX_FIFO_LEVEL_REG)
                receive_length = reg_data & 0x7F
                cmd.recv_buff[cmd.bytes_recved:cmd.bytes_recved+receive_length] = self.__fifo_read(receive_length)
                cmd.bytes_recved += receive_length
                if ((cmd.bytes_to_recv != cmd.bytes_recved) and (cmd.bytes_to_recv != 0)):
                    result = Constants.FM175XX_CARD_LENGTH_ERR
                    break
                self.__register_write(Constants.FM175XX_COM_IRQ_REG, 0x20)
                result = Constants.FM175XX_OK
                break

            # Completed data transmission
            if (irq & 0x40):
                self.__register_write(Constants.FM175XX_COM_IRQ_REG, 0x40)
                if (cmd.cmd == Constants.FM175XX_CMD_TRANSCEIVE):
                    send_finish = 1

        self.__register_modify(Constants.FM175XX_BIT_FRAMING_REG, 0x80, Constants.FM175XX_RESET)
        self.__register_write(Constants.FM175XX_COMMAND_REG, Constants.FM175XX_CMD_IDLE)

        ret = Fm175xxReturnVal()
        ret.err_code = result
        ret.out_data = cmd.recv_buff[:cmd.bytes_recved]

        if (len(ret.out_data) < cmd.bytes_recved):
            raise Exception("Fm175xx command exec error: recv data length less than expected")

        return ret

    # Reader-A: init
    def __reader_a_init(self) -> None:
        self.__register_write(Constants.FM175XX_TX_MODE_REG, 0x00)
        self.__register_write(Constants.FM175XX_RX_MODE_REG, 0x08)
        self.__register_modify(Constants.FM175XX_TX_AUTO_REG, 0x40, Constants.FM175XX_SET)
        self.__register_write(Constants.FM175XX_MODE_WIDTH_REG, 0x26)
        self.__register_write(Constants.FM175XX_CONTROL_REG, 0x10)
        self.__register_write(Constants.FM175XX_GSN_ON_REG, 0xF0)
        self.__register_write(Constants.FM175XX_CW_GSP_REG, 0x3F)
        self.__register_write(Constants.FM175XX_RF_CFG_REG, 0x60)
        self.__register_write(Constants.FM175XX_RX_THRESHOLD_REG, 0x84)
        self.__register_modify(Constants.FM175XX_STATUS_2_REG, 0x08, Constants.FM175XX_RESET)

    # Reader-A: wake up picc(s)
    def __reader_a_wakeup(self) -> tuple[int, list[int]]:
        ret = Constants.FM175XX_ERR
        outbuf = [0]
        inbuf = [0] * 2
        cmd = Fm175xxCmdMetaData()

        cmd.send_crc_en = Constants.FM175XX_RESET
        cmd.recv_crc_en = Constants.FM175XX_RESET
        cmd.send_buff = outbuf
        cmd.recv_buff = inbuf
        cmd.send_buff[0] = Constants.FM175XX_RF_CMD_WUPA
        cmd.bytes_to_send = 1
        cmd.bits_to_send = 7
        cmd.bits_to_recv = 0
        cmd.bytes_to_recv = 2
        cmd.timeout = 10
        cmd.cmd = Constants.FM175XX_CMD_TRANSCEIVE
        result = self.__command_exe(cmd)
        ret = result.err_code

        ATQA = [0, 0]

        if (result.err_code == Constants.FM175XX_OK):
            if (len(result.out_data) == 2):
                ATQA[0] = result.out_data[0]
                ATQA[1] = result.out_data[1]
            else:
                ret = Constants.FM175XX_CARD_COMM_ERR

        return (ret, ATQA)

    # Reader-A: anti-collision
    def __reader_a_anticoll(self, cascade_level:int) -> tuple[int, list[int], int]:
        ret = Constants.FM175XX_ERR
        outbuf = [0] * 2
        inbuf = [0] * 5
        cmd = Fm175xxCmdMetaData()

        if(cascade_level > 2):
            return (Constants.FM175XX_PARAM_ERR, [], 0)

        cmd.send_crc_en = Constants.FM175XX_RESET
        cmd.recv_crc_en = Constants.FM175XX_RESET
        cmd.send_buff = outbuf
        cmd.recv_buff = inbuf
        cmd.send_buff[0] = Constants.FM175XX_RF_CMD_ANTICOL[cascade_level]
        cmd.send_buff[1] = 0x20
        cmd.bytes_to_send = 2
        cmd.bits_to_send = 0
        cmd.bits_to_recv = 0
        cmd.bytes_to_recv = 5
        cmd.timeout = 10
        cmd.cmd = Constants.FM175XX_CMD_TRANSCEIVE
        result = self.__command_exe(cmd)
        ret = result.err_code
        self.__register_modify(Constants.FM175XX_COLL_REG, 0x80, Constants.FM175XX_SET)

        UID_part = [0] * 4
        BCC_part = 0

        if (result.err_code == Constants.FM175XX_OK):
            if (len(result.out_data) == 5):
                if((result.out_data[0] ^ \
                    result.out_data[1] ^ \
                    result.out_data[2] ^ \
                    result.out_data[3] ^ \
                    result.out_data[4]) != 0):
                    ret = Constants.FM175XX_CARD_COMM_ERR
                else:
                    UID_part = result.out_data[0:4]
                    BCC_part = result.out_data[4]
            else:
                ret = Constants.FM175XX_CARD_COMM_ERR

        return (ret, UID_part, BCC_part)

    # Reader-A: select a picc
    def __reader_a_select(self, cascade_level : int, UID_part: list[int], BCC_part : int) -> tuple[int, int]:
        ret = Constants.FM175XX_ERR
        outbuf = [0] * 7
        inbuf = [0]
        cmd = Fm175xxCmdMetaData()

        if(cascade_level > 2 or len(UID_part) != 4):
            return (Constants.FM175XX_PARAM_ERR, 0)

        cmd.send_crc_en = Constants.FM175XX_SET
        cmd.recv_crc_en = Constants.FM175XX_SET
        cmd.send_buff = outbuf
        cmd.recv_buff = inbuf
        cmd.send_buff[0] = Constants.FM175XX_RF_CMD_SELECT[cascade_level]
        cmd.send_buff[1] = 0x70
        cmd.send_buff[2] = UID_part[0]
        cmd.send_buff[3] = UID_part[1]
        cmd.send_buff[4] = UID_part[2]
        cmd.send_buff[5] = UID_part[3]
        cmd.send_buff[6] = BCC_part
        cmd.bytes_to_send = 7
        cmd.bits_to_send = 0
        cmd.bits_to_recv = 0
        cmd.bytes_to_recv = 1
        cmd.timeout = 10
        cmd.cmd = Constants.FM175XX_CMD_TRANSCEIVE
        result = self.__command_exe(cmd)
        ret = result.err_code

        SAK_part = 0

        if (result.err_code == Constants.FM175XX_OK):
            if (len(result.out_data) == 1):
                SAK_part = result.out_data[0]
            else:
                ret = Constants.FM175XX_CARD_COMM_ERR

        return (ret, SAK_part)

    # Reader-A: halt
    def __reader_a_halt(self) -> int:
        outbuf = [0] * 2
        inbuf = [0] * 2
        cmd = Fm175xxCmdMetaData()

        cmd.send_crc_en = Constants.FM175XX_SET
        cmd.recv_crc_en = Constants.FM175XX_SET
        cmd.send_buff = outbuf
        cmd.recv_buff = inbuf
        cmd.send_buff[0] = Constants.FM175XX_RF_CMD_HALT[0]
        cmd.send_buff[1] = Constants.FM175XX_RF_CMD_HALT[1]
        cmd.bytes_to_send = 2
        cmd.bits_to_send = 0
        cmd.bits_to_recv = 0
        cmd.bytes_to_recv = 0
        cmd.timeout = 10
        cmd.cmd = Constants.FM175XX_CMD_TRANSCEIVE
        result = self.__command_exe(cmd)

        # If there is no response within 1ms, the 'halt' is successful
        if (result.err_code == Constants.FM175XX_CARD_TIMER_ERR):
            result.err_code = Constants.FM175XX_OK
        else:
            result.err_code = Constants.FM175XX_CARD_HALT_ERR

        return result.err_code

    # Reader-A: activate a picc
    def __reader_a_activate(self) -> tuple[int, list[int], list[int], list[int], list[int]]:
        ret = Constants.FM175XX_ERR
        cascade_level = 0

        (ret, ATQA) = self.__reader_a_wakeup()
        if (Constants.FM175XX_OK != ret):
            self.logger.error("wakeup err: %d", ret)
            return (Constants.FM175XX_CARD_WAKEUP_ERR, [], [], [], [])

        if ((ATQA[0] & 0xC0) == 0x00):
            cascade_level = 1
        elif ((ATQA[0] & 0xC0) == 0x40):
            cascade_level = 2
        elif ((ATQA[0] & 0xC0) == 0x80):
            cascade_level = 3
        else:
            pass  # RFU

        UID : list[int] = []
        BCC : list[int] = []
        SAK : list[int] = []

        for level in range(cascade_level):
            (ret, UID_part, BCC_part) = self.__reader_a_anticoll(level)
            if (Constants.FM175XX_OK != ret):
                self.logger.error("anticoll err: %d", ret)
                ret = Constants.FM175XX_CARD_COLL_ERR
                break

            if level < cascade_level - 1:
                UID += UID_part[1:]
            else:
                UID += UID_part
            BCC.append(BCC_part)

            (ret, SAK_part) = self.__reader_a_select(level, UID_part, BCC_part)
            if (Constants.FM175XX_OK != ret):
                self.logger.error("select err: %d", ret)
                ret = Constants.FM175XX_CARD_SELECT_ERR
                break

            SAK.append(SAK_part)

        if (Constants.FM175XX_OK != ret):
            return (ret, [], [], [], [])

        return (ret, UID, ATQA, BCC, SAK)

    # Reader-A: M1 authentication
    def __reader_a_mifare_auth(self, mode:int, sector:int, mifare_key:list, card_uid:list) -> int:
        ret = Constants.FM175XX_ERR
        reg_data = 0
        outbuf = [0] * 12
        inbuf = [0] * 1
        cmd = Fm175xxCmdMetaData()

        cmd.send_crc_en = Constants.FM175XX_SET
        cmd.recv_crc_en = Constants.FM175XX_SET
        cmd.send_buff = outbuf
        cmd.recv_buff = inbuf
        if (Constants.FM175XX_M1_CARD_AUTH_MODE_A == mode):
            cmd.send_buff[0] = 0x60
        else:
            cmd.send_buff[0] = 0x61
        cmd.send_buff[1] = sector * 4
        cmd.send_buff[2] = mifare_key[0]
        cmd.send_buff[3] = mifare_key[1]
        cmd.send_buff[4] = mifare_key[2]
        cmd.send_buff[5] = mifare_key[3]
        cmd.send_buff[6] = mifare_key[4]
        cmd.send_buff[7] = mifare_key[5]
        cmd.send_buff[8] = card_uid[0]
        cmd.send_buff[9] = card_uid[1]
        cmd.send_buff[10] = card_uid[2]
        cmd.send_buff[11] = card_uid[3]
        cmd.bytes_to_send = 12
        cmd.bits_to_send = 0
        cmd.bits_to_recv = 0
        cmd.bytes_to_recv = 0
        cmd.timeout = 10
        cmd.cmd = Constants.FM175XX_CMD_MF_AUTHENT
        result = self.__command_exe(cmd)
        ret = result.err_code
        if (Constants.FM175XX_OK == result.err_code):
            reg_data = self.__register_read(Constants.FM175XX_STATUS_2_REG)
            if (reg_data & 0x08):
                ret =  Constants.FM175XX_OK
            else:
                ret =  Constants.FM175XX_CARD_COMM_ERR

        return ret

    # Reader-A: M1, read a block
    def __reader_a_m1_block_read(self, block:int) -> Fm175xxReturnVal:
        outbuf = [0] * 2
        inbuf = [0] * 16
        cmd = Fm175xxCmdMetaData()
        ret = Fm175xxReturnVal()

        cmd.send_crc_en = Constants.FM175XX_SET
        cmd.recv_crc_en = Constants.FM175XX_SET
        cmd.send_buff = outbuf
        cmd.recv_buff = inbuf
        cmd.send_buff[0] = 0x30
        cmd.send_buff[1] = block
        cmd.bytes_to_send = 2
        cmd.bits_to_send = 0
        cmd.bits_to_recv = 0
        cmd.bytes_to_recv = 16
        cmd.timeout = 10
        cmd.cmd = Constants.FM175XX_CMD_TRANSCEIVE
        result = self.__command_exe(cmd)
        ret.err_code = result.err_code

        if (Constants.FM175XX_OK == result.err_code):
            if (len(result.out_data) == 16):
                ret.out_data = result.out_data[0:16]
            else:
                ret.err_code = Constants.FM175XX_CARD_COMM_ERR

        return ret

    # Reader-A: M1, write a block
    def __reader_a_m1_block_write(self, block:int, buff:list) -> int:
        ret = 0
        outbuf = [0] * 16
        inbuf = [0] * 1
        cmd = Fm175xxCmdMetaData()

        cmd.send_crc_en = Constants.FM175XX_SET
        cmd.recv_crc_en = Constants.FM175XX_RESET
        cmd.send_buff = outbuf
        cmd.recv_buff = inbuf
        cmd.send_buff = outbuf
        cmd.recv_buff = inbuf
        cmd.send_buff[0] = 0xA0
        cmd.send_buff[1] = block
        cmd.bytes_to_send = 2
        cmd.bits_to_send = 0
        cmd.bits_to_recv = 0
        cmd.bytes_to_recv = 1
        cmd.timeout = 10
        cmd.cmd = Constants.FM175XX_CMD_TRANSCEIVE
        result = self.__command_exe(cmd)
        ret = result.err_code

        if ((result.err_code != Constants.FM175XX_OK) or (cmd.bits_recved != 4) or (cmd.recv_buff[0] & 0x0F != 0x0A)):
            if (result.err_code == Constants.FM175XX_OK):
                ret = Constants.FM175XX_CARD_COMM_ERR
        else:
            self.__set_timeout(10)
            cmd.send_buff[0:16] = buff[0:16]
            cmd.bytes_to_send = 16
            cmd.bytes_to_recv = 1
            cmd.cmd = Constants.FM175XX_CMD_TRANSCEIVE
            result = self.__command_exe(cmd)
            ret = result.err_code

            if ((cmd.bits_recved != 4) or (cmd.recv_buff[0] & 0x0F != 0x0A)):
                ret = Constants.FM175XX_CARD_COMM_ERR

        return ret

    # Reader-A: M1, read all data
    def __reader_a_m1_read_all_data(self, uid:list, auth_mode:int, auth_key : TagAuthentication, retry_times = 3) -> Fm175xxReturnVal:
        ret = Fm175xxReturnVal()
        card_data_tmp = [0] * Constants.FM175XX_M1_CARD_EEPROM_SIZE
        area = 0

        # Traverse all sectors
        for sector_no in range(Constants.FM175XX_M1_CARD_SECTORS):
            # Authentication
            result = Constants.FM175XX_ERR
            #print(auth_key.hkdf_key_a[sector_no])
            for _ in range(retry_times):
                result = self.__reader_a_mifare_auth(auth_mode, sector_no, auth_key.hkdf_key_a[sector_no], uid)
                if (result == Constants.FM175XX_OK):
                    break
            if (Constants.FM175XX_OK != result):
                ret.err_code = Constants.FM175XX_CARD_AUTH_ERR
                self.logger.error( "------ M1 AUTH ERROR------\r\n" )
                return ret

            # Traverse all blocks
            for block_no in range(Constants.FM175XX_M1_CARD_BLOCKS_PER_SEC - 1):
                result = Fm175xxReturnVal()
                for _ in range(retry_times):
                    result = self.__reader_a_m1_block_read(sector_no * Constants.FM175XX_M1_CARD_BLOCKS_PER_SEC + block_no)
                    if (result.err_code == Constants.FM175XX_OK):
                        break
                if (result.err_code != Constants.FM175XX_OK):
                    ret.err_code = Constants.FM175XX_CARD_READ_ERR
                    return ret

                area = Constants.FM175XX_M1_CARD_BYTES_PER_BLK * (sector_no * Constants.FM175XX_M1_CARD_BLOCKS_PER_SEC + block_no)
                card_data_tmp[area : area + Constants.FM175XX_M1_CARD_BYTES_PER_BLK] = result.out_data[0 : Constants.FM175XX_M1_CARD_BYTES_PER_BLK]

            area = sector_no * Constants.FM175XX_M1_CARD_BYTES_PER_SEC + 3 * Constants.FM175XX_M1_CARD_BYTES_PER_BLK
            card_data_tmp[area : area + Constants.FM175XX_M1_CARD_BYTES_PER_BLK] = \
                    auth_key.hkdf_key_a[sector_no] + Constants.FM175XX_M1_CARD_ACCESS_CODE + auth_key.hkdf_key_b[sector_no]

        ret.err_code = Constants.FM175XX_OK
        ret.out_data = card_data_tmp
        return ret
    
    # Reader-A: NTAG/Ultralight, read a page (4 bytes)
    def __reader_a_ultralight_page_read(self, page:int) -> Fm175xxReturnVal:
        outbuf = [0] * 2
        inbuf = [0] * 16
        cmd = Fm175xxCmdMetaData()
        ret = Fm175xxReturnVal()

        cmd.send_crc_en = Constants.FM175XX_SET
        cmd.recv_crc_en = Constants.FM175XX_SET
        cmd.send_buff = outbuf
        cmd.recv_buff = inbuf
        cmd.send_buff[0] = 0x30
        cmd.send_buff[1] = page
        cmd.bytes_to_send = 2
        cmd.bits_to_send = 0
        cmd.bits_to_recv = 0
        cmd.bytes_to_recv = 16
        cmd.timeout = 10
        cmd.cmd = Constants.FM175XX_CMD_TRANSCEIVE
        result = self.__command_exe(cmd)
        ret.err_code = result.err_code

        if (Constants.FM175XX_OK == result.err_code):
            if (len(result.out_data) == 16):
                ret.out_data = result.out_data
            else:
                ret.err_code = Constants.FM175XX_CARD_COMM_ERR

        return ret

    # TODO: Maybe don't call it ultralight but the actual ISO specification
    # Reader-A: NTAG215, read all data
    def __reader_a_ultralight_read_all_data(self, retry_times = 3) -> Fm175xxReturnVal:
        ret = Fm175xxReturnVal()
        card_data_tmp = [0] * Constants.FM175XX_NTAG215_TOTAL_SIZE

        for page_no in range(0, Constants.FM175XX_NTAG215_TOTAL_PAGES, 4):
            result = Fm175xxReturnVal()
            for _ in range(retry_times):
                result = self.__reader_a_ultralight_page_read(page_no)
                if (result.err_code == Constants.FM175XX_OK):
                    break
            if (result.err_code != Constants.FM175XX_OK):
                if (page_no - 4) in Constants.FM175XX_ULTRALIGHT_VALID_END_PAGES:
                    card_data_tmp = card_data_tmp[0 : (page_no * Constants.FM175XX_NTAG215_BYTES_PER_PAGE)]
                    break

                ret.err_code = Constants.FM175XX_CARD_READ_ERR
                return ret

            area = page_no * Constants.FM175XX_NTAG215_BYTES_PER_PAGE
            bytes_to_copy = min(16, Constants.FM175XX_NTAG215_TOTAL_SIZE - area)
            if bytes_to_copy > 0:
                card_data_tmp[area : area + bytes_to_copy] = result.out_data[0 : bytes_to_copy]

        ret.err_code = Constants.FM175XX_OK
        ret.out_data = card_data_tmp
        return ret