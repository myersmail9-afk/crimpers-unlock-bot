"""Print the bot application's public info (id, public key, intent flags)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from unlock_core import request

app = request("GET", "/applications/@me")
f = app.get("flags", 0)
print("app_id:", app["id"])
print("verify_key:", app["verify_key"])
print("interactions_endpoint_url:", app.get("interactions_endpoint_url"))
print("members intent:", bool(f & (1 << 14) or f & (1 << 15)), "| message content intent:", bool(f & (1 << 18) or f & (1 << 19)))
