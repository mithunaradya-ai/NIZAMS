"""Small systemd notification client; no extra runtime dependency is required."""

from __future__ import annotations

import os
import socket


def notify(message: str) -> None:
    """Send a systemd service-manager datagram when running under systemd."""
    address = os.environ.get("NOTIFY_SOCKET")
    if not address:
        return
    if address.startswith("@"):
        address = "\0" + address[1:]
    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as client:
        client.connect(address)
        client.sendall(message.encode("utf-8"))
