#pragma once
#include "atsplugin.h"

#define ATS_HORN_NUM 3
#define ATS_PANEL_NUM 256
#define ATS_SOUBLE_NUM 256
#define ATS_SOUND_NUM 256

// python実行ファイルのパス
TCHAR pythonExePath[MAX_PATH];

// pythonスクリプトのパス
TCHAR pythonScriptPath[MAX_PATH];

// コンソール最小化
bool CLI_minimize = false;

// 書き込み可能状態
bool writable = false;

// プロセス情報
PROCESS_INFORMATION ProcessInformation;

// 読み込みパイプ
HANDLE hReadPipe;

// 書き込みパイプ
HANDLE hWritePipe;

// 出力用ハンドル
ATS_HANDLES ret_handles;

// パネル変化検知用
int panel_tmp[ATS_PANEL_NUM];

// サウンド変化検知用
int sound_tmp[ATS_SOUND_NUM];
