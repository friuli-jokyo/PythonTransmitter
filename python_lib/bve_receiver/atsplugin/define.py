from __future__ import annotations

from enum import IntEnum

class AtsKey(IntEnum):
    """ATSキー"""

    S = 0
    """default: Space"""
    A1 = 1
    """default: Insert"""
    A2 = 2
    """default: Delete"""
    B1 = 3
    """default: Home"""
    B2 = 4
    """default: End"""
    C1 = 5
    """default: Page Up"""
    C2 = 6
    """default: Page Down"""
    D = 7
    """default: フルキーボードの2"""
    E = 8
    """default: フルキーボードの3"""
    F = 9
    """default: フルキーボードの4"""
    G = 10
    """default: フルキーボードの5"""
    H = 11
    """default: フルキーボードの6"""
    I = 12
    """default: フルキーボードの7"""
    J = 13
    """default: フルキーボードの8"""
    K = 14
    """default: フルキーボードの9"""
    L = 15
    """default: フルキーボードの0"""

class AtsInitHandle(IntEnum):
    """ゲーム開始時のブレーキ弁の状態"""

    REMOVED = 2
    """抜き取り"""
    EMG = 1
    """非常位置"""
    SVC = 0
    """常用位置"""

class AtsSound(IntEnum):
    """ATSサウンド"""

    STOP = -10000
    """停止"""
    PLAY = 1
    """1回再生"""
    PLAYLOOPING = 0
    """繰り返し再生"""
    CONTINUE = 2
    """継続"""

class AtsHorn(IntEnum):
    """ATS警笛"""

    PRIMARY = 0
    """警笛1"""
    SECONDARY = 1
    """警笛2"""
    MUSIC = 2
    """ミュージックホーン"""

class AtsConstantSpeed(IntEnum):
    """定速制御"""

    CONTINUE = 0
    """継続"""
    ENABLE = 1
    """有効化"""
    DISABLE = 2
    """無効化"""
