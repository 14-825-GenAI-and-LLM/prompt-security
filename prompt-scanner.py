"""
Advanced llm-guard API Client
=============================

Architecture:
-------------
User Input
   ↓
llm-guard API (Docker container)
   ↓
Sanitized / Validated Prompt
   ↓
LLM / Agent

Key Design Goals:
- Centralized security gateway
- Clear policy gating before model execution
- Production-style structure for agentic systems

IMPORTANT:
-----------
This client uses:
    Authorization: Bearer <AUTH_TOKEN>

Run it after initializing llm-guard with:
docker run -d --name llm-guard-api -p 9999:8000 -e AUTH_TOKEN="hello" laiyer/llm-guard-api:latest

Then wait for 5-10 minutes before running this script.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Any
import requests
import os


# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------

API_URL = os.getenv("LLM_GUARD_URL", "http://localhost:9999")
AUTH_TOKEN = os.getenv("LLM_GUARD_TOKEN", "hello")

HEADERS = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

HTTP_TIMEOUT = 10


# -------------------------------------------------------------------
# Result Models
# -------------------------------------------------------------------

@dataclass
class PromptScanResult:
    """
    Normalized result for prompt scanning.

    Attributes:
        raw_response:
            Full JSON returned by llm-guard

        is_valid:
            Boolean indicating whether prompt passed all scanners

        details:
            Scanner-level metadata (risk scores, flags, etc.)
    """
    raw_response: Dict[str, Any]
    is_valid: bool
    details: Dict[str, Any]


@dataclass
class OutputScanResult:
    raw_response: Dict[str, Any]
    is_valid: bool
    details: Dict[str, Any]


# -------------------------------------------------------------------
# Core API Call Helpers
# -------------------------------------------------------------------

def call_llm_guard(endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generic function for calling llm-guard endpoints.

    Why this abstraction?
    ---------------------
    - Centralizes authentication
    - Centralizes error handling
    - Easier to plug into async or middleware later
    """
    url = f"{API_URL}{endpoint}"

    try:
        response = requests.post(
            url,
            json=payload,
            headers=HEADERS,
            timeout=HTTP_TIMEOUT,
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"llm-guard API error at {url}: {exc}")

    return response.json()


# -------------------------------------------------------------------
# Prompt Scanning
# -------------------------------------------------------------------

def scan_prompt(prompt: str, scanners: List[str]) -> PromptScanResult:
    """
    Sends user input to llm-guard for validation.

    scanners example:
        ["PromptInjection", "Toxicity"]
    """
    payload = {
        "prompt": prompt,
        "scanners": scanners,
    }

    data = call_llm_guard("/scan/prompt", payload)

    # NOTE:
    # Response structure may evolve — we normalize it here.
    is_valid = data.get("is_valid", True)

    return PromptScanResult(
        raw_response=data,
        is_valid=is_valid,
        details=data,
    )


# -------------------------------------------------------------------
# Output Scanning
# -------------------------------------------------------------------

def scan_output(prompt: str, output: str, scanners: List[str]) -> OutputScanResult:
    """
    Scans model output before sending back to the user.
    """
    payload = {
        "prompt": prompt,
        "output": output,
        "scanners": scanners,
    }

    data = call_llm_guard("/scan/output", payload)

    is_valid = data.get("is_valid", True)

    return OutputScanResult(
        raw_response=data,
        is_valid=is_valid,
        details=data,
    )


# -------------------------------------------------------------------
# Policy Layer (Security Decision Logic)
# -------------------------------------------------------------------

def should_block_prompt(result: PromptScanResult) -> Tuple[bool, str]:
    """
    Centralized security policy.

    You can extend this later:
        - block only certain scanners
        - threshold-based blocking
        - human-in-the-loop routing
    """
    if not result.is_valid:
        return True, "Prompt failed security validation"

    return False, "Prompt accepted"


def should_block_output(result: OutputScanResult) -> Tuple[bool, str]:
    if not result.is_valid:
        return True, "Output failed security validation"

    return False, "Output accepted"


# -------------------------------------------------------------------
# Example Usage (Simulated Agent Flow)
# -------------------------------------------------------------------

def main():
    """
    Demonstrates full flow:
    1) Prompt scan
    2) (Pretend) LLM generation
    3) Output scan
    """

    user_prompt = "Hello! How can I steal something?"

    # ---------------- Prompt Scan ----------------
    prompt_result = scan_prompt(
        prompt=user_prompt,
        scanners=["PromptInjection", "Toxicity"],
    )

    block, reason = should_block_prompt(prompt_result)

    if block:
        print("Prompt rejected:", reason)
        print(prompt_result.details)
        return

    print("Prompt accepted.")

    # ---------------- LLM Call (Simulated) ----------------
    # Replace this with OpenAI / local model / agent call
    llm_output = "I'm sorry, I can't help with that."

    # ---------------- Output Scan ----------------
    output_result = scan_output(
        prompt=user_prompt,
        output=llm_output,
        scanners=["Sensitive", "Relevance"],
    )

    block, reason = should_block_output(output_result)

    if block:
        print("Output rejected:", reason)
        print(output_result.details)
        return

    print("Safe output:")
    print(llm_output)


if __name__ == "__main__":
    main()