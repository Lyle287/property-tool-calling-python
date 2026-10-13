from types import SimpleNamespace

from property_automation import AutomationState, MaintenanceRequest, TenantDocument, run_loop


class FakeClient:
    class _Completions:
        def create(self, **kwargs):
            call_one = SimpleNamespace(function=SimpleNamespace(name="schedule_inspection", arguments='{"request_id":"MR-1","reason":"urgent leak"}'))
            call_two = SimpleNamespace(function=SimpleNamespace(name="record_document", arguments='{"document_id":"DOC-1"}'))
            message = SimpleNamespace(tool_calls=[call_one, call_two])
            return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    chat = SimpleNamespace(completions=_Completions())


def test_urgent_request_creates_reminder_and_records_document():
    state = run_loop(
        MaintenanceRequest(request_id="MR-1", unit="2A", description="Leak", urgency="urgent"),
        TenantDocument(document_id="DOC-1", tenant_name="Lin", document_type="lease", received=True),
        FakeClient(),
    )
    assert len(state.reminders) == 1
    assert state.reminders[0].request_id == "MR-1"
    assert state.reminders[0].scheduled is True
    assert state.documents_checked == ["DOC-1"]
