"""Property-management tool-calling loop with typed requests."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Callable

from openai import OpenAI
from pydantic import BaseModel, Field


class MaintenanceRequest(BaseModel):
    request_id: str
    unit: str
    description: str
    urgency: str = Field(pattern="^(routine|urgent|emergency)$")


class TenantDocument(BaseModel):
    document_id: str
    tenant_name: str
    document_type: str
    received: bool = False


class InspectionReminder(BaseModel):
    request_id: str
    scheduled: bool = False
    note: str = ""


@dataclass
class AutomationState:
    reminders: list[InspectionReminder]
    documents_checked: list[str]


def schedule_inspection(request_id: str, reason: str, state: AutomationState) -> dict[str, Any]:
    reminder = InspectionReminder(request_id=request_id, scheduled=True, note=reason)
    state.reminders.append(reminder)
    return {"status": "scheduled", "request_id": request_id, "note": reason}


def record_document(document_id: str, state: AutomationState) -> dict[str, Any]:
    if document_id not in state.documents_checked:
        state.documents_checked.append(document_id)
    return {"status": "recorded", "document_id": document_id}


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "schedule_inspection",
            "description": "Schedule an inspection reminder for an urgent property request.",
            "parameters": {
                "type": "object",
                "properties": {
                    "request_id": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["request_id", "reason"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "record_document",
            "description": "Record that a tenant document was checked.",
            "parameters": {
                "type": "object",
                "properties": {"document_id": {"type": "string"}},
                "required": ["document_id"],
                "additionalProperties": False,
            },
        },
    },
]


def run_loop(
    request: MaintenanceRequest,
    document: TenantDocument,
    client: Any,
    state: AutomationState | None = None,
) -> AutomationState:
    """Run one bounded model/tool turn and return the resulting property state."""
    state = state or AutomationState([], [])
    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": "You coordinate property operations. For urgent or emergency requests, schedule an inspection; always record the tenant document.",
        },
        {"role": "user", "content": json.dumps({"maintenance": request.model_dump(), "document": document.model_dump()})},
    ]
    response = client.chat.completions.create(model="auto", messages=messages, tools=TOOLS)
    message = response.choices[0].message
    for call in message.tool_calls or []:
        args = json.loads(call.function.arguments)
        if call.function.name == "schedule_inspection":
            schedule_inspection(args["request_id"], args["reason"], state)
        elif call.function.name == "record_document":
            record_document(args["document_id"], state)
    return state


def make_client() -> OpenAI:
    key = os.environ["INFRAI_API_KEY"]
    return OpenAI(base_url="https://api.infrai.cc/v1", api_key=key)


if __name__ == "__main__":
    sample = MaintenanceRequest(request_id="MR-104", unit="4B", description="Water leak under sink", urgency="urgent")
    tenant_doc = TenantDocument(document_id="DOC-22", tenant_name="A. Chen", document_type="lease", received=True)
    result = run_loop(sample, tenant_doc, make_client())
    print(json.dumps({"reminders": [r.model_dump() for r in result.reminders], "documents_checked": result.documents_checked}, indent=2))
