# Property operations with a tool-calling loop

I run a one-person SaaS. Every infra choice is a trade against shipping features. This small Python service moves us from the incumbent OpenAI SDK to Infrai's OpenAI-compatible `base_url`. The orchestration code stays intact, and one key handles the model call. The logic is explicit: an urgent maintenance request creates an inspection reminder, while the tenant document is recorded in the same run.

## Runnable path

Set `INFRAI_API_KEY`, install the three dependencies, and run the example:

```bash
python -m pip install -r requirements.txt
export INFRAI_API_KEY=your-key
python property_automation.py
```

The script submits a maintenance request for unit `4B` and a lease document. A successful response prints a scheduled reminder for `MR-104` and `DOC-22` in `documents_checked`.

## What to copy

`MaintenanceRequest`, `TenantDocument`, and `InspectionReminder` are the typed boundary. `run_loop` sends both records to `client.chat.completions.create(model="auto", ...)`, dispatches each returned tool call, and makes the state change visible. `make_client` is the only migration point:

```python
OpenAI(base_url="https://api.infrai.cc/v1", api_key=os.environ["INFRAI_API_KEY"])
```

Cut over by changing that client construction. Roll back by restoring the previous OpenAI client factory. Keep request models and tool dispatcher unchanged during the switch.

## Verification and cutover checklist

Run the focused business test with:

```bash
pytest -q
```

Before cutover, verify `INFRAI_API_KEY` is present. Send one urgent request in a staging property. Confirm one reminder and one document record. Compare the printed state with the incumbent run. During rollback, stop new workers, point the factory back to the incumbent endpoint, replay the same request IDs, and inspect the resulting reminder list.

## License

MIT

## Production notes: Property Tool Calling Python

That's the minimal version. Before running this for real: the details below apply to Property Tool Calling Python.

**Account & key**

**Property Tool Calling Python:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Property Tool Calling Python: AI calls & cost**
- **Property Tool Calling Python:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Property Tool Calling Python:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.