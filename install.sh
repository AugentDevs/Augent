#!/bin/bash
# Augent Installer
# Works everywhere. Installs everything.
# curl -fsSL https://augent.dev/install.sh | bash

set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================
AUGENT_VERSION="${AUGENT_VERSION:-latest}"
AUGENT_REPO="AugentDevs/Augent"
AUGENT_MIN_PYTHON="3.9"
INSTALL_METHOD="${AUGENT_INSTALL_METHOD:-pip}"  # pip or git
NO_ONBOARD="${AUGENT_NO_ONBOARD:-false}"
VERBOSE="${AUGENT_VERBOSE:-false}"

# ============================================================================
# Colors & Formatting
# ============================================================================
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

# ============================================================================
# Logging
# ============================================================================
log_info()    { echo -e "${BLUE}[info]${NC} $*"; }
log_success() { echo -e "${GREEN}[ok]${NC} $*"; }
log_warn()    { echo -e "${YELLOW}[warn]${NC} $*"; }
log_error()   { echo -e "${RED}[error]${NC} $*" >&2; }
log_step()    { echo -e "${CYAN}==>${NC} ${BOLD}$*${NC}"; }
log_verbose() { [[ "$VERBOSE" == "true" ]] && echo -e "${DIM}[debug] $*${NC}" || true; }

# ============================================================================
# Taglines (because why not)
# ============================================================================
TAGLINES=(
    "Audio intelligence for Claude agents"
    "Transcribe. Search. Analyze. Locally."
    "Your audio, your machine, your data"
    "Making Claude hear things"
    "Whisper-powered audio superpowers"
    "Because reading transcripts is so 2023"
)

get_tagline() {
    local idx=$((RANDOM % ${#TAGLINES[@]}))
    echo "${TAGLINES[$idx]}"
}

# ============================================================================
# OS Detection
# ============================================================================
detect_os() {
    case "$OSTYPE" in
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

log_verbose "Detected OS: $OS, Arch: $ARCH, Package Manager: $PKG_MGR"

# ============================================================================
# Utility Functions
# ============================================================================
command_exists() {
    command -v "$1" &>/dev/null
}

version_gte() {
    # Returns 0 if $1 >= $2
    printf '%s\n%s\n' "$2" "$1" | sort -V -C
}

retry() {
    local max_attempts=$1
    local delay=$2
    shift 2
    local attempt=1

    while [[ $attempt -le $max_attempts ]]; do
        if "$@"; then
            return 0
        fi
        log_warn "Attempt $attempt/$max_attempts failed, retrying in ${delay}s..."
        sleep "$delay"
        ((attempt++))
    done
    return 1
}

ensure_dir() {
    [[ -d "$1" ]] || mkdir -p "$1"
}

add_to_path() {
    local dir=$1
    local shell_rc

    # Determine shell config file
    if [[ -n "${ZSH_VERSION:-}" ]] || [[ "$SHELL" == */zsh ]]; then
        shell_rc="$HOME/.zshrc"
    else
        shell_rc="$HOME/.bashrc"
    fi

    # Check if already in PATH
    if [[ ":$PATH:" == *":$dir:"* ]]; then
        log_verbose "$dir already in PATH"
        return 0
    fi

    # Check if already in rc file
    if [[ -f "$shell_rc" ]] && grep -q "$dir" "$shell_rc" 2>/dev/null; then
        log_verbose "$dir already in $shell_rc"
        export PATH="$dir:$PATH"
        return 0
    fi

    # Add to rc file
    echo "" >> "$shell_rc"
    echo "# Added by Augent installer" >> "$shell_rc"
    echo "export PATH=\"$dir:\$PATH\"" >> "$shell_rc"
    export PATH="$dir:$PATH"
    log_success "Added $dir to PATH in $shell_rc"
}

# ============================================================================
# Dependency Installation
# ============================================================================
install_homebrew() {
    if command_exists brew; then
        log_success "Homebrew found"
        return 0
    fi

    log_step "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    # Add brew to PATH for this session
    if [[ "$ARCH" == "arm64" ]]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
    else
        eval "$(/usr/local/bin/brew shellenv)"
    fi

    log_success "Homebrew installed"
}

install_python() {
    log_step "Checking Python..."

    # Check if Python 3.9+ exists
    local python_cmd=""
    for cmd in python3 python; do
        if command_exists "$cmd"; then
            local ver
            ver=$($cmd -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || echo "0.0")
            if version_gte "$ver" "$AUGENT_MIN_PYTHON"; then
                python_cmd=$cmd
                log_success "Python $ver found ($cmd)"
                break
            fi
        fi
    done

    if [[ -n "$python_cmd" ]]; then
        PYTHON_CMD=$python_cmd
        return 0
    fi

    log_warn "Python $AUGENT_MIN_PYTHON+ not found, installing..."

    case "$PKG_MGR" in
        brew)
            brew install python@3.12
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
            log_error "Cannot auto-install Python. Please install Python $AUGENT_MIN_PYTHON+ manually."
            exit 1
            ;;
    esac

    log_success "Python installed"
}

install_pip() {
    log_step "Checking pip..."

    if $PYTHON_CMD -m pip --version &>/dev/null; then
        log_success "pip found"
        return 0
    fi

    log_warn "pip not found, installing..."

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
    log_step "Checking FFmpeg..."

    if command_exists ffmpeg; then
        log_success "FFmpeg found"
        return 0
    fi

    log_warn "FFmpeg not found, installing..."

    case "$PKG_MGR" in
        brew)
            brew install ffmpeg
            ;;
        apt)
            sudo apt-get update -qq
            sudo apt-get install -y ffmpeg
            ;;
        dnf)
            # FFmpeg requires RPM Fusion on Fedora
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
            log_warn "Cannot auto-install FFmpeg. Some features may be limited."
            log_warn "Install manually: https://ffmpeg.org/download.html"
            return 0
            ;;
    esac

    log_success "FFmpeg installed"
}

