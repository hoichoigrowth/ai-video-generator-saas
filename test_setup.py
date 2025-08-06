import sys
import importlib
import os
import time
import requests
from pymongo import MongoClient
from config.settings import settings
from agents.screenplay.screenplay_agent import ScreenplayFormattingAgent

print("[1] Verifying imports...")
try:
    import fastapi
    import uvicorn
    import celery
    import redis
    import pymongo
    import langchain
    import openai
    import anthropic
    import google.generativeai
    print("  All core imports successful.")
except ImportError as e:
    print(f"  Import error: {e}")
    sys.exit(1)

print("[2] Verifying API keys loading...")
try:
    assert settings.openai_api_key, "Missing OpenAI API key"
    assert settings.anthropic_api_key, "Missing Anthropic API key"
    assert settings.google_api_key, "Missing Google API key"
    print("  API keys loaded from environment/config.")
except Exception as e:
    print(f"  API key error: {e}")
    sys.exit(1)

print("[3] Verifying MongoDB connection...")
try:
    client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=3000)
    client.server_info()  # Will throw if cannot connect
    print("  MongoDB connection successful.")
except Exception as e:
    print(f"  MongoDB connection error: {e}")
    sys.exit(1)

print("[4] Verifying agent initialization...")
try:
    agent = ScreenplayFormattingAgent(
        openai_api_key=settings.openai_api_key,
        anthropic_api_key=settings.anthropic_api_key,
        google_api_key=settings.google_api_key
    )
    print("  Agent initialized successfully.")
except Exception as e:
    print(f"  Agent initialization error: {e}")
    sys.exit(1)

print("[5] Verifying API startup...")
try:
    import subprocess
    proc = subprocess.Popen([
        sys.executable, "-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", "8888"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(3)
    try:
        resp = requests.get("http://127.0.0.1:8888/docs", timeout=3)
        assert resp.status_code == 200
        print("  API started and /docs endpoint reachable.")
    except Exception as e:
        print(f"  API did not start or /docs not reachable: {e}")
        proc.terminate()
        sys.exit(1)
    proc.terminate()
except Exception as e:
    print(f"  API startup error: {e}")
    sys.exit(1)

print("\nAll setup tests passed!")