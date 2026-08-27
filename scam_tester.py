#!/usr/bin/env python3
"""
Scam Awareness Tool — Test Runner
==================================
Sends test messages to your n8n webhook and prints a results table.

SETUP:
  1. Install requests:  pip install requests
  2. Set your webhook URL below in WEBHOOK_URL
  3. Run:  python scam_tester.py

OPTIONS:
  python scam_tester.py                  # run all tests
  python scam_tester.py --tag smishing   # run only tests tagged "smishing"
  python scam_tester.py --tag harmless   # run only harmless tests
  python scam_tester.py --verbose        # show full explanation in output
  python scam_tester.py --save           # save results to results.json
"""

import requests
import json
import argparse
import time
import sys
from datetime import datetime

# ── CONFIGURATION ─────────────────────────────────────────────────────────────
WEBHOOK_URL = "https://mbaghdadi6g.app.n8n.cloud/webhook/fraud-check"   # paste your n8n test or production URL
TIMEOUT_SECONDS = 60                    # max wait per request
DELAY_BETWEEN_TESTS = 15.0              # seconds between requests (avoid rate limits)
# ─────────────────────────────────────────────────────────────────────────────


# ── TEST CASES ────────────────────────────────────────────────────────────────
# Each test case has:
#   id          : unique identifier
#   name        : human readable name
#   tags        : list of tags for filtering (e.g. smishing, narrative, harmless)
#   message     : the text to send to the tool
#   expected    : what we expect back
#     risk_level  : exact expected value
#     scam_type   : exact expected value
#     score_min   : minimum acceptable score
#     score_max   : maximum acceptable score
# ─────────────────────────────────────────────────────────────────────────────
TEST_CASES = [
    {
        "id": "T01",
        "name": "Toll smishing",
        "tags": ["smishing", "high_risk", "link"],
        "message": "Your EZPass account has an unpaid toll balance of $3.85. Failure to pay within 24 hours will result in a $35 late fee. Tap here to pay now: https://ezpass.com-verify.vip/pay",
        "expected": {
            "risk_level": "high risk",
            "scam_type": "toll_smishing",
            "score_min": 75,
            "score_max": 100,
        },
    },
    {
        "id": "T02",
        "name": "USPS package smishing",
        "tags": ["smishing", "high_risk", "link", "usps"],
        "message": "USPS: Your package has been held at our facility due to an incomplete address. Please update your delivery details within 24 hours to avoid return: https://usps.com-track.vip/update",
        "expected": {
            "risk_level": "high risk",
            "scam_type": "usps_package_smishing",
            "score_min": 75,
            "score_max": 100,
        },
    },
    {
        "id": "T03",
        "name": "Bank phishing",
        "tags": ["phishing", "high_risk", "bank"],
        "message": "ALERT: Unusual activity has been detected on your bank account. Your account has been temporarily restricted. Please verify your identity immediately by clicking here: https://secure-bank-verify.xyz/login",
        "expected": {
            "risk_level": "high risk",
            "scam_type": "bank_phishing",
            "score_min": 75,
            "score_max": 100,
        },
    },
    {
        "id": "T04",
        "name": "Tech support scam with phone",
        "tags": ["tech_support", "high_risk"],
        "message": "WARNING: Your computer has been infected with a virus. Your personal data is at risk. Call Microsoft Support immediately at +1-800-555-0199 to prevent data loss. Do not shut down your computer.",
        "expected": {
            "risk_level": "high risk",
            "scam_type": "tech_support",
            "score_min": 75,
            "score_max": 100,
        },
    },
    {
        "id": "T05",
        "name": "Tech support scam without phone",
        "tags": ["tech_support", "high_risk"],
        "message": "WARNING: Your computer has been infected with a virus. Your personal data is at risk. Call Microsoft Support immediately to prevent data loss. Do not shut down your computer.",
        "expected": {
            "risk_level": "high risk",
            "scam_type": "tech_support",
            "score_min": 60,
            "score_max": 100,
        },
    },
    {
        "id": "T06",
        "name": "IRS government impersonation",
        "tags": ["government", "high_risk", "arrest_threat"],
        "message": "This is the IRS. You owe $2,400 in back taxes. A warrant has been issued for your arrest. You must call back immediately at +1-800-555-0100 to resolve this before law enforcement arrives.",
        "expected": {
            "risk_level": "high risk",
            "scam_type": "government_impersonation",
            "score_min": 80,
            "score_max": 100,
        },
    },
    {
        "id": "T07",
        "name": "Social Security impersonation",
        "tags": ["government", "high_risk"],
        "message": "This is the Social Security Administration. Your SSN has been suspended due to suspicious activity. You must call back immediately to avoid arrest. Call +1-800-555-0101.",
        "expected": {
            "risk_level": "high risk",
            "scam_type": "government_impersonation",
            "score_min": 75,
            "score_max": 100,
        },
    },
    {
        "id": "T08",
        "name": "Gift card scam",
        "tags": ["gift_card", "high_risk"],
        "message": "Your Microsoft account has been compromised. To protect your account you must purchase a $200 Google Play gift card immediately and send us the code. Do not tell anyone about this notice.",
        "expected": {
            "risk_level": "high risk",
            "scam_type": "gift_card_scam",
            "score_min": 78,
            "score_max": 100,
        },
    },
    {
        "id": "T09",
        "name": "Lottery prize scam",
        "tags": ["lottery", "high_risk"],
        "message": "Congratulations! You have been selected to receive $850,000 from our annual sweepstakes. To release your winnings a small processing fee of $99 is required. Reply with your details to claim your prize today.",
        "expected": {
            "risk_level": "high risk",
            "scam_type": "lottery_prize",
            "score_min": 75,
            "score_max": 100,
        },
    },
    {
        "id": "T10",
        "name": "Romance crypto scam",
        "tags": ["romance", "high_risk", "crypto", "narrative"],
        "message": "I've been thinking about you so much lately. I want to share a special investment opportunity my uncle taught me — guaranteed returns on crypto. Don't share this with anyone, it's only for people I truly trust.",
        "expected": {
            "risk_level": "high risk",
            "scam_type": "romance_or_pig_butchering",
            "score_min": 75,
            "score_max": 100,
        },
    },
    {
        "id": "T11",
        "name": "Overseas emergency scam",
        "tags": ["romance", "high_risk", "narrative", "overseas"],
        "message": "I care about you deeply, but I'm stuck overseas and need help paying for my flight home. My wallet was stolen and I have no way to get back. Can you send me some money? I promise I will pay you back as soon as I get home.",
        "expected": {
            "risk_level": "high risk",
            "scam_type": "romance_or_pig_butchering",
            "score_min": 75,
            "score_max": 100,
        },
    },
    {
        "id": "T12",
        "name": "Grandparent scam",
        "tags": ["romance", "high_risk", "narrative", "grandparent"],
        "message": "Grandma it's me, I'm in jail and need bail money urgently. Please don't tell mom or dad. Send $500 through Western Union as soon as possible. I will explain everything later.",
        "expected": {
            "risk_level": "high risk",
            "scam_type": "romance_or_pig_butchering",
            "score_min": 78,
            "score_max": 100,
        },
    },
    {
        "id": "T13",
        "name": "Overpayment scam",
        "tags": ["overpayment", "high_risk"],
        "message": "Hi, I am interested in buying the item you listed. I will send you a cashier's check for $2,500 but I accidentally made it out for $3,000. Please just wire back the $500 difference when you receive it. Thanks.",
        "expected": {
            "risk_level": "high risk",
            "scam_type": "overpayment",
            "score_min": 65,
            "score_max": 100,
        },
    },
    {
        "id": "T14",
        "name": "Fake PayPal billing",
        "tags": ["fake_billing", "high_risk"],
        "message": "PayPal. Initiating Business Account Setup for PayPal. Your business account has been successfully created and verified using your Social Security Number. A one-time account setup fee of $304.76 has been processed. If you did not request this account please contact support immediately.",
        "expected": {
            "risk_level": "high risk",
            "scam_type": "fake_billing_notice",
            "score_min": 75,
            "score_max": 100,
        },
    },
    {
        "id": "T15",
        "name": "Job scam — reshipping",
        "tags": ["job_scam", "risky"],
        "message": "We are hiring work from home package processors. Earn $500 per week receiving and reshipping packages from your home address. No experience needed. Reply to apply.",
	"expected": {
    		"risk_level": "unclear",
    		"scam_type": "job_scam",
    		"score_min": 40,
    		"score_max": 65,
	},
    },
    {
        "id": "T16",
        "name": "Romance subtle money request",
        "tags": ["romance", "risky", "narrative"],
        "message": "You mean the world to me. I have never felt this way about anyone before. I hate to ask but I am in a difficult situation right now and could really use your help with a small amount just to get through this week.",
        "expected": {
            "risk_level": "high risk",
            "scam_type": "romance_or_pig_butchering",
            "score_min": 60,
            "score_max": 100,
        },
    },
    {
        "id": "T17",
        "name": "Ambiguous account review",
        "tags": ["unclear"],
        "message": "Hi, this is a reminder that your annual account review is coming up. Please call us at your convenience to go over your options.",
        "expected": {
            "risk_level": "harmless",
            "scam_type": "none_detected",
            "score_min": 0,
            "score_max": 29,
        },
    },
    {
        "id": "T18",
        "name": "Dental appointment reminder",
        "tags": ["harmless", "short_circuit"],
        "message": "Reminder: You have a dental appointment scheduled for tomorrow at 2:00 PM. Please call us if you need to reschedule.",
        "expected": {
            "risk_level": "harmless",
            "scam_type": "none_detected",
            "score_min": 0,
            "score_max": 15,
        },
    },
    {
        "id": "T19",
        "name": "Order confirmation",
        "tags": ["harmless", "short_circuit"],
        "message": "Thank you for your order. Your package has been shipped and is on its way. You will receive a delivery confirmation when it arrives.",
        "expected": {
            "risk_level": "harmless",
            "scam_type": "none_detected",
            "score_min": 0,
            "score_max": 15,
        },
    },
    {
        "id": "T20",
        "name": "Very short input",
        "tags": ["harmless", "short_circuit"],
        "message": "Call me back",
        "expected": {
            "risk_level": "harmless",
            "scam_type": "none_detected",
            "score_min": 0,
            "score_max": 15,
        },
    },

{
    "id": "T21",
    "name": "Emotional financial coercion",
    "tags": ["behavioral", "narrative", "novel"],
    "message": "I really love you but I can not continue this relationship unless you transfer your salary to my account",
    "expected": {
        "risk_level": "risky",
        "scam_type": "romance_or_pig_butchering",
        "score_min": 60,
        "score_max": 100,
    },
},



{
    "id": "T22",
    "name": "Fake urgency with vague threat",
    "tags": ["behavioral", "narrative", "novel"],
    "message": "I need to speak with you urgently about something that could seriously affect your future. Please respond within the next 2 hours or I will have no choice but to proceed without you.",
    "expected": {
        "risk_level": "risky",
        "scam_type": "none_detected",
        "score_min": 60,
        "score_max": 100,
    },
},
{
    "id": "T23",
    "name": "Isolation with financial pressure",
    "tags": ["behavioral", "narrative", "novel"],
    "message": "Please do not mention this to anyone in your family. I have found a way for us to secure our future together but we need to move quickly and quietly before others find out about this opportunity.",
    "expected": {
        "risk_level": "risky",
        "scam_type": "none_detected",
        "score_min": 60,
        "score_max": 100,
    },
},
{
    "id": "T24",
    "name": "Authority impersonation without keywords",
    "tags": ["behavioral", "narrative", "novel"],
    "message": "This is an official notice. Your file has been flagged and requires immediate attention. Failure to respond within 48 hours will result in automatic processing which may not be in your favor.",
    "expected": {
        "risk_level": "risky",
        "scam_type": "none_detected",
        "score_min": 60,
        "score_max": 100,
    },
},
{
    "id": "T25",
    "name": "Too good to be true without prize language",
    "tags": ["behavioral", "narrative", "novel"],
    "message": "You were specifically selected from thousands of candidates based on your profile. This is a time-sensitive opportunity that guarantees a significant return. Only a handful of people receive this each year.",
    "expected": {
        "risk_level": "risky",
        "scam_type": "none_detected",
        "score_min": 60,
        "score_max": 100,
    },
},
{
    "id": "T26",
    "name": "Grandparent scam without jail keywords",
    "tags": ["behavioral", "narrative", "novel"],
    "message": "It is me. I am in a very bad situation right now and I really need your help. Please do not tell anyone else in the family. I need you to send me some money as soon as possible and I will explain everything later.",
    "expected": {
        "risk_level": "risky",
        "scam_type": "none_detected",
        "score_min": 60,
        "score_max": 100,
    },
},
{
    "id": "T27",
    "name": "Crypto investment without crypto keywords",
    "tags": ["behavioral", "narrative", "novel"],
    "message": "My mentor showed me a trading method that has changed my life completely. I have been making consistent returns every week with almost no risk. I want to share this with you because I trust you. Can we talk about getting you started?",
    "expected": {
        "risk_level": "risky",
        "scam_type": "none_detected",
        "score_min": 60,
        "score_max": 100,
    },
},
{
    "id": "T28",
    "name": "Job scam without job keywords",
    "tags": ["behavioral", "narrative", "novel"],
    "message": "We came across your profile and believe you would be perfect for a flexible arrangement we are offering. You would work from home on your own schedule and receive weekly payments. No experience necessary. Interested?",
    "expected": {
        "risk_level": "unclear",
        "scam_type": "none_detected",
        "score_min": 60,
        "score_max": 100,
    },
},
{
    "id": "T29",
    "name": "Emotional blackmail",
    "tags": ["behavioral", "narrative", "novel"],
    "message": "After everything I have done for you I cannot believe you would leave me in this situation. I just need this one thing from you and I promise I will never ask again. If you really care about me you will help me right now.",
    "expected": {
        "risk_level": "risky",
        "scam_type": "none_detected",
        "score_min": 60,
        "score_max": 100,
    },
},


{
    "id": "T30",
    "name": "Phone check - no phone number in message",
    "tags": ["phone_check"],
    "message": "Your package has been held. Please confirm your address to release it.",
    "expected": {
        "risk_level": "risky",
        "scam_type": "none_detected",
        "score_min": 0,
        "score_max": 59,
    },
},
{
    "id": "T31",
    "name": "Phone check - phone number present but not spam",
    "tags": ["phone_check"],
    "message": "This is the IRS. You owe back taxes. Call us immediately at +1-800-829-1040 to resolve this.",
    "expected": {
        "risk_level": "high risk",
        "scam_type": "government_impersonation",
        "score_min": 75,
        "score_max": 100,
    },
},

{
    "id": "T32",
    "name": "Phone check - multiple phone numbers in message",
    "tags": ["phone_check"],
    "message": "Microsoft Support Alert: Your computer is infected. Call +1-888-555-0191 or +1-877-555-0142 immediately to fix this before your data is lost.",
    "expected": {
        "risk_level": "high risk",
        "scam_type": "tech_support",
        "score_min": 75,
        "score_max": 100,
    },
},

{
    "id": "T33",
    "name": "USPS smishing — newly registered .vip domain",
    "tags": ["smishing", "high_risk", "link", "usps", "domain_age"],
    # Key signal: usps.com-trackingupdate.vip — brand name prepended before a
    # hyphen to mimic a legitimate subdomain, registered on a .vip TLD which is
    # typically days old. Domain/IP age layer should boost score significantly.
    "message": "USPS: Your package could not be delivered. A $3.50 redelivery fee is required immediately or your package will be returned. Pay now to avoid delays: https://usps.com-trackingupdate.vip/pay?id=8842991",
    "expected": {
        "risk_level": "high risk",
        "scam_type": "usps_package_smishing",
        "score_min": 75,
        "score_max": 100,
    },
},


]
# ─────────────────────────────────────────────────────────────────────────────


