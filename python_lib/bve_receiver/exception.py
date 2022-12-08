
class BveReceiverException(Exception):
    pass

class VersionUnsupported(BveReceiverException):
    """サポートされていないバイナリ形式のバージョン"""

    def __init__(self, version:list[int], *args: object) -> None:
        version_str:list[str] = [str(v) for v in version]
        message = f"Version {'.'.join(version_str)} is not supported"
        super().__init__(message, *args)

class UndefinedHeader(BveReceiverException):
    """不明なヘッダ"""

    def __init__(self, header:bytes, *args: object) -> None:
        message = f"Undefined header: {header}"
        super().__init__(message, *args)
