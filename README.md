# CyberGym Mini Baseline Runner

Lightweight baseline harness for CyberGym task generation, OpenAI-compatible agent runs, trajectory logging, and aggregate metrics.

This project intentionally does not implement RL training or distributed execution. It is designed to be easy to audit and modify for baseline evaluation of DeepSeek, Qwen DashScope, and local vLLM models.

## Project Tree

```text
cybergym-mini-runner/
  README.md
  requirements.txt
  pyproject.toml
  run_agent.py
  scripts/
    setup_cybergym_subset.sh
  tools/
    gen_cases.py
    start_server.py
    summarize_results.py
  src/cybergym_mini_runner/
    actions.py
    agent.py
    case.py
    cybergym_adapter.py
    metrics.py
    model_client.py
    safety.py
    tools.py
    trajectory.py
```

## Installation

Python 3.11 is recommended for this runner. CyberGym itself may require its own Python version; the setup script follows CyberGym's official editable install.

```bash
cd cybergym-mini-runner
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set up the official CyberGym subset:

```bash
bash scripts/setup_cybergym_subset.sh
```

For the smallest local smoke test, set up only `arvo:368`:

```bash
bash scripts/setup_arvo368.sh
```

This pulls only `data/arvo/368/**` from `cybergym_data` and the two verifier images:

```text
n132/arvo:368-vul
n132/arvo:368-fix
```

Expect roughly `10-20 GB` of free disk for the `arvo:368` smoke path after Docker extraction and working files.

The script is idempotent. By default it uses sibling directories:

```text
../cybergym
../cybergym_data
```

It clones CyberGym, installs `git-lfs`, clones the Hugging Face `cybergym_data` repository with LFS smudge disabled, pulls LFS files for the official 10-task subset, and runs CyberGym's official subset Docker image downloader.

## Model Configuration

All models use the same OpenAI-compatible client:

```bash
export OPENAI_BASE_URL=https://api.deepseek.com/v1
export OPENAI_API_KEY=xxx
export MODEL=deepseek-chat
```

```bash
export OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
export OPENAI_API_KEY=xxx
export MODEL=qwen-plus
```

```bash
export OPENAI_BASE_URL=http://127.0.0.1:8000/v1
export OPENAI_API_KEY=EMPTY
export MODEL=qwen3-32b
```

Provider-specific OpenAI-compatible options can be passed without changing clients:

```bash
python run_agent.py --case-dir ./runs/cases/arvo_10400 --model deepseek-v4-pro --enable-thinking
python run_agent.py --case-dir ./runs/cases/arvo_10400 --model deepseek-v4-pro --reasoning-effort high
python run_agent.py --case-dir ./runs/cases/arvo_10400 --model qwen-plus --extra-body-json '{"enable_thinking":false}'
```

Equivalent environment variables are also supported:

```bash
export DASHSCOPE_API_KEY=xxx
export OPENAI_ENABLE_THINKING=true
export OPENAI_REASONING_EFFORT=high
export OPENAI_EXTRA_BODY_JSON='{"enable_thinking":true}'
```

## Start CyberGym Server

```bash
python tools/start_server.py \
  --host 127.0.0.1 \
  --port 8666 \
  --log-dir ./runs/server_poc \
  --db-path ./runs/server_poc/poc.db
```

For binary-only server data:

```bash
python tools/start_server.py \
  --binary-dir ../cybergym-server-data \
  --log-dir ./runs/server_poc \
  --db-path ./runs/server_poc/poc.db
```

## arvo:368 Smoke Run

After `bash scripts/setup_arvo368.sh`, start the local verifier:

```bash
python tools/start_server.py \
  --host 127.0.0.1 \
  --port 8666 \
  --log-dir ./runs/server_poc \
  --db-path ./runs/server_poc/poc.db
```

Generate only the `arvo:368` case:

```bash
python tools/gen_cases.py \
  --task-ids arvo:368 \
  --difficulty level3 \
  --out-dir ./runs/cases \
  --server http://127.0.0.1:8666
```

Run DeepSeek v4 through an OpenAI-compatible endpoint:

```bash
export OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
export OPENAI_API_KEY=xxx
export MODEL=deepseek-v4-pro

python run_agent.py \
  --case-dir ./runs/cases/arvo_368 \
  --model deepseek-v4-pro \
  --max-steps 30 \
  --enable-thinking
```

## Generate Cases

```bash
python tools/gen_cases.py \
  --task-ids arvo:10400 arvo:368 oss-fuzz:42535201 \
  --difficulty level3 \
  --out-dir ./runs/cases \
  --server http://127.0.0.1:8666
```

Each task is generated into a sanitized directory:

```text
runs/cases/arvo_10400/
  README.md
  description.txt
  repo-vul.tar.gz
  submit.sh
  case_meta.json
```

## Run Agent

```bash
python run_agent.py \
  --case-dir ./runs/cases/arvo_10400 \
  --model deepseek-chat \
  --max-steps 50
```

Outputs:

```text
runs/cases/arvo_10400/agent_runs/<model_timestamp>/
  args.json
  trajectory.jsonl
  final_report.json
  workspace/
```

The model must emit only JSON:

```json
{"thought":"inspect repository","action":"shell","command":"ls -la"}
```

Supported actions:

```text
shell
read_file
write_file
submit_poc
finish
```

Malformed JSON is recorded and reprompted up to `--max-json-retries`.

## Summarize Results

```bash
python tools/summarize_results.py ./runs
```

Metrics:

```text
pass@1
submission_rate
timeout_rate
average_steps
failure_distribution
```

Failure categories:

```text
build_failed
no_poc_generated
invalid_poc
no_crash
tool_error
timeout
json_error
unknown
```

## Safety Model

The runner restricts file tools to the per-run workspace and blocks common network scanning, external fetching, package installation, privilege escalation, system mounts, and destructive system commands. `submit_poc` is the only action allowed to contact the configured local CyberGym verifier through the generated `submit.sh`.

This is a benchmark harness, not a hardened sandbox. For stronger isolation, run agents inside a container or VM and use CyberGym's firewall/proxy tooling.

## Assumptions

- CyberGym is available at `CYBERGYM_ROOT` or `../cybergym`.
- CyberGym task data is available at `CYBERGYM_DATA_DIR` or `../cybergym_data/data`.
- The CyberGym PoC server is running before generating tasks or submitting PoCs.
- `repo-vul.tar.gz` contains paths safe to extract inside the per-run workspace.

## Known Limitations

- Success is inferred from CyberGym submission output: non-zero vulnerable exit codes or returned flags count as success.
- The shell tool uses policy checks plus workspace cwd restriction, not kernel-level sandboxing.
- The harness records single-run pass@1; repeated sampling and pass@k are intentionally out of scope.
