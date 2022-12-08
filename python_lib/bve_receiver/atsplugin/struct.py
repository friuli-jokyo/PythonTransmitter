import dataclasses

from .define import *

@dataclasses.dataclass
class AtsVehicleSpec:
    """車両諸元"""

    brake_notches: int
    """ブレーキノッチの数"""
    power_notches: int
    """力行ノッチの数"""
    ats_notch: int
    """ATSキャンセルノッチ"""
    b67_notch: int
    """80%ブレーキ(67°)"""
    cars: int
    """両数"""

@dataclasses.dataclass
class AtsVehicleState:
    """車両状態"""

    location: float
    """z軸車両位置[m]"""
    speed: float
    """車両速度[km/h]"""
    time: int
    """時刻[ms]"""
    bc_pressure: float
    """ブレーキシリンダの圧力[Pa]"""
    mr_pressure: float
    """MR圧[Pa]"""
    er_pressure: float
    """ER圧[Pa]"""
    bp_pressure: float
    """BP圧[Pa]"""
    sap_pressure: float
    """SAP圧[Pa]"""
    current: float
    """電流[A]"""

@dataclasses.dataclass
class AtsBeaconData:
    """地上子データ"""

    type: int
    signal: int
    distance: float
    optional: int

@dataclasses.dataclass
class AtsHandles:
    """車両操作指令"""
    brake: int
    power: int
    reverser: int
    constant_speed: AtsConstantSpeed
