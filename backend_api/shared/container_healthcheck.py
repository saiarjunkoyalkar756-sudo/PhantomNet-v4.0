"""Bounded container-local HTTP readiness checker used by Compose health checks."""

from __future__ import annotations

import argparse
import sys
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


def check(url: str, timeout: float) -> int:
    try:
        with urlopen(url, timeout=timeout) as response:  # nosec B310 - URL is operator-supplied container-local health target
            return 0 if 200 <= response.status < 300 else 1
    except (HTTPError, URLError, TimeoutError, ValueError):
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a local service readiness endpoint.")
    parser.add_argument("--url", required=True, help="Container-local HTTP readiness URL.")
    parser.add_argument("--timeout", type=float, default=2.0)
    args = parser.parse_args()
    if not 0.1 <= args.timeout <= 10:
        return 2
    return check(args.url, args.timeout)


if __name__ == "__main__":
    sys.exit(main())
