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
        WHITE='\033[1;37m'
        BOLD='\033[1m'
        DIM='\033[2m'
        NC='\033[0m'
    else
        RED='' GREEN='' YELLOW='' BLUE='' MAGENTA='' CYAN='' WHITE='' BOLD='' DIM='' NC=''
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
        log_success "Homebrew"
        return 0
    fi

    log_info "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" </dev/null >/dev/null 2>&1

    if [[ "$ARCH" == "arm64" ]]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
    else
        eval "$(/usr/local/bin/brew shellenv)"
    fi

    log_success "Homebrew"
}

install_python() {
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
            brew install python@3.12 >/dev/null 2>&1
            PYTHON_CMD="python3"
            ;;
        apt)
            sudo apt-get update -qq >/dev/null 2>&1
            sudo apt-get install -y python3 python3-pip python3-venv >/dev/null 2>&1
            PYTHON_CMD="python3"
            ;;
        dnf|yum)
            sudo $PKG_MGR install -y python3 python3-pip >/dev/null 2>&1
            PYTHON_CMD="python3"
            ;;
        pacman)
            sudo pacman -Sy --noconfirm python python-pip >/dev/null 2>&1
            PYTHON_CMD="python"
            ;;
        apk)
            sudo apk add python3 py3-pip >/dev/null 2>&1
            PYTHON_CMD="python3"
            ;;
        *)
            log_error "Please install Python $AUGENT_MIN_PYTHON+ manually"
            exit 1
            ;;
    esac

    log_success "Python"
}

install_pip() {
    if $PYTHON_CMD -m pip --version &>/dev/null; then
        log_success "pip"
        return 0
    fi

    log_info "Installing pip..."

    case "$PKG_MGR" in
        apt)
            sudo apt-get install -y python3-pip >/dev/null 2>&1
            ;;
        *)
            curl -fsSL https://bootstrap.pypa.io/get-pip.py 2>/dev/null | $PYTHON_CMD >/dev/null 2>&1
            ;;
    esac

    log_success "pip"
}

install_ffmpeg() {
    if command_exists ffmpeg; then
        log_success "FFmpeg"
        return 0
    fi

    log_info "Installing FFmpeg..."

    case "$PKG_MGR" in
        brew)
            brew install ffmpeg >/dev/null 2>&1
            ;;
        apt)
            sudo apt-get update -qq >/dev/null 2>&1
            sudo apt-get install -y ffmpeg >/dev/null 2>&1
            ;;
        dnf)
            sudo dnf install -y https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm >/dev/null 2>&1 || true
            sudo dnf install -y ffmpeg >/dev/null 2>&1
            ;;
        yum)
            sudo yum install -y epel-release >/dev/null 2>&1
            sudo yum install -y ffmpeg >/dev/null 2>&1
            ;;
        pacman)
            sudo pacman -Sy --noconfirm ffmpeg >/dev/null 2>&1
            ;;
        apk)
            sudo apk add ffmpeg >/dev/null 2>&1
            ;;
        *)
            log_warn "Install FFmpeg manually for full functionality"
            return 0
            ;;
    esac

    log_success "FFmpeg"
}

# ============================================================================
# Augent Installation
# ============================================================================
install_augent() {
    log_info "Installing Augent..."

    local script_dir=""
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}" 2>/dev/null)" 2>/dev/null && pwd 2>/dev/null)" || true

    if [[ -n "$script_dir" ]] && [[ -f "$script_dir/pyproject.toml" ]]; then
        # Local install (development mode)
        $PYTHON_CMD -m pip install -e "$script_dir[all]" --quiet --user 2>/dev/null || \
        $PYTHON_CMD -m pip install -e "$script_dir[all]" --quiet 2>/dev/null || true
    else
        # Install from GitHub (always latest)
        $PYTHON_CMD -m pip install "augent[all] @ git+https://github.com/$AUGENT_REPO.git" --quiet --upgrade --user 2>/dev/null || \
        $PYTHON_CMD -m pip install "augent[all] @ git+https://github.com/$AUGENT_REPO.git" --quiet --upgrade 2>/dev/null || true
    fi

    log_success "Augent"
}

