"""Estimated API-equivalent cost from usage counters and pricing.json."""
import json

RATE_KEYS = ("input", "output", "cache_write_5m", "cache_write_1h", "cache_read")


class Pricing:
    def __init__(self, path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.models = data.get("models", {})
        self.source = data.get("source")
        self.checked = data.get("checked")

    def lookup(self, model):
        if not model:
            return None
        best = None
        for key in self.models:
            if model.startswith(key) and (best is None or len(key) > len(best)):
                best = key
        return self.models[best] if best else None

    def context_window(self, model):
        entry = self.lookup(model)
        return entry.get("context") if entry else None

    def label(self, model):
        entry = self.lookup(model)
        return entry.get("label") if entry else model

    def cost(self, model, usage, speed=None):
        """USD for one response, or None when the model or usage is unknown."""
        entry = self.lookup(model)
        if entry is None or usage is None:
            return None
        rates = {k: entry[k] for k in RATE_KEYS}
        total_in = usage["input"] + usage["cacheRead"] + usage["cacheWrite"]
        above = entry.get("above")
        if above and total_in > above["input_tokens"]:
            rates.update({k: above[k] for k in RATE_KEYS if k in above})
        if speed == "fast" and entry.get("fast"):
            rates.update(entry["fast"])
        cost = (
            usage["input"] * rates["input"]
            + usage["output"] * rates["output"]
            + usage["cacheRead"] * rates["cache_read"]
            + usage["cacheWrite5m"] * rates["cache_write_5m"]
            + usage["cacheWrite1h"] * rates["cache_write_1h"]
        )
        return cost / 1e6

    def uncached_cost(self, model, usage, speed=None):
        """Cost of the same request (same speed and tier) if nothing was cached."""
        entry = self.lookup(model)
        if entry is None or usage is None:
            return None
        total_in = usage["input"] + usage["cacheRead"] + usage["cacheWrite"]
        rates = {k: entry[k] for k in RATE_KEYS}
        above = entry.get("above")
        if above and total_in > above["input_tokens"]:
            rates.update({k: above[k] for k in RATE_KEYS if k in above})
        if speed == "fast" and entry.get("fast"):
            rates.update(entry["fast"])
        return (total_in * rates["input"] + usage["output"] * rates["output"]) / 1e6
