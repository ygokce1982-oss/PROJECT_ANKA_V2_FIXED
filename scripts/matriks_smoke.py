"""Safe read-only Matriks test CLI. Never prints JWT or performs trading."""

from __future__ import annotations

import argparse
import sys

from core.providers.matriks_provider import MatriksProvider


def main() -> int:
    parser = argparse.ArgumentParser(description="Matriks read-only connectivity checks")
    parser.add_argument("--discovery", action="store_true", help="Public issuer-based discovery")
    parser.add_argument("--bars", action="store_true", help="Authenticated bar request")
    parser.add_argument("--symbol", default="GARAN")
    parser.add_argument("--start", default="2026-10-01")
    parser.add_argument("--end", default="2026-10-08")
    parser.add_argument("--period", default="1day")
    args = parser.parse_args()
    if not (args.discovery or args.bars):
        parser.error("Specify --discovery and/or --bars")
    client = MatriksProvider()
    try:
        if args.discovery:
            payload = client.discover()
            print(
                "Matriks discovery: OK; REST groups:",
                len(payload.get("rest", {})),
                "MQTT groups:",
                len(payload.get("mqtt", {})),
            )
        if args.bars:
            bars = client.fetch_bars(
                symbol=args.symbol, start=args.start, end=args.end, period=args.period
            )
            print(
                "Matriks bars: OK; symbol:",
                args.symbol,
                "count:",
                len(bars),
                "latest timestamp (ms):",
                bars[-1]["timestamp_ms"] if bars else "none",
            )
    except Exception as exc:
        # Avoid dumping HTTP headers or credentials to console/logs.
        print(f"Matriks check failed: {type(exc).__name__}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
