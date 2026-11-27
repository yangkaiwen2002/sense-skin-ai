"""Bounded, read-only Ollama tool calling and schema-constrained synthesis.

Model output is untrusted: tool names/arguments are allowlisted, evidence quotes
must match verbatim, and numbers in claims must occur in the cited quote.
This is provenance validation, not a claim of semantic entailment.
"""
import json
import re
import time
from decimal import Decimal
from typing import Literal
import httpx
from pydantic import BaseModel, ConfigDict, Field
from app.config import settings
from app.services.research_model import SYSTEM


class ToolArguments(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    scope: Literal["current_request"] = Field(description="Always current_request. Item IDs, question, days and budget are fixed by the user; do not supply them.")
    # Scope, rental inputs and retrieval query come from the validated user request.


class Finding(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    source_id: str = Field(pattern=r"^S[1-9]\d*$")
    quote: str = Field(min_length=8, max_length=500)
    observation: str = Field(min_length=1, max_length=300, description="用中文定性解释这段证据，不重复价格、数量、百分比等数字，具体数字留在 quote 中展示。不能引入其他来源的事实。")


class ResearchReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    conclusion: Literal["仅供演示", "数据不足", "报价待核验", "知识说明"]
    findings: list[Finding] = Field(min_length=1, max_length=5)
    next_action: Literal["核对平台原始报价", "补充真实历史数据", "核对租赁押金与费用", "阅读来源全文"]


def validate_report(raw, sources):
    report = ResearchReport.model_validate_json(raw)
    index = {s["id"]: s for s in sources}
    errors = []
    for i, finding in enumerate(report.findings):
        if len(re.findall(r"[\u4e00-\u9fff]", finding.observation)) < 3:
            raise ValueError("observation 必须使用中文解释证据")
        source = index.get(finding.source_id)
        if not source or finding.quote not in source["summary"]:
            raise ValueError("引用不存在或引文未逐字匹配来源")
        numbers = lambda s: {Decimal(n) for n in re.findall(r"\d+(?:\.\d+)?", s.replace(",", ""))}
        # Exact catalog identifiers (AK-47, M4A1, CS2) are entity names,
        # not amounts. Only identifiers present in this source title are exempt.
        observation, quote = finding.observation, finding.quote
        for identifier in re.findall(r"[A-Za-z]+[- ]?\d+[A-Za-z0-9-]*", source.get("title", "")):
            observation = observation.replace(identifier, "")
            quote = quote.replace(identifier, "")
        unsupported = numbers(observation) - numbers(quote)
        if unsupported:
            errors.append(f"findings[{i}].observation 的数字 {sorted(map(str, unsupported))} 未出现在该引文中；请删去观察中的数字，只保留中文定性说明，数字由 quote 展示。")
    if errors:
        raise ValueError("；".join(errors))
    market = [s for s in sources if s["kind"] == "market"]
    if market and all(all(p.get("price_kind") == "demo" for p in s.get("data", {}).get("overview", {}).get("platforms", [])) for s in market):
        report.conclusion = "仅供演示"  # deterministic data policy overrides the model
    return report


def render_report(report):
    lines = [f"结论：{report.conclusion}"]
    for f in report.findings:
        lines.append(f"{f.observation} [{f.source_id}]\n原文：{f.quote}")
    lines.append(f"下一步：{report.next_action}")
    lines.append("证据边界：引文与数字已核对来源；这不等于结论正确性验证。演示价格不能用于交易，静态资料不代表当前行情，公告与价格之间的因果关系尚未验证。")
    return "\n\n".join(lines)


async def chat(messages, *, tools=None, schema=None):
    body = {"model": settings.OLLAMA_MODEL, "messages": messages, "stream": False,
            "think": False, "options": {"temperature": 0, "num_ctx": 16384, "num_predict": 1800}, "keep_alive": "10m"}
    if tools: body["tools"] = tools
    if schema: body["format"] = schema
    started = time.monotonic()
    async with httpx.AsyncClient(timeout=90, follow_redirects=False) as client:
        response = await client.post(settings.OLLAMA_URL.rstrip("/") + "/api/chat", json=body)
        response.raise_for_status()
        result = response.json()
    if not result.get("done") or result.get("done_reason") != "stop":
        raise ValueError("模型输出未完整结束")
    return result["message"], {"model": result.get("model"), "input_tokens": result.get("prompt_eval_count", 0),
        "output_tokens": result.get("eval_count", 0), "duration_ms": round((time.monotonic()-started)*1000)}


def tool_definitions(names):
    descriptions = {"market": "核对用户所选饰品的各平台报价、数据来源和时间", "rental": "计算用户指定天数和预算的租买方案", "news": "读取公告背景，不能推断价格因果", "knowledge": "按用户问题与饰品名称检索知识库"}
    return [{"type": "function", "function": {"name": name, "description": descriptions[name],
             "parameters": ToolArguments.model_json_schema()}} for name in names]


class EvidenceSelection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    evidence_id: str
    observation: str = Field(min_length=3, max_length=220,
        description="中文解释本条证据；数字只能来自所选引文，不得自行计算或使用其他条目的数字。")




class ReportDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    conclusion: Literal["仅供演示", "数据不足", "报价待核验", "知识说明"]
    findings: list[EvidenceSelection] = Field(min_length=1, max_length=5)
    next_action: Literal["核对平台原始报价", "补充真实历史数据", "核对租赁押金与费用", "阅读来源全文"]


def evidence_catalog(sources):
    """Slice contiguous source text, never synthesize a quote with the model."""
    catalog = []
    ordered = sorted(sources, key=lambda s: {"rental":0,"market":1,"knowledge":2,"news":3}.get(s["kind"],4))
    for source in ordered:
        fragments = re.findall(r"[^；。\n]+[；。]?", source["summary"])
        for fragment in fragments[:6]:
            quote = fragment.strip()[:500]
            if len(quote) < 8: continue
            catalog.append({"evidence_id": f"E{len(catalog)+1}", "source_id": source["id"],
                "kind": source["kind"], "quote": quote})
    return catalog[:40]


async def structured_answer(question, sources, history):
    evidence = evidence_catalog(sources)
    if not evidence: raise ValueError("本轮没有足够的可引用证据")
    index = {e["evidence_id"]: e for e in evidence}
    schema = ReportDraft.model_json_schema()
    schema["$defs"]["EvidenceSelection"]["properties"]["evidence_id"]["enum"] = list(index)
    messages = [{"role":"system", "content":SYSTEM + "\n你负责选择相关证据并解释，不自行计算或编造数字。findings.evidence_id 只选择证据目录中直接回答问题的条目，observation 为中文解释，其中的数字必须出现在该 evidence_id 的 quote 中。由程序自动附上原文。不要用完所有来源；租买问题优先使用 rental，知识库是未核验的静态背景，不能用其价格代替工具结果。"},
        *[{**m,"content":m["content"][:1000]} for m in history[-4:]],
        {"role":"user", "content":json.dumps({"question":question,"evidence":evidence},ensure_ascii=False)}]
    calls = []
    for attempt in range(2):
        message, usage = await chat(messages, schema=schema)
        calls.append(usage)
        try:
            draft = ReportDraft.model_validate_json(message.get("content", ""))
            findings = []
            for choice in draft.findings:
                ref = index.get(choice.evidence_id)
                if not ref: raise ValueError("证据编号不在本轮目录中")
                findings.append(Finding(source_id=ref["source_id"], quote=ref["quote"], observation=choice.observation))
            report = ResearchReport(conclusion=draft.conclusion, findings=findings, next_action=draft.next_action)
            fallbacks = []
            for i, finding in enumerate(report.findings):
                try:
                    validate_report(ResearchReport(conclusion=report.conclusion, findings=[finding], next_action=report.next_action).model_dump_json(), sources)
                except ValueError as exc:
                    if not attempt: raise
                    # Keep the model-selected, server-resolved quote; discard the
                    # unsupported interpretation. This is explicitly a degraded
                    # evidence extract, never an accepted model explanation.
                    report.findings[i] = finding.model_copy(update={"observation":"模型解释未通过校验，请以这条来源原文为准。"})
                    fallbacks.append({"finding":i, "reason":str(exc)[:300]})
            report = validate_report(report.model_dump_json(), sources)
            return report, {"schema_version":"1.1", "grounding":"server_resolved_evidence", "validated":True,
                            "repair_attempts":attempt, "model_calls":calls, "fallbacks":fallbacks}
        except ValueError as exc:
            if attempt: raise ValueError("结构或证据校验未通过，未发布模型报告") from exc
            messages += [message, {"role":"user", "content":"校验失败："+str(exc)[:1600]+"。只修复 JSON；选择已有证据编号，observation 的数字必须出现在所选引文中。"}]
    raise AssertionError("unreachable")

class ToolDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    tool: Literal["market", "rental", "news", "knowledge", "finish"]
    scope: Literal["current_request"]


async def choose_tool(messages, names):
    """Constrained tool routing works even when a small model's native function
    argument generation is unreliable. The model chooses; Python validates and
    executes. No synthetic tool calls are presented as native API calls.
    """
    schema = ToolDecision.model_json_schema()
    schema["properties"]["tool"]["enum"] = [*names, "finish"]
    catalog = [{"name": t["function"]["name"], "purpose": t["function"]["description"]} for t in tool_definitions(names)]
    message, usage = await chat([*messages, {"role":"user", "content": "选择下一步。仅返回 JSON，tool 为一个可用工具或 finish，scope 固定为 current_request。可用工具：" + json.dumps(catalog, ensure_ascii=False)}], schema=schema)
    decision = ToolDecision.model_validate_json(message.get("content", ""))
    if decision.tool not in [*names, "finish"]:
        raise ValueError("模型选择了不可用的工具")
    return decision, message, usage