# ============================================================================
# Augent Installation
# ============================================================================
install_augent() {
    log_step "Installing Augent..."

    # Get script directory (if running from local clone)
    local script_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}" 2>/dev/null)" && pwd 2>/dev/null)" || script_dir=""

    if [[ -n "$script_dir" ]] && [[ -f "$script_dir/pyproject.toml" ]]; then
        # Local install (development mode)
        log_info "Installing from local source..."
        $PYTHON_CMD -m pip install -e "$script_dir[all]" --quiet --user 2>/dev/null || \
        $PYTHON_CMD -m pip install -e "$script_dir[all]" --quiet
    elif [[ "$INSTALL_METHOD" == "git" ]]; then
        # Git clone install
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
        $PYTHON_CMD -m pip install -e ".[all]" --quiet
    else
        # PyPI install
        if [[ "$AUGENT_VERSION" == "latest" ]]; then
            $PYTHON_CMD -m pip install augent[all] --quiet --upgrade --user 2>/dev/null || \
            $PYTHON_CMD -m pip install augent[all] --quiet --upgrade
        else
            $PYTHON_CMD -m pip install "augent[all]==$AUGENT_VERSION" --quiet --user 2>/dev/null || \
            $PYTHON_CMD -m pip install "augent[all]==$AUGENT_VERSION" --quiet
        fi
    fi

    log_success "Augent installed"
}

verify_installation() {
    log_step "Verifying installation..."

    local user_bin="$HOME/.local/bin"
    local pip_bin
    pip_bin=$($PYTHON_CMD -m site --user-base 2>/dev/null)/bin || pip_bin="$user_bin"

    # Add common bin directories to PATH if needed
    for bindir in "$user_bin" "$pip_bin" "$HOME/Library/Python/3.12/bin" "$HOME/Library/Python/3.11/bin"; do
        if [[ -d "$bindir" ]] && [[ ":$PATH:" != *":$bindir:"* ]]; then
            add_to_path "$bindir"
        fi
    done

    # Verify augent command
    if command_exists augent; then
        log_success "CLI ready: augent"
    elif $PYTHON_CMD -m augent.cli --help &>/dev/null; then
        log_success "CLI ready: $PYTHON_CMD -m augent.cli"
        AUGENT_CMD="$PYTHON_CMD -m augent.cli"
    else
        log_warn "CLI not in PATH. You may need to restart your terminal."
    fi

    # Verify MCP server
    if command_exists augent-mcp; then
        log_success "MCP server ready: augent-mcp"
        MCP_CMD="augent-mcp"
    elif $PYTHON_CMD -m augent.mcp --help &>/dev/null 2>&1; then
        log_success "MCP server ready: $PYTHON_CMD -m augent.mcp"
        MCP_CMD="$PYTHON_CMD -m augent.mcp"
    else
        log_warn "MCP server not verified"
        MCP_CMD="$PYTHON_CMD -m augent.mcp"
    fi
}

