"""Unit tests. Run from the project folder: python3 -m unittest discover -s tests"""
import copy
import hashlib
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from inspector.pricing import Pricing  # noqa: E402
from inspector.session import Transcript, canon  # noqa: E402
from inspector.tailer import JsonlTail  # noqa: E402

PRICING = Pricing(os.path.join(ROOT, "pricing.json"))


def h(message):
    return hashlib.sha256(canon(message).encode("utf-8")).hexdigest()


def reference_digest(params, shape, messages, cache_control):
    """Straightforward version of the digest rule, independent of the optimised one."""
    payload = copy.deepcopy({**params, **shape, "messages": messages})
    for mark in cache_control:
        target = payload
        for comp in mark["path"]:
            target = target[comp]
        target["cache_control"] = mark["value"]
    return hashlib.sha256(canon(payload).encode("utf-8")).hexdigest()


def usage(inp, read, write, out, thinking=None):
    u = {"input_tokens": inp, "cache_read_input_tokens": read, "cache_creation_input_tokens": write,
         "output_tokens": out, "cache_creation": {"ephemeral_1h_input_tokens": write, "ephemeral_5m_input_tokens": 0}}
    if thinking is not None:
        u["output_tokens_details"] = {"thinking_tokens": thinking}
    return u


SHAPE = {
    "system": [{"type": "text", "text": "You are a test agent."}, {"type": "text", "text": "Be brief. " * 20}],
    "tools": [{"name": "Bash", "description": "Run a command", "input_schema": {"type": "object"}}],
}
PARAMS = {"model": "claude-opus-5-5", "max_tokens": 1000}


class Builder:
    """Builds a synthetic request-mode log."""

    def __init__(self):
        self.records = [{"type": "api-request-shape", "shapeHash": "S1", "shape": SHAPE}]
        self.n = 0

    def user(self, content, **extra):
        rec = {"type": "user", "uuid": "u%d" % len(self.records), "message": {"role": "user", "content": content}}
        rec.update(extra)
        self.records.append(rec)
        return {"role": "user", "content": content}

    def blob(self, message):
        self.records.append({"type": "api-request-blob", "hash": h(message), "message": message})
        return message

    def request(self, rid, messages, base=None, keep=0, digest=None, cc=None):
        cc = cc or []
        rec = {"type": "api-request", "id": rid, "shapeHash": "S1", "params": PARAMS, "querySource": "repl_main_thread",
               "keep": keep, "tail": [h(m) for m in messages[keep:]], "cacheControl": cc,
               "requestDigest": digest or reference_digest(PARAMS, SHAPE, messages, cc)}
        if base:
            rec["base"] = base
        self.records.append(rec)
        return rec

    def assistant(self, mid, rid, blocks, u):
        out = []
        for i, b in enumerate(blocks):
            rec = {"type": "assistant", "requestRef": rid, "apiBlockIndex": i,
                   "message": {"id": mid, "role": "assistant", "model": "claude-opus-5-5", "content": [b],
                               "usage": u if i == len(blocks) - 1 else dict(u, output_tokens=1)}}
            out.append(rec)
        self.records.extend(out)
        return {"role": "assistant", "content": blocks}


def build(records, kind="main"):
    t = Transcript(kind)
    t.ingest(records)
    return t, t.build(PRICING)


def row_sum(model, row):
    """Expand the delta encoding (base/keep/add) like the browser does, then add up."""
    entries = []
    for r in model["rows"]:
        e = entries[r["base"]][: r["keep"]] + r["add"] if r["base"] is not None else r["add"]
        entries.append(e)
        if r is row:
            return sum(tk for _, tk in e) + r["unattributed"]
    raise AssertionError("row not in model")


