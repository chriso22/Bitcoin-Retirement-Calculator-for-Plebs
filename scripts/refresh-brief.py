#!/usr/bin/env python3
"""Fetch market data and headlines for the Daily Investment Brief."""

from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "brief-data.json"
UA = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; BitcoinRetirementBrief/1.0; "
        "+https://github.com/chriso22/Bitcoin-Retirement-Calculator-for-Plebs)"
    )
}

# Watchlist: symbol -> display metadata
WATCHLIST = [
    {
        "id": "BTC",
        "kind": "crypto",
        "symbol": "BTC-USD",
        "name": "Bitcoin",
        "blurb": "Digital reserve asset; the core of this portfolio lens.",
        "yahoo": "BTC-USD",
        "news_q": "Bitcoin",
    },
    {
        "id": "MSTR",
        "kind": "stock",
        "symbol": "MSTR",
        "name": "Strategy Inc",
        "blurb": "Largest public Bitcoin treasury company.",
        "yahoo": "MSTR",
        "news_q": "MSTR Strategy Bitcoin",
    },
    {
        "id": "ASST",
        "kind": "stock",
        "symbol": "ASST",
        "name": "Strive, Inc.",
        "blurb": "Asset-management Bitcoin treasury (Nasdaq: ASST).",
        "yahoo": "ASST",
        "news_q": "Strive ASST Bitcoin",
    },
    {
        "id": "XXI",
        "kind": "stock",
        "symbol": "XXI",
        "name": "Twenty One Capital",
        "blurb": "Pure-play Bitcoin treasury company.",
        "yahoo": "XXI",
        "news_q": "Twenty One Capital XXI",
    },
    {
        "id": "MRLN",
        "kind": "stock",
        "symbol": "MRLN",
        "name": "Merlin, Inc.",
        "blurb": "Aerospace & defense autonomous-flight software.",
        "yahoo": "MRLN",
        "news_q": "Merlin MRLN autonomous flight",
    },
    {
        "id": "ASTS",
        "kind": "stock",
        "symbol": "ASTS",
        "name": "AST SpaceMobile",
        "blurb": "Space-based cellular broadband (Nasdaq: ASTS).",
        "yahoo": "ASTS",
        "news_q": "ASTS AST SpaceMobile",
    },
    {
        "id": "SPCX",
        "kind": "stock",
        "symbol": "SPCX",
        "name": "SpaceX",
        "blurb": "Space Exploration Technologies Corp. (Nasdaq: SPCX).",
        "yahoo": "SPCX",
        "news_q": "SpaceX SPCX",
    },
]

CTX = ssl.create_default_context()


def fetch_json(url: str, timeout: float = 20.0) -> dict | list | None:
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=CTX) as resp:
            return json.load(resp)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"warn: fetch failed {url}: {exc}")
        return None


