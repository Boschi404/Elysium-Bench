#!/usr/bin/env bash
# =============================================================================
# Elysium-Bench One-Command Launcher
# 
# Usage:
#   ./run.sh                    # Full benchmark (all categories)
#   ./run.sh --category api     # Single category
#   ./run.sh --mode docker      # Docker mode (recommended for clean runs)
#   ./run.sh --no-cleanup       # Keep temp files for debugging
#   ./run.sh --list             # List all tasks without running
#   ./run.sh --quick            # Quick test: 1 category, 3 tasks max
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║           🚀  Elysium-Bench v0.1.0                       ║"
echo "║     Multi-Agent Self-Improvement Benchmark                ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ─── Parse Arguments ────────────────────────────────────────────────────────
MODE="venv"
CATEGORY=""
CLEANUP="--no-cleanup=false"
LIST_ONLY=false
QUICK=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --mode)
            MODE="$2"
            shift 2
            ;;
        --category|-C)
            CATEGORY="$2"
            shift 2
            ;;
        --no-cleanup)
            CLEANUP="--no-cleanup"
            shift
            ;;
        --list)
            LIST_ONLY=true
            shift
            ;;
        --quick)
            QUICK=true
            shift
            ;;
        --help|-h)
            echo "Usage: ./run.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --mode venv|docker    Execution mode (default: venv)"
            echo "  --category CAT_ID     Run only this category"
            echo "  --no-cleanup          Keep temp files after run"
            echo "  --list                List all tasks without running"
            echo "  --quick               Quick test: 1 category, reduced tasks"
            echo "  --help                Show this help"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# ─── Prerequisites ──────────────────────────────────────────────────────────
echo -e "${YELLOW}🔍 Checking prerequisites...${NC}"

# Python check
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo -e "${RED}❌ Python 3.10+ is required but not found.${NC}"
    echo "   Install from https://python.org"
    exit 1
fi

PYTHON=$(command -v python3 || command -v python)
echo -e "   ✅ Python: $($PYTHON --version)"

# Pip check
if ! $PYTHON -m pip --version &> /dev/null; then
    echo -e "${RED}❌ pip is required but not found.${NC}"
    exit 1
fi

# Docker check (only if docker mode)
if [ "$MODE" = "docker" ]; then
    if ! command -v docker &> /dev/null; then
        echo -e "${YELLOW}⚠️  Docker not found. Falling back to venv mode.${NC}"
        MODE="venv"
    else
        echo -e "   ✅ Docker: $(docker --version)"
    fi
fi

# ─── Install Dependencies ───────────────────────────────────────────────────
echo -e "\n${YELLOW}📦 Installing dependencies...${NC}"

if [ "$QUICK" = true ]; then
    $PYTHON -m pip install -q pyyaml rich click pydantic httpx pytest fastapi 2>&1 | tail -1
else
    $PYTHON -m pip install -q -e ".[dev]" 2>&1 | tail -1
fi

echo -e "   ✅ Dependencies ready"

# ─── Run Benchmark ──────────────────────────────────────────────────────────
if [ "$LIST_ONLY" = true ]; then
    echo -e "\n${CYAN}📋 Listing tasks...${NC}"
    $PYTHON -m elysium_bench.cli list-tasks
    exit 0
fi

echo -e "\n${GREEN}▶️  Running benchmark...${NC}\n"

# Build command
CMD="$PYTHON -m elysium_bench.cli run --mode $MODE"

if [ -n "$CATEGORY" ]; then
    CMD="$CMD --category $CATEGORY"
fi

if [ "$CLEANUP" = "--no-cleanup" ]; then
    CMD="$CMD --no-cleanup"
fi

# Execute
$CMD

EXIT_CODE=$?

# ─── Cleanup ────────────────────────────────────────────────────────────────
echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ Benchmark completed successfully!${NC}"
else
    echo -e "${RED}❌ Benchmark failed with exit code $EXIT_CODE${NC}"
fi

# Show results location
if [ -d "./results" ]; then
    LATEST=$(ls -t ./results/*.json 2>/dev/null | head -1)
    if [ -n "$LATEST" ]; then
        echo -e "${CYAN}📁 Latest results: $LATEST${NC}"
    fi
fi

exit $EXIT_CODE
