#Advanced llm-guard API Client
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
