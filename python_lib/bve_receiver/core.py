import dataclasses
import logging
import queue
import struct
import sys
import threading
from abc import ABC
from typing import Any, Callable

from .atsplugin.define import *
from .atsplugin.struct import *
from .exception import UndefinedHeader, VersionUnsupported

logger = logging.getLogger(__name__)

@dataclasses.dataclass
class KeyState:
    is_pressed: bool = False

@dataclasses.dataclass
class HornState:
    is_blowing: bool = False

class BveReceiver(ABC):

    __to_int: struct.Struct = struct.Struct('i')
    __to_unsigned_char: struct.Struct = struct.Struct('B')
    __to_float: struct.Struct = struct.Struct('f')
    __to_double: struct.Struct = struct.Struct('d')

    __queue:queue.Queue[tuple[Callable[...,None],tuple[Any,...]]]
    """BVEからの受信データのキュー"""
    __thread_queue:threading.Thread
    """キューの供給用スレッド"""

    panel: list[int]
    """パネルの配列"""
    sound: list[AtsSound|int]
    """音声の配列"""
    keys: dict[AtsKey, KeyState]
    """キー状態の辞書"""
    horns: dict[AtsHorn, HornState]
    """警笛状態の辞書"""
    vehicle_spec: AtsVehicleSpec
    """車両スペック"""
    vehicle_state: AtsVehicleState
    """車両状態"""
    handles: AtsHandles
    """ハンドル状態"""
    signal: int
    """信号現示"""
    is_door_closed: bool = True
    """ドアが閉まっているかどうか"""

    def __init__(self) -> None:
        self.panel = [0] * 256
        self.sound = [AtsSound.STOP] * 256
        self.handles = AtsHandles(brake=0, power=0, reverser=0, constant_speed=AtsConstantSpeed.CONTINUE)
        self.keys = { key: KeyState() for key in AtsKey}
        self.horns = { horn: HornState() for horn in AtsHorn }
        self.__queue = queue.Queue()
        self.__thread_queue = threading.Thread(target=self.__queue_putter, daemon=True)
        self.__thread_queue.start()

    def __read_int(self) -> int:
        binary = sys.stdin.buffer.read(4)
        return self.__to_int.unpack(binary)[0]

    def __read_unsigned_char(self) -> int:
        binary = sys.stdin.buffer.read(1)
        return self.__to_unsigned_char.unpack(binary)[0]

    def __read_float(self) -> float:
        binary = sys.stdin.buffer.read(4)
        return self.__to_float.unpack(binary)[0]

    def __read_double(self) -> float:
        binary = sys.stdin.buffer.read(8)
        return self.__to_double.unpack(binary)[0]

    def __queue_getter(self):
        while True:
            func, args = self.__queue.get()
            try:
                func(*args)
            except VersionUnsupported:
                logger.exception(f"Failed to execute {getattr(func, '__name__', 'unknown')}{args}", exc_info=True)
                sys.exit(1)
            except:
                logger.exception(f"Failed to execute {getattr(func, '__name__', 'unknown')}{args}", exc_info=True)
            finally:
                self.__queue.task_done()
                if func == self._on_dispose:
                    return

    def __queue_putter(self):
        while True:
            try:
                header:bytes = sys.stdin.buffer.read(1)
                match header:
                    case b'\x00':
                        self.__queue.put((self._on_load, (
                            self.__read_unsigned_char(),
                            self.__read_unsigned_char(),
                            self.__read_unsigned_char(),
                        )))
                    case b'\x01':
                        self.__queue.put((self._on_dispose, tuple()))
                        return
                    case b'\x10':
                        vehicle_spec = AtsVehicleSpec(
                            self.__read_int(),
                            self.__read_int(),
                            self.__read_int(),
                            self.__read_int(),
                            self.__read_int(),
                        )
                        self.__queue.put((self._set_vehicle_spec, (vehicle_spec,)))
                    case b'\x20':
                        init_handle:AtsInitHandle|int = self.__read_int()
                        try:
                            init_handle = AtsInitHandle(init_handle)
                        except ValueError:
                            pass
                        self.__queue.put((self._on_initialize, (init_handle,)))
                    case b'\x30':
                        vehicle_state = AtsVehicleState(
                            self.__read_double(),
                            self.__read_float(),
                            self.__read_int(),
                            self.__read_float(),
                            self.__read_float(),
                            self.__read_float(),
                            self.__read_float(),
                            self.__read_float(),
                            self.__read_float(),
                        )
                        self.__queue.put((self._on_elapse, (vehicle_state,)))
                    case b'\x40':
                        self.__queue.put((self._on_set_power, (self.__read_int(),)))
                    case b'\x41':
                        self.__queue.put((self._on_set_brake, (self.__read_int(),)))
                    case b'\x42':
                        self.__queue.put((self._on_set_reverser, (self.__read_int(),)))
                    case b'\x50':
                        self.__queue.put((self._on_key_down, (self.__read_int(),)))
                    case b'\x51':
                        self.__queue.put((self._on_key_up, (self.__read_int(),)))
                    case b'\x60':
                        self.__queue.put((self._on_horn_blow, (self.__read_int(),)))
                    case b'\x61':
                        self.__queue.put((self._on_horn_stop, (self.__read_int(),)))
                    case b'\x70':
                        self.__queue.put((self._on_door_open, tuple()))
                    case b'\x71':
                        self.__queue.put((self._on_door_close, tuple()))
                    case b'\x80':
                        self.__queue.put((self._on_set_signal, (self.__read_int(),)))
                    case b'\x90':
                        beacon_data = AtsBeaconData(
                            self.__read_int(),
                            self.__read_int(),
                            self.__read_float(),
                            self.__read_int(),
                        )
                        self.__queue.put((self._on_set_beacon_data, (beacon_data,)))
                    case b'\xA0':
                        self.__queue.put((self._on_panel_update, (self.__read_unsigned_char(), self.__read_int(),)))
                    case b'\xA1':
                        self.__queue.put((self._on_sound_update, (self.__read_unsigned_char(), self.__read_int(),)))
                    case _:
                        raise UndefinedHeader(header)
            except UndefinedHeader:
                logger.exception("", exc_info=True)
                sys.exit(1)

    def qsize(self) -> int:
        """キューのサイズ"""
        return self.__queue.qsize()

    def run(self):
        """BVEからのデータ処理を開始"""
        self.__queue_getter()

    def _on_load(self, major_version:int, minor_version:int, build_version:int):
        logger.info("Plugin loaded")
        if [major_version, minor_version, build_version] != [0, 3, 0]:
            raise VersionUnsupported([major_version, minor_version, build_version])
        self.on_load()

    def on_load(self):
        """プラグインが読み込まれたとき"""
        pass

    def _on_dispose(self):
        logger.info("Plugin disposed")
        self.on_dispose()

    def on_dispose(self):
        """プラグインが解放されたとき"""
        pass

    def _set_vehicle_spec(self, vehicle_spec:AtsVehicleSpec):
        self.vehicle_spec = vehicle_spec
        self.set_vehicle_spec(vehicle_spec)

    def set_vehicle_spec(self, vehicle_spec:AtsVehicleSpec):
        """車両読み込み時

        Parameters
        ----------
        vehicle_spec : AtsVehicleSpec
            車両諸元
        """
        pass

    def _on_initialize(self, init_handle:AtsInitHandle|int):
        self.on_initialize(init_handle)

    def on_initialize(self, init_handle:AtsInitHandle|int):
        """ゲーム開始時

        Parameters
        ----------
        init_handle : AtsInitHandle|int
            AtsInitHandle: ハンドルの初期状態
            int: 駅ジャンプ時に渡されることがある(専ら負数)
        """
        pass

    def _on_elapse(self, vehicle_state:AtsVehicleState):
        self.vehicle_state = vehicle_state
        self.on_elapse(vehicle_state)

    def on_elapse(self, vehicle_state:AtsVehicleState):
        """1フレームごとに呼ばれる

        Parameters
        ----------
        vehicle_state : AtsVehicleState
            車両の状態量
        """
        pass

    def _on_set_power(self, notch:int):
        self.handles.power = notch
        self.on_set_power(notch)

    def on_set_power(self, notch:int):
        """力行ノッチが変更されたとき

        Parameters
        ----------
        notch : int
            力行ノッチの値
        """
        pass

    def _on_set_brake(self, brake:int):
        self.handles.brake = brake
        self.on_set_brake(brake)

    def on_set_brake(self, brake:int):
        """ブレーキノッチが変更されたとき

        Parameters
        ----------
        brake : int
            ブレーキノッチの値
        """
        pass

    def _on_set_reverser(self, reverser:int):
        self.handles.reverser = reverser
        self.on_set_reverser(reverser)

    def on_set_reverser(self, reverser:int):
        """レバーサーが変更されたとき

        Parameters
        ----------
        reverser : int
            レバーサ位置
        """
        pass

    def _on_key_down(self, key:AtsKey):
        self.keys[key].is_pressed = True
        self.on_key_down(key)

    def on_key_down(self, key:AtsKey):
        """ATSキーが押されたとき

        Parameters
        ----------
        key : AtsKey
            押されたキー
        """
        pass

    def _on_key_up(self, key:AtsKey):
        self.keys[key].is_pressed = False
        self.on_key_up(key)

    def on_key_up(self, key:AtsKey):
        """ATSキーが離されたとき

        Parameters
        ----------
        key : AtsKey
            離されたキー
        """
        pass

    def _on_horn_blow(self, horn:AtsHorn):
        self.horns[horn].is_blowing = True
        self.on_horn_blow(horn)

    def on_horn_blow(self, horn:AtsHorn):
        """警笛が鳴り始めたとき

        Parameters
        ----------
        horn : AtsHorn
            鳴り始めた警笛
        """
        pass

    def _on_horn_stop(self, horn:AtsHorn):
        self.horns[horn].is_blowing = False
        self.on_horn_stop(horn)

    def on_horn_stop(self, horn:AtsHorn):
        """警笛が鳴りやんだとき

        Parameters
        ----------
        horn : AtsHorn
            鳴りやんだ警笛
        """

    def _on_door_open(self):
        self.is_door_closed = False
        self.on_door_open()

    def on_door_open(self):
        """ドアが開いたとき"""
        pass

    def _on_door_close(self):
        self.is_door_closed = True
        self.on_door_close()

    def on_door_close(self):
        """ドアが閉まったとき"""
        pass

    def _on_set_signal(self, index:int):
        self.signal = index
        self.on_set_signal(index)

    def on_set_signal(self, index:int):
        """現在の信号現示が変わったとき

        Parameters
        ----------
        index : int
            信号現示のインデックス
        """
        pass

    def _on_set_beacon_data(self, data:AtsBeaconData):
        self.on_set_beacon_data(data)

    def on_set_beacon_data(self, data:AtsBeaconData):
        """地上子を踏んだとき

        Parameters
        ----------
        data : AtsBeaconData
            地上子のデータ
        """
        pass

    def _on_panel_update(self, index:int, value:int):
        self.panel[index] = value
        self.on_panel_update(index, value)

    def on_panel_update(self, index:int, value:int):
        """パネルの値が変わったとき

        Parameters
        ----------
        index : int
            パネルのインデックス
        value : int
            パネルの値
        """
        pass

    def _on_sound_update(self, index:int, value:AtsSound|int):
        self.sound[index] = value
        self.on_sound_update(index, value)

    def on_sound_update(self, index:int, value:AtsSound|int):
        """音声の値が変わったとき

        Parameters
        ----------
        index : int
            音声のインデックス
        value : AtsSound|int
            AtsSound: 音声の状態
            int: 音量を下げているときのデシベル値(負)
        """
        pass
