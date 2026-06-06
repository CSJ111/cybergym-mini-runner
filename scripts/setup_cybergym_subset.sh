#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
WORKSPACE_DIR="${WORKSPACE_DIR:-$(cd "$ROOT_DIR/.." && pwd)}"
CYBERGYM_ROOT="${CYBERGYM_ROOT:-$WORKSPACE_DIR/cybergym}"
CYBERGYM_DATA_DIR="${CYBERGYM_DATA_DIR:-$WORKSPACE_DIR/cybergym_data}"
CYBERGYM_REPO="${CYBERGYM_REPO:-https://github.com/sunblaze-ucb/cybergym.git}"
CYBERGYM_DATA_REPO="${CYBERGYM_DATA_REPO:-https://huggingface.co/datasets/sunblaze-ucb/cybergym}"
MAX_WORKERS="${MAX_WORKERS:-1}"
CYBERGYM_PULL_IMAGES="${CYBERGYM_PULL_IMAGES:-1}"
CYBERGYM_TASK_IDS="${CYBERGYM_TASK_IDS:-}"

DEFAULT_SUBSET_TASKS=(
  "arvo:47101"
  "arvo:3938"
  "arvo:24993"
  "arvo:1065"
  "arvo:10400"
  "arvo:368"
  "oss-fuzz:42535201"
  "oss-fuzz:42535468"
  "oss-fuzz:370689421"
  "oss-fuzz:385167047"
)

if [ -n "$CYBERGYM_TASK_IDS" ]; then
  # Space-separated list, for example: CYBERGYM_TASK_IDS="arvo:368 oss-fuzz:42535201"
  read -r -a SELECTED_TASKS <<< "$CYBERGYM_TASK_IDS"
else
  SELECTED_TASKS=("${DEFAULT_SUBSET_TASKS[@]}")
fi

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "missing required command: $1" >&2
    exit 1
  }
}

ensure_git_lfs() {
  if command -v git-lfs >/dev/null 2>&1 || git lfs version >/dev/null 2>&1; then
    return
  fi
  if command -v apt-get >/dev/null 2>&1 && [ "$(id -u)" = "0" ]; then
    apt-get update
    apt-get install -y git-lfs
  elif command -v brew >/dev/null 2>&1; then
    brew install git-lfs
  else
    echo "git-lfs is required. Install it, then rerun this script." >&2
    exit 1
  fi
}

pull_task_images() {
  if [ "$CYBERGYM_PULL_IMAGES" = "0" ]; then
    echo "Skipping Docker image pull because CYBERGYM_PULL_IMAGES=0"
    return
  fi

  need_cmd docker

  local needs_oss_fuzz_base=0
  local task family ident mode
  for task in "${SELECTED_TASKS[@]}"; do
    family="${task%%:*}"
    ident="${task#*:}"
    case "$family" in
      arvo)
        for mode in vul fix; do
          docker pull "n132/arvo:${ident}-${mode}"
        done
        ;;
      oss-fuzz)
        needs_oss_fuzz_base=1
        for mode in vul fix; do
          docker pull "cybergym/oss-fuzz:${ident}-${mode}"
        done
        ;;
      *)
        echo "unsupported subset task family for image pull: $task" >&2
        exit 1
        ;;
    esac
  done

  if [ "$needs_oss_fuzz_base" = "1" ]; then
    docker pull "cybergym/oss-fuzz-base-runner:latest"
  fi
}

need_cmd git
need_cmd python3
ensure_git_lfs
git lfs install

if [ ! -d "$CYBERGYM_ROOT/.git" ]; then
  git clone "$CYBERGYM_REPO" "$CYBERGYM_ROOT"
else
  echo "CyberGym already present: $CYBERGYM_ROOT"
fi

python3 -m pip install -e "${CYBERGYM_ROOT}[dev,server]"

if [ ! -d "$CYBERGYM_DATA_DIR/.git" ]; then
  GIT_LFS_SKIP_SMUDGE=1 git clone "$CYBERGYM_DATA_REPO" "$CYBERGYM_DATA_DIR"
else
  echo "cybergym_data already present: $CYBERGYM_DATA_DIR"
fi

if [ "${CYBERGYM_SKIP_LFS_PULL:-0}" != "1" ]; then
  includes=("tasks.json")
  for task in "${SELECTED_TASKS[@]}"; do
    family="${task%%:*}"
    ident="${task#*:}"
    includes+=("data/${family}/${ident}/**")
  done
  include_csv="$(IFS=,; echo "${includes[*]}")"
  git -C "$CYBERGYM_DATA_DIR" lfs pull --include "$include_csv" --exclude ""
fi

pull_task_images

cat <<EOF
CyberGym subset setup complete.
TASK_IDS=${SELECTED_TASKS[*]}
CYBERGYM_ROOT=$CYBERGYM_ROOT
CYBERGYM_DATA_DIR=$CYBERGYM_DATA_DIR/data
EOF