class TailerTests(unittest.TestCase):
    def test_partial_line_and_split_utf8(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "s.jsonl")
            line = json.dumps({"type": "user", "text": "åäö ✓"}, ensure_ascii=False).encode("utf-8")
            with open(p, "wb") as f:
                f.write(line[:-4])  # cut inside a multi-byte character
            tail = JsonlTail(p)
            self.assertEqual(tail.poll(), (False, []))
            with open(p, "ab") as f:
                f.write(line[-4:] + b"\n")
            reset, recs = tail.poll()
            self.assertFalse(reset)
            self.assertEqual(recs[0]["text"], "åäö ✓")

    def test_truncation_resets(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "s.jsonl")
            with open(p, "w") as f:
                f.write('{"a": 1}\n{"a": 2}\n')
            tail = JsonlTail(p)
            self.assertEqual(len(tail.poll()[1]), 2)
            with open(p, "w") as f:
                f.write('{"a": 3}\n')
            reset, recs = tail.poll()
            self.assertTrue(reset)
            self.assertEqual(recs, [{"a": 3}])


class RequestModeTests(unittest.TestCase):
    def two_requests(self, digest2=None):
        b = Builder()
        m1 = b.user("Hello there, please list the files.")
        m2 = b.blob({"role": "system", "content": [{"type": "text", "text": "<total_tokens>100 left</total_tokens>"}]})
        b.request("r1", [m1, m2])
        a1 = b.assistant("msg1", "r1", [{"type": "thinking", "thinking": "", "signature": "SIG1" * 30},
                                        {"type": "tool_use", "id": "tu1", "name": "Bash", "input": {"command": "ls"}}],
                         usage(3, 0, 1200, 300, thinking=200))
        m3 = b.user([{"type": "tool_result", "tool_use_id": "tu1", "content": "a.txt\nb.txt"}])
        msgs2 = [m1, m2, a1, m3]
        b.request("r2", msgs2, base="r1", keep=2, digest=digest2,
                  cc=[{"path": ["messages", 3, "content", 0], "value": {"type": "ephemeral"}}])
        b.assistant("msg2", "r2", [{"type": "text", "text": "Two files."}], usage(5, 1200, 400, 20))
        return b

    def test_rebuild_is_verified_and_totals_exact(self):
        t, m = build(self.two_requests().records)
        self.assertEqual(m["mode"], "request")
        self.assertEqual([r["state"] for r in m["rows"]], ["verified", "verified"])
        r1, r2 = m["rows"]
        self.assertEqual(r1["total"], 1203)
        self.assertEqual(r2["total"], 1605)
        self.assertEqual(r2["base"], 0)  # continuity: second row extends the first
        for r in m["rows"]:
            self.assertEqual(row_sum(m, r), r["total"])
        self.assertEqual(len(r2["markers"]), 1)

    def test_digest_mismatch_is_flagged(self):
        _, m = build(self.two_requests(digest2="0" * 64).records)
        self.assertEqual(m["rows"][1]["state"], "mismatch")

    def test_usage_takes_latest_snapshot_not_sum(self):
        _, m = build(self.two_requests().records)
        self.assertEqual(m["rows"][0]["usage"]["output"], 300)

    def test_hidden_thinking_weighted_by_reported_tokens(self):
        t, m = build(self.two_requests().records)
        hidden = [it for it in t.items if it.hidden_owner]
        self.assertEqual(len(hidden), 1)
        self.assertAlmostEqual(hidden[0].weight, 200)

    def test_request_before_previous_response_is_pending_then_resolved(self):
        recs = self.two_requests().records
        # move request r2 before the assistant blocks of msg1
        r2 = next(r for r in recs if r.get("id") == "r2")
        recs.remove(r2)
        first_assistant = next(i for i, r in enumerate(recs) if r["type"] == "assistant")
        recs.insert(first_assistant, r2)
        cut = first_assistant + 1
        t = Transcript()
        t.ingest(recs[:cut])
        m = t.build(PRICING)
        self.assertEqual(m["rows"][1]["state"], "pending")
        t.ingest(recs[cut:])
        m = t.build(PRICING)
        self.assertEqual(m["rows"][1]["state"], "verified")

    def test_consecutive_user_lines_merge_into_one_message(self):
        b = Builder()
        b.user([{"type": "tool_result", "tool_use_id": "x", "content": "Launching skill: demo"}])
        b.user([{"type": "text", "text": "Base directory for this skill: /tmp/demo\n\n# Demo skill"}], isMeta=True)
        merged = {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "x", "content": "Launching skill: demo"},
            {"type": "text", "text": "Base directory for this skill: /tmp/demo\n\n# Demo skill"}]}
        b.request("r1", [merged])
        b.assistant("m1", "r1", [{"type": "text", "text": "ok"}], usage(10, 0, 100, 2))
        t, m = build(b.records)
        self.assertEqual(m["rows"][0]["state"], "verified")
        self.assertIn("skills", m["rows"][0]["cats"])

    def test_synthetic_error_reply_is_not_a_request(self):
        b = self.two_requests()
        b.records.append({"type": "assistant", "isApiErrorMessage": True,
                          "message": {"id": "err", "model": "<synthetic>", "role": "assistant",
                                      "content": [{"type": "text", "text": "API Error"}], "usage": usage(0, 0, 0, 0)}})
        _, m = build(b.records)
        self.assertEqual(len(m["rows"]), 2)

    def test_cost_uses_model_rates(self):
        _, m = build(self.two_requests().records)
        r = m["rows"][1]
        expected = (5 * 4.0 + 1200 * 0.20 + 400 * 8.0 + 20 * 20.0) / 1e6
        self.assertAlmostEqual(r["cost"], expected)


