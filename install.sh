#!/bin/bash
# Augent Installer
# Works everywhere. Installs everything.
# curl -fsSL https://augent.app/install.sh | bash

set -eo pipefail

# ============================================================================
# Configuration
# ============================================================================
AUGENT_VERSION="${AUGENT_VERSION:-latest}"
AUGENT_REPO="AugentDevs/Augent"
AUGENT_MIN_PYTHON="3.9"
INSTALL_METHOD="${AUGENT_INSTALL_METHOD:-pip}"
NO_ONBOARD="${AUGENT_NO_ONBOARD:-false}"
VERBOSE="${AUGENT_VERBOSE:-false}"
PATH_MODIFIED=false
PYTHON_CMD=""
MCP_CMD=""

# ============================================================================
# Colors & Formatting
# ============================================================================
setup_colors() {
    if [[ -t 1 ]]; then
        RED='\033[0;31m'
        GREEN='\033[0;32m'
        YELLOW='\033[1;33m'
        BLUE='\033[0;34m'
        MAGENTA='\033[0;35m'
        CYAN='\033[0;36m'
        BOLD='\033[1m'
        DIM='\033[2m'
        NC='\033[0m'
    else
        RED='' GREEN='' YELLOW='' BLUE='' MAGENTA='' CYAN='' BOLD='' DIM='' NC=''
    fi
}
setup_colors

# ============================================================================
# Logging
# ============================================================================
log_info()    { echo -e "${BLUE}::${NC} $*"; }
log_success() { echo -e "${GREEN}✓${NC} $*"; }
log_warn()    { echo -e "${YELLOW}!${NC} $*"; }
log_error()   { echo -e "${RED}✗${NC} $*" >&2; }
log_step()    { echo -e "\n${CYAN}▶${NC} ${BOLD}$*${NC}"; }

# ============================================================================
# OS Detection
# ============================================================================
detect_os() {
    case "${OSTYPE:-}" in
        darwin*)  echo "macos" ;;
        linux*)
            if grep -qi microsoft /proc/version 2>/dev/null; then
                echo "wsl"
            else
                echo "linux"
            fi
            ;;
        msys*|cygwin*) echo "windows" ;;
        *)        echo "unknown" ;;
    esac
}

detect_arch() {
    local arch
    arch=$(uname -m)
    case "$arch" in
        x86_64|amd64) echo "x64" ;;
        arm64|aarch64) echo "arm64" ;;
        *) echo "$arch" ;;
    esac
}

detect_package_manager() {
    local os=$1
    if [[ "$os" == "macos" ]]; then
        echo "brew"
    elif command -v apt-get &>/dev/null; then
        echo "apt"
    elif command -v dnf &>/dev/null; then
        echo "dnf"
    elif command -v yum &>/dev/null; then
        echo "yum"
    elif command -v pacman &>/dev/null; then
        echo "pacman"
    elif command -v apk &>/dev/null; then
        echo "apk"
    else
        echo "unknown"
    fi
}

OS=$(detect_os)
ARCH=$(detect_arch)
PKG_MGR=$(detect_package_manager "$OS")

# ============================================================================
# Utility Functions
# ============================================================================
command_exists() {
    command -v "$1" &>/dev/null
}

version_gte() {
    printf '%s\n%s\n' "$2" "$1" | sort -V -C
}

ensure_dir() {
    [[ -d "$1" ]] || mkdir -p "$1"
}

add_to_path() {
    local dir=$1
    local shell_rc

    if [[ -n "${ZSH_VERSION:-}" ]] || [[ "${SHELL:-}" == */zsh ]]; then
        shell_rc="$HOME/.zshrc"
    else
        shell_rc="$HOME/.bashrc"
    fi

    if [[ ":$PATH:" == *":$dir:"* ]]; then
        return 0
    fi

    if [[ -f "$shell_rc" ]] && grep -q "$dir" "$shell_rc" 2>/dev/null; then
        export PATH="$dir:$PATH"
        return 0
    fi

    echo "" >> "$shell_rc"
    echo "# Added by Augent installer" >> "$shell_rc"
    echo "export PATH=\"$dir:\$PATH\"" >> "$shell_rc"
    export PATH="$dir:$PATH"
    PATH_MODIFIED=true
    log_success "Added $dir to PATH"
}

# ============================================================================
# Dependency Installation
# ============================================================================
install_homebrew() {
    if command_exists brew; then
        log_success "Homebrew found"
        return 0
    fi

    log_info "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" </dev/null

    if [[ "$ARCH" == "arm64" ]]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
    else
        eval "$(/usr/local/bin/brew shellenv)"
    fi

    log_success "Homebrew installed"
}