# ============================================================================
# Configuration & Onboarding
# ============================================================================
configure_claude_code() {
    local mcp_json=".mcp.json"

    if [[ -f "$mcp_json" ]]; then
        # Check if augent already configured
        if grep -q "augent" "$mcp_json" 2>/dev/null; then
            log_success "Augent already configured in $mcp_json"
            return 0
        fi

        log_info "Adding Augent to existing $mcp_json..."
        # This is tricky without jq, so we'll just inform the user
        log_warn "Please add Augent manually to your existing $mcp_json"
        return 0
    fi

    # Create new .mcp.json
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
}

configure_claude_desktop() {
    local config_dir config_file

    case "$OS" in
        macos)
            config_dir="$HOME/Library/Application Support/Claude"
            ;;
        linux|wsl)
            config_dir="$HOME/.config/Claude"
            ;;
        *)
            return 0
            ;;
    esac

    config_file="$config_dir/claude_desktop_config.json"

    if [[ ! -d "$config_dir" ]]; then
        log_verbose "Claude Desktop config directory not found, skipping"
        return 0
    fi

    if [[ -f "$config_file" ]] && grep -q "augent" "$config_file" 2>/dev/null; then
        log_success "Augent already configured in Claude Desktop"
        return 0
    fi

    if [[ -f "$config_file" ]]; then
        log_warn "Claude Desktop config exists. Add Augent manually:"
        echo ""
        echo "  \"augent\": {"
        echo "    \"command\": \"$PYTHON_CMD\","
        echo "    \"args\": [\"-m\", \"augent.mcp\"]"
        echo "  }"
        echo ""
        return 0
    fi

    # Create new config
    ensure_dir "$config_dir"
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
}

run_onboarding() {
    if [[ "$NO_ONBOARD" == "true" ]]; then
        return 0
    fi

    echo ""
    echo -e "${BOLD}Quick Setup${NC}"
    echo ""

    # Ask about Claude Code
    read -r -p "Configure for Claude Code (current directory)? [Y/n] " response
    case "$response" in
        [nN][oO]|[nN]) ;;
        *) configure_claude_code ;;
    esac

    # Ask about Claude Desktop
    if [[ "$OS" == "macos" ]] || [[ "$OS" == "linux" ]]; then
        read -r -p "Configure for Claude Desktop? [Y/n] " response
        case "$response" in
            [nN][oO]|[nN]) ;;
            *) configure_claude_desktop ;;
        esac
    fi
}

# ============================================================================
# Main
# ============================================================================
main() {
    echo ""
    echo -e "${MAGENTA}${BOLD}"
    echo "    _                         _   "
    echo "   / \\  _   _  __ _  ___ _ __ | |_ "
    echo "  / _ \\| | | |/ _\` |/ _ \\ '_ \\| __|"
    echo " / ___ \\ |_| | (_| |  __/ | | | |_ "
    echo "/_/   \\_\\__,_|\\__, |\\___|_| |_|\\__|"
    echo "              |___/                "
    echo -e "${NC}"
    echo -e "${DIM}$(get_tagline)${NC}"
    echo ""

    log_info "Detected: $OS ($ARCH)"
    echo ""

    # macOS: Ensure Homebrew first
    if [[ "$OS" == "macos" ]]; then
        install_homebrew
    fi

    # Install dependencies
    install_python
    install_pip
    install_ffmpeg

    echo ""

    # Install Augent
    install_augent
    verify_installation

    echo ""

    # Onboarding
    run_onboarding

    # Done!
    echo ""
    echo -e "${GREEN}${BOLD}============================================${NC}"
    echo -e "${GREEN}${BOLD}  Installation Complete!${NC}"
    echo -e "${GREEN}${BOLD}============================================${NC}"
    echo ""
    echo -e "  ${BOLD}Test it:${NC}"
    echo "    augent --help"
    echo ""
    echo -e "  ${BOLD}Quick start:${NC}"
    echo "    augent transcribe audio.mp3"
    echo "    augent search audio.mp3 \"keyword\""
    echo ""
    echo -e "  ${BOLD}Web UI:${NC}"
    echo "    augent-web"
    echo ""
    echo -e "  ${BOLD}Docs:${NC} https://github.com/$AUGENT_REPO"
    echo ""

    # Remind about terminal restart if PATH was modified
    if [[ "${PATH_MODIFIED:-false}" == "true" ]]; then
        echo -e "${YELLOW}Note: Restart your terminal or run 'source ~/.bashrc' to update PATH${NC}"
        echo ""
    fi
}

# Run main
main "$@"