install_audio_downloader() {
    log_info "Installing audio-downloader..."

    local script_dir=""
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}" 2>/dev/null)" 2>/dev/null && pwd 2>/dev/null)" || true

    local user_bin="$HOME/.local/bin"
    ensure_dir "$user_bin"

    # Install yt-dlp and aria2 for speed optimization
    case "$PKG_MGR" in
        brew)
            command_exists yt-dlp || brew install yt-dlp >/dev/null 2>&1
            command_exists aria2c || brew install aria2 >/dev/null 2>&1
            ;;
        apt)
            command_exists yt-dlp || (sudo apt-get update -qq && sudo apt-get install -y yt-dlp) >/dev/null 2>&1 || \
            $PYTHON_CMD -m pip install yt-dlp --quiet --user 2>/dev/null || true
            command_exists aria2c || sudo apt-get install -y aria2 >/dev/null 2>&1
            ;;
        *)
            command_exists yt-dlp || $PYTHON_CMD -m pip install yt-dlp --quiet --user 2>/dev/null || true
            ;;
    esac

    # Install the audio-downloader script
    if [[ -n "$script_dir" ]] && [[ -f "$script_dir/bin/audio-downloader" ]]; then
        cp "$script_dir/bin/audio-downloader" "$user_bin/"
        chmod +x "$user_bin/audio-downloader"
    else
        # Download from GitHub
        curl -fsSL "https://raw.githubusercontent.com/$AUGENT_REPO/main/bin/audio-downloader" -o "$user_bin/audio-downloader" 2>/dev/null || true
        chmod +x "$user_bin/audio-downloader" 2>/dev/null || true
    fi

    add_to_path "$user_bin"
    log_success "audio-downloader"
}

verify_installation() {
    local user_bin="$HOME/.local/bin"
    local pip_bin=""
    pip_bin="$($PYTHON_CMD -m site --user-base 2>/dev/null)/bin" || pip_bin="$user_bin"

    # Add bin directories to PATH silently
    for bindir in "$user_bin" "$pip_bin" "$HOME/Library/Python/3.12/bin" "$HOME/Library/Python/3.11/bin" "$HOME/Library/Python/3.10/bin" "$HOME/Library/Python/3.9/bin"; do
        if [[ -d "$bindir" ]] && [[ ":$PATH:" != *":$bindir:"* ]]; then
            add_to_path "$bindir"
        fi
    done

    # Set MCP_CMD
    if command_exists augent-mcp; then
        MCP_CMD="augent-mcp"
    else
        MCP_CMD="$PYTHON_CMD -m augent.mcp"
    fi

    log_success "CLI ready"
}

# ============================================================================
# Configuration
# ============================================================================
configure_mcp() {
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
        log_success "Created .mcp.json"
    elif ! grep -q "augent" "$mcp_json" 2>/dev/null; then
        log_info "Add augent to your existing .mcp.json"
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
        fi
    fi
}

# ============================================================================
# Main
# ============================================================================
main() {
    echo ""
    echo -e "${GREEN}"
    cat << 'EOF'
    _                          _
   / \  _   _  __ _  ___ _ __ | |_
  / _ \| | | |/ _` |/ _ \ '_ \| __|
 / ___ \ |_| | (_| |  __/ | | | |_
/_/   \_\__,_|\__, |\___|_| |_|\__|
              |___/
EOF
    echo -e "${NC}${DIM}Audio intelligence for Claude agents${NC}"
    echo ""

    # macOS: Ensure Homebrew first
    if [[ "$OS" == "macos" ]]; then
        install_homebrew
    fi

    # Install dependencies
    install_python
    install_pip
    install_ffmpeg
    install_augent
    install_audio_downloader
    verify_installation

    # Configure MCP (auto when piped)
    if [[ -t 0 ]]; then
        read -r -p "Configure MCP for Claude? [Y/n] " response </dev/tty || response="y"
        case "$response" in
            [nN]) ;;
            *) configure_mcp ;;
        esac
    else
        configure_mcp
    fi

    # Done
    echo ""
    echo -e "${GREEN}${BOLD}════════════════════════════════════════════"
    echo "  ✓ Installation Complete"
    echo "════════════════════════════════════════════${NC}"
    echo ""
    echo "  ${BOLD}augent --help${NC}              Show commands"
    echo "  ${BOLD}augent-web${NC}                 Launch Web UI"
    echo "  ${BOLD}augent transcribe f.mp3${NC}   Transcribe audio"
    echo "  ${BOLD}audio-downloader URL${NC}      Download audio from video"
    echo ""
    if [[ "$PATH_MODIFIED" == "true" ]]; then
        echo -e "${YELLOW}↪ Restart terminal to update PATH${NC}"
        echo ""
    fi
}

main "$@"
exit 0
