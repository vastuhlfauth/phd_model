# mobility-france

Multimodal O-D costs, accessibility and bodily energy for metropolitan France, at 200 m and 1 km, for 2021, 2023 and scenarios. The specification is in [docs/spec/](docs/spec/README.md).

## Setup in VS Code

1. Install Python 3.12 and [uv](https://docs.astral.sh/uv/).
2. Turn on the setting `github.copilot.chat.codeGeneration.useInstructionFiles`, so that `.github/copilot-instructions.md` and `.github/instructions/*.instructions.md` are always applied.
3. In Copilot Chat, choose **Agent** mode and your model.
4. Let the agent run `uv run pytest` and `uv run ruff` without asking each time (terminal auto-approval).
5. Download the pilot data in [docs/data/download_checklist.md](docs/data/download_checklist.md).

## Workflow

The prompts live in `.github/prompts/` and are run by typing `/` and their name in the chat.

| When | Prompt | What it does |
|---|---|---|
| Once | `/bootstrap` | Creates the repository skeleton and the configuration |
| Before a dataset is first used | `/schema` | Writes the dataset's page in `docs/data/` |
| For each step of section 14.5 | `/step` | Plan, tests first, implementation, checks, progress log |
| Before merging a step | `/review` | Reviews the branch against the spec, without changing files |

Rules that keep the agent fast and accurate:

- **One step = one new chat = one branch.** Start a new chat for each step, so the agent only has what it needs.
- **Order:** step 1, then `/schema` for the pilot datasets, then step 2, then steps 0 and 3 to 11. Step 0 needs only DuckDB and can run in parallel.
- **Tests come before code;** reference numbers are in the spec and in `.github/instructions/mobgrid.instructions.md`.
- **Pilot first:** Gironde (33) with a 50 km halo. National runs come after the pilot passes validation (section 13).
- **`docs/progress.md`** is the memory between chats: steps, decisions, assumptions, open points.
- **Review each step in a separate chat** with `/review` before merging into `main`.

## Folders

```
.github/                 instructions for the agents and prompt files
docs/spec/               specification, one file per section
docs/data/               one page per dataset, download checklist
docs/progress.md         progress log
config/                  all parameters (created by /bootstrap)
scenarios/               infrastructure and macro scenario files
packages/                common, acquire, landgrid, mobgrid (created by /bootstrap)
tests/                   tests and small fixtures
legacy/                  previous scripts, for reference only
data/                    raw and derived data, not committed
```
