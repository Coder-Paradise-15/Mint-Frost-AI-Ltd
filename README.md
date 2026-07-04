# Mint Frost AI Chat - Enhanced Version 7.0

A modern, feature-rich AI chat application built with Flask, featuring advanced UI/UX, real-time model discovery, connection-status based model selection, a gamification system, and comprehensive analytics.

---

## 🚀 New Features & Enhancements (v7.0)

### 🎨 **Dynamic Models Selection & Search (v7.0)**
- **Segregated Connection Categories**: Models are grouped dynamically under two primary headers:
  - **Connected / Registered Models** (Active count, green badge): Providers for which the user has configured an API key in settings.
  - **Other Available Models** (Active count, gray badge): Remaining providers.
- **Searchable Model Filter**: Integrated an interactive search input field at the top of the pill dropdown. Auto-filters models, provider group sub-headers, and main categories instantly as you type.
- **Auto-Focus & Reset**: Opening the pill selector automatically clears any past search query and focuses the input field for instant keyboard navigation.
- **Premium Brand Logos**: High-fidelity inline SVGs designed for all major AI brands:
  1. **ChatGPT**: Line-art flower spiral logo (`#10a37f`) with inner path cutouts.
  2. **Gemini**: Gradient-filled spark logo with orbiting satellite dots.
  3. **Claude**: Signature hand-drawn asterisk/starburst shape (`#d97706`).
  4. **OpenRouter**: Two curved diverging paths with arrowheads (`#a855f7`).
  5. **DeepSeek**: Blue whale badge (`#1c64f2`).
  6. **Groq**: Modern bold circular letter **G** with a center bar (`#f55035`).
- **Flexbox Compression Fix**: SVGs are locked with `min-width`/`min-height` to prevent layout engines from compressing brand logos.

### ⚙️ **Dynamic Model Discovery & Registry (v7.0)**
- **Automated Discovery**: Scan and fetch available models dynamically from OpenAI, Anthropic, Gemini, Groq, OpenRouter, and Mistral based on active API keys.
- **Custom Model Registration**: A dedicated UI form modal in the Admin Dashboard allows administrators to register custom model IDs with custom Display Names, descriptions, context lengths, and capability flags (Reasoning, Vision, etc.).
- **Tired Capability Badge Sorting**: Re-organized model selector option list items dynamically by capability tiers (e.g. `Recommended`, `🧠 Reasoning`, `👁 Vision`, `⚡ Fast`).

### 🎮 **Gamification & Analytics Tab (v6.0 - v7.0)**
- **Gamification Rewards**: Earn XP, levels, and badges by completing daily plans, tasks, subtasks, or recovery cycles.
- **Daily Planner integration**: Automatically scans and awards leveling progress when completing daily routines.
- **Analytics Dashboard**: View level progress bars, streak metrics, XP curves, and badge shelves directly within the Analytics view.

---

## 📋 **New API Endpoints (v7.0)**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/settings/models` | Get all discovered and custom registered models |
| `POST` | `/api/admin/models/custom` | Register a new custom model |
| `POST` | `/api/admin/models/discover` | Refresh and scan discovered models |
| `GET` | `/api/gamification/stats` | Get current user leveling, XP, and badge statistics |
| `POST` | `/api/panic/analyze` | Run AI workload load balancing analysis |

---

## 🛠️ **Ongoing Issues & Workarounds**

### 1. Local Storage Key Syncing
> [!WARNING]
> **Issue**: Stored API keys are saved on a per-browser/device basis in local storage, meaning keys do not automatically sync when opening the app on a new device.
>
> **Workaround**: Open the User Settings modal on the new browser/device and re-enter your API keys once. They will persist locally on that device.

### 2. SQLite Database Lock Mismatches
> [!NOTE]
> **Issue**: In rare high-concurrency production scenarios, SQLite may raise a `database is locked` error.
>
> **Workaround**: The database layer is pre-configured with Write-Ahead Logging (WAL) mode (`PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;`) and a connection timeout of `10.0` seconds to resolve locks automatically.

### 3. OpenRouter Network Timeouts
> [!IMPORTANT]
> **Issue**: Discovered models from OpenRouter may fail to load or timeout if the remote OpenRouter API encounters network delays.
>
> **Workaround**: The app automatically uses local cached discovery registries to populate the selector if network calls timeout, ensuring uninterrupted usage.

---

## 🎯 **Installation & Setup**

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set API Keys**
   - Configure OpenAI, Gemini, Claude, Groq, OpenRouter, or Mistral keys directly inside the **User Settings Modal** in the UI.

3. **Run Application**
   ```bash
   python app.py
   ```