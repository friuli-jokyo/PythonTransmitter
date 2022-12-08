#define MAX_BUFFER 96

#include <string.h>
#include <Windows.h>



int charcpy_r(char* cbuffer, int* written_bytes)
{
	return 0;
}

template <class Head, class... Tail>
int charcpy_r(char* cbuffer, int* written_bytes, Head&& head, Tail&&... tail)
{
	*written_bytes += sizeof(head);
	if (*written_bytes >= MAX_BUFFER) { return -1; }
	memcpy(cbuffer, &head, sizeof(head));
	return charcpy_r(cbuffer + sizeof(head), written_bytes, tail...) + sizeof(head);
}