def fetch_btc_spot() -> tuple[float | None, str | None]:
    data = fetch_json("https://api.coinbase.com/v2/prices/BTC-USD/spot")
    if isinstance(data, dict):
        try:
            price = float(data["data"]["amount"])
            if price > 0:
                return price, "coinbase"
        except (KeyError, TypeError, ValueError):
            pass
    data = fetch_json(
        "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    )
    if isinstance(data, dict):
        try:
            price = float(data["bitcoin"]["usd"])
            if price > 0:
                return price, "coingecko"
        except (KeyError, TypeError, ValueError):
            pass
    return None, None


def yahoo_chart(symbol: str, range_: str = "1mo") -> dict | None:
    url = (
        "https://query2.finance.yahoo.com/v8/finance/chart/"
        f"{urllib.parse.quote(symbol)}?interval=1d&range={range_}"
    )
    data = fetch_json(url)
    if not isinstance(data, dict):
        return None
    result = (data.get("chart") or {}).get("result")
    if not result:
        return None
    return result[0]


def yahoo_news(query: str, limit: int = 3) -> list[dict]:
    url = (
        "https://query2.finance.yahoo.com/v1/finance/search?"
        + urllib.parse.urlencode({"q": query, "newsCount": limit, "quotesCount": 0})
    )
    data = fetch_json(url)
    if not isinstance(data, dict):
        return []
    out = []
    for item in data.get("news") or []:
        title = item.get("title")
        if not title:
            continue
        out.append(
            {
                "title": title,
                "publisher": item.get("publisher") or "",
                "link": item.get("link") or "",
                "published": item.get("providerPublishTime"),
            }
        )
        if len(out) >= limit:
            break
    return out


def closes_from_chart(chart: dict) -> list[float | None]:
    try:
        closes = chart["indicators"]["quote"][0]["close"]
    except (KeyError, IndexError, TypeError):
        return []
    return [None if c is None else float(c) for c in closes]


def pct_change(price: float | None, prev: float | None) -> float | None:
    if price is None or prev is None or prev == 0:
        return None
    return ((price - prev) / prev) * 100.0


def build_asset(meta: dict) -> dict:
    asset = {
        "id": meta["id"],
        "kind": meta["kind"],
        "symbol": meta["symbol"],
        "name": meta["name"],
        "blurb": meta["blurb"],
        "price": None,
        "prevClose": None,
        "changePct": None,
        "currency": "USD",
        "exchange": None,
        "high52w": None,
        "low52w": None,
        "volume": None,
        "spark": [],
        "news": [],
        "status": "ok",
        "note": None,
        "source": None,
    }

    if meta["id"] == "BTC":
        spot, source = fetch_btc_spot()
        chart = yahoo_chart(meta["yahoo"], "1mo")
        if chart:
            m = chart.get("meta") or {}
            closes = [c for c in closes_from_chart(chart) if c is not None]
            prev = m.get("chartPreviousClose") or m.get("previousClose")
            price = spot if spot is not None else m.get("regularMarketPrice")
            if prev is None and len(closes) >= 2:
                prev = closes[-2]
            asset.update(
                {
                    "price": float(price) if price is not None else None,
                    "prevClose": float(prev) if prev is not None else None,
                    "changePct": pct_change(
                        float(price) if price is not None else None,
                        float(prev) if prev is not None else None,
                    ),
                    "high52w": m.get("fiftyTwoWeekHigh"),
                    "low52w": m.get("fiftyTwoWeekLow"),
                    "spark": closes[-30:],
                    "source": source or "yahoo",
                    "exchange": m.get("fullExchangeName") or "Crypto",
                }
            )
        elif spot is not None:
            asset.update({"price": spot, "source": source, "exchange": "Crypto"})
        else:
            asset["status"] = "unavailable"
            asset["note"] = "Could not fetch Bitcoin price."
        asset["news"] = yahoo_news(meta["news_q"], 3)
        return asset

    chart = yahoo_chart(meta["yahoo"], "1mo")
    if not chart:
        asset["status"] = "unavailable"
        asset["note"] = meta.get("blurb")
        if meta.get("optional_alt"):
            alt = yahoo_chart(meta["optional_alt"], "5d")
            if alt:
                am = alt.get("meta") or {}
                asset["note"] = (
                    f"No quote for {meta['symbol']}. Nearby listing "
                    f"{meta['optional_alt']} ({am.get('shortName') or meta['optional_alt']}) "
                    f"last traded at {am.get('regularMarketPrice')}."
                )
                asset["altSymbol"] = meta["optional_alt"]
                asset["altPrice"] = am.get("regularMarketPrice")
                asset["altName"] = am.get("shortName")
        asset["news"] = yahoo_news(meta["news_q"], 2)
        return asset

    m = chart.get("meta") or {}
    closes = [c for c in closes_from_chart(chart) if c is not None]
    price = m.get("regularMarketPrice")
    prev = m.get("previousClose") or m.get("chartPreviousClose")
    if prev is None and len(closes) >= 2:
        prev = closes[-2]
    # Prefer Yahoo's reported change when present
    chg = m.get("regularMarketChangePercent")
    if chg is None:
        chg = pct_change(
            float(price) if price is not None else None,
            float(prev) if prev is not None else None,
        )

    asset.update(
        {
            "name": (m.get("shortName") or m.get("longName") or meta["name"]).strip(),
            "price": float(price) if price is not None else None,
            "prevClose": float(prev) if prev is not None else None,
            "changePct": float(chg) if chg is not None else None,
            "currency": m.get("currency") or "USD",
            "exchange": m.get("fullExchangeName") or m.get("exchangeName"),
            "high52w": m.get("fiftyTwoWeekHigh"),
            "low52w": m.get("fiftyTwoWeekLow"),
            "volume": m.get("regularMarketVolume"),
            "spark": closes[-30:],
            "source": "yahoo",
        }
    )
    asset["news"] = yahoo_news(meta["news_q"], 3)
    return asset


def movers_summary(assets: list[dict]) -> list[str]:
    ranked = [
        a
        for a in assets
        if a.get("status") == "ok" and isinstance(a.get("changePct"), (int, float))
    ]
    ranked.sort(key=lambda a: abs(a["changePct"]), reverse=True)
    lines = []
    for a in ranked[:3]:
        sign = "+" if a["changePct"] >= 0 else ""
        lines.append(f"{a['id']} {sign}{a['changePct']:.2f}%")
    return lines


def main() -> None:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    assets = [build_asset(meta) for meta in WATCHLIST]
    payload = {
        "generatedAt": generated_at,
        "title": "Daily Investment Brief",
        "watchlist": ["BTC", "MSTR", "ASST", "XXI", "MRLN", "ASTS", "SPCX"],
        "assets": assets,
        "highlights": movers_summary(assets),
        "disclaimer": (
            "Snapshot for personal monitoring only — not financial advice. "
            "Prices may be delayed; verify with your broker before trading."
        ),
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} at {generated_at}")
    for a in assets:
        price = a.get("price")
        chg = a.get("changePct")
        if a["status"] != "ok":
            print(f"  {a['id']}: unavailable")
        else:
            chg_s = f"{chg:+.2f}%" if isinstance(chg, (int, float)) else "n/a"
            print(f"  {a['id']}: {price} ({chg_s})")


if __name__ == "__main__":
    main()