install_python() {
    log_step "Checking Python"

    for cmd in python3 python; do
        if command_exists "$cmd"; then
            local ver
            ver=$($cmd -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || echo "0.0")
            if version_gte "$ver" "$AUGENT_MIN_PYTHON"; then
                PYTHON_CMD=$cmd
                log_success "Python $ver"
                return 0
            fi
        fi
    done

    log_info "Installing Python..."

    case "$PKG_MGR" in
        brew)
            brew install python@3.12 2>/dev/null
            PYTHON_CMD="python3"
            ;;
        apt)
            sudo apt-get update -qq
            sudo apt-get install -y python3 python3-pip python3-venv
            PYTHON_CMD="python3"
            ;;
        dnf|yum)
            sudo $PKG_MGR install -y python3 python3-pip
            PYTHON_CMD="python3"
            ;;
        pacman)
            sudo pacman -Sy --noconfirm python python-pip
            PYTHON_CMD="python"
            ;;
        apk)
            sudo apk add python3 py3-pip
            PYTHON_CMD="python3"
            ;;
        *)
            log_error "Please install Python $AUGENT_MIN_PYTHON+ manually"
            exit 1
            ;;
    esac

    log_success "Python installed"
}

install_pip() {
    log_step "Checking pip"

    if $PYTHON_CMD -m pip --version &>/dev/null; then
        log_success "pip found"
        return 0
    fi

    log_info "Installing pip..."

    case "$PKG_MGR" in
        apt)
            sudo apt-get install -y python3-pip
            ;;
        *)
            curl -fsSL https://bootstrap.pypa.io/get-pip.py | $PYTHON_CMD
            ;;
    esac

    log_success "pip installed"
}

install_ffmpeg() {
    log_step "Checking FFmpeg"

    if command_exists ffmpeg; then
        log_success "FFmpeg found"
        return 0
    fi

    log_info "Installing FFmpeg..."

    case "$PKG_MGR" in
        brew)
            brew install ffmpeg 2>/dev/null
            ;;
        apt)
            sudo apt-get update -qq
            sudo apt-get install -y ffmpeg
            ;;
        dnf)
            sudo dnf install -y https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm 2>/dev/null || true
            sudo dnf install -y ffmpeg
            ;;
        yum)
            sudo yum install -y epel-release
            sudo yum install -y ffmpeg
            ;;
        pacman)
            sudo pacman -Sy --noconfirm ffmpeg
            ;;
        apk)
            sudo apk add ffmpeg
            ;;
        *)
            log_warn "Install FFmpeg manually for full functionality"
            return 0
            ;;
    esac

    log_success "FFmpeg installed"
}

# ============================================================================
# Augent Installation
# ============================================================================
install_augent() {
    log_step "Installing Augent"

    local script_dir=""
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}" 2>/dev/null)" 2>/dev/null && pwd 2>/dev/null)" || true

    if [[ -n "$script_dir" ]] && [[ -f "$script_dir/pyproject.toml" ]]; then
        log_info "Installing from local source..."
        $PYTHON_CMD -m pip install -e "$script_dir[all]" --quiet --user 2>/dev/null || \
        $PYTHON_CMD -m pip install -e "$script_dir[all]" --quiet || true
    elif [[ "$INSTALL_METHOD" == "git" ]]; then
        local install_dir="$HOME/.augent/src"
        ensure_dir "$install_dir"

        if [[ -d "$install_dir/Augent" ]]; then
            log_info "Updating existing installation..."
            cd "$install_dir/Augent"
            git pull --quiet
        else
            log_info "Cloning repository..."
            git clone --quiet "https://github.com/$AUGENT_REPO.git" "$install_dir/Augent"
            cd "$install_dir/Augent"
        fi

        $PYTHON_CMD -m pip install -e ".[all]" --quiet --user 2>/dev/null || \
        $PYTHON_CMD -m pip install -e ".[all]" --quiet || true
    else
        if [[ "$AUGENT_VERSION" == "latest" ]]; then
            $PYTHON_CMD -m pip install "augent[all]" --quiet --upgrade --user 2>/dev/null || \
            $PYTHON_CMD -m pip install "augent[all]" --quiet --upgrade || true
        else
            $PYTHON_CMD -m pip install "augent[all]==$AUGENT_VERSION" --quiet --user 2>/dev/null || \
            $PYTHON_CMD -m pip install "augent[all]==$AUGENT_VERSION" --quiet || true
        fi
    fi

    log_success "Augent installed"
}

