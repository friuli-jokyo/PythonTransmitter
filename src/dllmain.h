#pragma once
#include "atsplugin.h"

#define ATS_HORN_NUM 3
#define ATS_PANEL_NUM 256
#define ATS_SOUBLE_NUM 256
#define ATS_SOUND_NUM 256

// python���s�t�@�C���̃p�X
TCHAR pythonExePath[MAX_PATH];

// python�X�N���v�g�̃p�X
TCHAR pythonScriptPath[MAX_PATH];

// �R���\�[���ŏ���
bool CLI_minimize = false;

// �������݉\���
bool writable = false;

// �v���Z�X���
PROCESS_INFORMATION ProcessInformation;

// �ǂݍ��݃p�C�v
HANDLE hReadPipe;

// �������݃p�C�v
HANDLE hWritePipe;

// �o�͗p�n���h��
ATS_HANDLES ret_handles;

// �p�l���ω����m�p
int panel_tmp[ATS_PANEL_NUM];

// �T�E���h�ω����m�p
int sound_tmp[ATS_SOUND_NUM];
