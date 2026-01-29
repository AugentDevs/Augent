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
AUGENT_MIN_PYTHON="3.10"
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

# Fix Python user base for multi-user systems
# Sets USER_PYTHON_BASE if Python's user directory doesn't match $HOME
USER_PYTHON_BASE=""
setup_python_user_base() {
    local py_user_base
    py_user_base="$($PYTHON_CMD -m site --user-base 2>/dev/null)" || py_user_base=""

    # If Python's user base doesn't match current $HOME, override it
    if [[ -n "$py_user_base" ]] && [[ "$py_user_base" != "$HOME"* ]]; then
        local py_ver
        py_ver="$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null)" || py_ver="3.9"

        case "$OS" in
            macos)
                USER_PYTHON_BASE="$HOME/Library/Python/$py_ver"
                ;;
            *)
                USER_PYTHON_BASE="$HOME/.local"
                ;;
        esac
        ensure_dir "$USER_PYTHON_BASE/bin"
        ensure_dir "$USER_PYTHON_BASE/lib/python/site-packages"
        add_to_path "$USER_PYTHON_BASE/bin"
    fi
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

check_homebrew_permissions() {
    # Only check on macOS with Homebrew
    [[ "$OS" != "macos" ]] && return 0

    local brew_prefix
    if [[ "$ARCH" == "arm64" ]]; then
        brew_prefix="/opt/homebrew"
    else
        brew_prefix="/usr/local"
    fi

    # If brew prefix exists but isn't writable, show helpful error
    if [[ -d "$brew_prefix" ]] && [[ ! -w "$brew_prefix" ]]; then
        echo ""
        log_error "Homebrew permission denied"
        echo ""
        echo -e "  ${DIM}$brew_prefix is owned by another user.${NC}"
        echo ""
        echo -e "  ${BOLD}Fix with:${NC}"
        echo -e "    sudo chown -R \$(whoami) $brew_prefix"
        echo ""
        echo -e "  Then re-run the installer."
        echo ""
        exit 1
    fi
}

install_python() {
    # Prefer python3.12 - has best wheel support; avoid 3.14 (missing prebuilt wheels)
    for cmd in python3.12 python3.13 python3.11 python3.10 python3 python; do
        if command_exists "$cmd"; then
            local ver
            ver=$($cmd -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || echo "0.0")
            if version_gte "$ver" "$AUGENT_MIN_PYTHON" && ! version_gte "$ver" "3.14"; then
                PYTHON_CMD=$(command -v "$cmd")
                log_success "Python $ver"
                return 0
            fi
        fi
    done

    log_info "Installing Python..."

    case "$PKG_MGR" in
        brew)
            brew install python@3.12 >/dev/null 2>&1
            if [[ "$ARCH" == "arm64" ]]; then
                PYTHON_CMD="/opt/homebrew/bin/python3.12"
            else
                PYTHON_CMD="/usr/local/bin/python3.12"
            fi
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
    # Determine pip flags based on package manager
    local pip_upgrade_flags=""
    if [[ "$PKG_MGR" == "brew" ]]; then
        pip_upgrade_flags="--break-system-packages"
    else
        pip_upgrade_flags="--user"
    fi

    if $PYTHON_CMD -m pip --version &>/dev/null; then
        # Upgrade pip to avoid bugs with pyproject.toml in old versions
        $PYTHON_CMD -m pip install --upgrade pip --quiet $pip_upgrade_flags 2>/dev/null || true
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

    # Homebrew Python: needs --break-system-packages (PEP 668)
    # Other systems: install with --user flag
    local pip_flags=""
    local pip_env=""
    if [[ "$PKG_MGR" == "brew" ]]; then
        pip_flags="--break-system-packages"
    else
        pip_flags="--user"
        if [[ -n "$USER_PYTHON_BASE" ]]; then
            pip_env="PYTHONUSERBASE=$USER_PYTHON_BASE"
        fi
    fi

    if [[ -n "$script_dir" ]] && [[ -f "$script_dir/pyproject.toml" ]]; then
        # Local install (development mode)
        env $pip_env $PYTHON_CMD -m pip install -e "$script_dir[all]" --quiet $pip_flags 2>/dev/null || \
        env $pip_env $PYTHON_CMD -m pip install -e "$script_dir[all]" --quiet 2>/dev/null || true
    else
        # Uninstall old version and clear pip cache
        $PYTHON_CMD -m pip uninstall augent -y --quiet 2>/dev/null || true
        $PYTHON_CMD -m pip cache purge 2>/dev/null || true
        # Install from GitHub (always latest)
        env $pip_env $PYTHON_CMD -m pip install "augent[all] @ git+https://github.com/$AUGENT_REPO.git@main" --quiet --no-cache-dir $pip_flags 2>/dev/null || \
        env $pip_env $PYTHON_CMD -m pip install "augent[all] @ git+https://github.com/$AUGENT_REPO.git@main" --quiet --no-cache-dir 2>/dev/null || true
    fi

    log_success "Augent"
}

