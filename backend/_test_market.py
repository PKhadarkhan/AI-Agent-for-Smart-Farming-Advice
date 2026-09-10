"""
_test_market.py — Market Price Service Test
============================================
Tests the internal MSP-based market service (no external API calls).
"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.market import get_market_prices, get_product_info

PASS = "[PASS]"
FAIL = "[FAIL]"


def run_tests():
    print("=" * 70)
    print("         SMART FARMING MARKET PRICE SERVICE TEST SUITE          ")
    print("=" * 70)

    # 1. Test MSP products
    targets = [
        ("rice",       "en"),
        ("wheat",      "hi"),
        ("tomato",     "te"),
        ("potato",     "en"),
        ("onion",      "hi"),
        ("groundnut",  "te"),
        ("cotton",     "en"),
        ("arhar",      "hi"),
        ("mustard",    "te"),
    ]

    print("=== Testing Product Resolution + MSP/Mandi Data ===")
    all_ok = True
    for crop, lang in targets:
        res = get_market_prices(crop, language=lang)
        # price_type is now "msp_and_sample"
        ok = res.get("success") is True and "msp" in res.get("price_type", "")
        has_msp = res.get("has_msp", False)
        msp = res.get("msp_price")
        mandi_count = len(res.get("mandi_data", []))
        msg = (
            f"display='{res.get('display')}', has_msp={has_msp}, msp=Rs{msp}, mandi_records={mandi_count}"
            if ok else
            res.get("message", res.get("error_type", "unknown"))
        )
        print(f"  {PASS if ok else FAIL} [{lang}] {crop:12s} -> {msg}")
        if not ok:
            all_ok = False

    print()
    # 2. Test alias resolution
    print("=== Testing Alias Resolution ===")
    aliases = [
        ("tomatoes", "tomato",     "Tomato"),
        ("paddy",    "rice",       "Rice"),
        ("aam",      "mango",      "Mango"),
        ("gehun",    "wheat",      "Wheat"),
        ("peanut",   "groundnut",  "Groundnut"),
    ]
    for alias, expected_key, expected_display in aliases:
        info = get_product_info(alias)
        ok = info is not None and info["key"] == expected_key
        print(f"  {PASS if ok else FAIL} '{alias}' → '{info['key'] if info else 'None'}' (expected '{expected_key}')")

    print()
    # 3. Test no-MSP product (fruits / vegetables)
    print("=== Testing No-MSP Product (apple) ===")
    res = get_market_prices("apple")
    ok = res.get("success") is True and res.get("has_msp") is False
    print(f"  {PASS if ok else FAIL} apple has no MSP: has_msp={res.get('has_msp')} notice={'notice' in res}")

    print()
    # 4. Test unknown product
    print("=== Testing Unknown Product ===")
    res = get_market_prices("non_existent_crop_xyz")
    ok = res.get("error_type") == "product_not_found"
    print(f"  {PASS if ok else FAIL} Unknown product returns product_not_found: {ok}")

    print()
    print("=" * 70)
    if all_ok:
        print("SUCCESS: All market service tests passed.")
    else:
        print("WARNING: Some items failed. Check output above.")
    print("=" * 70)
    return all_ok


if __name__ == "__main__":
    run_tests()
