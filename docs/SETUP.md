# Setup

BidRoom runs on your machine: Python for the workflow engine, Switch for the agents and rooms, Mattermost (provisioned by Switch) for the chat, and OpenCode as the agent runtime.

## Prerequisites

- macOS or Linux
- Python 3.10+
- [Switch Console](https://www.switchagents.ai) 0.40.1 or newer
- Docker Desktop (Switch uses it to run Mattermost beside the local Switch server)
- OpenCode CLI, signed in to a provider with a **tool-capable** model

> **OpenCode version note.** Switch 0.40.1 checks OpenCode's sign-in using the v1 CLI surface. If `opencode --version` is v2.x, Switch may report *"Sign-in could not be checked"*. Install OpenCode **1.18.27** on a separate PATH for Switch (or use a machine that already runs 1.18.x). You do not need to replace your main OpenCode install.

## 1. Install the project

```bash
git clone <this repo>
cd bidroom
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest        # 19 passed
```

## 2. Import the Switch template

1. Open **Switch Console → Templates → Import template**.
2. Upload [`switch/bidroom.template.yaml`](../switch/bidroom.template.yaml) (or paste it).
3. Save it to the workspace.

The template declares:

- 5 agents: `{client}-scout`, `{client}-matcher`, `{client}-writer`, `{client}-redteam`, `{client}-evidence`
- 2 rooms: `Bid: {client_name}` and `{client}-evidence-desk`
- room roles, three room documents (`BID-BRIEF.md`, `RUNBOOK.md`, `EVIDENCE-POLICY.md`) and a kickoff that starts the scout

## 3. Create the group

1. Open the template and click **Use template**.
2. Set **Client slug** (`northwind`), **Client name** (`Northwind City Council`), **RFP reference** and **Submission deadline**.
3. Open **Advanced → Change** and set **Shared checkout** to the absolute path of this repo. All five agents must share this directory; that is how they share `.bidroom/`.
4. Click **Create all**.

Switch creates the agents and both rooms and bridges them to Mattermost. The kickoff is posted on your behalf.

## 4. Set the agents' model before the first turn

This is the one step that will bite you if you skip it. A newly created OpenCode agent can inherit a default model that does not support tool calls. The first turn then fails with:

```
APIError: No endpoints found that support tool use. Try disabling "bash".
```

For **each** of the five agents:

1. **Your Agents → open the agent → Agent settings**.
2. Expand **Advanced configuration**.
3. Set **Model** to a tool-capable model, for example `opencode/deepseek-v4.1-flash-free` (or `openrouter/nvidia/nemotron-3-ultra-550b-a55b:free`).
4. Set **Utility model** to the same value, so background work stays on the same model.
5. Repeat for the other four agents.

If an agent already has a session with the wrong model, start a new chat or switch that session's model; the existing session keeps its original model.

## 5. Run the room

The kickoff tells the scout to initialize `.bidroom/`, ingest the example RFP, post the requirement summary and hand off to the matcher. Watch the room; each agent posts its result and mentions the next agent.

The human steps happen in your terminal, not in the room:

```bash
# 1. Review the evidence desk's queue, then approve by name.
.venv/bin/bidroom -w .bidroom evidence approve E-DEL-09 \
  --by "Your Name" --note "Checked the delivery report; covers the top-20 journey."

# 2. When the matrix and approvals are frozen, ask the writer to draft.
#    The writer runs: .venv/bin/bidroom -w .bidroom draft

# 3. When the red team reports zero blockers, sign.
.venv/bin/bidroom -w .bidroom signoff \
  --by "Your Name" \
  --note "Reviewed the matrix, the draft and the red-team findings." \
  --accept-gaps
```

`--accept-gaps` needs a written reason of at least 20 characters. The signature pins the approved evidence with a SHA-256 digest; if a record changes afterwards, the report shows **stale**.

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `No endpoints found that support tool use` | Agent model cannot call tools | Set **Model** and **Utility model** in agent settings to a tool-capable model |
| Switch says OpenCode "Sign-in could not be checked" | OpenCode v2 on PATH; Switch 0.40.1 expects v1.18.x | Put OpenCode 1.18.27 on a separate PATH for Switch |
| Mattermost unavailable | Docker Desktop is not running | Start Docker Desktop, then **Admin → Status → Restart** |
| `Invalid RootId parameter` in `switch-core.log` | Non-fatal bridge warning for tool-activity posts | Ignore; the main room still works |
| Agent creates a new workspace | Its `directory` is not the shared checkout | Set **Shared checkout** to this repo in the template form (or agent settings) |
| Approval seems ignored | The agent is reading a different `.bidroom` | Check `bidroom -w .bidroom status` in the repo root |

## What not to do

- Do **not** run `bidroom demo --force` against `.bidroom/`. It reseeds the directory and destroys approvals and signatures.
- Do **not** give an agent the `evidence approve` or `signoff` permission. The CLI commands exist; the MCP surface deliberately does not expose them.
- Do **not** edit an approved record after sign-off. If you must, re-run `evidence approve`/`unapprove` and sign again; the old signature will be marked stale.

## Running without Switch

You can use the engine on its own:

```bash
.venv/bin/bidroom init --rfp examples/northwind/rfp.md --evidence examples/northwind/evidence
.venv/bin/bidroom ingest .bidroom/inbox/rfp.md
.venv/bin/bidroom matrix
.venv/bin/bidroom draft
.venv/bin/bidroom review --strict
.venv/bin/bidroom report --open
```

Switch adds the room, the relay, the roles and the visible human gates. The CLI is the same engine the agents use.