class RegressionTests(unittest.TestCase):
    def test_same_result_for_any_read_order(self):
        recs = RequestModeTests().two_requests().records
        # an assistant blob that arrives before its transcript lines (hidden thinking owner unknown at first)
        t1, whole = build(recs)
        t2 = Transcript()
        for rec in recs:
            t2.ingest([rec])
            t2.build(PRICING)
        step = t2.build(PRICING)
        self.assertEqual([r["cats"] for r in whole["rows"]], [r["cats"] for r in step["rows"]])
        named = lambda t, m: [[(t.items[i].label, tk) for i, tk in r["add"]] for r in m["rows"]]
        self.assertEqual(named(t1, whole), named(t2, step))

    def test_five_user_lines_merged_without_blob(self):
        b = Builder()
        parts = []
        for i in range(5):
            block = {"type": "tool_result", "tool_use_id": "t%d" % i, "content": "out %d" % i}
            b.user([block])
            parts.append(block)
        b.request("r1", [{"role": "user", "content": parts}])
        b.assistant("m1", "r1", [{"type": "text", "text": "ok"}], usage(10, 0, 100, 2))
        _, m = build(b.records)
        self.assertEqual(m["rows"][0]["state"], "verified")

    def test_string_prompt_sent_as_text_block(self):
        b = Builder()
        b.user("How do I install Python?")
        b.request("r1", [{"role": "user", "content": [{"type": "text", "text": "How do I install Python?"}]}])
        b.assistant("m1", "r1", [{"type": "text", "text": "Like this."}], usage(10, 0, 100, 2))
        _, m = build(b.records)
        self.assertEqual(m["rows"][0]["state"], "verified")

    def test_redacted_thinking_gets_reported_tokens(self):
        b = Builder()
        m1 = b.user("hi")
        b.request("r1", [m1])
        a1 = b.assistant("msg1", "r1", [{"type": "redacted_thinking", "data": "ENC" * 40},
                                        {"type": "text", "text": "hello"}], usage(3, 0, 500, 300, thinking=250))
        m2 = b.user("again")
        b.request("r2", [m1, a1, m2], base="r1", keep=1)
        b.assistant("msg2", "r2", [{"type": "text", "text": "ok"}], usage(3, 500, 400, 5))
        t, _ = build(b.records)
        hidden = [it for it in t.items if it.hidden_owner]
        self.assertEqual([round(it.weight) for it in hidden], [250])

    def test_fast_mode_saving_uses_fast_rates_on_both_sides(self):
        u = {"input": 1_000_000, "cacheRead": 0, "cacheWrite": 0, "cacheWrite5m": 0, "cacheWrite1h": 0, "output": 0}
        self.assertAlmostEqual(PRICING.cost("claude-opus-5-5", u, "fast"), PRICING.uncached_cost("claude-opus-5-5", u, "fast"))

    def test_config_change_breaks_continuity(self):
        b = RequestModeTests().two_requests()
        r2 = next(r for r in b.records if r.get("id") == "r2")
        r2["params"] = dict(PARAMS, context_management={"edits": [{"type": "clear_thinking_20251015"}]})
        _, m = build(b.records)
        self.assertIsNone(m["rows"][1]["base"])