verify_installation() {
    log_step "Verifying installation"

    local user_bin="$HOME/.local/bin"
    local pip_bin=""
    pip_bin="$($PYTHON_CMD -m site --user-base 2>/dev/null)/bin" || pip_bin="$user_bin"

    # Add bin directories to PATH
    for bindir in "$user_bin" "$pip_bin" "$HOME/Library/Python/3.12/bin" "$HOME/Library/Python/3.11/bin" "$HOME/Library/Python/3.10/bin" "$HOME/Library/Python/3.9/bin"; do
        if [[ -d "$bindir" ]] && [[ ":$PATH:" != *":$bindir:"* ]]; then
            add_to_path "$bindir"
        fi
    done

    # Set MCP_CMD
    if command_exists augent-mcp; then
        MCP_CMD="augent-mcp"
        log_success "MCP server ready"
    else
        MCP_CMD="$PYTHON_CMD -m augent.mcp"
        log_success "MCP server ready (via python -m)"
    fi

    # Verify CLI
    if command_exists augent; then
        log_success "CLI ready: augent"
    else
        log_success "CLI ready: $PYTHON_CMD -m augent.cli"
    fi
}

# ============================================================================
# Configuration
# ============================================================================
configure_mcp() {
    log_step "Configuring MCP"

    # Claude Code config
    local mcp_json=".mcp.json"
    if [[ ! -f "$mcp_json" ]]; then
        cat > "$mcp_json" << EOF
{
  "mcpServers": {
    "augent": {
      "command": "$MCP_CMD"
    }
  }
}
EOF
        log_success "Created $mcp_json"
    elif ! grep -q "augent" "$mcp_json" 2>/dev/null; then
        log_info "Add to your $mcp_json: \"augent\": {\"command\": \"$MCP_CMD\"}"
    else
        log_success "Already configured in $mcp_json"
    fi

    # Claude Desktop config
    local config_dir=""
    case "$OS" in
        macos) config_dir="$HOME/Library/Application Support/Claude" ;;
        linux|wsl) config_dir="$HOME/.config/Claude" ;;
    esac

    if [[ -n "$config_dir" ]] && [[ -d "$config_dir" ]]; then
        local config_file="$config_dir/claude_desktop_config.json"
        if [[ ! -f "$config_file" ]]; then
            cat > "$config_file" << EOF
{
  "mcpServers": {
    "augent": {
      "command": "$PYTHON_CMD",
      "args": ["-m", "augent.mcp"]
    }
  }
}
EOF
            log_success "Configured Claude Desktop"
        elif ! grep -q "augent" "$config_file" 2>/dev/null; then
            log_info "Add Augent to Claude Desktop config manually"
        fi
    fi
}

# ============================================================================
# Main
# ============================================================================
main() {
    echo ""
    echo -e "${MAGENTA}${BOLD}"
    cat << 'EOF'
    _                         _
   / \  _   _  __ _  ___ _ __ | |_
  / _ \| | | |/ _` |/ _ \ '_ \| __|
 / ___ \ |_| | (_| |  __/ | | | |_
/_/   \_\__,_|\__, |\___|_| |_|\__|
              |___/
EOF
    echo -e "${NC}"
    echo -e "${DIM}Audio intelligence for Claude agents${NC}"
    echo ""

    log_info "Detected: $OS ($ARCH)"

    # macOS: Ensure Homebrew first
    if [[ "$OS" == "macos" ]]; then
        install_homebrew
    fi

    # Install dependencies
    install_python
    install_pip
    install_ffmpeg

    # Install Augent
    install_augent
    verify_installation

    # Configure MCP (skip interactive prompts when piped)
    if [[ -t 0 ]]; then
        # Interactive mode
        echo ""
        read -r -p "Configure MCP for Claude? [Y/n] " response </dev/tty || response="y"
        case "$response" in
            [nN]) ;;
            *) configure_mcp ;;
        esac
    else
        # Non-interactive (piped) - auto-configure
        configure_mcp
    fi

    # Done!
    echo ""
    echo -e "${GREEN}${BOLD}════════════════════════════════════════════${NC}"
    echo -e "${GREEN}${BOLD}  ✓ Installation Complete${NC}"
    echo -e "${GREEN}${BOLD}════════════════════════════════════════════${NC}"
    echo ""
    echo "  Test it:"
    echo "    ${BOLD}augent --help${NC}"
    echo ""
    echo "  Quick start:"
    echo "    ${BOLD}augent transcribe audio.mp3${NC}"
    echo "    ${BOLD}augent search audio.mp3 \"keyword\"${NC}"
    echo ""
    echo "  Web UI:"
    echo "    ${BOLD}augent-web${NC}"
    echo ""
    echo "  Docs: https://github.com/$AUGENT_REPO"
    echo ""

    if [[ "$PATH_MODIFIED" == "true" ]]; then
        echo -e "${YELLOW}Note: Restart your terminal to update PATH${NC}"
        echo ""
    fi
}

main "$@"
