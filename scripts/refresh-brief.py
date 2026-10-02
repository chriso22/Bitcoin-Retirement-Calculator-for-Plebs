#!/usr/bin/env python3
"""Fetch market data and headlines for the Daily Investment Brief."""

from __future__ import annotations

import json
import ssl
import time
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

GROUPS = [
    {
        "id": "bitcoin",
        "title": "Bitcoin",
        "summary": "Spot bitcoin — the core of this brief.",
        "ids": ["BTC"],
        "news_q": "Bitcoin",
    },
    {
        "id": "bitcoin-stocks",
        "title": "Bitcoin-linked equities",
        "summary": "Public companies whose equity often moves with bitcoin exposure.",
        "ids": ["MSTR", "ASST", "XXI"],
        "news_q": "MSTR",
    },
    {
        "id": "space-defense",
        "title": "Space & defense",
        "summary": "Launch, satellite broadband, and autonomous flight names.",
        "ids": ["SPCX", "ASTS", "MRLN"],
        "news_q": "SpaceX",
    },
]

WATCHLIST = [
    {
        "id": "BTC",
        "group": "bitcoin",
        "kind": "crypto",
        "symbol": "BTC-USD",
        "name": "Bitcoin",
        "blurb": "Digital reserve asset.",
        "yahoo": "BTC-USD",
        "news_q": "Bitcoin",
    },
    {
        "id": "MSTR",
        "group": "bitcoin-stocks",
        "kind": "stock",
        "symbol": "MSTR",
        "name": "Strategy Inc",
        "blurb": "Largest public Bitcoin treasury.",
        "yahoo": "MSTR",
        "news_q": "MSTR Strategy Bitcoin",
    },
    {
        "id": "ASST",
        "group": "bitcoin-stocks",
        "kind": "stock",
        "symbol": "ASST",
        "name": "Strive, Inc.",
        "blurb": "Asset-management Bitcoin treasury.",
        "yahoo": "ASST",
        "news_q": "Strive ASST Bitcoin",
    },
    {
        "id": "XXI",
        "group": "bitcoin-stocks",
        "kind": "stock",
        "symbol": "XXI",
        "name": "Twenty One Capital",
        "blurb": "Pure-play Bitcoin treasury.",
        "yahoo": "XXI",
        "news_q": "Twenty One Capital XXI",
    },
    {
        "id": "SPCX",
        "group": "space-defense",
        "kind": "stock",
        "symbol": "SPCX",
        "name": "SpaceX",
        "blurb": "Launch, Starlink, and orbital infrastructure.",
        "yahoo": "SPCX",
        "news_q": "SpaceX SPCX",
    },
    {
        "id": "ASTS",
        "group": "space-defense",
        "kind": "stock",
        "symbol": "ASTS",
        "name": "AST SpaceMobile",
        "blurb": "Space-based cellular broadband.",
        "yahoo": "ASTS",
        "news_q": "ASTS AST SpaceMobile",
    },
    {
        "id": "MRLN",
        "group": "space-defense",
        "kind": "stock",
        "symbol": "MRLN",
        "name": "Merlin, Inc.",
        "blurb": "Autonomous flight software for aerospace & defense.",
        "yahoo": "MRLN",
        "news_q": "Merlin MRLN autonomous flight",
    },
]

CTX = ssl.create_default_context()
_NEWS_CACHE: dict[str, list[dict]] = {}


def fetch_json(url: str, timeout: float = 20.0) -> dict | list | None:
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=CTX) as resp:
            return json.load(resp)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"warn: fetch failed {url}: {exc}")
        return None
    finally:
        time.sleep(0.15)


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


def yahoo_news(query: str, limit: int = 4) -> list[dict]:
    if query in _NEWS_CACHE:
        return _NEWS_CACHE[query][:limit]
    url = (
        "https://query2.finance.yahoo.com/v1/finance/search?"
        + urllib.parse.urlencode({"q": query, "newsCount": max(limit, 4), "quotesCount": 0})
    )
    data = fetch_json(url)
    out: list[dict] = []
    if isinstance(data, dict):
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
            if len(out) >= 6:
                break
    _NEWS_CACHE[query] = out
    return out[:limit]


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


def range_position(price: float | None, low: float | None, high: float | None) -> float | None:
    if price is None or low is None or high is None or high <= low:
        return None
    return max(0.0, min(100.0, (price - low) / (high - low) * 100.0))