class FallbackModeTests(unittest.TestCase):
    def test_rows_from_transcript(self):
        recs = [
            {"type": "attachment", "uuid": "a1", "attachment": {"type": "skill_listing"},
             "rendered": [{"content": "<system-reminder>\nThe following skills are available: x\n</system-reminder>"}]},
            {"type": "user", "uuid": "u1", "message": {"role": "user", "content": "Do the thing"}},
            {"type": "assistant", "message": {"id": "m1", "model": "claude-sonnet-5-5", "role": "assistant",
                                              "content": [{"type": "tool_use", "id": "t1", "name": "Read", "input": {"file_path": "/a/b/c.py"}}],
                                              "usage": usage(10, 0, 5000, 50)}},
            {"type": "user", "uuid": "u2", "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t1", "content": "print(1)"}]}},
            {"type": "assistant", "message": {"id": "m2", "model": "claude-sonnet-5-5", "role": "assistant",
                                              "content": [{"type": "text", "text": "Done."}],
                                              "usage": usage(10, 5000, 30, 5)}},
        ]
        t, m = build(recs)
        self.assertEqual(m["mode"], "fallback")
        self.assertEqual(len(m["rows"]), 2)
        for r in m["rows"]:
            self.assertEqual(row_sum(m, r), r["total"])
        # system prompt and tools are not in this log -> shown as unattributed, never hidden
        self.assertGreater(m["rows"][0]["unattributed"], 0)
        self.assertIn("skills", m["rows"][0]["cats"])
        labels = [it.label for it in t.items]
        self.assertIn("Read: b/c.py", labels)

    def test_subagent_sidechain_records_are_kept_for_agents(self):
        rec = {"type": "user", "isSidechain": True, "uuid": "u1", "message": {"role": "user", "content": "task"}}
        asst = {"type": "assistant", "isSidechain": True,
                "message": {"id": "m1", "model": "claude-haiku-5-5", "role": "assistant",
                            "content": [{"type": "text", "text": "ok"}], "usage": usage(1, 0, 900, 2)}}
        self.assertEqual(len(build([rec, asst], kind="agent")[1]["rows"]), 1)
        self.assertEqual(len(build([rec, asst], kind="main")[1]["rows"]), 0)


class RealLogSmokeTest(unittest.TestCase):
    """Runs the model over every local log. Skipped when there are no logs."""

    def test_all_local_logs(self):
        import glob
        base = os.path.join(os.path.expanduser("~"), ".claude", "projects")
        files = glob.glob(os.path.join(glob.escape(base), "*", "*.jsonl"))[:200]
        if not files:
            self.skipTest("no local Claude Code logs")
        mismatches = 0
        for p in files:
            t = Transcript("main")
            t.ingest(JsonlTail(p).poll()[1])
            m = t.build(PRICING)
            for r in m["rows"]:
                if r["total"] is not None:
                    self.assertEqual(row_sum(m, r), r["total"], p)
                mismatches += r["state"] == "mismatch"
        self.assertEqual(mismatches, 0)


if __name__ == "__main__":
    unittest.main()
