"""Minimal SMB/CIFS helpers for reading a NAS share over the network.

Lets the integration read images straight from a Windows/NAS share path such as
``//192.168.0.228/Public/Posters`` without the share being mounted into the
Home Assistant host. Backed by the pure-python ``smbprotocol`` package.
"""

from __future__ import annotations


def is_smb(path: str | None) -> bool:
    """True for //server/share, \\\\server\\share, or smb:// paths."""
    if not path:
        return False
    return path.startswith(("//", "\\\\")) or path[:6].lower() == "smb://"


def normalize(path: str) -> str:
    """Return a UNC path using backslashes: \\\\server\\share\\dir."""
    p = path
    if p[:6].lower() == "smb://":
        p = p[6:]
    p = p.replace("/", "\\")
    return "\\\\" + p.lstrip("\\")


def server(path: str) -> str:
    return normalize(path).lstrip("\\").split("\\", 1)[0]


def basename(path: str) -> str:
    return path.replace("/", "\\").rstrip("\\").rsplit("\\", 1)[-1]


def _register(path: str, username: str | None, password: str | None) -> None:
    import smbclient

    smbclient.register_session(
        server(path),
        username=username or "guest",
        password=password or "",
    )


def scan(
    path: str,
    recursive: bool,
    extensions: tuple[str, ...],
    username: str | None = None,
    password: str | None = None,
) -> list[str]:
    """List image files on the share (blocking; run in an executor)."""
    import smbclient

    base = normalize(path)
    _register(path, username, password)
    result: list[str] = []
    if recursive:
        for root, _dirs, files in smbclient.walk(base):
            for name in files:
                if name.lower().endswith(extensions):
                    result.append(root.rstrip("\\") + "\\" + name)
    else:
        for name in smbclient.listdir(base):
            if name.lower().endswith(extensions):
                result.append(base.rstrip("\\") + "\\" + name)
    return sorted(result)


def read(path: str, username: str | None = None, password: str | None = None) -> bytes:
    """Read a single file from the share (blocking; run in an executor)."""
    import smbclient

    _register(path, username, password)
    with smbclient.open_file(path, mode="rb") as handle:
        return handle.read()
