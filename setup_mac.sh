#!/bin/bash
# ============================================================
#  Airbnb Guest Assistant — Mac Setup Script
#  Run this once: bash setup_mac.sh
# ============================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo "🏠 Airbnb Guest Assistant — Mac Setup"
echo "======================================"
echo ""

# ── Step 1: Install Homebrew if missing ──────────────────────
if ! command -v brew &>/dev/null; then
  echo -e "${YELLOW}Installing Homebrew (Mac package manager)...${NC}"
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
  eval "$(/opt/homebrew/bin/brew shellenv)"
else
  echo -e "${GREEN}✅ Homebrew already installed${NC}"
fi

# ── Step 2: Install Python ───────────────────────────────────
if ! command -v python3 &>/dev/null; then
  echo -e "${YELLOW}Installing Python...${NC}"
  brew install python
else
  echo -e "${GREEN}✅ Python already installed: $(python3 --version)${NC}"
fi

# ── Step 3: Install dependencies ─────────────────────────────
echo ""
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip3 install anthropic flask python-dotenv \
  google-auth google-auth-oauthlib google-api-python-client \
  gspread --quiet
echo -e "${GREEN}✅ Dependencies installed${NC}"

# ── Step 4: Create .env if missing ───────────────────────────
if [ ! -f .env ]; then
  cp .env.example .env
  echo ""
  echo -e "${YELLOW}⚙️  Let's configure your assistant...${NC}"
  echo ""

  read -p "   Paste your Anthropic API key (sk-ant-...): " api_key
  sed -i '' "s|your_anthropic_api_key_here|$api_key|g" .env

  read -p "   Paste your Google Sheet URL: " sheet_url
  sed -i '' "s|https://docs.google.com/spreadsheets/d/your_sheet_id_here|$sheet_url|g" .env

  read -p "   Enter Gmail account #1 (e.g. host1@gmail.com): " gmail1
  sed -i '' "s|host1@gmail.com|$gmail1|g" .env

  read -p "   Enter Gmail account #2 (leave blank to skip): " gmail2
  [ -n "$gmail2" ] && sed -i '' "s|host2@gmail.com|$gmail2|g" .env

  read -p "   Alert email for complaints (leave blank = same as Gmail #1): " alert_email
  if [ -n "$alert_email" ]; then
    echo "ALERT_EMAIL=$alert_email" >> .env
  fi

  echo ""
  echo -e "${GREEN}✅ Configuration saved to .env${NC}"
else
  echo -e "${GREEN}✅ .env already exists — skipping configuration${NC}"
fi

# ── Step 5: Check for Gmail OAuth credentials ─────────────────
if [ ! -f gmail_credentials.json ]; then
  echo ""
  echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${YELLOW}  One more thing: Gmail OAuth credentials needed${NC}"
  echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo ""
  echo "  1. Go to: https://console.cloud.google.com"
  echo "  2. Create a project (or select existing)"
  echo "  3. Enable the Gmail API"
  echo "  4. Go to APIs & Services → Credentials"
  echo "  5. Create OAuth 2.0 Client ID → Desktop App"
  echo "  6. Download the JSON file"
  echo "  7. Save it as 'gmail_credentials.json' in this folder"
  echo ""
  read -p "  Press Enter when done..."
fi

# ── Done ──────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✅ Setup complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  To start the agent, run:"
echo ""
echo -e "    ${YELLOW}bash run_agent.sh${NC}"
echo ""
echo "  The agent will:"
echo "  • Check Gmail every 60 seconds"
echo "  • Auto-reply to guest questions"
echo "  • Email you if there's a complaint"
echo ""
