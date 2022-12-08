// dllmain.cpp : DLL アプリケーションのエントリ ポイントを定義します。
#include <windows.h>

#include "charcpy.cpp"
#include "dllmain.h"
#include <iostream>
#include <string.h>
#include <tchar.h>


BOOL APIENTRY DllMain( HMODULE hModule,
                       DWORD  ul_reason_for_call,
                       LPVOID lpReserved
                     )
{
    switch (ul_reason_for_call)
    {
    case DLL_PROCESS_ATTACH:
    case DLL_THREAD_ATTACH:
        break;
    case DLL_THREAD_DETACH:
    case DLL_PROCESS_DETACH:
        return FALSE;
        break;
    }

    if (sizeof(int) != 4)
    {
        MessageBox(NULL, "データ型: intのサイズが想定と異なるため、PythonTransmitterを起動せずに続行します。", "PythonTransmitter", MB_OK);
        return FALSE;
    }

    if (sizeof(float) != 4)
    {
        MessageBox(NULL, "データ型: floatのサイズが想定と異なるため、PythonTransmitterを起動せずに続行します。", "PythonTransmitter", MB_OK);
        return FALSE;
    }

    if (sizeof(double) != 8)
    {
        MessageBox(NULL, "データ型: doubleのサイズが想定と異なるため、PythonTransmitterを起動せずに続行します。", "PythonTransmitter", MB_OK);
        return FALSE;
    }
    
    // iniのパス
    TCHAR iniPath[MAX_PATH];

    // dllのフルパスを代入
    GetModuleFileName(hModule, pythonScriptPath, MAX_PATH);
    GetModuleFileName(hModule, iniPath, MAX_PATH);

    // 最後の\を取得することでディレクトリ名化
    TCHAR* last_div = _tcsrchr(pythonScriptPath, _T('\\'));
    if (last_div != NULL)
    {
        last_div = _tcsinc(last_div);
        *last_div = _T('\0');
    }
    char* posIni;
    posIni = strstr(iniPath, ".dll");
    memmove(posIni, ".ini", 4);

    // iniをロード

    // python実行ファイルの場所
    GetPrivateProfileString("Python", "exe", "python", pythonExePath, MAX_PATH, iniPath);

    // pythonスクリプトファイルの相対パス
    TCHAR pythonScriptPathRelative[MAX_PATH];

    GetPrivateProfileString("Python", "script", "PythonTransmitter\\main.py", pythonScriptPathRelative, MAX_PATH, iniPath);

    // コンソール最小化
    CLI_minimize = (GetPrivateProfileInt("Python", "minimize", 0, iniPath) == (UINT)1);

    // pythonの絶対パスを作成
    lstrcat(pythonScriptPath, pythonScriptPathRelative);

    FILE* fp_py;

    // 実行コマンド名が"python"以外なら python実行ファイルの存在確認
    if (_tcscmp(pythonExePath, "python"))
    {
        fopen_s(&fp_py, pythonExePath, "r");
        if (fp_py == NULL)
        {
            MessageBox(NULL, "pythonインタープリタが見つかりませんでした。\nPythonTransmitterを起動せずに続行します。", "PythonTransmitter", MB_OK);
            return FALSE;
        }
        fclose(fp_py);
    }

    // pythonスクリプトの存在確認
    fopen_s(&fp_py, pythonScriptPath, "r");
    if (fp_py == NULL)
    {
        MessageBox(NULL, "pythonスクリプトファイルが見つかりませんでした。\nPythonTransmitterを起動せずに続行します。", "PythonTransmitter", MB_OK);
        return FALSE;
    }
    fclose(fp_py);

    // パネル状態変数初期化
    for (int tmp = 0; tmp < ATS_PANEL_NUM; tmp++)
    {
        panel_tmp[tmp] = 0;
    }

    // サウンド状態変数初期化
    for (int tmp = 0; tmp < ATS_SOUND_NUM; tmp++)
    {
        sound_tmp[tmp] = 0;
    }

    return TRUE;
}

void WINAPI CloseHandles()
{
    writable = false;

    CloseHandle(ProcessInformation.hProcess);
    CloseHandle(ProcessInformation.hThread);

    CloseHandle(hReadPipe);
    CloseHandle(hWritePipe);
}

template<class... T>
void WritePipe(HANDLE hHandle, T... t)
{
    if (!writable) { return; }

    DWORD cpExitCode;

    GetExitCodeProcess(ProcessInformation.hProcess, &cpExitCode);

    char cbuffer[MAX_BUFFER];
    int written_bytes = 0;
    int len = charcpy_r(cbuffer, &written_bytes, t...);
    if (cpExitCode != STILL_ACTIVE || len < 0 || WriteFile(
        hHandle,
        cbuffer,
        len,
        NULL,
        NULL
    ) == 0) {
        CloseHandles();
    }
}