install_audio_downloader() {
    log_info "Installing audio-downloader..."

    local script_dir=""
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}" 2>/dev/null)" 2>/dev/null && pwd 2>/dev/null)" || true

    local user_bin="$HOME/.local/bin"
    ensure_dir "$user_bin"

    # Homebrew Python: needs --break-system-packages (PEP 668)
    local pip_flags=""
    local pip_env=""
    if [[ "$PKG_MGR" == "brew" ]]; then
        pip_flags="--break-system-packages"
    else
        pip_flags="--user"
        if [[ -n "$USER_PYTHON_BASE" ]]; then
            pip_env="PYTHONUSERBASE=$USER_PYTHON_BASE"
        fi
    fi

    # Install yt-dlp (pinned version for aria2c compatibility) and aria2
    local ytdlp_version="2025.03.31"
    case "$PKG_MGR" in
        brew)
            if ! command_exists yt-dlp; then
                $PYTHON_CMD -m pip install $pip_flags "yt-dlp==$ytdlp_version" --quiet 2>/dev/null || \
                brew install yt-dlp >/dev/null 2>&1
            fi
            command_exists aria2c || brew install aria2 >/dev/null 2>&1
            ;;
        apt)
            if ! command_exists yt-dlp; then
                env $pip_env $PYTHON_CMD -m pip install "yt-dlp==$ytdlp_version" --quiet $pip_flags 2>/dev/null || \
                (sudo apt-get update -qq && sudo apt-get install -y yt-dlp) >/dev/null 2>&1 || true
            fi
            command_exists aria2c || sudo apt-get install -y aria2 >/dev/null 2>&1
            ;;
        *)
            command_exists yt-dlp || env $pip_env $PYTHON_CMD -m pip install "yt-dlp==$ytdlp_version" --quiet $pip_flags 2>/dev/null || true
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

    # Homebrew bin directory (where Homebrew Python installs scripts)
    local brew_bin=""
    if [[ "$OS" == "macos" ]]; then
        if [[ "$ARCH" == "arm64" ]]; then
            brew_bin="/opt/homebrew/bin"
        else
            brew_bin="/usr/local/bin"
        fi
    fi

    # Add bin directories to PATH
    for bindir in "$brew_bin" "$user_bin" "$pip_bin" "$HOME/Library/Python/3.12/bin" "$HOME/Library/Python/3.11/bin" "$HOME/Library/Python/3.10/bin"; do
        if [[ -n "$bindir" ]] && [[ -d "$bindir" ]] && [[ ":$PATH:" != *":$bindir:"* ]]; then
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
    # Get absolute path to Python (fixes multi-user and PATH issues)
    local python_abs=""
    python_abs="$(command -v $PYTHON_CMD 2>/dev/null)" || python_abs="$PYTHON_CMD"

    # Resolve symlinks to get true path
    if [[ -L "$python_abs" ]]; then
        python_abs="$(readlink -f "$python_abs" 2>/dev/null || readlink "$python_abs" 2>/dev/null || echo "$python_abs")"
    fi

    # Claude Code global config (~/.claude/settings.json)
    local claude_dir="$HOME/.claude"
    local settings_file="$claude_dir/settings.json"
    ensure_dir "$claude_dir"

    if [[ -f "$settings_file" ]]; then
        # Check if augent already configured
        if grep -q '"augent"' "$settings_file" 2>/dev/null; then
            log_success "Claude Code MCP (already configured)"
        else
            # File exists but no augent - need to merge
            # Try jq first, fall back to manual instruction
            if command_exists jq; then
                local tmp_file="$claude_dir/settings.tmp.json"
                jq --arg py "$python_abs" '.mcpServers.augent = {"command": $py, "args": ["-m", "augent.mcp"]}' "$settings_file" > "$tmp_file" 2>/dev/null && mv "$tmp_file" "$settings_file"
                log_success "Claude Code MCP (added to existing config)"
            else
                log_warn "Add augent to $settings_file manually (jq not installed)"
                log_info "  \"augent\": {\"command\": \"$python_abs\", \"args\": [\"-m\", \"augent.mcp\"]}"
            fi
        fi
    else
        # Create new settings file
        cat > "$settings_file" << EOF
{
  "mcpServers": {
    "augent": {
      "command": "$python_abs",
      "args": ["-m", "augent.mcp"]
    }
  }
}
EOF
        log_success "Claude Code MCP"
    fi

    # Claude Desktop config
    local config_dir=""
    case "$OS" in
        macos) config_dir="$HOME/Library/Application Support/Claude" ;;
        linux|wsl) config_dir="$HOME/.config/Claude" ;;
    esac

    if [[ -n "$config_dir" ]]; then
        ensure_dir "$config_dir"
        local config_file="$config_dir/claude_desktop_config.json"
        if [[ -f "$config_file" ]]; then
            if grep -q '"augent"' "$config_file" 2>/dev/null; then
                log_success "Claude Desktop MCP (already configured)"
            elif command_exists jq; then
                local tmp_file="$config_dir/claude_desktop_config.tmp.json"
                jq --arg py "$python_abs" '.mcpServers.augent = {"command": $py, "args": ["-m", "augent.mcp"]}' "$config_file" > "$tmp_file" 2>/dev/null && mv "$tmp_file" "$config_file"
                log_success "Claude Desktop MCP (added to existing config)"
            else
                log_warn "Add augent to Claude Desktop config manually"
            fi
        else
            cat > "$config_file" << EOF
{
  "mcpServers": {
    "augent": {
      "command": "$python_abs",
      "args": ["-m", "augent.mcp"]
    }
  }
}
EOF
            log_success "Claude Desktop MCP"
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
        check_homebrew_permissions
    fi

    # Install dependencies
    install_python
    install_pip
    setup_python_user_base
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
    echo -e "  ✓ Installation Complete"
    echo -e "════════════════════════════════════════════${NC}"
    echo ""
    echo -e "  ${BOLD}CLI Commands${NC}"
    echo -e "  ${DIM}augent --help${NC}              Show commands"
    echo -e "  ${DIM}augent-web${NC}                 Launch Web UI"
    echo -e "  ${DIM}augent transcribe f.mp3${NC}   Transcribe audio"
    echo -e "  ${DIM}audio-downloader URL${NC}      Download audio from video"
    echo ""
    echo -e "  ${BOLD}Claude Integration${NC}"
    echo -e "  MCP configured globally - works in any project directory"
    echo ""
    if [[ "$PATH_MODIFIED" == "true" ]]; then
        echo -e "${YELLOW}Next steps:${NC}"
        echo -e "  1. Close this terminal and open a new one"
        echo -e "  2. Restart Claude Code (or Claude Desktop) to connect MCP"
    else
        echo -e "${YELLOW}Next step:${NC} Restart Claude Code (or Claude Desktop) to connect MCP"
    fi
    echo ""
}

main "$@"
exit 0