def send_test(message: str) -> dict:
    """Send a message to the webhook and return the response."""
    payload = {"raw_text": message}
    response = requests.post(WEBHOOK_URL, json=payload, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    data = response.json()
    print(f"\nRAW RESPONSE: {json.dumps(data, indent=2)[:500]}")
    return data if isinstance(data, dict) else data[0] if isinstance(data, list) else {}


def evaluate_result(test: dict, result: dict) -> dict:
    expected = test["expected"]
    actual_score = result.get("risk_score", 0)
    actual_level = result.get("risk_level", "unknown")
    actual_type = result.get("scam_type", "unknown")

    score_pass = expected["score_min"] <= actual_score <= expected["score_max"]
    
    # For novel tests, pass if detected as risky or high risk
    if "novel" in test.get("tags", []):
        level_pass = actual_level in ["risky", "high risk"]
    else:
        level_pass = actual_level == expected["risk_level"]
    
    type_pass = actual_type == expected["scam_type"]
    overall_pass = score_pass and level_pass




    return {
        "score_pass": score_pass,
        "level_pass": level_pass,
        "type_pass": type_pass,
        "overall_pass": overall_pass,
        "actual_score": actual_score,
        "actual_level": actual_level,
        "actual_type": actual_type,
        "expected_score_range": f"{expected['score_min']}–{expected['score_max']}",
        "expected_level": expected["risk_level"],
        "expected_type": expected["scam_type"],
    }


def print_results_table(results: list):
    """Print a formatted results table to the terminal."""
    col_widths = {
        "id": 4,
        "name": 35,
        "score": 12,
        "level": 20,
        "type": 28,
        "pass": 6,
    }

    header = (
        f"{'ID':<{col_widths['id']}} "
        f"{'Test Name':<{col_widths['name']}} "
        f"{'Score':<{col_widths['score']}} "
        f"{'Risk Level':<{col_widths['level']}} "
        f"{'Scam Type':<{col_widths['type']}} "
        f"{'Pass':<{col_widths['pass']}}"
    )
    separator = "─" * len(header)

    print("\n" + separator)
    print(header)
    print(separator)

    passed = 0
    failed = 0
    errors = 0

    for r in results:
        if r.get("error"):
            status = "ERROR"
            row = (
                f"{r['id']:<{col_widths['id']}} "
                f"{r['name']:<{col_widths['name']}} "
                f"{'—':<{col_widths['score']}} "
                f"{'—':<{col_widths['level']}} "
                f"{str(r['error'])[:26]:<{col_widths['type']}} "
                f"{'✗ ERR':<{col_widths['pass']}}"
            )
            errors += 1
        else:
            ev = r["evaluation"]
            status = "PASS" if ev["overall_pass"] else "FAIL"
            score_display = f"{ev['actual_score']} ({ev['expected_score_range']})"
            level_display = ev["actual_level"]
            if not ev["level_pass"]:
                level_display += f" ≠ {ev['expected_level']}"
            type_display = ev["actual_type"]
            if not ev["type_pass"]:
                type_display += f"*"

            row = (
                f"{r['id']:<{col_widths['id']}} "
                f"{r['name'][:34]:<{col_widths['name']}} "
                f"{score_display[:11]:<{col_widths['score']}} "
                f"{level_display[:19]:<{col_widths['level']}} "
                f"{type_display[:27]:<{col_widths['type']}} "
                f"{'✓ PASS' if status == 'PASS' else '✗ FAIL':<{col_widths['pass']}}"
            )
            if status == "PASS":
                passed += 1
            else:
                failed += 1

        print(row)

    print(separator)

    # Summary
    total = len(results)
    print(f"\nResults: {passed}/{total} passed  |  {failed} failed  |  {errors} errors")

    if failed > 0 or errors > 0:
        print("\nFailed tests:")
        for r in results:
            if r.get("error"):
                print(f"  {r['id']} {r['name']}: ERROR — {r['error']}")
            elif not r["evaluation"]["overall_pass"]:
                ev = r["evaluation"]
                issues = []
                if not ev["score_pass"]:
                    issues.append(f"score {ev['actual_score']} not in {ev['expected_score_range']}")
                if not ev["level_pass"]:
                    issues.append(f"level '{ev['actual_level']}' expected '{ev['expected_level']}'")
                print(f"  {r['id']} {r['name']}: {', '.join(issues)}")

    print()


def print_verbose(test: dict, result: dict, evaluation: dict):
    """Print full details for a single test."""
    print(f"\n{'═' * 60}")
    print(f"  {test['id']} — {test['name']}")
    print(f"{'═' * 60}")
    print(f"  Message:     {test['message'][:80]}...")
    print(f"  Score:       {evaluation['actual_score']} (expected {evaluation['expected_score_range']})")
    print(f"  Risk Level:  {evaluation['actual_level']} (expected {evaluation['expected_level']})")
    print(f"  Scam Type:   {evaluation['actual_type']} (expected {evaluation['expected_type']})")
    print(f"  Explanation: {result.get('plain_language_explanation', '')[:200]}")
    print(f"  Pass:        {'✓' if evaluation['overall_pass'] else '✗'}")


def run_tests(tags=None, verbose=False, save=False):
    """Run all tests or a filtered subset."""

    if WEBHOOK_URL == "YOUR_WEBHOOK_URL_HERE":
        print("ERROR: Please set your webhook URL in the WEBHOOK_URL variable at the top of this file.")
        sys.exit(1)

    # Filter by tags if specified
    tests_to_run = TEST_CASES
    if tags:
        tests_to_run = [t for t in TEST_CASES if any(tag in t["tags"] for tag in tags)]
        if not tests_to_run:
            print(f"No tests found with tags: {tags}")
            sys.exit(1)

    print(f"\nScam Awareness Tool — Test Runner")
    print(f"Webhook: {WEBHOOK_URL}")
    print(f"Running {len(tests_to_run)} tests at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'─' * 50}")

    all_results = []

    for i, test in enumerate(tests_to_run):
        print(f"  Running {test['id']} {test['name']}...", end=" ", flush=True)

        try:
            result = send_test(test["message"])
            evaluation = evaluate_result(test, result)
            status = "✓" if evaluation["overall_pass"] else "✗"
            print(f"{status} (score: {evaluation['actual_score']}, level: {evaluation['actual_level']})")

            all_results.append({
                "id": test["id"],
                "name": test["name"],
                "result": result,
                "evaluation": evaluation,
            })

            if verbose:
                print_verbose(test, result, evaluation)

        except requests.exceptions.Timeout:
            print("✗ TIMEOUT")
            all_results.append({"id": test["id"], "name": test["name"], "error": "Request timed out"})

        except requests.exceptions.ConnectionError:
            print("✗ CONNECTION ERROR")
            all_results.append({"id": test["id"], "name": test["name"], "error": "Could not connect to webhook"})

        except Exception as e:
            print(f"✗ ERROR: {e}")
            all_results.append({"id": test["id"], "name": test["name"], "error": str(e)})

        # Delay between requests to avoid overwhelming the workflow
        if i < len(tests_to_run) - 1:
            time.sleep(DELAY_BETWEEN_TESTS)

    # Print summary table
    print_results_table(all_results)

    # Save results to file if requested
    if save:
        filename = f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "webhook": WEBHOOK_URL,
                "total": len(all_results),
                "results": all_results,
            }, f, indent=2)
        print(f"Results saved to {filename}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scam Awareness Tool Test Runner")
    parser.add_argument("--tag", nargs="+", help="Run only tests with these tags")
    parser.add_argument("--verbose", action="store_true", help="Show full explanation for each test")
    parser.add_argument("--save", action="store_true", help="Save results to a JSON file")
    args = parser.parse_args()

    run_tests(tags=args.tag, verbose=args.verbose, save=args.save)
