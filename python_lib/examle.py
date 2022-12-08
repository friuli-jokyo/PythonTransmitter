from ctypes import byref, windll, wintypes
from typing import Optional

from bve_receiver import *


def enable_virtual_terminal():
    """コンソール上のカーソルを上に動かしたりするのに必要な設定を行う"""

    STD_OUTPUT_HANDLE = -11
    ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004

    kernel32 = windll.kernel32
    h_out = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
    dw_mode = wintypes.DWORD()
    kernel32.GetConsoleMode(h_out, byref(dw_mode))
    dw_mode.value = dw_mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING
    kernel32.SetConsoleMode(h_out, dw_mode)


class PrintPanelAndAcceleration(BveReceiver):

    # 最後のフレームの時刻と速度
    last_time: Optional[int] = None
    last_speed: Optional[float] = None

    def on_elapse(self, vehicle_state: AtsVehicleState):

        # 最初のフレームは現在時刻と速度を記録して終了
        if self.last_time is None or self.last_speed is None:
            self.last_time = vehicle_state.time
            self.last_speed = vehicle_state.speed
            return

        dv = vehicle_state.speed - self.last_speed # dv [km/h]
        dt = (vehicle_state.time - self.last_time) # dt [ms]

        acceleration = dv / dt * 1000 # [km/h/s]

        self.last_time = vehicle_state.time
        self.last_speed = vehicle_state.speed

        print("\x1b[1;1H", end="") # カーソルを左上に移動
        print("パネル")
        for i in range(16):
            for j in range(16):
                print(f"{self.panel[i*16+j]:4}", end=" ")
            print("\x1b[0K") # 行末までを消去
        print()
        print(f"　速度: {vehicle_state.speed: >+06.3f} km/h")
        print(f"加速度: {acceleration: >+06.3f}km/h/s")
        print(f"ドア開扉: {not self.is_door_closed}")
        print(f"キュー：{self.qsize()}\x1b[0K") # 行末までを消去

if __name__ == "__main__":
    enable_virtual_terminal()
    print("\x1b[?25l" ,flush=True) # カーソル非表示
    PrintPanelAndAcceleration().run()