def build_asset(meta: dict) -> dict:
    asset = {
        "id": meta["id"],
        "group": meta["group"],
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
        "rangePos": None,
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
            high52 = m.get("fiftyTwoWeekHigh")
            low52 = m.get("fiftyTwoWeekLow")
            asset.update(
                {
                    "price": float(price) if price is not None else None,
                    "prevClose": float(prev) if prev is not None else None,
                    "changePct": pct_change(
                        float(price) if price is not None else None,
                        float(prev) if prev is not None else None,
                    ),
                    "high52w": high52,
                    "low52w": low52,
                    "rangePos": range_position(
                        float(price) if price is not None else None,
                        float(low52) if low52 is not None else None,
                        float(high52) if high52 is not None else None,
                    ),
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
        asset["news"] = yahoo_news(meta["news_q"], 4)
        return asset

    chart = yahoo_chart(meta["yahoo"], "1mo")
    if not chart:
        asset["status"] = "unavailable"
        asset["note"] = f"No active quote for {meta['symbol']}."
        return asset

    m = chart.get("meta") or {}
    closes = [c for c in closes_from_chart(chart) if c is not None]
    price = m.get("regularMarketPrice")
    prev = m.get("previousClose") or m.get("chartPreviousClose")
    if prev is None and len(closes) >= 2:
        prev = closes[-2]
    chg = m.get("regularMarketChangePercent")
    if chg is None:
        chg = pct_change(
            float(price) if price is not None else None,
            float(prev) if prev is not None else None,
        )
    high52 = m.get("fiftyTwoWeekHigh")
    low52 = m.get("fiftyTwoWeekLow")

    asset.update(
        {
            "name": (m.get("shortName") or m.get("longName") or meta["name"]).strip(),
            "price": float(price) if price is not None else None,
            "prevClose": float(prev) if prev is not None else None,
            "changePct": float(chg) if chg is not None else None,
            "currency": m.get("currency") or "USD",
            "exchange": m.get("fullExchangeName") or m.get("exchangeName"),
            "high52w": high52,
            "low52w": low52,
            "rangePos": range_position(
                float(price) if price is not None else None,
                float(low52) if low52 is not None else None,
                float(high52) if high52 is not None else None,
            ),
            "volume": m.get("regularMarketVolume"),
            "spark": closes[-30:],
            "source": "yahoo",
        }
    )
    return asset


def fmt_pct(n: float) -> str:
    sign = "+" if n >= 0 else ""
    return f"{sign}{n:.2f}%"


def analyze_bitcoin(btc: dict | None) -> list[str]:
    if not btc or btc.get("status") != "ok" or not isinstance(btc.get("price"), (int, float)):
        return ["Bitcoin quote unavailable."]
    lines = []
    chg = btc.get("changePct")
    if isinstance(chg, (int, float)):
        tone = "up" if chg >= 0 else "down"
        lines.append(f"Spot is {tone} {fmt_pct(abs(chg))} versus the prior close.")
    rp = btc.get("rangePos")
    if isinstance(rp, (int, float)):
        if rp >= 75:
            band = "near the top of its 52-week range"
        elif rp <= 25:
            band = "near the bottom of its 52-week range"
        else:
            band = "mid-range on a 52-week basis"
        lines.append(f"Trading {band} ({rp:.0f}th percentile).")
    if btc.get("high52w") and btc.get("low52w"):
        lines.append(
            f"52-week band: ${btc['low52w']:,.0f} – ${btc['high52w']:,.0f}."
        )
    return lines[:3]


def analyze_group(assets: list[dict], btc: dict | None, group_id: str) -> list[str]:
    ok = [
        a
        for a in assets
        if a.get("status") == "ok" and isinstance(a.get("changePct"), (int, float))
    ]
    if not ok:
        return ["No usable quotes for this group."]

    ranked = sorted(ok, key=lambda a: a["changePct"], reverse=True)
    best, worst = ranked[0], ranked[-1]
    avg = sum(a["changePct"] for a in ok) / len(ok)
    lines = [
        f"Group average {fmt_pct(avg)}; leader {best['id']} {fmt_pct(best['changePct'])}, "
        f"laggard {worst['id']} {fmt_pct(worst['changePct'])}."
    ]

    btc_chg = btc.get("changePct") if btc else None
    if group_id == "bitcoin-stocks" and isinstance(btc_chg, (int, float)):
        if avg > btc_chg + 1:
            lines.append("Treasury names are outrunning spot bitcoin today.")
        elif avg < btc_chg - 1:
            lines.append("Treasury names are lagging spot bitcoin today.")
        else:
            lines.append("Treasury names are roughly tracking spot bitcoin.")

    if group_id == "space-defense":
        lines.append(
            f"{best['id']} is the session’s standout in space/defense; "
            f"{worst['id']} is the softest print."
        )

    return lines[:3]


def dedupe_news(items: list[dict], limit: int = 4) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for item in items:
        key = (item.get("title") or "").strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item)
        if len(out) >= limit:
            break
    return out


def movers_summary(assets: list[dict]) -> list[str]:
    ranked = [
        a
        for a in assets
        if a.get("status") == "ok" and isinstance(a.get("changePct"), (int, float))
    ]
    ranked.sort(key=lambda a: abs(a["changePct"]), reverse=True)
    return [f"{a['id']} {fmt_pct(a['changePct'])}" for a in ranked[:4]]


def build_sections(assets: list[dict]) -> list[dict]:
    by_id = {a["id"]: a for a in assets}
    meta_by_id = {m["id"]: m for m in WATCHLIST}
    btc = by_id.get("BTC")
    sections = []
    for g in GROUPS:
        members = [by_id[i] for i in g["ids"] if i in by_id]
        news_pool: list[dict] = []
        for a in members:
            news_pool.extend(a.get("news") or [])
            # Ensure ticker news even if build_asset skipped under rate pressure
            q = (meta_by_id.get(a["id"]) or {}).get("news_q") or a["id"]
            news_pool.extend(yahoo_news(q, 3))
        news_pool.extend(yahoo_news(g["news_q"], 4))
        if g["id"] == "bitcoin":
            analysis = analyze_bitcoin(btc)
        else:
            analysis = analyze_group(members, btc, g["id"])
        sections.append(
            {
                "id": g["id"],
                "title": g["title"],
                "summary": g["summary"],
                "assetIds": [a["id"] for a in members],
                "analysis": analysis,
                "news": dedupe_news(news_pool, 4),
            }
        )
    return sections


def main() -> None:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    assets = [build_asset(meta) for meta in WATCHLIST]
    payload = {
        "generatedAt": generated_at,
        "title": "Daily Investment Brief",
        "watchlist": [m["id"] for m in WATCHLIST],
        "assets": assets,
        "sections": build_sections(assets),
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