ATS_API void WINAPI Load(void)
{

    // パイプ生成
    SECURITY_ATTRIBUTES PipeAttributes;
    ZeroMemory(&PipeAttributes, sizeof(SECURITY_ATTRIBUTES));

    PipeAttributes.nLength = sizeof(SECURITY_ATTRIBUTES);
    PipeAttributes.bInheritHandle = TRUE;
    PipeAttributes.lpSecurityDescriptor = NULL;

    if (!CreatePipe(&hReadPipe, &hWritePipe, &PipeAttributes, 0))
    {
        return;
    }

    ZeroMemory(&ProcessInformation, sizeof(PROCESS_INFORMATION));

    // 起動オプション初期化
    STARTUPINFO StartUpInfo;
    ZeroMemory(&StartUpInfo, sizeof(STARTUPINFO));
    StartUpInfo.cb = sizeof(STARTUPINFO);
    StartUpInfo.dwFlags = STARTF_USESTDHANDLES | STARTF_USESHOWWINDOW;
    StartUpInfo.hStdInput = hReadPipe;
    StartUpInfo.lpTitle = (LPSTR)"出力ログ";
    if (CLI_minimize)
    {
        StartUpInfo.wShowWindow = SW_SHOWMINNOACTIVE;
    }
    else {
        StartUpInfo.wShowWindow = SW_SHOW;
    }

    // プロセス生成
    char cmd[MAX_PATH*2+10];
    snprintf(cmd, MAX_PATH*2+10, "\"%s\" \"%s\"", pythonExePath, pythonScriptPath);

    if (!CreateProcess(
        NULL,
        cmd,
        NULL,
        NULL,
        TRUE,
        0,
        NULL,
        NULL,
        &StartUpInfo,
        &ProcessInformation
    ))
    {
        CloseHandles();
        return;
    }

    writable = true;

    // 出力用のハンドル初期化
    ret_handles.Power = 0;
    ret_handles.Brake = 0;
    ret_handles.Reverser = 0;
    ret_handles.ConstantSpeed = ATS_CONSTANTSPEED_CONTINUE;

    WritePipe(hWritePipe, '\x00',
        // 0.3.0
        (unsigned char) 0,
        (unsigned char) 3,
        (unsigned char) 0
    );
}

ATS_API void WINAPI Dispose()
{
    WritePipe(hWritePipe, '\x01');
    CloseHandles();
}

ATS_API int WINAPI GetPluginVersion()
{
    return ATS_VERSION;
}

ATS_API void WINAPI SetVehicleSpec(ATS_VEHICLESPEC vehicleSpec)
{
    WritePipe(
        hWritePipe,
        '\x10',
        vehicleSpec.BrakeNotches,
        vehicleSpec.PowerNotches,
        vehicleSpec.AtsNotch,
        vehicleSpec.B67Notch,
        vehicleSpec.Cars
    );
}

ATS_API void WINAPI Initialize(int brake)
{
    WritePipe(
        hWritePipe,
        '\x20',
        brake
    );
}

ATS_API ATS_HANDLES WINAPI Elapse(ATS_VEHICLESTATE vehicleState, int* panel, int* sound)
{
    // パネル変化出力
    for (int tmp = 0; tmp < ATS_PANEL_NUM; tmp++)
    {
        if (panel_tmp[tmp] != panel[tmp])
        {
            WritePipe(
                hWritePipe,
                '\xA0',
                (unsigned char)tmp,
                panel[tmp]
            );
            panel_tmp[tmp] = panel[tmp];
        }
    }

    // サウンド変化出力
    for (int tmp = 0; tmp < ATS_SOUND_NUM; tmp++)
    {
        if (sound_tmp[tmp] != sound[tmp])
        {
            WritePipe(
                hWritePipe,
                '\xA1',
                (unsigned char)tmp,
                sound[tmp]
            );
            sound_tmp[tmp] = sound[tmp];
        }
    }
    
    WritePipe(
        hWritePipe,
        '\x30',
        vehicleState.Location,
        vehicleState.Speed,
        vehicleState.Time,
        vehicleState.BcPressure,
        vehicleState.MrPressure,
        vehicleState.ErPressure,
        vehicleState.BpPressure,
        vehicleState.SapPressure,
        vehicleState.Current
    );

    return ret_handles;
}

ATS_API void WINAPI SetPower(int notch)
{
    WritePipe(
        hWritePipe,
        '\x40',
        notch
    );
    ret_handles.Power = notch;
}

ATS_API void WINAPI SetBrake(int notch)
{
    WritePipe(
        hWritePipe,
        '\x41',
        notch
    );
    ret_handles.Brake = notch;
}

ATS_API void WINAPI SetReverser(int pos)
{
    WritePipe(
        hWritePipe,
        '\x42',
        pos
    );
    ret_handles.Reverser = pos;
}

ATS_API void WINAPI KeyDown(int atsKeyCode)
{
    WritePipe(
        hWritePipe,
        '\x50',
        atsKeyCode
    );
}

ATS_API void WINAPI KeyUp(int atsKeyCode)
{
    WritePipe(
        hWritePipe,
        '\x51',
        atsKeyCode
    );
}

ATS_API void WINAPI HornBlow(int atsHornBlowIndex)
{
    WritePipe(
        hWritePipe,
        '\x60',
        atsHornBlowIndex
    );
}

ATS_API void WINAPI DoorOpen()
{
    WritePipe(hWritePipe, '\x70');
}

ATS_API void WINAPI DoorClose()
{
    WritePipe(hWritePipe, '\x71');
}

ATS_API void WINAPI SetSignal(int signal)
{
    WritePipe(
        hWritePipe,
        '\x80',
        signal
    );
}

ATS_API void WINAPI SetBeaconData(ATS_BEACONDATA beaconData)
{
    WritePipe(
        hWritePipe,
        '\x90',
        beaconData.Type,
        beaconData.Signal,
        beaconData.Distance,
        beaconData.Optional
    );
}