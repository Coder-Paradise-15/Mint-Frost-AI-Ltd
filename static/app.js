// Scope localStorage per logged-in user to prevent sharing API keys/settings
(function () {
  const originalGet = Storage.prototype.getItem;
  const originalSet = Storage.prototype.setItem;
  const originalRemove = Storage.prototype.removeItem;

  const prefixableKeys = [
    "apiProvider",
    "apiOpenAIKey",
    "apiOpenAIModel",
    "apiGeminiKey",
    "apiGeminiModel",
    "apiAnthropicKey",
    "apiAnthropicModel",
    "apiGroqKey",
    "apiGroqModel",
    "apiOpenRouterKey",
    "apiOpenRouterModel",
    "apiMistralKey",
    "apiMistralModel",
    "chatboxModel",
    "chatDraft",
    "theme",
    "autoTheme",
    "mint_custom_playlists",
  ];

  function getPrefixedKey(key) {
    const user = window.currentUser || "";
    if (user && prefixableKeys.includes(key)) {
      return `${user}_${key}`;
    }
    return key;
  }

  Storage.prototype.getItem = function (key) {
    return originalGet.call(this, getPrefixedKey(key));
  };

  Storage.prototype.setItem = function (key, value) {
    return originalSet.call(this, getPrefixedKey(key), value);
  };

  Storage.prototype.removeItem = function (key) {
    return originalRemove.call(this, getPrefixedKey(key));
  };
})();

function getProviderLogoHtml(provider, size = 16) {
  provider = (provider || "").toLowerCase();
  if (provider === "openai") {
    return `<svg class="brand-logo-svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="${size}" height="${size}" fill="#10a37f" style="vertical-align: middle; flex-shrink: 0;">
      <path d="M21.74 11.53c0-.36-.07-.72-.2-1.06-.1-.28-.27-.53-.48-.74l.01-.01c-.13-.15-.29-.27-.47-.36.21-.49.31-1.02.28-1.54-.03-.49-.16-.97-.39-1.4-.24-.46-.6-.84-1.03-1.11-.43-.27-.93-.41-1.43-.41-.33 0-.66.06-.97.17-.18-.17-.4-.3-.64-.38-.34-.58-.84-1.02-1.45-1.27-.6-.24-1.26-.29-1.89-.13a3.85 3.85 0 0 0-1.89 1.1c-.2-.03-.4-.05-.61-.05-1.04 0-2.04.41-2.77 1.15A3.94 3.94 0 0 0 4.7 8.3c-.6.31-1.07.82-1.34 1.44a3.88 3.88 0 0 0 .1 3.52 3.86 3.86 0 0 0 .37.5c-.15.22-.24.47-.28.74-.15.48-.19.98-.12 1.48.06.49.23.96.49 1.38.26.43.62.77 1.05 1 .43.23.91.36 1.4.37.28 0 .56-.04.83-.12.16.14.35.25.56.32.4.52.93.9 1.54 1.1.6.2 1.25.21 1.86.04a3.84 3.84 0 0 0 2-.95c.21.05.42.08.64.08 1.04 0 2.04-.41 2.77-1.15.74-.73 1.15-1.73 1.15-2.77 0-.25-.03-.5-.08-.74.19-.15.35-.34.46-.56.45-.4.77-.92.93-1.5.17-.57.19-1.18.06-1.76zm-8.87 8.1c-.6.28-1.27.32-1.89.12-.6-.2-1.12-.6-1.49-1.13l3.66-2.11c.21-.12.38-.29.5-.5.12-.21.18-.45.18-.69V10.2l2.3 1.33c.09.05.17.13.23.22.06.09.09.2.09.31v4.25c0 .64-.26 1.25-.71 1.7-.45.45-1.06.71-1.7.71a2.38 2.38 0 0 1-1.11-.29zm-7.66-3.8c-.3-.53-.42-1.16-.32-1.77.1-.6.38-1.16.82-1.56l3.66 2.11c.2.12.44.18.68.18s.48-.06.69-.18l4.43-2.56v2.66c0 .1.03.2.08.29a.57.57 0 0 0 .23.23l-3.69 2.13c-.56.32-1.2.45-1.84.36a2.41 2.41 0 0 1-1.58-.91 2.38 2.38 0 0 1-.36-1.84c.1-.64.44-1.22.93-1.63zM4.64 7.68c.28-.6.76-1.07 1.36-1.33.6-.26 1.27-.3 1.89-.1l3.66 2.11c.21.12.38.29.5.5s.18.45.18.69v5.12L9.93 13.4c-.09-.05-.17-.13-.23-.22a.58.58 0 0 1-.09-.31V8.62c0-.64.26-1.25.71-1.7a2.4 2.4 0 0 1 2.81-.42zm7.66 2.5l-3.66-2.11c-.2-.12-.44-.18-.68-.18s-.48.06-.69.18l-4.43 2.56v-2.66c0-.1-.03-.2-.08-.29a.57.57 0 0 0-.23-.23l3.69-2.13a2.39 2.39 0 0 1 3.42.55 2.41 2.41 0 0 1 .36 1.84c-.1.64-.44 1.22-.93 1.63zm3.76-2.5c.3.53.42 1.16.32 1.77-.1.6-.38 1.16-.82 1.56l-3.66-2.11a1.36 1.36 0 0 0-1.37 0l-4.43 2.56V8.8c0-.1-.03-.2-.08-.29a.57.57 0 0 0-.23-.23l3.69-2.13c.56-.32 1.2-.45 1.84-.36a2.41 2.41 0 0 1 1.58.91 2.38 2.38 0 0 1 .36 1.84c-.1.64-.44 1.22-.93 1.63zm2.3 8.1c-.28.6-.76 1.07-1.36 1.33a2.43 2.43 0 0 1-1.89.1l-3.66-2.11c-.21-.12-.38-.29-.5-.5a1.36 1.36 0 0 1-.18-.69V9.82l2.3 1.33c.09.05.17.13.23.22.06.09.09.2.09.31v4.25c0 .64-.26 1.25-.71 1.7a2.4 2.4 0 0 1-2.81.42z"/>
    </svg>`;
  }
  if (provider === "gemini") {
    return `<svg class="brand-logo-svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="${size}" height="${size}" style="vertical-align: middle; flex-shrink: 0;">
      <path fill="#4285F4" d="M12 2C12 2 12 7.5 6.5 7.5C12 7.5 12 13 12 13C12 13 12 7.5 17.5 7.5C12 7.5 12 2 12 2Z"/>
      <path fill="#ea4335" d="M19 13C19 13 19 15.5 16.5 15.5C19 15.5 19 18 19 18C19 18 19 15.5 21.5 15.5C19 15.5 19 13 19 13Z"/>
    </svg>`;
  }
  if (provider === "anthropic") {
    return `<svg class="brand-logo-svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="${size}" height="${size}" fill="#cc5843" style="vertical-align: middle; flex-shrink: 0;">
      <path d="M12 2c-.8 0-1.5.7-1.5 1.5v6.3l-4.5-4.5c-.6-.6-1.5-.6-2.1 0s-.6 1.5 0 2.1l4.5 4.5H2c-.8 0-1.5.7-1.5 1.5S1.2 15 2 15h6.4l-4.5 4.5c-.6.6-.6 1.5 0 2.1.3.3.7.4 1.1.4.4 0 .8-.1 1.1-.4l4.5-4.5v6.4c0 .8.7 1.5 1.5 1.5s1.5-.7 1.5-1.5v-6.4l4.5 4.5c.3.3.7.4 1.1.4.4 0 .8-.1 1.1-.4.6-.6.6-1.5 0-2.1l-4.5-4.5H22c.8 0 1.5-.7 1.5-1.5S22.8 12 22 12h-6.4l4.5-4.5c.6-.6.6-1.5 0-2.1s-1.5-.6-2.1 0l-4.5 4.5V3.5C13.5 2.7 12.8 2 12 2z"/>
    </svg>`;
  }
  if (provider === "groq") {
    return `<svg class="brand-logo-svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="${size}" height="${size}" fill="#eb5757" style="vertical-align: middle; flex-shrink: 0;">
      <path d="M19.5 2.5L3.5 12.5H11.5L9.5 21.5L20.5 10.5H12.5L19.5 2.5Z"/>
    </svg>`;
  }
  if (provider === "openrouter") {
    return `<svg class="brand-logo-svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="${size}" height="${size}" fill="#7c3aed" style="vertical-align: middle; flex-shrink: 0;">
      <path d="M12 2L2 7v10l10 5 10-5V7L12 2zm0 2.8l7.6 3.8v6.8L12 19.2l-7.6-3.8V8.6L12 4.8zm0 2.8c-2.4 0-4.4 2-4.4 4.4s2 4.4 4.4 4.4 4.4-2 4.4-4.4-2-4.4-4.4-4.4z"/>
    </svg>`;
  }
  if (provider === "mistral") {
    return `<svg class="brand-logo-svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="${size}" height="${size}" fill="#ff7000" style="vertical-align: middle; flex-shrink: 0;">
      <path d="M2 4h4v12h4V8l4 6 4-6v8h4V4h-4l-4 6-4-6H2z"/>
    </svg>`;
  }
  return "";
}

// DOM Elements
const messagesEl = document.getElementById("messages");
const inputEl = document.getElementById("message-input");
const sendBtn = document.getElementById("send-btn");
const statusText = document.getElementById("status-text");
const statusDot = document.getElementById("status-dot");
const typingIndicator = document.getElementById("typing-indicator");
const charCount = document.getElementById("char-count");
const messageCount = document.getElementById("message-count");
const themeToggle = document.getElementById("theme-toggle");
const themeIcon = document.getElementById("theme-icon");
const searchBtn = document.getElementById("search-btn");
const searchPanel = document.getElementById("search-panel");
const searchInput = document.getElementById("search-input");
const searchClose = document.getElementById("search-close");
const clearBtn = document.getElementById("clear-btn");
const exportBtn = document.getElementById("export-btn");
const voiceBtn = document.getElementById("voice-btn");
const shortcuts = document.getElementById("shortcuts");
const timeDisplay = document.getElementById("time-display");
const weatherDisplay = document.getElementById("weather-display");
const weatherTemp = document.getElementById("weather-temp");
const weatherIcon = weatherDisplay.querySelector("i");
const panel = document.querySelector(".panel");
const historyToggle = document.getElementById("history-toggle");
const historyPanel = document.getElementById("history-panel");
const recentChats = document.getElementById("recent-chats");
const newChatBtn = document.getElementById("new-chat-btn");
const hoverPanel = document.getElementById("hover-panel");
const emojiBtn = document.getElementById("emoji-btn");
const emojiPicker = document.getElementById("emoji-picker");
const emojiGrid = document.getElementById("emoji-grid");
const emojiCategories = document.querySelectorAll(".emoji-category");

// State
let inFlight = false;
let messageHistory = [];
let currentTheme = localStorage.getItem("theme") || "dark";
let autoTheme = localStorage.getItem("autoTheme") === "true";
let recognition = null;
let isListening = false;

let currentSessionId = window.currentSessionId || null;
let historyVisible = true;
let hoverPanelTarget = null;
let hoverTimeout = null;
let emojiPickerVisible = false;
let themeSelectorVisible = false;
let themeCreatorVisible = false;
let customThemes = {};

// Emoji data
const emojiData = {
  smileys: [
    "😀",
    "😃",
    "😄",
    "😁",
    "😆",
    "😅",
    "🤣",
    "😂",
    "🙂",
    "🙃",
    "😉",
    "😊",
    "😇",
    "🥰",
    "😍",
    "🤩",
    "😘",
    "😗",
    "😚",
    "😙",
    "😋",
    "😛",
    "😜",
    "🤪",
    "😝",
    "🤑",
    "🤗",
    "🤭",
    "🤫",
    "🤔",
    "🤐",
    "🤨",
    "😐",
    "😑",
    "😶",
    "😏",
    "😒",
    "🙄",
    "😬",
    "🤥",
  ],
  people: [
    "👶",
    "🧒",
    "👦",
    "👧",
    "🧑",
    "👱",
    "👨",
    "🧔",
    "👩",
    "🧓",
    "👴",
    "👵",
    "🙍",
    "🙎",
    "🙅",
    "🙆",
    "💁",
    "🙋",
    "🧏",
    "🙇",
    "🤦",
    "🤷",
    "👮",
    "🕵️",
    "💂",
    "👷",
    "🤴",
    "👸",
    "👳",
    "👲",
    "🧕",
    "🤵",
    "👰",
    "🤰",
    "🤱",
    "👼",
    "🎅",
    "🤶",
    "🦸",
    "🦹",
  ],
  nature: [
    "🐶",
    "🐱",
    "🐭",
    "🐹",
    "🐰",
    "🦊",
    "🐻",
    "🐼",
    "🐨",
    "🐯",
    "🦁",
    "🐮",
    "🐷",
    "🐽",
    "🐸",
    "🐵",
    "🙈",
    "🙉",
    "🙊",
    "🐒",
    "🐔",
    "🐧",
    "🐦",
    "🐤",
    "🐣",
    "🐥",
    "🦆",
    "🦅",
    "🦉",
    "🦇",
    "🐺",
    "🐗",
    "🐴",
    "🦄",
    "🐝",
    "🐛",
    "🦋",
    "🐌",
    "🐞",
    "🐜",
  ],
  food: [
    "🍎",
    "🍐",
    "🍊",
    "🍋",
    "🍌",
    "🍉",
    "🍇",
    "🍓",
    "🍈",
    "🍒",
    "🍑",
    "🥭",
    "🍍",
    "🥥",
    "🥝",
    "🍅",
    "🍆",
    "🥑",
    "🥦",
    "🥬",
    "🥒",
    "🌶️",
    "🌽",
    "🥕",
    "🧄",
    "🧅",
    "🥔",
    "🍠",
    "🥐",
    "🍞",
    "🥖",
    "🥨",
    "🧀",
    "🥚",
    "🍳",
    "🧈",
    "🥞",
    "🧇",
    "🥓",
    "🥩",
  ],
  activities: [
    "⚽",
    "🏀",
    "🏈",
    "⚾",
    "🥎",
    "🎾",
    "🏐",
    "🏉",
    "🥏",
    "🎱",
    "🪀",
    "🏓",
    "🏸",
    "🏒",
    "🏑",
    "🥍",
    "🏏",
    "🪃",
    "🥅",
    "⛳",
    "🪁",
    "🏹",
    "🎣",
    "🤿",
    "🥊",
    "🥋",
    "🎽",
    "🛹",
    "🛷",
    "⛸️",
    "🥌",
    "🎿",
    "⛷️",
    "🏂",
    "🪂",
    "🏋️",
    "🤼",
    "🤸",
    "⛹️",
    "🤺",
  ],
  travel: [
    "🚗",
    "🚕",
    "🚙",
    "🚌",
    "🚎",
    "🏎️",
    "🚓",
    "🚑",
    "🚒",
    "🚐",
    "🛻",
    "🚚",
    "🚛",
    "🚜",
    "🏍️",
    "🛵",
    "🚲",
    "🛴",
    "🛹",
    "🛼",
    "🚁",
    "🛸",
    "✈️",
    "🛩️",
    "🛫",
    "🛬",
    "🪂",
    "💺",
    "🚀",
    "🛰️",
    "🚢",
    "⛵",
    "🚤",
    "🛥️",
    "🛳️",
    "⛴️",
    "🚂",
    "🚃",
    "🚄",
    "🚅",
  ],
  objects: [
    "⌚",
    "📱",
    "📲",
    "💻",
    "⌨️",
    "🖥️",
    "🖨️",
    "🖱️",
    "🖲️",
    "🕹️",
    "🗜️",
    "💽",
    "💾",
    "💿",
    "📀",
    "📼",
    "📷",
    "📸",
    "📹",
    "🎥",
    "📽️",
    "🎞️",
    "📞",
    "☎️",
    "📟",
    "📠",
    "📺",
    "📻",
    "🎙️",
    "🎚️",
    "🎛️",
    "🧭",
    "⏱️",
    "⏲️",
    "⏰",
    "🕰️",
    "⌛",
    "⏳",
    "📡",
    "🔋",
  ],
  symbols: [
    "❤️",
    "🧡",
    "💛",
    "💚",
    "💙",
    "💜",
    "🖤",
    "🤍",
    "🤎",
    "💔",
    "❣️",
    "💕",
    "💞",
    "💓",
    "💗",
    "💖",
    "💘",
    "💝",
    "💟",
    "☮️",
    "✝️",
    "☪️",
    "🕉️",
    "☸️",
    "✡️",
    "🔯",
    "🕎",
    "☯️",
    "☦️",
    "🛐",
    "⛎",
    "♈",
    "♉",
    "♊",
    "♋",
    "♌",
    "♍",
    "♎",
    "♏",
  ],
};

// Modal elements
const modalOverlay = document.getElementById("modal-overlay");
const modal = document.getElementById("modal");
const modalTitle = document.getElementById("modal-title");
const modalBody = document.getElementById("modal-body");
const modalFooter = document.getElementById("modal-footer");
const modalClose = document.getElementById("modal-close");

// Theme selector elements
const themeSelector = document.getElementById("theme-selector");
const themeClose = document.getElementById("theme-close");
const themeOptions = document.querySelectorAll(".theme-option");
const autoThemeCheckbox = document.getElementById("auto-theme");
const createThemeBtn = document.getElementById("create-theme-btn");
const customThemesList = document.getElementById("custom-themes-list");
const customThemesContainer = document.getElementById(
  "custom-themes-container",
);

// Simple theme creator elements
const themeCreatorOverlay = document.getElementById("theme-creator-overlay");
const themeCreator = document.getElementById("theme-creator");
const creatorClose = document.getElementById("creator-close");
const creatorCancel = document.getElementById("creator-cancel");
const creatorSave = document.getElementById("creator-save");
const themeNameInput = document.getElementById("theme-name");
const themePreview = document.getElementById("theme-preview");

// Simple color pickers
const colorPrimary = document.getElementById("color-primary");
const colorBg0 = document.getElementById("color-bg0");
const colorBg1 = document.getElementById("color-bg1");
const colorFg = document.getElementById("color-fg");

// API Settings Elements
const apiSettingsBtn = document.getElementById("api-settings-btn");
const apiSettingsOverlay = document.getElementById("api-settings-overlay");
const apiSettingsClose = document.getElementById("api-settings-close");
const apiSettingsCancel = document.getElementById("api-settings-cancel");
const apiSettingsSave = document.getElementById("api-settings-save");
const apiSettingsReset = document.getElementById("api-settings-reset");
const apiProviderSelect = document.getElementById("api-provider");
const apiOpenAIKeyInput = document.getElementById("api-openai-key");
const apiOpenAIModelSelect = document.getElementById("api-openai-model");
const apiGeminiKeyInput = document.getElementById("api-gemini-key");
const apiGeminiModelSelect = document.getElementById("api-gemini-model");
const openaiKeyCard = document.getElementById("openai-key-card");
const geminiKeyCard = document.getElementById("gemini-key-card");

// Initialize theme
async function initTheme() {
  // 1. Immediately apply localStorage theme first (instant UI, no blank flash or loading block!)
  try {
    currentTheme = localStorage.getItem("theme") || "dark";
    autoTheme = localStorage.getItem("autoTheme") === "true";
    if (autoTheme) {
      detectSystemTheme();
    } else if (currentTheme.startsWith("custom_")) {
      applyCustomTheme(currentTheme);
    } else {
      applyTheme(currentTheme);
    }
    updateThemeIcon();
    updateThemeSelector();
  } catch (e) {
    console.error("Initial theme apply error:", e);
  }

  // 2. Concurrently load and sync with the backend database in the background
  loadThemeFromBackend()
    .then((backendLoaded) => {
      if (backendLoaded) {
        if (autoTheme) {
          detectSystemTheme();
        } else if (currentTheme.startsWith("custom_")) {
          applyCustomTheme(currentTheme);
        } else {
          applyTheme(currentTheme);
        }
        updateThemeIcon();
        updateThemeSelector();
        console.log("Theme synchronized with database:", currentTheme);
      }
    })
    .catch((error) => {
      console.error("Non-blocking theme sync failed:", error);
    });
}

// Load theme from backend
async function loadThemeFromBackend() {
  try {
    const response = await fetch("/api/theme");
    const data = await response.json();

    if (data.theme) {
      currentTheme = data.theme;
      // Update localStorage to match backend
      localStorage.setItem("theme", currentTheme);
    }

    if (data.auto_theme !== undefined) {
      autoTheme = data.auto_theme;
      localStorage.setItem("autoTheme", autoTheme.toString());
    }

    if (data.custom_themes) {
      customThemes = data.custom_themes;
    }

    return true;
  } catch (error) {
    console.log("Backend theme load failed, using localStorage fallback");
    // Fallback to localStorage if backend fails
    currentTheme = localStorage.getItem("theme") || "dark";
    autoTheme = localStorage.getItem("autoTheme") === "true";
    return false;
  }
}

// Apply theme
function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  currentTheme = theme;
}

// Update theme icon
function updateThemeIcon() {
  const iconMap = {
    dark: "fas fa-moon",
    light: "fas fa-sun",
    mint: "fas fa-leaf",
    ocean: "fas fa-water",
    sunset: "fas fa-sun",
    forest: "fas fa-tree",
  };
  themeIcon.className = iconMap[currentTheme] || "fas fa-palette";
}

// Detect system theme
function detectSystemTheme() {
  if (
    window.matchMedia &&
    window.matchMedia("(prefers-color-scheme: dark)").matches
  ) {
    applyTheme("dark");
  } else {
    applyTheme("light");
  }
}

// Toggle theme (now opens selector)
function toggleTheme() {
  showThemeSelector();
}

// Show theme selector
function showThemeSelector() {
  themeSelectorVisible = true;
  themeSelector.classList.add("show");
  updateThemeSelector();
}

// Hide theme selector
function hideThemeSelector() {
  themeSelectorVisible = false;
  themeSelector.classList.remove("show");
}

// Update theme selector UI
function updateThemeSelector() {
  themeOptions.forEach((option) => {
    option.classList.toggle("active", option.dataset.theme === currentTheme);
  });
  autoThemeCheckbox.checked = autoTheme;
  updateCustomThemesList();
}

// Load custom themes
async function loadCustomThemes() {
  try {
    const response = await fetch("/api/theme");
    const data = await response.json();
    customThemes = data.custom_themes || {};
    updateCustomThemesList();
  } catch (error) {
    console.error("Failed to load custom themes:", error);
  }
}

// Update custom themes list
function updateCustomThemesList() {
  const hasCustomThemes = Object.keys(customThemes).length > 0;
  customThemesList.style.display = hasCustomThemes ? "block" : "none";

  customThemesContainer.innerHTML = "";

  Object.entries(customThemes).forEach(([themeId, theme]) => {
    const item = document.createElement("div");
    item.className = "custom-theme-item";

    const span = document.createElement("span");
    span.style.color = "var(--fg)";
    span.style.cursor = "pointer";
    span.textContent = `🎨 ${sanitizeHTML(theme.name)}`;
    span.onclick = () => setTheme(sanitizeHTML(themeId));

    const button = document.createElement("button");
    button.className = "custom-theme-delete";
    button.title = "Delete theme";
    button.innerHTML = '<i class="fas fa-trash"></i>';
    button.onclick = () => deleteCustomTheme(sanitizeHTML(themeId));

    item.appendChild(span);
    item.appendChild(button);
    customThemesContainer.appendChild(item);
  });
}

// Simple theme creator functions
function showThemeCreator() {
  if (!themeCreatorOverlay) {
    showToast("Theme creator not available", "error");
    return;
  }
  themeCreatorVisible = true;
  themeCreatorOverlay.classList.add("show");
  hideThemeSelector();
  resetThemeCreator();
}

function hideThemeCreator() {
  themeCreatorVisible = false;
  if (themeCreatorOverlay) {
    themeCreatorOverlay.classList.remove("show");
  }
}

function resetThemeCreator() {
  if (themeNameInput) themeNameInput.value = "";
  if (colorPrimary) colorPrimary.value = "#37e6b5";
  if (colorBg0) colorBg0.value = "#0b0f14";
  if (colorBg1) colorBg1.value = "#0f1620";
  if (colorFg) colorFg.value = "#e9fbf5";
  updatePreview();
}

function updatePreview() {
  if (!themePreview) return;
  const primary = colorPrimary?.value || "#37e6b5";
  const bg = colorBg1?.value || "#0f1620";
  const fg = colorFg?.value || "#e9fbf5";

  themePreview.style.setProperty("--preview-primary", primary);
  themePreview.style.setProperty("--preview-bg", bg);
  themePreview.style.setProperty("--preview-fg", fg);
}

// Hex to RGB converter
function hexToRgb(hex) {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result
    ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16),
      }
    : { r: 55, g: 230, b: 181 };
}

// Apply custom theme
function applyCustomTheme(themeId) {
  const theme = customThemes[themeId];
  if (!theme) return;

  const colors = theme.colors;
  const primaryRgb = hexToRgb(colors.primary);

  // Calculate derived colors
  const primaryDark = adjustBrightness(colors.primary, -20);
  const primaryDarker = adjustBrightness(colors.primary, -40);
  const glass = `rgba(${primaryRgb.r}, ${primaryRgb.g}, ${primaryRgb.b}, 0.08)`;
  const border = `rgba(${primaryRgb.r}, ${primaryRgb.g}, ${primaryRgb.b}, 0.16)`;
  const shadow = `0 10px 30px rgba(${primaryRgb.r}, ${primaryRgb.g}, ${primaryRgb.b}, 0.2)`;

  // Apply to document
  const root = document.documentElement;
  root.style.setProperty("--custom-primary", colors.primary);
  root.style.setProperty("--custom-primary-dark", primaryDark);
  root.style.setProperty("--custom-primary-darker", primaryDarker);
  root.style.setProperty("--custom-bg0", colors.bg0);
  root.style.setProperty("--custom-bg1", colors.bg1);
  root.style.setProperty("--custom-fg", colors.fg);
  root.style.setProperty("--custom-muted", colors.muted);
  root.style.setProperty("--custom-glass", glass);
  root.style.setProperty("--custom-border", border);
  root.style.setProperty("--custom-shadow", shadow);

  root.setAttribute("data-theme", themeId);
}

// Adjust brightness helper
function adjustBrightness(hex, percent) {
  const rgb = hexToRgb(hex);
  const factor = 1 + percent / 100;

  const r = Math.min(255, Math.max(0, Math.round(rgb.r * factor)));
  const g = Math.min(255, Math.max(0, Math.round(rgb.g * factor)));
  const b = Math.min(255, Math.max(0, Math.round(rgb.b * factor)));

  return `#${r.toString(16).padStart(2, "0")}${g.toString(16).padStart(2, "0")}${b.toString(16).padStart(2, "0")}`;
}

async function saveCustomTheme() {
  const name = themeNameInput?.value?.trim();
  if (!name) {
    showToast("Please enter a theme name", "error");
    return;
  }

  const colors = {
    primary: colorPrimary?.value || "#37e6b5",
    bg0: colorBg0?.value || "#0b0f14",
    bg1: colorBg1?.value || "#0f1620",
    fg: colorFg?.value || "#e9fbf5",
    muted: "#a6b7b2",
  };

  try {
    const response = await fetch("/api/custom-theme", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, colors }),
    });

    const data = await response.json();

    if (response.ok) {
      await loadCustomThemes();
      hideThemeCreator();
      showToast(`Theme "${name}" created!`);
      setTimeout(() => setTheme(data.theme_id), 300);
    } else {
      showToast(data.error || "Failed to save theme", "error");
    }
  } catch (error) {
    showToast("Failed to save theme", "error");
  }
}

// Delete custom theme
async function deleteCustomTheme(themeId) {
  try {
    const response = await fetch("/api/custom-theme", {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ theme_id: themeId }),
    });

    if (response.ok) {
      delete customThemes[themeId];
      updateCustomThemesList();

      // Switch to default theme if current theme was deleted
      if (currentTheme === themeId) {
        setTheme("dark");
      }

      showToast("Theme deleted successfully");
    } else {
      showToast("Failed to delete theme", "error");
    }
  } catch (error) {
    console.error("Delete theme error:", error);
    showToast("Failed to delete theme", "error");
  }
}

// Set theme
async function setTheme(theme) {
  try {
    // Update backend first
    const response = await fetch("/api/theme", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ theme, auto_theme: false }),
    });

    if (response.ok) {
      currentTheme = theme;
      autoTheme = false;

      // Update localStorage to match backend
      localStorage.setItem("theme", theme);
      localStorage.setItem("autoTheme", "false");

      // Apply theme
      if (theme.startsWith("custom_")) {
        applyCustomTheme(theme);
      } else {
        applyTheme(theme);
      }

      updateThemeIcon();
      updateThemeSelector();

      const themeName = theme.startsWith("custom_")
        ? customThemes[theme]?.name || "Custom"
        : theme;
      showToast(`Theme changed to ${themeName}`);
    } else {
      throw new Error("Backend theme update failed");
    }
  } catch (error) {
    console.error("Theme change error:", error);
    showToast("Failed to change theme", "error");
  }
}

// Toggle auto theme
async function toggleAutoTheme() {
  autoTheme = !autoTheme;

  try {
    // Update backend
    const response = await fetch("/api/theme", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ theme: currentTheme, auto_theme: autoTheme }),
    });

    if (response.ok) {
      // Update localStorage to match backend
      localStorage.setItem("autoTheme", autoTheme.toString());

      if (autoTheme) {
        detectSystemTheme();
        showToast("Auto theme enabled");

        // Listen for system theme changes
        if (window.matchMedia) {
          window
            .matchMedia("(prefers-color-scheme: dark)")
            .addEventListener("change", detectSystemTheme);
        }
      } else {
        showToast("Auto theme disabled");
        if (window.matchMedia) {
          window
            .matchMedia("(prefers-color-scheme: dark)")
            .removeEventListener("change", detectSystemTheme);
        }
      }

      updateThemeIcon();
      updateThemeSelector();
    } else {
      // Revert on failure
      autoTheme = !autoTheme;
      showToast("Failed to update auto theme setting", "error");
    }
  } catch (error) {
    // Revert on error
    autoTheme = !autoTheme;
    console.error("Auto theme toggle error:", error);
    showToast("Failed to update auto theme setting", "error");
  }
}

// Format timestamp
function formatTime(timestamp) {
  try {
    if (timestamp && typeof timestamp === "string") {
      // Safely transform SQLite 'YYYY-MM-DD HH:MM:SS' format to standard ISO-8601 'YYYY-MM-DDTHH:MM:SSZ'
      let cleanTimestamp = timestamp.trim().replace(" ", "T");
      if (
        !cleanTimestamp.includes("Z") &&
        !cleanTimestamp.includes("+") &&
        !cleanTimestamp.includes("-")
      ) {
        cleanTimestamp += "Z"; // SQLite CURRENT_TIMESTAMP is UTC
      }
      const date = new Date(cleanTimestamp);
      if (!isNaN(date.getTime())) {
        return date.toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        });
      }
    }
    const date = timestamp ? new Date(timestamp) : new Date();
    if (!isNaN(date.getTime())) {
      return date.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      });
    }
    return "";
  } catch (e) {
    console.error("Error formatting time:", e);
    return "";
  }
}

// Create a message bubble element (without side-effects or direct DOM appending)
function createMessageElement(
  text,
  who = "ai",
  timestamp = null,
  messageId = null,
) {
  const div = document.createElement("div");
  div.className = who === "user" ? "bubble bubble--user" : "bubble bubble--ai";
  div.setAttribute("data-message-id", messageId || Date.now());

  const content = document.createElement("div");
  content.className = "bubble__content";

  const p = document.createElement("p");
  // If text already contains HTML formatting from backend, use it directly
  if (text.includes("<") && text.includes(">")) {
    p.innerHTML = text;
  } else {
    p.innerHTML = formatMessage(text);
  }
  content.appendChild(p);

  // Store raw text for copying
  div.setAttribute("data-raw-text", text);

  // Ellipsis menu trigger button
  const menuBtn = document.createElement("button");
  menuBtn.className = "bubble__menu-btn";
  menuBtn.title = "Message Actions";
  menuBtn.innerHTML = '<i class="fas fa-bars"></i>';

  // Custom dropdown panel
  const actionsDropdown = document.createElement("div");
  actionsDropdown.className = "bubble__actions-dropdown";

  menuBtn.onclick = (e) => {
    e.stopPropagation();
    document
      .querySelectorAll(".bubble__actions-dropdown")
      .forEach((dropdown) => {
        if (dropdown !== actionsDropdown) dropdown.classList.remove("show");
      });
    actionsDropdown.classList.toggle("show");
  };

  const copyBtn = document.createElement("button");
  copyBtn.className = "bubble__action";
  copyBtn.innerHTML = '<i class="fas fa-copy"></i><span>Copy</span>';
  copyBtn.onclick = (e) => {
    e.stopPropagation();
    copyMessage(text);
    actionsDropdown.classList.remove("show");
  };
  actionsDropdown.appendChild(copyBtn);

  if (who === "ai") {
    const likeBtn = document.createElement("button");
    likeBtn.className = "bubble__action";
    likeBtn.innerHTML = '<i class="far fa-thumbs-up"></i><span>Like</span>';
    likeBtn.onclick = (e) => {
      e.stopPropagation();
      toggleReaction(likeBtn, "like");
      actionsDropdown.classList.remove("show");
    };

    const regenerateBtn = document.createElement("button");
    regenerateBtn.className = "bubble__action";
    regenerateBtn.innerHTML = '<i class="fas fa-redo"></i><span>Retry</span>';
    regenerateBtn.onclick = (e) => {
      e.stopPropagation();
      regenerateResponse(div);
      actionsDropdown.classList.remove("show");
    };

    actionsDropdown.appendChild(likeBtn);
    actionsDropdown.appendChild(regenerateBtn);
  } else {
    const editBtn = document.createElement("button");
    editBtn.className = "bubble__action";
    editBtn.innerHTML = '<i class="fas fa-edit"></i><span>Edit</span>';
    editBtn.onclick = (e) => {
      e.stopPropagation();
      editMessage(div);
      actionsDropdown.classList.remove("show");
    };
    actionsDropdown.appendChild(editBtn);
  }

  div.appendChild(menuBtn);
  div.appendChild(actionsDropdown);

  const t = document.createElement("time");
  const timeStr = formatTime(timestamp);
  t.textContent = who === "user" ? `you • ${timeStr}` : `ai • ${timeStr}`;

  div.appendChild(content);
  div.appendChild(t);

  return div;
}

// Push message to chat panel
function pushMessage(text, who = "ai", timestamp = null, messageId = null) {
  const div = createMessageElement(text, who, timestamp, messageId);
  messagesEl.appendChild(div);

  // Store in history
  messageHistory.push({
    text,
    who,
    timestamp: timestamp || new Date().toISOString(),
    id: div.getAttribute("data-message-id"),
  });

  smoothScrollToBottom();
  return div;
}

// Sanitize HTML to prevent XSS
function sanitizeHTML(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function formatMessage(text) {
  if (typeof text !== "string") {
    text = String(text || "");
  }

  // 1. Handle image HTML from backend image generation
  let safeImages = [];
  let textWithoutImages = text;
  if (text.includes('<img src="data:image/')) {
    const imgRegex = /<img src="data:image\/[^"]*"[^>]*>/g;
    safeImages = text.match(imgRegex) || [];
    textWithoutImages = text.replace(imgRegex, "__IMAGE_PLACEHOLDER__");
  }

  // 2. Sanitize user input to prevent XSS (standard tags)
  let sanitizedText = sanitizeHTML(textWithoutImages);

  // 3. Render Markdown using marked.js with GFM enabled
  let formatted = "";
  if (typeof marked !== "undefined" && typeof marked.parse === "function") {
    marked.setOptions({
      gfm: true,
      breaks: true,
      headerIds: false,
      mangle: false
    });
    formatted = marked.parse(sanitizedText);
  } else {
    // Fallback if marked library is not available
    formatted = sanitizedText.replace(/\n/g, "<br>");
  }

  // 4. Re-insert safe image tags
  safeImages.forEach((img) => {
    formatted = formatted.replace("__IMAGE_PLACEHOLDER__", img);
  });

  return formatted;
}

// Smooth scroll to bottom
function smoothScrollToBottom() {
  messagesEl.scrollTo({
    top: messagesEl.scrollHeight,
    behavior: "smooth",
  });
}

// Copy message to clipboard
async function copyMessage(text) {
  try {
    // Clean the text by removing HTML tags using DOM parser for safety
    const tempDiv = document.createElement("div");
    tempDiv.innerHTML = text;
    const cleanText = tempDiv.textContent || tempDiv.innerText || "";

    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(cleanText);
      showToast("Message copied to clipboard!");
    } else {
      // Fallback for older browsers (deprecated API)
      console.warn(
        "Using deprecated document.execCommand for clipboard access",
      );
      const textArea = document.createElement("textarea");
      textArea.value = cleanText;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand("copy");
      document.body.removeChild(textArea);
      showToast("Message copied to clipboard!");
    }
  } catch (err) {
    console.error("Failed to copy:", err);
    showToast("Failed to copy message", "error");
  }
}

// Toggle reaction
function toggleReaction(btn, type) {
  const icon = btn.querySelector("i");
  const span = btn.querySelector("span");
  const isActive = btn.classList.contains("active");

  if (isActive) {
    icon.className = `far fa-thumbs-${type === "like" ? "up" : "down"}`;
    btn.classList.remove("active");
    span.textContent = type === "like" ? "Like" : "Dislike";
    showToast("Reaction removed");
  } else {
    icon.className = `fas fa-thumbs-${type === "like" ? "up" : "down"}`;
    btn.classList.add("active");
    span.textContent = type === "like" ? "Liked" : "Disliked";
    showToast(`Message ${type === "like" ? "liked" : "disliked"}!`);
  }
}

// Show toast notification
function showToast(message, type = "success") {
  const toast = document.createElement("div");
  toast.className = `toast toast--${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);

  setTimeout(() => {
    toast.classList.add("toast--show");
  }, 100);

  setTimeout(() => {
    toast.classList.remove("toast--show");
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// Set status indicator
function setStatus(state, message = null) {
  const states = {
    sending: { text: "Thinking…", color: "var(--mint)", pulse: true },
    error: { text: "Error", color: "crimson", pulse: false },
    idle: { text: "Idle", color: "rgba(255,255,255,0.55)", pulse: false },
    ratelimit: { text: "Rate Limited", color: "orange", pulse: false },
  };

  const config = states[state] || states.idle;
  statusText.textContent = message || config.text;
  statusDot.style.background = config.color;
  statusDot.style.animation = config.pulse ? "pulse 1.5s infinite" : "none";
}

// Show/hide typing indicator
function showTyping(show = true) {
  typingIndicator.style.display = show ? "block" : "none";
  if (show) smoothScrollToBottom();
}

// Update character count
function updateCharCount() {
  const length = inputEl.value.length;
  charCount.textContent = `${length}/2000`;
  charCount.style.color = length > 1800 ? "var(--error)" : "var(--muted)";

  // Enable/disable send button
  sendBtn.disabled = length === 0 || length > 2000 || inFlight;
}

// Update message count
function updateMessageCount(count) {
  messageCount.textContent = `Messages: ${count || messageHistory.length}`;
}

// Get CSRF token (if implemented on backend)
function getCSRFToken() {
  const token = document.querySelector('meta[name="csrf-token"]');
  return token ? token.getAttribute("content") : null;
}

// Validate URL to prevent SSRF
function isValidURL(url) {
  try {
    const urlObj = new URL(url, window.location.origin);
    // Only allow same origin requests
    return urlObj.origin === window.location.origin;
  } catch {
    return false;
  }
}

// Send message to backend
async function sendMessage() {
  const userMessage = inputEl.value.trim();
  if (!userMessage || inFlight || userMessage.length > 2000) return;

  // Intercept emergency keywords to automatically launch Panic Mode
  const panicKeywords = [
    "panic",
    "help",
    "overwhelmed",
    "don't have enough time",
    "miss my deadline",
    "emergency schedule",
  ];
  const isPanicQuery = panicKeywords.some((kw) =>
    userMessage.toLowerCase().includes(kw),
  );
  if (isPanicQuery && typeof window.openPanicMode === "function") {
    window.openPanicMode();
  }

  inFlight = true;
  setStatus("sending");
  showTyping(true);
  pushMessage(userMessage, "user");

  // Reset input immediately
  inputEl.value = "";
  inputEl.focus();
  localStorage.removeItem("chatDraft"); // Clear draft
  updateCharCount();

  try {
    console.log("Sending message length:", userMessage.length);

    // Prepare headers with location if available
    const headers = { "Content-Type": "application/json" };

    // Add CSRF token if available
    const csrfToken = getCSRFToken();
    if (csrfToken) {
      headers["X-CSRF-Token"] = csrfToken;
    }

    // Validate and add location headers
    if (
      window.userLocation &&
      typeof window.userLocation.lat === "number" &&
      typeof window.userLocation.lon === "number"
    ) {
      headers["X-User-Latitude"] = window.userLocation.lat.toString();
      headers["X-User-Longitude"] = window.userLocation.lon.toString();
    }

    const requestBody = { message: sanitizeHTML(userMessage) };
    const byok = getBYOKConfig();
    if (byok) {
      requestBody.provider = byok.provider;
      requestBody.api_key = byok.api_key;
      requestBody.model = byok.model;
    }

    const res = await window.fetchWithRetry("/chat", {
      method: "POST",
      headers: headers,
      body: JSON.stringify(requestBody),
    });

    if (!res.ok) {
      if (res.status === 429) {
        setStatus("ratelimit", "Rate limited - please wait");
        showToast(
          "Too many messages. Please wait before sending another.",
          "warning",
        );
        return;
      }
      if (res.status === 504 || res.status === 524) {
        throw new Error("Gateway timeout - the AI took too long to respond. Please try again.");
      }
      if (res.status === 503 || res.status === 521) {
        throw new Error("Server temporarily unavailable. Please try again in a moment.");
      }
      const errorText = await res.text().catch(() => "");
      let errorMsg = `Server error ${res.status}`;
      try {
        const errorData = JSON.parse(errorText);
        errorMsg = errorData.error || errorMsg;
      } catch (e) {}
      throw new Error(errorMsg);
    }

    const data = await res.json();

    const aiText = data.reply || "No response";
    const bubbleElement = pushMessage(aiText, "ai", data.timestamp);
    updateMessageCount(data.message_count);
    setStatus("idle");

    // Render deadline cards if tasks are detected
    if (data.detected_tasks && data.detected_tasks.length > 0) {
      data.detected_tasks.forEach((task) => {
        renderDeadlineCard(task, bubbleElement);
      });
    }

    // Update session ID and refresh recent chats if new session
    if (data.session_id && data.session_id !== currentSessionId) {
      currentSessionId = data.session_id;
      updateRecentChats();
    }
  } catch (err) {
    console.error("Chat error:", err);
    const errorMsg = err.message.includes("Failed to fetch")
      ? "Connection error - please check your internet"
      : err.message;
    pushMessage(`⚠️ ${errorMsg}`, "ai");
    setStatus("error");
    showToast("Failed to send message", "error");
  } finally {
    showTyping(false);
    inFlight = false;
    updateCharCount();
    // Ensure input is focused and ready
    if (!inputEl.value) {
      inputEl.focus();
    }
  }
}

// Toggle history sidebar
function toggleHistory() {
  historyVisible = !historyVisible;
  historyPanel.classList.toggle("hidden", !historyVisible);
}

// Load chat session
async function loadChatSession(sessionId) {
  try {
    // Validate URL and add CSRF protection
    const loadUrl = `/api/sessions/${encodeURIComponent(sessionId)}/load`;
    if (!isValidURL(new URL(loadUrl, window.location.origin).href)) {
      throw new Error("Invalid session ID");
    }

    const headers = { "Content-Type": "application/json" };
    const csrfToken = getCSRFToken();
    if (csrfToken) {
      headers["X-CSRF-Token"] = csrfToken;
    }

    const response = await fetch(loadUrl, {
      method: "POST",
      headers: headers,
    });
    const data = await response.json();

    if (!response.ok) {
      showToast("Failed to load chat session", "error");
      return;
    }

    currentSessionId = sessionId;
    messageHistory = [...data.messages]; // Correctly set once (no duplicate pushes)

    // Clear current messages
    messagesEl.innerHTML = "";

    // Use Document Fragment to append all elements in a single DOM operation - HUGE performance boost!
    const fragment = document.createDocumentFragment();
    data.messages.forEach((msg) => {
      const msgId = msg.id || "msg_" + Math.random().toString(36).substr(2, 9);
      const div = createMessageElement(msg.text, msg.who, msg.timestamp, msgId);
      fragment.appendChild(div);
    });

    messagesEl.appendChild(fragment);

    updateMessageCount(messageHistory.length);
    updateRecentChats(); // Update to show active session
    smoothScrollToBottom();
    showToast("Chat session loaded");
  } catch (error) {
    console.error("Failed to load chat session:", error);
    showToast("Failed to load chat session", "error");
  }
}

// Start new chat
async function startNewChat() {
  try {
    // Add CSRF protection
    const headers = { "Content-Type": "application/json" };
    const csrfToken = getCSRFToken();
    if (csrfToken) {
      headers["X-CSRF-Token"] = csrfToken;
    }

    const response = await fetch("/api/new-session", {
      method: "POST",
      headers: headers,
    });

    if (response.ok) {
      currentSessionId = null;
      messageHistory = [];
      messagesEl.innerHTML = "";
      updateMessageCount(0);

      // Add welcome message
      pushMessage(
        "Welcome — ask me anything. I have context memory and can help with various tasks!",
        "ai",
      );

      // Update recent chats
      updateRecentChats();
      showToast("New chat started");
    }
  } catch (error) {
    console.error("Failed to start new chat:", error);
    showToast("Failed to start new chat", "error");
  }
}

// Show context panel
function showHoverPanel(e, sessionId) {
  hoverPanelTarget = sessionId;

  // Position the panel at mouse cursor
  const x = e.clientX;
  const y = e.clientY;

  // Ensure panel stays within viewport
  const panelWidth = 300;
  const panelHeight = 200;
  const adjustedX = x + panelWidth > window.innerWidth ? x - panelWidth : x;
  const adjustedY = y + panelHeight > window.innerHeight ? y - panelHeight : y;

  hoverPanel.style.left = adjustedX + "px";
  hoverPanel.style.top = adjustedY + "px";
  hoverPanel.classList.add("show");
}

// Hide context panel
function hideHoverPanel() {
  hoverPanel.classList.remove("show");
  hoverPanelTarget = null;
}

// Modal System Functions
function showModal(title, content, buttons = []) {
  modalTitle.textContent = title;
  modalBody.innerHTML = content;
  modalFooter.innerHTML = "";

  if (!buttons || buttons.length === 0) {
    modalFooter.style.display = "none";
  } else {
    modalFooter.style.display = "flex";
    buttons.forEach((btn) => {
      const button = document.createElement("button");
      button.className = `btn ${btn.class || "btn--secondary"}`;
      button.textContent = btn.text;
      button.onclick = btn.onclick;
      modalFooter.appendChild(button);
    });
  }

  const closeBtn = document.getElementById("modal-close");
  if (closeBtn) closeBtn.style.display = "flex";

  modalOverlay.classList.add("show");

  // Focus first input if exists
  const firstInput = modalBody.querySelector("input, textarea");
  if (firstInput) {
    setTimeout(() => firstInput.focus(), 100);
  }
}

function hideModal() {
  modalOverlay.classList.remove("show");
}

function showConfirmModal(title, message, onConfirm, options = {}) {
  const iconClass = options.danger
    ? "fas fa-exclamation-triangle"
    : "fas fa-question-circle";
  const confirmClass = options.danger ? "btn--danger" : "btn--mint";
  const confirmText = options.confirmText || "Confirm";

  const content = `
    <div class="modal--confirm ${options.danger ? "danger" : ""}">
      <div class="modal-icon">
        <i class="${iconClass}"></i>
      </div>
      <div class="modal-message">${message}</div>
      ${options.submessage ? `<div class="modal-submessage">${options.submessage}</div>` : ""}
    </div>
  `;

  showModal(title, content, [
    {
      text: "Cancel",
      class: "btn--secondary",
      onclick: hideModal,
    },
    {
      text: confirmText,
      class: confirmClass,
      onclick: () => {
        hideModal();
        onConfirm();
      },
    },
  ]);
}

function showInputModal(title, placeholder, onSubmit, options = {}) {
  const inputType = options.textarea ? "textarea" : "input";
  const inputClass = options.textarea
    ? "form-input form-textarea"
    : "form-input";
  const defaultValue = options.defaultValue || "";

  const content = `
    <div class="form-group">
      <label class="form-label">${options.label || title}</label>
      <${inputType}
        id="modal-input"
        class="${inputClass}"
        placeholder="${placeholder}"
        maxlength="${options.maxLength || 100}"
        ${options.required ? "required" : ""}
      >${defaultValue}</${inputType}>
      <div id="modal-input-error" class="form-error" style="display: none;"></div>
    </div>
  `;

  showModal(title, content, [
    {
      text: "Cancel",
      class: "btn--secondary",
      onclick: hideModal,
    },
    {
      text: options.submitText || "Save",
      class: "btn--mint",
      onclick: () => {
        const input = document.getElementById("modal-input");
        const value = input.value.trim();
        const errorEl = document.getElementById("modal-input-error");

        // Validation
        if (options.required && !value) {
          errorEl.textContent = "This field is required";
          errorEl.style.display = "block";
          input.focus();
          return;
        }

        if (options.maxLength && value.length > options.maxLength) {
          errorEl.textContent = `Maximum ${options.maxLength} characters allowed`;
          errorEl.style.display = "block";
          input.focus();
          return;
        }

        hideModal();
        onSubmit(value);
      },
    },
  ]);
}

// Handle hover panel actions
function handleHoverAction(action) {
  if (!hoverPanelTarget) {
    console.warn("No hover panel target set");
    return;
  }

  // Validate action parameter
  const validActions = ["duplicate", "rename", "copy", "export", "delete"];
  if (!validActions.includes(action)) {
    console.error("Invalid action:", action);
    showToast("Invalid action", "error");
    return;
  }

  switch (action) {
    case "duplicate":
      duplicateChatSession(hoverPanelTarget);
      break;
    case "rename":
      showRenameModal(hoverPanelTarget);
      break;
    case "copy":
      copySessionMessages(hoverPanelTarget);
      break;
    case "export":
      exportSingleChat(hoverPanelTarget);
      break;
    case "delete":
      showDeleteModal(hoverPanelTarget);
      break;
    default:
      console.error("Unhandled action:", action);
      showToast("Action not implemented", "error");
  }

  hoverPanel.classList.remove("show");
  hoverPanelTarget = null;
}

// Modal-based rename function
function showRenameModal(sessionId) {
  showInputModal(
    "Rename Chat",
    "Enter new chat title...",
    (newTitle) => renameChatSessionWithTitle(sessionId, newTitle),
    {
      label: "Chat Title",
      maxLength: 100,
      required: true,
      submitText: "Rename",
    },
  );
}

// Modal-based delete confirmation
function showDeleteModal(sessionId) {
  showConfirmModal(
    "Delete Chat",
    "Are you sure you want to delete this chat?",
    () => deleteChatSession(sessionId),
    {
      danger: true,
      confirmText: "Delete",
      submessage: "This action cannot be undone.",
    },
  );
}

// Modal-based message edit
function showEditMessageModal(bubbleElement) {
  const rawText = bubbleElement.getAttribute("data-raw-text") || "";

  showInputModal(
    "Edit Message",
    "Edit your message...",
    (newText) => editMessageRequest(bubbleElement, newText),
    {
      label: "Message Content",
      defaultValue: rawText,
      maxLength: 2000,
      required: true,
      textarea: true,
      submitText: "Update",
    },
  );
}

// Copy session messages
async function copySessionMessages(sessionId) {
  try {
    const response = await fetch(
      `/api/sessions/${encodeURIComponent(sessionId)}/copy`,
    );

    if (!response.ok) {
      const errorData = await response
        .json()
        .catch(() => ({ error: "Copy failed" }));
      throw new Error(errorData.error || "Copy failed");
    }

    const data = await response.json();

    if (data.success && data.formatted_text) {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(data.formatted_text);
      } else {
        console.warn(
          "Using deprecated document.execCommand for clipboard access - consider upgrading packages",
        );
        const textArea = document.createElement("textarea");
        textArea.value = data.formatted_text;
        textArea.style.position = "fixed";
        textArea.style.opacity = "0";
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand("copy");
        document.body.removeChild(textArea);
      }
      showToast(`Copied ${data.message_count || 0} messages!`);
    } else {
      throw new Error("No content to copy");
    }
  } catch (error) {
    console.error("Copy messages error:", error);
    showToast(error.message || "Failed to copy messages", "error");
  }
}

// Regenerate last AI response (keyboard shortcut)
async function regenerateLastResponse() {
  const aiBubbles = messagesEl.querySelectorAll(".bubble--ai");
  if (aiBubbles.length === 0) {
    showToast("No AI responses to regenerate", "warning");
    return;
  }

  const lastAiBubble = aiBubbles[aiBubbles.length - 1];
  await regenerateResponse(lastAiBubble);
}

// Edit user message
function editMessage(bubbleElement) {
  if (inFlight) {
    showToast("Please wait for current request to complete", "warning");
    return;
  }

  showEditMessageModal(bubbleElement);
}

// Send edit message request
async function editMessageRequest(bubbleElement, newText) {
  try {
    inFlight = true;
    setStatus("sending", "Editing message...");
    showTyping(true);

    const messageId = bubbleElement.getAttribute("data-message-id");

    // Add CSRF protection
    const headers = { "Content-Type": "application/json" };
    const csrfToken = getCSRFToken();
    if (csrfToken) {
      headers["X-CSRF-Token"] = csrfToken;
    }

    const requestBody = {
      message_id: sanitizeHTML(messageId),
      new_text: sanitizeHTML(newText),
    };
    const byok = getBYOKConfig();
    if (byok) {
      requestBody.provider = byok.provider;
      requestBody.api_key = byok.api_key;
      requestBody.model = byok.model;
    }

    const response = await fetch("/edit-message", {
      method: "POST",
      headers: headers,
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      const errorData = await response
        .json()
        .catch(() => ({ error: "Edit failed" }));
      throw new Error(errorData.error || "Edit failed");
    }

    const data = await response.json();

    // Update user message
    const userContent = bubbleElement.querySelector(".bubble__content p");
    if (userContent) {
      userContent.innerHTML = formatMessage(data.user_message);
      bubbleElement.setAttribute("data-raw-text", data.user_message);
    }

    // Find and update the corresponding AI response
    const nextBubble = bubbleElement.nextElementSibling;
    if (nextBubble && nextBubble.classList.contains("bubble--ai")) {
      const aiContent = nextBubble.querySelector(".bubble__content p");
      if (aiContent) {
        aiContent.innerHTML = formatMessage(data.ai_reply);
        nextBubble.setAttribute("data-raw-text", data.ai_reply);

        // Update timestamp
        const timeElement = nextBubble.querySelector("time");
        if (timeElement) {
          timeElement.textContent = `ai • ${formatTime(data.timestamp)}`;
        }
      }
    }

    setStatus("idle");
    showToast("Message edited successfully!");
  } catch (error) {
    console.error("Edit error:", error);
    setStatus("error");
    showToast(error.message || "Failed to edit message", "error");
  } finally {
    showTyping(false);
    inFlight = false;
  }
}

// Regenerate AI response
async function regenerateResponse(bubbleElement) {
  if (inFlight) {
    showToast("Please wait for current request to complete", "warning");
    return;
  }

  // Validate bubble element
  if (!bubbleElement || !bubbleElement.querySelector) {
    console.error("Invalid bubble element for regeneration");
    showToast("Cannot regenerate: invalid message element", "error");
    return;
  }

  const content = bubbleElement.querySelector(".bubble__content p");
  if (!content) {
    console.error("Cannot find message content for regeneration");
    showToast("Cannot regenerate: message content not found", "error");
    return;
  }

  try {
    inFlight = true;
    setStatus("sending", "Regenerating...");
    showTyping(true);

    // Store original content safely
    const originalText = content.innerHTML;
    content.innerHTML =
      '<i class="fas fa-spinner fa-spin"></i> Regenerating response...';

    // Add CSRF protection
    const headers = { "Content-Type": "application/json" };
    const csrfToken = getCSRFToken();
    if (csrfToken) {
      headers["X-CSRF-Token"] = csrfToken;
    }

    const requestBody = {
      message_id: bubbleElement.getAttribute("data-message-id"),
    };
    const byok = getBYOKConfig();
    if (byok) {
      requestBody.provider = byok.provider;
      requestBody.api_key = byok.api_key;
      requestBody.model = byok.model;
    }

    const response = await fetch("/regenerate", {
      method: "POST",
      headers: headers,
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      const errorData = await response
        .json()
        .catch(() => ({ error: "Unknown error" }));
      throw new Error(errorData.error || `HTTP ${response.status}`);
    }

    const data = await response.json();

    // Update the bubble with new response (safely formatted)
    const sanitizedReply = sanitizeHTML(data.reply || "No response");
    content.innerHTML = formatMessage(sanitizedReply);
    bubbleElement.setAttribute("data-raw-text", data.reply || "");

    // Update timestamp
    const timeElement = bubbleElement.querySelector("time");
    if (timeElement) {
      timeElement.textContent = `ai • ${formatTime(data.timestamp)}`;
    }

    setStatus("idle");
    showToast("Response regenerated successfully!");
  } catch (error) {
    console.error("Regenerate error:", error);

    // Restore original content on error
    if (content && originalText) {
      content.innerHTML = originalText;
    }

    setStatus("error");
    showToast(error.message || "Failed to regenerate response", "error");
  } finally {
    showTyping(false);
    inFlight = false;
  }
}

// Copy current chat messages
async function copyCurrentChatMessages() {
  if (!currentSessionId) {
    showToast("No active chat to copy", "warning");
    return;
  }

  try {
    // Get current messages from DOM
    const bubbles = messagesEl.querySelectorAll(".bubble");
    let formattedText = "";

    bubbles.forEach((bubble) => {
      const isUser = bubble.classList.contains("bubble--user");
      const sender = isUser ? "You" : "AI";
      const rawText =
        bubble.getAttribute("data-raw-text") ||
        bubble.querySelector("p").textContent;
      formattedText += `${sender}: ${rawText}\n\n`;
    });

    if (formattedText.trim()) {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(formattedText.trim());
      } else {
        // Fallback (deprecated API)
        console.warn(
          "Using deprecated document.execCommand for clipboard access",
        );
        const textArea = document.createElement("textarea");
        textArea.value = formattedText.trim();
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand("copy");
        document.body.removeChild(textArea);
      }
      showToast(`Copied ${bubbles.length} messages from current chat!`);
    } else {
      showToast("No messages to copy", "warning");
    }
  } catch (error) {
    console.error("Copy error:", error);
    showToast("Failed to copy messages", "error");
  }
}

// Export single chat
async function exportSingleChat(sessionId) {
  try {
    // Validate session ID format
    if (!sessionId || typeof sessionId !== "string") {
      throw new Error("Invalid session ID");
    }

    const response = await fetch(
      `/api/sessions/${encodeURIComponent(sessionId)}`,
    );

    if (!response.ok) {
      const errorData = await response
        .json()
        .catch(() => ({ error: "Export failed" }));
      throw new Error(errorData.error || "Export failed");
    }

    const data = await response.json();

    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `chat-${sessionId.substring(0, 8)}.json`; // Truncate for filename
    a.click();
    URL.revokeObjectURL(url);
    showToast("Chat exported successfully");
  } catch (error) {
    console.error("Export error:", error);
    showToast("Failed to export chat", "error");
  }
}

// Rename chat session with title
async function renameChatSessionWithTitle(sessionId, newTitle) {
  // Validate and sanitize input
  const trimmedTitle = newTitle.trim();
  if (trimmedTitle.length > 100) {
    showToast("Title too long (max 100 characters)", "error");
    return;
  }

  // Remove potentially dangerous characters
  const sanitizedTitle = trimmedTitle.replace(/[<>"'&]/g, "");

  if (!sanitizedTitle) {
    showToast("Invalid title after sanitization", "error");
    return;
  }

  try {
    const response = await fetch(
      `/api/sessions/${encodeURIComponent(sessionId)}/title`,
      {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: sanitizedTitle }),
      },
    );

    if (!response.ok) {
      const errorData = await response
        .json()
        .catch(() => ({ error: "Rename failed" }));
      throw new Error(errorData.error || "Rename failed");
    }

    updateRecentChats();
    showToast("Chat renamed successfully");
  } catch (error) {
    console.error("Failed to rename chat:", error);
    showToast(error.message || "Failed to rename chat", "error");
  }
}

// Legacy function for backward compatibility
async function renameChatSession(sessionId) {
  showRenameModal(sessionId);
}

// Duplicate chat session
async function duplicateChatSession(sessionId) {
  try {
    // Validate URL and add CSRF protection
    const duplicateUrl = `/api/sessions/${encodeURIComponent(sessionId)}/duplicate`;
    if (!isValidURL(new URL(duplicateUrl, window.location.origin).href)) {
      throw new Error("Invalid session ID");
    }

    const headers = { "Content-Type": "application/json" };
    const csrfToken = getCSRFToken();
    if (csrfToken) {
      headers["X-CSRF-Token"] = csrfToken;
    }

    const response = await fetch(duplicateUrl, {
      method: "POST",
      headers: headers,
    });
    const data = await response.json();

    if (response.ok) {
      updateRecentChats();
      showToast("Chat duplicated successfully");

      // Load the duplicated chat
      setTimeout(() => {
        loadChatSession(data.new_session_id);
      }, 500);
    } else {
      showToast("Failed to duplicate chat", "error");
    }
  } catch (error) {
    showToast("Failed to duplicate chat", "error");
  }
}

// Delete chat session
async function deleteChatSession(sessionId) {
  try {
    // Validate URL and add CSRF protection
    const deleteUrl = `/api/sessions/${encodeURIComponent(sessionId)}`;
    if (!isValidURL(new URL(deleteUrl, window.location.origin).href)) {
      throw new Error("Invalid session ID");
    }

    const headers = { "Content-Type": "application/json" };
    const csrfToken = getCSRFToken();
    if (csrfToken) {
      headers["X-CSRF-Token"] = csrfToken;
    }

    const response = await fetch(deleteUrl, {
      method: "DELETE",
      headers: headers,
    });

    if (response.ok) {
      // If deleting current session, start new chat
      if (sessionId === currentSessionId) {
        await startNewChat();
      }
      updateRecentChats();
      showToast("Chat deleted successfully");
    } else {
      showToast("Failed to delete chat", "error");
    }
  } catch (error) {
    console.error("Failed to delete chat:", error);
    showToast("Failed to delete chat", "error");
  }
}

// Update recent chats display (optimized with document fragment)
async function updateRecentChats() {
  try {
    // Append a unique cache-buster timestamp parameter to prevent browser caching of GET requests
    const response = await fetch("/api/sessions?t=" + Date.now());

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();

    recentChats.innerHTML = "";

    if (!data.sessions || data.sessions.length === 0) {
      recentChats.innerHTML =
        '<div class="chat-empty"><i class="fas fa-comments"></i>No recent chats</div>';
      return;
    }

    // Use document fragment for better performance
    const fragment = document.createDocumentFragment();

    data.sessions.forEach((session) => {
      const chatItem = document.createElement("div");
      chatItem.className = "chat-item";
      chatItem.title = "Click to load chat session";
      if (session.id === currentSessionId) {
        chatItem.classList.add("active");
      }

      // Click to load session
      chatItem.onclick = () => loadChatSession(session.id);

      // Right-click event for action panel
      chatItem.addEventListener("contextmenu", (e) => {
        e.preventDefault();
        showHoverPanel(e, session.id);
      });

      const title = document.createElement("div");
      title.className = "chat-item__title";
      title.textContent = session.title || "Untitled Chat";

      const preview = document.createElement("div");
      preview.className = "chat-item__preview";
      preview.textContent = session.preview || "No preview available";

      const time = document.createElement("div");
      time.className = "chat-item__time";
      time.textContent = formatTime(session.timestamp);

      chatItem.appendChild(title);
      chatItem.appendChild(preview);
      chatItem.appendChild(time);
      fragment.appendChild(chatItem);
    });

    recentChats.appendChild(fragment);
  } catch (error) {
    console.error("Failed to load chat sessions:", error);
    recentChats.innerHTML =
      '<p style="color: var(--error); text-align: center; padding: 20px;">Failed to load chats</p>';
  }
}

// Clear chat history with modal confirmation
async function clearHistory() {
  showConfirmModal(
    "Clear History",
    "Are you sure you want to clear all chat history?",
    async () => {
      try {
        // Add CSRF protection
        const headers = { "Content-Type": "application/json" };
        const csrfToken = getCSRFToken();
        if (csrfToken) {
          headers["X-CSRF-Token"] = csrfToken;
        }

        const res = await fetch("/clear-history", {
          method: "POST",
          headers: headers,
        });
        if (res.ok) {
          messagesEl.innerHTML = "";
          messageHistory = [];
          currentSessionId = null;
          updateMessageCount(0);
          updateRecentChats();
          showToast("All chat history cleared");

          // Clear local storage
          localStorage.removeItem("chatDraft");

          // Add welcome message
          pushMessage("All chat history cleared. Starting fresh!", "ai");
        }
      } catch (err) {
        showToast("Failed to clear history", "error");
      }
    },
    {
      danger: true,
      confirmText: "Clear All",
      submessage: "This will remove all messages from the current session.",
    },
  );
}

// Clear all data function with modal confirmation
async function clearAllData() {
  showConfirmModal(
    "Clear All Data",
    "This will permanently delete ALL chat data including sessions.",
    async () => {
      try {
        // Clear all data via backend
        // Add CSRF protection
        const headers = { "Content-Type": "application/json" };
        const csrfToken = getCSRFToken();
        if (csrfToken) {
          headers["X-CSRF-Token"] = csrfToken;
        }

        const res = await fetch("/clear-all-data", {
          method: "POST",
          headers: headers,
        });

        if (!res.ok) {
          const errorData = await res
            .json()
            .catch(() => ({ error: "Clear failed" }));
          throw new Error(errorData.error || "Clear failed");
        }

        // Clear UI
        messagesEl.innerHTML = "";
        messageHistory = [];
        currentSessionId = null;
        updateMessageCount(0);
        updateRecentChats();

        // Clear specific localStorage items instead of all
        const keysToRemove = ["chatDraft", "theme"];
        keysToRemove.forEach((key) => localStorage.removeItem(key));

        showToast("All data cleared successfully!");
        pushMessage("All data cleared. Fresh start!", "ai");
      } catch (err) {
        console.error("Clear all data error:", err);
        showToast(err.message || "Failed to clear all data", "error");
      }
    },
    {
      danger: true,
      confirmText: "Delete All",
      submessage: "This action cannot be undone.",
    },
  );
}

// Export chat history
async function exportChat() {
  try {
    const res = await fetch("/export-chat");
    const data = await res.json();

    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `chat-export-${new Date().toISOString().split("T")[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);

    showToast("Chat exported successfully");
  } catch (err) {
    showToast("Failed to export chat", "error");
  }
}

// Search messages (improved with null checks)
function searchMessages() {
  const query = searchInput.value.toLowerCase().trim();
  const bubbles = messagesEl.querySelectorAll(".bubble");

  bubbles.forEach((bubble) => {
    const textElement = bubble.querySelector("p");
    if (!textElement) {
      console.warn("Message bubble missing text element");
      return;
    }

    const text = textElement.textContent.toLowerCase();
    const match = !query || text.includes(query);
    bubble.style.display = match ? "block" : "none";

    if (match && query) {
      bubble.classList.add("highlight");
    } else {
      bubble.classList.remove("highlight");
    }
  });
}

// Voice input (if supported)
function initVoiceInput() {
  if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-US";

    recognition.onstart = () => {
      isListening = true;
      voiceBtn.classList.add("listening");
      voiceBtn.innerHTML = '<i class="fas fa-stop"></i>';
      setStatus("sending", "Listening...");
    };

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      inputEl.value = transcript;
      updateCharCount();
    };

    recognition.onend = () => {
      isListening = false;
      voiceBtn.classList.remove("listening");
      voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
      setStatus("idle");
    };

    recognition.onerror = (event) => {
      console.error("Speech recognition error:", event.error);
      showToast("Voice recognition failed", "error");
      // Properly handle the error state
      isListening = false;
      voiceBtn.classList.remove("listening");
      voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
      setStatus("idle");
    };
  } else {
    voiceBtn.style.display = "none";
  }
}

// Toggle voice input
function toggleVoice() {
  if (!recognition) return;

  if (isListening) {
    recognition.stop();
  } else {
    recognition.start();
  }
}

// Update time display with cached formatter
const timeFormatter = new Intl.DateTimeFormat([], {
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
  hour12: true,
});

function updateTime() {
  const now = new Date();
  timeDisplay.textContent = timeFormatter.format(now);
}

// Get weather data
async function updateWeather(location = "London") {
  try {
    const response = await fetch(
      `/weather?city=${encodeURIComponent(location)}`,
    );
    const data = await response.json();

    if (data.error) {
      weatherTemp.textContent = "22°C";
      weatherIcon.className = "fas fa-sun";
      return;
    }

    weatherTemp.textContent = `${data.temperature}°C`;

    // Enhanced icon mapping based on OpenWeatherMap icons
    const iconMap = {
      Clear: "fas fa-sun",
      Clouds: "fas fa-cloud",
      Rain: "fas fa-cloud-rain",
      Drizzle: "fas fa-cloud-drizzle",
      Thunderstorm: "fas fa-bolt",
      Snow: "fas fa-snowflake",
      Mist: "fas fa-smog",
      Fog: "fas fa-smog",
      Haze: "fas fa-smog",
    };

    weatherIcon.className = iconMap[data.condition] || "fas fa-sun";
    weatherIcon.title = `${data.description} in ${data.location}`;

    // Store current weather data for chat context
    window.currentWeather = data;
  } catch (error) {
    console.error("Weather update error:", error);
    weatherTemp.textContent = "22°C";
    weatherIcon.className = "fas fa-sun";
  }
}

// Initialize weather and time updates
function initWeatherTime() {
  updateTime();

  // Try to get user's location for weather first
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords;

        // Store user location globally for chat context
        window.userLocation = { lat: latitude, lon: longitude };

        try {
          const weatherData = await getWeatherByCoordinates(
            latitude,
            longitude,
          );
          if (weatherData && !weatherData.error) {
            weatherTemp.textContent = `${weatherData.temperature}°C`;
            const iconMap = {
              Clear: "fas fa-sun",
              Clouds: "fas fa-cloud",
              Rain: "fas fa-cloud-rain",
              Drizzle: "fas fa-cloud-drizzle",
              Thunderstorm: "fas fa-bolt",
              Snow: "fas fa-snowflake",
              Mist: "fas fa-smog",
              Fog: "fas fa-smog",
              Haze: "fas fa-smog",
            };
            weatherIcon.className =
              iconMap[weatherData.condition] || "fas fa-sun";
            weatherIcon.title = `${weatherData.description} in ${weatherData.location}`;
            window.currentWeather = weatherData;
          } else {
            // Fallback to default location
            updateWeather("London");
          }
        } catch (error) {
          console.error("Location weather error:", error);
          updateWeather("London");
        }
      },
      (error) => {
        console.log("Geolocation denied, using default location");
        updateWeather("London");
      },
      { timeout: 5000, enableHighAccuracy: false },
    );
  } else {
    // Geolocation not supported, use default
    updateWeather("London");
  }

  // Update time every second
  setInterval(updateTime, 1000);

  // Update weather every 10 minutes
  setInterval(() => {
    if (
      window.currentWeather &&
      window.currentWeather.location !== "Your Location"
    ) {
      // Re-get location weather if we have real location data
      getUserLocationWeather();
    } else {
      updateWeather("London");
    }
  }, 600000);
}

// Weather-specific functions
async function getWeatherForecast(location, days = 5) {
  try {
    const response = await fetch(
      `/api/weather/forecast?location=${encodeURIComponent(location)}&days=${days}`,
    );
    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Forecast error:", error);
    return null;
  }
}

async function searchCities(query) {
  try {
    const response = await fetch(
      `/api/weather/search?q=${encodeURIComponent(query)}`,
    );
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const data = await response.json();
    return data.cities || [];
  } catch (error) {
    console.error("City search error:", error);
    return [];
  }
}

async function getWeatherByCoordinates(lat, lon) {
  try {
    const response = await fetch(
      `/api/weather/coordinates?lat=${lat}&lon=${lon}`,
    );
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Coordinates weather error:", error);
    return null;
  }
}

// Weather icon mapping (moved to module level for performance)
const WEATHER_ICON_MAP = {
  Clear: "fas fa-sun",
  Clouds: "fas fa-cloud",
  Rain: "fas fa-cloud-rain",
  Drizzle: "fas fa-cloud-drizzle",
  Thunderstorm: "fas fa-bolt",
  Snow: "fas fa-snowflake",
  Mist: "fas fa-smog",
  Fog: "fas fa-smog",
  Haze: "fas fa-smog",
};

// Get user's location and update weather
function getUserLocationWeather() {
  console.log("Location button clicked");

  if (!navigator.geolocation) {
    showToast("Geolocation not supported by this browser", "error");
    return;
  }

  // Check if we're on HTTPS (required for geolocation)
  if (
    location.protocol !== "https:" &&
    location.hostname !== "localhost" &&
    location.hostname !== "127.0.0.1"
  ) {
    showToast("Location access requires HTTPS", "warning");
    return;
  }

  showToast("Requesting location access...", "info");

  navigator.geolocation.getCurrentPosition(
    async (position) => {
      console.log("Location obtained:", position.coords);
      const { latitude, longitude } = position.coords;

      // Validate coordinates
      if (
        typeof latitude !== "number" ||
        typeof longitude !== "number" ||
        latitude < -90 ||
        latitude > 90 ||
        longitude < -180 ||
        longitude > 180
      ) {
        showToast("Invalid location coordinates", "error");
        return;
      }

      // Store user location globally
      window.userLocation = { lat: latitude, lon: longitude };

      try {
        const weatherData = await getWeatherByCoordinates(latitude, longitude);
        if (weatherData && !weatherData.error) {
          weatherTemp.textContent = `${weatherData.temperature}°C`;
          weatherIcon.className =
            WEATHER_ICON_MAP[weatherData.condition] || "fas fa-sun";
          weatherIcon.title = `${weatherData.description} in ${weatherData.location}`;
          window.currentWeather = weatherData;
          showToast(`Weather updated for ${weatherData.location}`);
        } else {
          showToast("Failed to get weather data", "error");
        }
      } catch (error) {
        console.error("Location weather error:", error);
        showToast("Failed to get location weather", "error");
      }
    },
    (error) => {
      console.error("Geolocation error:", error);
      let message = "Location access failed";

      switch (error.code) {
        case error.PERMISSION_DENIED:
          message = "Location access denied by user";
          break;
        case error.POSITION_UNAVAILABLE:
          message = "Location information unavailable";
          break;
        case error.TIMEOUT:
          message = "Location request timed out";
          break;
      }

      showToast(message, "warning");
    },
    {
      timeout: 10000,
      enableHighAccuracy: true,
      maximumAge: 300000, // 5 minutes
    },
  );
}

// Set weather API key
async function setWeatherApiKey(apiKey) {
  try {
    const response = await fetch("/api/weather/set-key", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ api_key: apiKey }),
    });

    const data = await response.json();

    if (response.ok) {
      showToast("Weather API key set successfully!");
      updateWeather(); // Refresh weather with new key
      return true;
    } else {
      showToast(data.error || "Failed to set API key", "error");
      return false;
    }
  } catch (error) {
    showToast("Failed to set API key", "error");
    return false;
  }
}

// Modal event listeners
modalClose.addEventListener("click", hideModal);
modalOverlay.addEventListener("click", (e) => {
  if (e.target === modalOverlay) {
    hideModal();
  }
});

// Event Listeners
sendBtn.addEventListener("click", sendMessage);
if (themeToggle) themeToggle.addEventListener("click", toggleTheme);

// Theme selector events
themeClose.addEventListener("click", hideThemeSelector);
autoThemeCheckbox.addEventListener("change", toggleAutoTheme);
createThemeBtn.addEventListener("click", showThemeCreator);

themeOptions.forEach((option) => {
  option.addEventListener("click", () => {
    const theme = option.dataset.theme;
    setTheme(theme);
  });
});

// Simple event listeners
if (creatorClose) creatorClose.addEventListener("click", hideThemeCreator);
if (creatorCancel) creatorCancel.addEventListener("click", hideThemeCreator);
if (creatorSave) creatorSave.addEventListener("click", saveCustomTheme);
if (createThemeBtn) createThemeBtn.addEventListener("click", showThemeCreator);

// Color picker events
if (colorPrimary) colorPrimary.addEventListener("input", updatePreview);
if (colorBg0) colorBg0.addEventListener("input", updatePreview);
if (colorBg1) colorBg1.addEventListener("input", updatePreview);
if (colorFg) colorFg.addEventListener("input", updatePreview);

// Close on overlay click
if (themeCreatorOverlay) {
  themeCreatorOverlay.addEventListener("click", (e) => {
    if (e.target === themeCreatorOverlay) hideThemeCreator();
  });
}

// Test function for debugging
window.testThemeCreator = function () {
  console.log("Test function called");
  showThemeCreator();
};

// Close theme selector on outside click
document.addEventListener("click", (e) => {
  if (
    themeSelectorVisible &&
    !themeSelector.contains(e.target) &&
    (!themeToggle || !themeToggle.contains(e.target))
  ) {
    hideThemeSelector();
  }
});
clearBtn.addEventListener("click", clearHistory);

// Add clear all data button functionality
document.addEventListener("DOMContentLoaded", () => {
  // Add clear all button if it doesn't exist
  if (!document.getElementById("clear-all-btn")) {
    const clearAllBtn = document.createElement("button");
    clearAllBtn.id = "clear-all-btn";
    clearAllBtn.className = "btn btn--danger btn--sm";
    clearAllBtn.style.padding = "4px 8px";
    clearAllBtn.style.fontSize = "12px";
    clearAllBtn.style.height = "32px";
    clearAllBtn.innerHTML = '<i class="fas fa-trash-alt"></i> Clear All';
    clearAllBtn.title = "Clear all chat data and sessions";
    clearAllBtn.onclick = clearAllData;

    // Add to sidebar header controls (next to new-chat-btn)
    const sidebarHeader = document.querySelector(".sidebar-header");
    if (sidebarHeader) {
      // Find or create wrapper to align them nicely
      let btnGroup = sidebarHeader.querySelector(".sidebar-header-buttons");
      if (!btnGroup) {
        btnGroup = document.createElement("div");
        btnGroup.className = "sidebar-header-buttons";
        btnGroup.style.display = "flex";
        btnGroup.style.gap = "8px";
        btnGroup.style.alignItems = "center";

        const newChat = document.getElementById("new-chat-btn");
        if (newChat) {
          newChat.parentNode.insertBefore(btnGroup, newChat);
          btnGroup.appendChild(newChat);
        }
      }
      btnGroup.appendChild(clearAllBtn);
    }
  }
});
exportBtn.addEventListener("click", exportChat);
voiceBtn.addEventListener("click", toggleVoice);
historyToggle.addEventListener("click", toggleHistory);
const sidebarToggleBtn = document.getElementById("sidebar-toggle-btn");
if (sidebarToggleBtn) {
  sidebarToggleBtn.addEventListener("click", toggleHistory);
}
const sidebarCloseBtn = document.getElementById("sidebar-close-btn");
if (sidebarCloseBtn) {
  sidebarCloseBtn.addEventListener("click", toggleHistory);
}
newChatBtn.addEventListener("click", startNewChat);
document
  .getElementById("location-btn")
  .addEventListener("click", getUserLocationWeather);
emojiBtn.addEventListener("click", toggleEmojiPicker);

// Context panel events - no hover logic needed

hoverPanel.addEventListener("click", (e) => {
  e.preventDefault();
  e.stopPropagation();
  const menuItem = e.target.closest(".panel-item");
  if (menuItem && menuItem.dataset.action) {
    handleHoverAction(menuItem.dataset.action);
  }
});

// Hide context panel on click outside or scroll
document.addEventListener("click", (e) => {
  if (!hoverPanel.contains(e.target)) {
    hideHoverPanel();
  }

  // Hide emoji picker when clicking outside
  if (!emojiPicker.contains(e.target) && !emojiBtn.contains(e.target)) {
    hideEmojiPicker();
  }

  // Hide theme selector when clicking outside
  if (
    themeSelectorVisible &&
    !themeSelector.contains(e.target) &&
    (!themeToggle || !themeToggle.contains(e.target))
  ) {
    hideThemeSelector();
  }

  // Hide bubble actions dropdowns when clicking outside
  if (
    !e.target.closest(".bubble__menu-btn") &&
    !e.target.closest(".bubble__actions-dropdown")
  ) {
    document
      .querySelectorAll(".bubble__actions-dropdown")
      .forEach((dropdown) => {
        dropdown.classList.remove("show");
      });
  }
});

document.addEventListener("scroll", () => {
  hideHoverPanel();
  hideEmojiPicker();
});

// Search functionality
searchBtn.addEventListener("click", () => {
  searchPanel.style.display =
    searchPanel.style.display === "none" ? "flex" : "none";
  if (searchPanel.style.display === "flex") {
    searchInput.focus();
  } else {
    searchInput.value = "";
    searchMessages();
  }
});

searchClose.addEventListener("click", () => {
  searchPanel.style.display = "none";
  searchInput.value = "";
  searchMessages();
});

searchInput.addEventListener("input", searchMessages);

// Input events
inputEl.addEventListener("input", updateCharCount);
inputEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

// Keyboard shortcuts
document.addEventListener("keydown", (e) => {
  if (e.ctrlKey || e.metaKey) {
    switch (e.key) {
      case "k":
        e.preventDefault();
        if (shortcuts) {
          shortcuts.style.display =
            shortcuts.style.display === "none" ? "block" : "none";
        }
        break;
      case "l":
        e.preventDefault();
        clearHistory();
        break;
      case "d":
        if (e.shiftKey) {
          e.preventDefault();
          clearAllData();
        }
        break;
      case "e":
        e.preventDefault();
        exportChat();
        break;
      case "f":
        e.preventDefault();
        searchBtn.click();
        break;
      case "c":
        if (e.shiftKey) {
          e.preventDefault();
          copyCurrentChatMessages();
        }
        break;
      case "r":
        e.preventDefault();
        regenerateLastResponse();
        break;
      case "w":
        e.preventDefault();
        getUserLocationWeather();
        break;
      case "u":
        if (e.shiftKey) {
          e.preventDefault();
          // Use a more user-friendly modal instead of prompt
          showToast("API key setting moved to settings panel", "info");
        }
        break;
      case "t":
        e.preventDefault();
        showThemeSelector();
        break;
      case "t":
        e.preventDefault();
        showThemeSelector();
        break;
    }
  } else if (e.key === "Escape") {
    // Close panels in priority order
    if (modalOverlay.classList.contains("show")) {
      hideModal();
    } else if (apiSettingsVisible) {
      hideAPISettings();
    } else if (themeSelectorVisible) {
      hideThemeSelector();
    } else if (themeCreatorVisible) {
      hideThemeCreator();
    } else if (emojiPickerVisible) {
      hideEmojiPicker();
    } else {
      searchPanel.style.display = "none";
      shortcuts.style.display = "none";
      searchInput.value = "";
      searchMessages();
    }
  }
});

// Initialize on load
window.addEventListener("load", async () => {
  try {
    // Initialize theme system first (loads custom themes from backend)
    await initTheme();

    // Then initialize other components
    initVoiceInput();
    initWeatherTime();
    initEmojiPicker();
    await initAPISettings();
    updateCharCount();
    updateMessageCount(0);
    if (currentSessionId) {
      await loadChatSession(currentSessionId);
    } else {
      updateRecentChats();
    }

    inputEl.focus();
    setStatus("idle");

    // Set current year
    document.getElementById("year").textContent = new Date().getFullYear();

    console.log("App initialized successfully");
  } catch (error) {
    console.error("App initialization error:", error);
    // Ensure basic functionality works even if theme loading fails
    setStatus("idle");
    inputEl.focus();
  }
});

// Auto-save draft
let draftTimer;
inputEl.addEventListener("input", () => {
  clearTimeout(draftTimer);
  draftTimer = setTimeout(() => {
    localStorage.setItem("chatDraft", inputEl.value);
  }, 500);
});

// Restore draft on load
window.addEventListener("load", () => {
  const draft = localStorage.getItem("chatDraft");
  if (draft) {
    inputEl.value = draft;
    updateCharCount();
  }
});

// Clear draft on send - integrate into existing sendMessage function
// This is handled within the sendMessage function itself

// Emoji Picker Functions
function initEmojiPicker() {
  populateEmojiGrid("smileys");

  // Category click handlers
  emojiCategories.forEach((category) => {
    category.addEventListener("click", () => {
      emojiCategories.forEach((c) => c.classList.remove("active"));
      category.classList.add("active");
      populateEmojiGrid(category.dataset.category);
    });
  });
}

function populateEmojiGrid(category) {
  const emojis = emojiData[category] || emojiData.smileys;
  emojiGrid.innerHTML = "";

  emojis.forEach((emoji) => {
    const button = document.createElement("button");
    button.className = "emoji-item";
    button.textContent = emoji;
    button.onclick = () => insertEmoji(emoji);
    emojiGrid.appendChild(button);
  });
}

function insertEmoji(emoji) {
  const cursorPos = inputEl.selectionStart;
  const textBefore = inputEl.value.substring(0, cursorPos);
  const textAfter = inputEl.value.substring(inputEl.selectionEnd);

  inputEl.value = textBefore + emoji + textAfter;
  inputEl.setSelectionRange(cursorPos + emoji.length, cursorPos + emoji.length);
  inputEl.focus();
  updateCharCount();
  hideEmojiPicker();
}

function toggleEmojiPicker() {
  emojiPickerVisible = !emojiPickerVisible;
  emojiPicker.classList.toggle("show", emojiPickerVisible);

  if (emojiPickerVisible) {
    // Position picker relative to composer area
    const composer = document.querySelector(".composer");
    const rect = composer.getBoundingClientRect();

    let left = rect.right - 320;
    let bottom = window.innerHeight - rect.top + 10;

    if (left < 10) {
      left = 10;
    }

    emojiPicker.style.left = left + "px";
    emojiPicker.style.bottom = bottom + "px";
  }
}

function hideEmojiPicker() {
  emojiPickerVisible = false;
  emojiPicker.classList.remove("show");
}

// Remove deprecated fetchWeather function - replaced with getUserLocationWeather
// This function used alert() which is not recommended for production

// API Settings (BYOK) Modal State & Functions
let apiSettingsVisible = false;

function getBYOKConfig() {
  const select = document.getElementById("chatbox-model-select");
  if (!select) return null;

  const val = select.value;
  if (!val) return null;

  const parts = val.split(":");
  const provider = parts[0];
  const model = parts.slice(1).join(":");

  const keyMap = {
    openai: "apiOpenAIKey",
    gemini: "apiGeminiKey",
    anthropic: "apiAnthropicKey",
    groq: "apiGroqKey",
    openrouter: "apiOpenRouterKey",
    mistral: "apiMistralKey",
  };

  const apiKey = (localStorage.getItem(keyMap[provider] || "") || "").trim();
  return { provider, api_key: apiKey, model };
}

async function syncActiveSettingsToBackend() {
  const byok = getBYOKConfig();
  if (byok && byok.provider && byok.api_key) {
    try {
      await fetch("/api/settings/sync", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          api_provider: byok.provider,
          api_key: byok.api_key,
          api_model: byok.model,
        }),
      });
    } catch (e) {
      console.error("Failed to sync settings to backend:", e);
    }
  }
}

async function syncAPISettingsFromServer() {
  try {
    const res = await fetch("/api/settings/sync");
    if (!res.ok) return;
    const data = await res.json();
    if (data.success && data.settings) {
      const s = data.settings;
      if (s.api_provider && s.api_key) {
        let provider = s.api_provider;
        if (provider === "google") {
          provider = "gemini";
        }
        const keyMap = {
          openai: "apiOpenAIKey",
          gemini: "apiGeminiKey",
          google: "apiGeminiKey",
          anthropic: "apiAnthropicKey",
          groq: "apiGroqKey",
          openrouter: "apiOpenRouterKey",
          mistral: "apiMistralKey",
        };
        const storageKey = keyMap[provider];
        if (storageKey) {
          localStorage.setItem(storageKey, s.api_key);
          localStorage.setItem("apiProvider", provider);
          localStorage.setItem("chatboxModel", `${provider}:${s.api_model}`);

          const modelKeyMap = {
            openai: "apiOpenAIModel",
            gemini: "apiGeminiModel",
            google: "apiGeminiModel",
            anthropic: "apiAnthropicModel",
            groq: "apiGroqModel",
            openrouter: "apiOpenRouterModel",
            mistral: "apiMistralModel",
          };
          const modelStorageKey = modelKeyMap[provider];
          if (modelStorageKey) {
            localStorage.setItem(modelStorageKey, s.api_model);
          }
        }
      }
    }
  } catch (err) {
    console.error("Failed to sync API settings from server:", err);
  }
}

function populateAPISettings() {
  // Populate keys from localStorage (used by both entry points)
  apiProviderSelect.value = localStorage.getItem("apiProvider") || "default";
  apiOpenAIKeyInput.value = localStorage.getItem("apiOpenAIKey") || "";
  apiOpenAIModelSelect.value =
    localStorage.getItem("apiOpenAIModel") || "gpt-4o-mini";
  apiGeminiKeyInput.value = localStorage.getItem("apiGeminiKey") || "";
  apiGeminiModelSelect.value =
    localStorage.getItem("apiGeminiModel") || "gemini-1.5-flash";

  document.getElementById("api-anthropic-key").value =
    localStorage.getItem("apiAnthropicKey") || "";
  document.getElementById("api-anthropic-model").value =
    localStorage.getItem("apiAnthropicModel") || "claude-3-5-sonnet-20241022";
  document.getElementById("api-groq-key").value =
    localStorage.getItem("apiGroqKey") || "";
  document.getElementById("api-groq-model").value =
    localStorage.getItem("apiGroqModel") || "llama3-8b-8192";
  document.getElementById("api-openrouter-key").value =
    localStorage.getItem("apiOpenRouterKey") || "";
  document.getElementById("api-openrouter-model").value =
    localStorage.getItem("apiOpenRouterModel") || "openrouter/free";
  document.getElementById("api-mistral-key").value =
    localStorage.getItem("apiMistralKey") || "";
  document.getElementById("api-mistral-model").value =
    localStorage.getItem("apiMistralModel") || "mistral-small-latest";
  updateAPIKeyCards();
}

window.isModelRecommended = function(model) {
  const modelId = model.model_id.toLowerCase();
  const recommendedIds = [
    "gpt-4o-mini", "gpt-4o", "gemini-3.5-flash", "claude-3-5-sonnet-latest", 
    "llama-3.3-70b-versatile", "mistral-large-latest", "o3-mini"
  ];
  return recommendedIds.some(id => modelId === id || modelId.includes(id));
};

window.getModelTierScore = function(model) {
  if (window.isModelRecommended(model)) return 10;
  if (model.supports_reasoning || model.model_id.includes("o1") || model.model_id.includes("o3") || model.model_id.includes("r1")) return 9;
  if (model.supports_vision || model.model_id.includes("vision") || model.model_id.includes("pixtral")) return 8;
  if (model.model_id.includes("mini") || model.model_id.includes("flash") || model.model_id.includes("instant") || model.model_id.includes("8b") || model.model_id.includes("haiku")) return 7;
  if (model.model_id.includes("code") || model.model_id.includes("codestral")) return 6;
  if (model.model_id.includes("gpt-3.5") || model.model_id.includes("legacy") || model.model_id.includes("claude-2")) return 4;
  return 5; // Default Chat
};

window.getModelLabel = function(model) {
  const displayName = model.display_name || model.model_id;
  const provider = (model.provider || "").toLowerCase();
  const badges = [];
  const score = window.getModelTierScore(model);
  
  if (score === 10) badges.push("Recommended");
  if (model.supports_reasoning || score === 9) badges.push("🧠 Reasoning");
  else if (model.supports_vision || score === 8) badges.push("👁 Vision");
  else if (score === 7) badges.push("⚡ Fast");
  else if (score === 6) badges.push("💻 Coding");
  
  if (score === 4) badges.push("⏳ Legacy");
  
  let emoji = "🤖";
  if (provider === "gemini" || provider === "google") emoji = "✨";
  if (provider === "anthropic") emoji = "🎭";
  if (provider === "groq") emoji = "⚡";
  if (provider === "openrouter") emoji = "🌐";
  if (provider === "mistral") emoji = "🌀";
  if (model.api_owner === "admin") emoji = "⚙️";
  
  const badgeText = badges.length > 0 ? ` (${badges.join(" - ")})` : "";
  return `${emoji} ${displayName}${badgeText}`;
};

window.fetchWithRetry = async function(url, options, retries = 3) {
  try {
    const response = await fetch(url, options);
    if ((response.status === 504 || response.status === 521) && retries > 0) {
      console.warn(`Server status ${response.status} on ${url}. Retrying... (${retries} left)`);
      await new Promise(resolve => setTimeout(resolve, 1000));
      return window.fetchWithRetry(url, options, retries - 1);
    }
    return response;
  } catch (error) {
    if (retries > 0) {
      console.warn(`Network failure on ${url}. Retrying... (${retries} left)`, error);
      await new Promise(resolve => setTimeout(resolve, 1000));
      return window.fetchWithRetry(url, options, retries - 1);
    }
    throw error;
  }
};

async function populateAPISettingsDropdowns() {
  try {
    const resp = await fetch("/api/settings/models");
    const data = await resp.json();
    if (!data.success || !Array.isArray(data.models) || data.models.length === 0) {
      return;
    }
    const models = data.models;
    const providerDropdowns = {
      openai: document.getElementById("api-openai-model"),
      gemini: document.getElementById("api-gemini-model"),
      google: document.getElementById("api-gemini-model"),
      anthropic: document.getElementById("api-anthropic-model"),
      groq: document.getElementById("api-groq-model"),
      openrouter: document.getElementById("api-openrouter-model"),
      mistral: document.getElementById("api-mistral-model")
    };
    
    // Clear dynamic dropdowns first
    Object.values(providerDropdowns).forEach(select => {
      if (select) select.innerHTML = "";
    });
    
    // Group & Sort models by provider
    const grouped = {};
    models.forEach(model => {
      let p = (model.provider || "").toLowerCase();
      if (!grouped[p]) grouped[p] = [];
      grouped[p].push(model);
    });
    
    // Populate each dropdown
    Object.keys(providerDropdowns).forEach(p => {
      const select = providerDropdowns[p];
      if (!select) return;
      
      const providerModels = grouped[p] || [];
      // Sort providerModels
      providerModels.sort((a, b) => {
        const scoreA = window.getModelTierScore(a);
        const scoreB = window.getModelTierScore(b);
        if (scoreA !== scoreB) {
          return scoreB - scoreA;
        }
        return (a.display_name || a.model_id).localeCompare(b.display_name || b.model_id);
      });
      
      providerModels.forEach(model => {
        const opt = document.createElement("option");
        opt.value = model.model_id;
        opt.textContent = window.getModelLabel(model);
        select.appendChild(opt);
      });
    });
  } catch (err) {
    console.error("Error populating API settings dropdowns:", err);
  }
}

function showAPISettings() {
  populateAPISettingsDropdowns().then(() => {
    populateAPISettings();
    apiSettingsOverlay.classList.add("show");
    apiSettingsVisible = true;
  });
}

async function initAPISettings() {
  if (!apiSettingsBtn) return;

  await syncAPISettingsFromServer();

  // Show settings
  apiSettingsBtn.addEventListener("click", () => {
    populateAPISettings();
    showAPISettings();
  });

  // Toggle password eye visibility for all key fields
  document
    .querySelectorAll("#api-settings .toggle-password-btn")
    .forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const input = btn.previousElementSibling;
        const icon = btn.querySelector("i");
        if (input.type === "password") {
          input.type = "text";
          icon.className = "far fa-eye-slash";
        } else {
          input.type = "password";
          icon.className = "far fa-eye";
        }
      });
    });

  // Update visibility of provider cards on provider select change
  apiProviderSelect.addEventListener("change", updateAPIKeyCards);

  // Close / Cancel click
  document
    .getElementById("api-settings-close")
    .addEventListener("click", hideAPISettings);
  apiSettingsCancel.addEventListener("click", hideAPISettings);

  // Save button
  apiSettingsSave.addEventListener("click", async () => {
    const provider = apiProviderSelect.value;
    const openaiKey = apiOpenAIKeyInput.value.trim();
    const openaiModel = apiOpenAIModelSelect.value;
    const geminiKey = apiGeminiKeyInput.value.trim();
    const geminiModel = apiGeminiModelSelect.value;

    const anthropicKey = document
      .getElementById("api-anthropic-key")
      .value.trim();
    const anthropicModel = document.getElementById("api-anthropic-model").value;
    const groqKey = document.getElementById("api-groq-key").value.trim();
    const groqModel = document.getElementById("api-groq-model").value;
    const openrouterKey = document
      .getElementById("api-openrouter-key")
      .value.trim();
    const openrouterModel = document.getElementById(
      "api-openrouter-model",
    ).value;
    const mistralKey = document.getElementById("api-mistral-key").value.trim();
    const mistralModel = document.getElementById("api-mistral-model").value;

    // Simple key format validations
    if (provider === "openai" && openaiKey && !openaiKey.startsWith("sk-")) {
      showToast("Warning: OpenAI key usually starts with sk-", "warning");
    }
    if (provider === "gemini" && geminiKey && !geminiKey.startsWith("AIzaSy")) {
      showToast("Warning: Gemini key usually starts with AIzaSy", "warning");
    }

    localStorage.setItem("apiProvider", provider);
    localStorage.setItem("apiOpenAIKey", openaiKey);
    localStorage.setItem("apiOpenAIModel", openaiModel);
    localStorage.setItem("apiGeminiKey", geminiKey);
    localStorage.setItem("apiGeminiModel", geminiModel);

    localStorage.setItem("apiAnthropicKey", anthropicKey);
    localStorage.setItem("apiAnthropicModel", anthropicModel);
    localStorage.setItem("apiGroqKey", groqKey);
    localStorage.setItem("apiGroqModel", groqModel);
    localStorage.setItem("apiOpenRouterKey", openrouterKey);
    localStorage.setItem("apiOpenRouterModel", openrouterModel);
    localStorage.setItem("apiMistralKey", mistralKey);
    localStorage.setItem("apiMistralModel", mistralModel);

    // Sync the CURRENTLY selected provider/key to the backend database
    // (read directly from modal, NOT from the chat dropdown via getBYOKConfig)
    const keyMap = {
      openai: openaiKey,
      gemini: geminiKey,
      anthropic: anthropicKey,
      groq: groqKey,
      openrouter: openrouterKey,
      mistral: mistralKey,
    };
    const modelMap = {
      openai: openaiModel,
      gemini: geminiModel,
      anthropic: anthropicModel,
      groq: groqModel,
      openrouter: openrouterModel,
      mistral: mistralModel,
    };
    const activeKey = keyMap[provider] || "";
    const activeModel = modelMap[provider] || "";
    if (provider && provider !== "default" && activeKey) {
      // Also update the chat model selector so getBYOKConfig() picks it up
      const chatboxModelSelect = document.getElementById(
        "chatbox-model-select",
      );
      const newModelVal = `${provider}:${activeModel}`;
      if (chatboxModelSelect) {
        const optionExists = chatboxModelSelect.querySelector(
          `option[value="${CSS.escape(newModelVal)}"]`,
        );
        if (optionExists) {
          chatboxModelSelect.value = newModelVal;
        }
      }
      localStorage.setItem("chatboxModel", newModelVal);
      try {
        await fetch("/api/settings/sync", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            api_provider: provider,
            api_key: activeKey,
            api_model: activeModel,
          }),
        });
      } catch (e) {
        console.error("Failed to sync settings to backend:", e);
      }
      // Auto-fetch live models so the model selector populates immediately
      try {
        await fetch("/api/fetch-models", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ provider, api_key: activeKey }),
        });
      } catch (e) {
        console.error("Failed to auto-fetch models:", e);
      }
    }
    hideAPISettings();
    showToast("API Key settings saved successfully!");
    // Notify model-selector badge to refresh
    document.dispatchEvent(new CustomEvent("apikeysSaved"));
  });

  // Reset button
  apiSettingsReset.addEventListener("click", () => {
    const keysToRemove = [
      "apiProvider",
      "apiOpenAIKey",
      "apiOpenAIModel",
      "apiGeminiKey",
      "apiGeminiModel",
      "apiAnthropicKey",
      "apiAnthropicModel",
      "apiGroqKey",
      "apiGroqModel",
      "apiOpenRouterKey",
      "apiOpenRouterModel",
      "apiMistralKey",
      "apiMistralModel",
    ];
    keysToRemove.forEach((k) => localStorage.removeItem(k));

    apiProviderSelect.value = "default";
    apiOpenAIKeyInput.value = "";
    apiOpenAIModelSelect.value = "gpt-4o-mini";
    apiGeminiKeyInput.value = "";
    apiGeminiModelSelect.value = "gemini-1.5-flash";

    document.getElementById("api-anthropic-key").value = "";
    document.getElementById("api-anthropic-model").value =
      "claude-3-5-sonnet-20241022";
    document.getElementById("api-groq-key").value = "";
    document.getElementById("api-groq-model").value = "llama3-8b-8192";
    document.getElementById("api-openrouter-key").value = "";
    document.getElementById("api-openrouter-model").value = "openrouter/free";
    document.getElementById("api-mistral-key").value = "";
    document.getElementById("api-mistral-model").value = "mistral-small-latest";

    updateAPIKeyCards();
    // Clear backend database too
    try {
      fetch("/api/settings/sync", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          api_provider: "",
          api_key: "",
          api_model: "",
        }),
      });
    } catch (e) {
      console.error("Failed to clear backend settings:", e);
    }
    hideAPISettings();
    showToast("API configurations reset to Server Default", "info");
    document.dispatchEvent(new CustomEvent("apikeysSaved"));
  });
}

function updateAPIKeyCards() {
  const provider = apiProviderSelect.value;
  openaiKeyCard.style.display = provider === "openai" ? "block" : "none";
  geminiKeyCard.style.display = provider === "gemini" ? "block" : "none";
  document.getElementById("anthropic-key-card").style.display =
    provider === "anthropic" ? "block" : "none";
  document.getElementById("groq-key-card").style.display =
    provider === "groq" ? "block" : "none";
  document.getElementById("openrouter-key-card").style.display =
    provider === "openrouter" ? "block" : "none";
  document.getElementById("mistral-key-card").style.display =
    provider === "mistral" ? "block" : "none";
}

function hideAPISettings() {
  apiSettingsOverlay.classList.remove("show");
  apiSettingsVisible = false;
}

// ── Toolbar menu & model-selector orchestration ────────────────
document.addEventListener("DOMContentLoaded", () => {
  let loadDynamicModels;
  const toolbarMenuBtn = document.getElementById("toolbar-menu-btn");
  const toolbarDropdown = document.getElementById("toolbar-dropdown");
  const chatboxModelSelect = document.getElementById("chatbox-model-select");
  const modelKeyBadge = document.getElementById("model-key-badge");

  function updateModelKeyBadge() {
    if (!modelKeyBadge || !chatboxModelSelect) return;

    const val = chatboxModelSelect.value;
    const provider = val ? val.split(":")[0] : "";

    const keyMap = {
      openai: "apiOpenAIKey",
      gemini: "apiGeminiKey",
      google: "apiGeminiKey",
      anthropic: "apiAnthropicKey",
      groq: "apiGroqKey",
      openrouter: "apiOpenRouterKey",
      mistral: "apiMistralKey",
    };

    const storageKey = keyMap[provider];
    const savedKey = storageKey
      ? (localStorage.getItem(storageKey) || "").trim()
      : "";

    if (savedKey) {
      modelKeyBadge.className = "model-key-badge model-key-badge--ok";
      modelKeyBadge.title = `✓ API key configured for ${provider}`;
    } else {
      modelKeyBadge.className = "model-key-badge model-key-badge--warn";
      modelKeyBadge.title = `⚠ No API key for ${provider} — open ☰ → API Settings`;
    }
  }

  if (chatboxModelSelect) {
    // Restore saved model — fall back to first option if stale value
    const stored = localStorage.getItem("chatboxModel") || "";
    const optionExists =
      stored && chatboxModelSelect.querySelector(`option[value="${stored}"]`);
    chatboxModelSelect.value = optionExists
      ? stored
      : chatboxModelSelect.options[0].value;
    // Persist the resolved selection
    localStorage.setItem("chatboxModel", chatboxModelSelect.value);
    updateModelKeyBadge();

    chatboxModelSelect.addEventListener("change", () => {
      localStorage.setItem("chatboxModel", chatboxModelSelect.value);
      updateModelKeyBadge();

      const val = chatboxModelSelect.value;
      const provider = val.split(":")[0];
      const model = val.split(":").slice(1).join(":");
      const keyMap = {
        openai: "apiOpenAIKey",
        gemini: "apiGeminiKey",
        google: "apiGeminiKey",
        anthropic: "apiAnthropicKey",
        groq: "apiGroqKey",
        openrouter: "apiOpenRouterKey",
        mistral: "apiMistralKey",
      };
      const hasKey = !!(
        localStorage.getItem(keyMap[provider] || "") || ""
      ).trim();
      if (hasKey) {
        showToast(`Model → ${model}`, "success");
      } else {
        showToast(`⚠ No ${provider} key — open ☰ → API Settings`, "warning");
      }
      syncActiveSettingsToBackend();
    });
  }

  // Re-check badge whenever API Settings saves new keys
  document.addEventListener("apikeysSaved", () => {
    updateModelKeyBadge();
    if (typeof loadDynamicModels === "function") {
      loadDynamicModels();
    }
  });

  // ── CUSTOM MODEL SEARCHER CONTROLLER ──────────────────────────
  const modelSearcher = document.getElementById("custom-model-searcher");
  const modelPillTrigger = document.getElementById("model-pill-trigger");
  const selectedModelDisplay = document.getElementById(
    "selected-model-display",
  );
  const modelSearcherDropdown = document.getElementById(
    "model-searcher-dropdown",
  );
  const modelSearcherInput = document.getElementById("model-searcher-input");
  const modelSearcherClear = document.getElementById("model-searcher-clear");
  const modelSearcherList = document.getElementById("model-searcher-list");
  const fetchLiveModelsBtn = document.getElementById("fetch-live-models-btn");
  const addCustomModelBtn = document.getElementById("add-custom-model-btn");

  if (modelSearcher && chatboxModelSelect) {
    // 1. Sync displaying selected model name
    function syncSelectedModelDisplay() {
      const selectedOpt =
        chatboxModelSelect.options[chatboxModelSelect.selectedIndex];
      if (selectedOpt) {
        const val = chatboxModelSelect.value || "";
        const provider = val.split(":")[0] || "";
        modelPillTrigger.dataset.provider = provider;

        const cleanText = selectedOpt.textContent
          .replace(/^[\p{Emoji}\p{Extended_Pictographic}]\s*/u, "")
          .trim();
        const logoHtml = getProviderLogoHtml(provider, 14);

        selectedModelDisplay.innerHTML = `${logoHtml} <span style="margin-left: 6px;">${cleanText}</span>`;
      }
    }

    function renderModelOptionItem(model, isActive) {
      const itemDiv = document.createElement("div");
      itemDiv.className = `model-searcher-item ${isActive ? "active" : ""}`;
      const provider = (model.provider || "").toLowerCase();
      const label = model.display_name || model.model_id || "Unknown model";
      const logoHtml = getProviderLogoHtml(provider, 14);
      const subtitle = model.context_window
        ? `Context ${model.context_window}`
        : "Dynamic model";
      const badgeBits = [];
      if (model.supports_reasoning) badgeBits.push("🧠 Reasoning");
      if (model.supports_vision) badgeBits.push("👁 Vision");
      if (model.supports_streaming) badgeBits.push("⚡ Fast");
      if (model.supports_function_calling) badgeBits.push("💻 Coding");
      if (model.supports_audio) badgeBits.push("🎵 Audio");
      if (model.supports_image_generation) badgeBits.push("🖼 Image");
      const badges = badgeBits.slice(0, 3).join(" • ");

      const textSpan = document.createElement("span");
      textSpan.style.display = "flex";
      textSpan.style.flexDirection = "column";
      textSpan.style.alignItems = "flex-start";
      textSpan.style.gap = "2px";
      textSpan.innerHTML = `<span style="display:flex; align-items:center; gap:8px;">${logoHtml} <span>${label}</span></span><span style="font-size:11px; color:var(--muted);">${subtitle}${badges ? ` • ${badges}` : ""}</span>`;
      itemDiv.appendChild(textSpan);

      const providerSpan = document.createElement("span");
      providerSpan.className = "item-provider";
      providerSpan.textContent = provider;
      itemDiv.appendChild(providerSpan);

      itemDiv.addEventListener("click", () => {
        const optValue = `${provider}:${model.model_id}`;
        chatboxModelSelect.value = optValue;
        chatboxModelSelect.dispatchEvent(new Event("change"));
        syncSelectedModelDisplay();
        closeDropdown();
      });
      return itemDiv;
    }

    function buildModelSearcherList(filterText = "") {
      modelSearcherList.innerHTML = "";
      const query = filterText.toLowerCase().trim();
      let totalVisible = 0;
      const providerGroups = {};
      const options = Array.from(chatboxModelSelect.querySelectorAll("option"));
      options.forEach((opt) => {
        const value = opt.value || "";
        const text = opt.textContent || "";
        if (!value) return;
        if (
          query &&
          !text.toLowerCase().includes(query) &&
          !value.toLowerCase().includes(query)
        )
          return;
        const provider = value.split(":")[0] || "custom";
        if (!providerGroups[provider]) providerGroups[provider] = [];
        providerGroups[provider].push({ opt, value, text });
      });

      Object.entries(providerGroups)
        .sort(([a], [b]) => a.localeCompare(b))
        .forEach(([provider, items]) => {
          const titleDiv = document.createElement("div");
          titleDiv.className = "model-searcher-group-title";
          titleDiv.textContent = provider.toUpperCase();
          modelSearcherList.appendChild(titleDiv);
          items.forEach((item) => {
            const itemDiv = document.createElement("div");
            const isActive = chatboxModelSelect.value === item.value;
            itemDiv.className = `model-searcher-item ${isActive ? "active" : ""}`;
            const logoHtml = getProviderLogoHtml(provider, 14);
            const cleanText = item.text
              .replace(/^[\p{Emoji}\p{Extended_Pictographic}]\s*/u, "")
              .trim();
            const textSpan = document.createElement("span");
            textSpan.style.display = "flex";
            textSpan.style.alignItems = "center";
            textSpan.style.gap = "8px";
            textSpan.innerHTML = `${logoHtml} <span>${cleanText}</span>`;
            itemDiv.appendChild(textSpan);
            const providerSpan = document.createElement("span");
            providerSpan.className = "item-provider";
            providerSpan.textContent = provider;
            itemDiv.appendChild(providerSpan);
            itemDiv.addEventListener("click", () => {
              chatboxModelSelect.value = item.value;
              chatboxModelSelect.dispatchEvent(new Event("change"));
              syncSelectedModelDisplay();
              closeDropdown();
            });
            modelSearcherList.appendChild(itemDiv);
            totalVisible++;
          });
        });

      if (query.includes(":") && query.split(":")[1].length > 1) {
        addCustomModelBtn.style.display = "flex";
        addCustomModelBtn.title = `Add "${query}" as a custom model option`;
      } else {
        addCustomModelBtn.style.display = "none";
      }

      if (totalVisible === 0) {
        const emptyDiv = document.createElement("div");
        emptyDiv.style.padding = "20px 12px";
        emptyDiv.style.textAlign = "center";
        emptyDiv.style.color = "var(--muted)";
        emptyDiv.style.fontSize = "12px";
        emptyDiv.textContent =
          'No matching models. Type "provider:model" to add a custom one!';
        modelSearcherList.appendChild(emptyDiv);
      }
    }

    // Toggle dropdown
    function toggleDropdown(e) {
      if (e) e.stopPropagation();
      const isOpen = modelSearcherDropdown.classList.contains("show");
      if (isOpen) {
        closeDropdown();
      } else {
        document
          .querySelectorAll(".toolbar-dropdown, .bubble__actions-dropdown")
          .forEach((d) => d.classList.remove("show"));
        modelSearcherDropdown.classList.add("show");
        modelPillTrigger.querySelector("i").className = "fas fa-chevron-down";
        modelSearcherInput.focus();
        buildModelSearcherList(modelSearcherInput.value);
      }
    }

    function closeDropdown() {
      modelSearcherDropdown.classList.remove("show");
      modelPillTrigger.querySelector("i").className = "fas fa-chevron-up";
    }

    // Close on click outside
    document.addEventListener("click", (e) => {
      if (!modelSearcher.contains(e.target)) {
        closeDropdown();
      }
    });

    modelPillTrigger.addEventListener("click", toggleDropdown);

    // Filter input events
    modelSearcherInput.addEventListener("input", (e) => {
      const val = e.target.value;
      modelSearcherClear.style.display = val ? "flex" : "none";
      buildModelSearcherList(val);
    });

    modelSearcherClear.addEventListener("click", () => {
      modelSearcherInput.value = "";
      modelSearcherClear.style.display = "none";
      buildModelSearcherList("");
      modelSearcherInput.focus();
    });

    // Add Custom Model Registration
    addCustomModelBtn.addEventListener("click", () => {
      const customString = modelSearcherInput.value.trim();
      const parts = customString.split(":");
      if (parts.length < 2 || !parts[0] || !parts[1]) {
        showToast(
          'Please type custom model as "provider:name" (e.g. openai:my-gpt)',
          "warning",
        );
        return;
      }

      const provider = parts[0].toLowerCase();
      const modelName = parts.slice(1).join(":");

      // Create dynamic option
      const newOpt = document.createElement("option");
      newOpt.value = customString;
      newOpt.textContent = `⚙️ Custom: ${modelName}`;

      // Find or create "Custom Models" optgroup in native select
      let customGroup = Array.from(
        chatboxModelSelect.querySelectorAll("optgroup"),
      ).find((g) => g.label.includes("Custom Registered"));
      if (!customGroup) {
        customGroup = document.createElement("optgroup");
        customGroup.label = "⚙️ Custom Registered Models";
        chatboxModelSelect.appendChild(customGroup);
      }

      // Check if already exists
      const existing = chatboxModelSelect.querySelector(
        `option[value="${customString}"]`,
      );
      if (existing) {
        chatboxModelSelect.value = customString;
      } else {
        customGroup.appendChild(newOpt);
        chatboxModelSelect.value = customString;
      }

      chatboxModelSelect.dispatchEvent(new Event("change"));
      syncSelectedModelDisplay();
      closeDropdown();
      showToast(`Registered custom model: ${modelName}`, "success");

      // Reset input
      modelSearcherInput.value = "";
      modelSearcherClear.style.display = "none";
    });

    // Model recommendation, tier, and label helpers are defined globally above

    loadDynamicModels = async function() {
      try {
        const resp = await fetch("/api/settings/models");
        const data = await resp.json();
        if (!data.success || !Array.isArray(data.models) || data.models.length === 0) {
          console.warn("No models returned from API, using static options");
          return;
        }
        
        const models = data.models;
        const groups = {
          openai: { label: "OpenAI - reasoning & flagship", element: null, models: [] },
          gemini: { label: "Google AI Studio (Gemini & Gemma)", element: null, models: [] },
          google: { label: "Google AI Studio (Gemini & Gemma)", element: null, models: [] },
          anthropic: { label: "Anthropic Claude - Smart & Coding", element: null, models: [] },
          groq: { label: "⚡ Groq — High Speed LPU Inference", element: null, models: [] },
          openrouter: { label: "🌐 OpenRouter — Global Aggregator", element: null, models: [] },
          mistral: { label: "🌀 Mistral AI — Developer Platform", element: null, models: [] },
          custom: { label: "⚙️ Custom Registered Models", element: null, models: [] }
        };
        
        models.forEach(model => {
          let p = (model.provider || "").toLowerCase();
          if (model.api_owner === "admin" || !groups[p]) {
            p = "custom";
          }
          if (p === "google") p = "gemini";
          groups[p].models.push(model);
        });
        
        const currentVal = chatboxModelSelect.value;
        chatboxModelSelect.innerHTML = "";
        
        const groupKeys = ["openai", "gemini", "anthropic", "groq", "openrouter", "mistral", "custom"];
        groupKeys.forEach(k => {
          const groupInfo = groups[k];
          if (groupInfo.models.length === 0) return;
          
          groupInfo.models.sort((a, b) => {
            const scoreA = getModelTierScore(a);
            const scoreB = getModelTierScore(b);
            if (scoreA !== scoreB) {
              return scoreB - scoreA;
            }
            return (a.display_name || a.model_id).localeCompare(b.display_name || b.model_id);
          });
          
          const optgroup = document.createElement("optgroup");
          optgroup.label = groupInfo.label;
          
          groupInfo.models.forEach(model => {
            const opt = document.createElement("option");
            opt.value = `${model.provider}:${model.model_id}`;
            opt.textContent = getModelLabel(model);
            optgroup.appendChild(opt);
          });
          
          chatboxModelSelect.appendChild(optgroup);
        });
        
        if (currentVal && chatboxModelSelect.querySelector(`option[value="${currentVal}"]`)) {
          chatboxModelSelect.value = currentVal;
        } else {
          const stored = localStorage.getItem("chatboxModel");
          if (stored && chatboxModelSelect.querySelector(`option[value="${stored}"]`)) {
            chatboxModelSelect.value = stored;
          } else if (chatboxModelSelect.options.length > 0) {
            chatboxModelSelect.value = chatboxModelSelect.options[0].value;
          }
        }
        
        localStorage.setItem("chatboxModel", chatboxModelSelect.value);
        syncSelectedModelDisplay();
        buildModelSearcherList(modelSearcherInput.value);
      } catch (err) {
        console.warn("Unable to load stored provider models dynamically:", err);
      }
    };

    // Fetch Live Models via Backend Proxy API
    fetchLiveModelsBtn.addEventListener("click", async () => {
      const activeOpt =
        chatboxModelSelect.options[chatboxModelSelect.selectedIndex];
      if (!activeOpt) return;
      const provider = chatboxModelSelect.value.split(":")[0];

      const keyMap = {
        openai: "apiOpenAIKey",
        gemini: "apiGeminiKey",
        google: "apiGeminiKey",
        anthropic: "apiAnthropicKey",
        groq: "apiGroqKey",
        openrouter: "apiOpenRouterKey",
        mistral: "apiMistralKey",
      };

      const storageKey = keyMap[provider];
      const savedKey = storageKey
        ? (localStorage.getItem(storageKey) || "").trim()
        : "";

      if (!savedKey) {
        showToast(
          `No API key saved for ${provider}! Click ☰ → API Settings to configure.`,
          "warning",
        );
        return;
      }

      fetchLiveModelsBtn.disabled = true;
      fetchLiveModelsBtn.querySelector("span").textContent = "Fetching...";
      fetchLiveModelsBtn.querySelector("i").className =
        "fas fa-spinner fa-spin";

      try {
        const resp = await fetch("/api/fetch-models", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ provider, api_key: savedKey }),
        });

        const result = await resp.json();
        if (result.error) {
          showToast(`Fetch error: ${result.error}`, "error");
        } else if (result.models && result.models.length > 0) {
          await loadDynamicModels(provider);
          showToast(
            `Loaded ${result.models.length} live models from ${provider}!`,
            "success",
          );
        } else {
          await loadDynamicModels(provider);
          showToast(
            "No fresh models returned, using the last cached list.",
            "warning",
          );
        }
      } catch (err) {
        showToast(`API Connection failed: ${err.message}`, "error");
      } finally {
        fetchLiveModelsBtn.disabled = false;
        fetchLiveModelsBtn.querySelector("span").textContent =
          "Fetch Live Models";
        fetchLiveModelsBtn.querySelector("i").className = "fas fa-sync-alt";
      }
    });

    setTimeout(() => {
      syncSelectedModelDisplay();
      chatboxModelSelect.addEventListener("change", syncSelectedModelDisplay);
      loadDynamicModels();
    }, 100);
  }

  // ── Toolbar dropdown ──────────────────────────────────────────
  if (toolbarMenuBtn && toolbarDropdown) {
    toolbarMenuBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      document
        .querySelectorAll(".bubble__actions-dropdown")
        .forEach((d) => d.classList.remove("show"));
      // Close profile dropdown
      const profileDropdown = document.getElementById("profile-dropdown");
      if (profileDropdown) profileDropdown.style.display = "none";
      toolbarDropdown.classList.toggle("show");
    });

    toolbarDropdown.querySelectorAll(".btn").forEach((btn) => {
      btn.addEventListener("click", () =>
        toolbarDropdown.classList.remove("show"),
      );
    });

    document.addEventListener("click", (e) => {
      if (
        !toolbarDropdown.contains(e.target) &&
        !toolbarMenuBtn.contains(e.target)
      ) {
        toolbarDropdown.classList.remove("show");
      }
    });
  }

  // ── Profile dropdown & Account Modal ──────────────────────────
  const profileMenuBtn = document.getElementById("profile-menu-btn");
  const profileDropdown = document.getElementById("profile-dropdown");
  const profileAccountBtn = document.getElementById("profile-account-btn");

  if (profileMenuBtn && profileDropdown) {
    profileMenuBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      document
        .querySelectorAll(".bubble__actions-dropdown")
        .forEach((d) => d.classList.remove("show"));
      if (toolbarDropdown) toolbarDropdown.classList.remove("show");

      const isOpen = profileDropdown.style.display === "flex";
      profileDropdown.style.display = isOpen ? "none" : "flex";
    });

    profileDropdown.querySelectorAll(".btn, a").forEach((item) => {
      item.addEventListener("click", () => {
        profileDropdown.style.display = "none";
      });
    });

    document.addEventListener("click", (e) => {
      if (
        !profileDropdown.contains(e.target) &&
        !profileMenuBtn.contains(e.target)
      ) {
        profileDropdown.style.display = "none";
      }
    });
  }

  if (profileAccountBtn) {
    profileAccountBtn.addEventListener("click", showAccountDetailsModal);
  }

  const navProfileBtn = document.getElementById("nav-profile-btn");
  if (navProfileBtn) {
    navProfileBtn.addEventListener("click", showAccountDetailsModal);
  }

  // Handle Account Modal
  async function showAccountDetailsModal() {
    let googleLinked = true; // Connected by default!
    let googleEmail = "connected@gmail.com";

    try {
      const resp = await fetch("/api/accounts/linked");
      if (resp.ok) {
        const data = await resp.json();
        const googleLink = (data.linked || []).find(
          (l) => l.provider === "google",
        );
        if (googleLink) {
          googleEmail = googleLink.account_id;
        }
      }
    } catch (e) {
      console.warn("Failed to load linked accounts:", e);
    }

    const username = window.currentUser || "Guest";
    const displayName = window.currentUserDisplayName || "Not Set";
    const avatarChar = username.charAt(0).toUpperCase();

    const contentHtml = `
      <div style="text-align: center; margin-bottom: 20px;">
        <div style="width: 72px; height: 72px; border-radius: 50%; background: linear-gradient(135deg, var(--mint) 0%, rgba(64, 224, 208, 0.8) 100%); display: flex; align-items: center; justify-content: center; font-size: 2.2em; font-weight: 700; color: #1a1a1a; margin: 0 auto 12px auto; box-shadow: 0 4px 14px rgba(55, 230, 181, 0.3);">
          ${avatarChar}
        </div>
        <h3 style="margin: 0; font-size: 1.4em; color: var(--fg); font-weight: 600;">${username}</h3>
        <p style="margin: 4px 0 0 0; font-size: 0.9em; color: var(--muted);">Display Name: <strong style="color: var(--mint);">${displayName}</strong></p>
      </div>

      <div class="glass" style="padding: 16px; border-radius: var(--radius-md); border: 1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.02); margin-bottom: 16px;">
        <h4 style="margin: 0 0 12px 0; font-size: 1em; font-weight: 600; color: var(--fg); display: flex; align-items: center; gap: 8px;">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="16" height="16" style="vertical-align: middle; flex-shrink: 0;"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22c-.22-.67-.35-1.37-.35-2.09l.81 1.46z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/></svg> Google Integration
        </h4>

        ${
          googleLinked
            ? `
          <div style="display: flex; align-items: center; justify-content: space-between; gap: 12px;">
            <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1;">
              <span style="display: inline-block; font-size: 0.8em; padding: 2px 8px; border-radius: 12px; background: rgba(55,230,181,0.15); color: var(--mint); font-weight: 500;">Connected</span>
            </div>
            <button id="modal-unlink-google-btn" class="btn btn--danger btn--sm" style="padding: 6px 12px; font-size: 0.85em; display: flex; align-items: center; gap: 6px; flex-shrink: 0;">
              <i class="fas fa-unlink"></i> Disconnect
            </button>
          </div>
        `
            : `
          <div style="display: flex; align-items: center; justify-content: space-between; gap: 12px;">
            <div style="font-size: 0.9em; color: var(--muted); flex: 1;">Link your Google account for single sign-on.</div>
            <button id="modal-link-google-btn" class="btn btn--mint btn--sm" style="padding: 6px 12px; font-size: 0.85em; display: flex; align-items: center; gap: 6px; flex-shrink: 0;">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="14" height="14" style="vertical-align: middle; flex-shrink: 0;"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22c-.22-.67-.35-1.37-.35-2.09l.81 1.46z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/></svg> Connect
            </button>
          </div>
        `
        }
      </div>

      <div style="display: flex; justify-content: space-between; gap: 10px;">
        <button id="modal-api-shortcut-btn" class="btn btn--ghost btn--sm" style="flex: 1; display: flex; align-items: center; justify-content: center; gap: 6px; border: 1px solid rgba(255,255,255,0.1); background: rgba(255,255,255,0.03);">
          <i class="fas fa-key"></i> API Settings
        </button>
        <button id="modal-profile-shortcut-btn" class="btn btn--ghost btn--sm" style="flex: 1; display: flex; align-items: center; justify-content: center; gap: 6px; border: 1px solid rgba(255,255,255,0.1); background: rgba(255,255,255,0.03);">
          <i class="fas fa-user-edit"></i> Profile
        </button>
      </div>

      <div style="display: flex; justify-content: space-between; gap: 10px; margin-top: 10px;">
        <button id="modal-backup-data-btn" class="btn btn--ghost btn--sm" style="flex: 1; display: flex; align-items: center; justify-content: center; gap: 6px; border: 1px solid rgba(255,255,255,0.1); background: rgba(255,255,255,0.03);">
          <i class="fas fa-download"></i> Backup My Data
        </button>
        <button id="modal-delete-account-btn" class="btn btn--danger btn--sm" style="flex: 1; display: flex; align-items: center; justify-content: center; gap: 6px;">
          <i class="fas fa-trash-alt"></i> Delete My Account
        </button>
      </div>
    `;

    showModal("Account Profile", contentHtml, []);

    const closeBtn = document.getElementById("modal-close");
    if (closeBtn) closeBtn.style.display = "none";

    // Attach shortcut action listeners inside modal
    const linkBtn = document.getElementById("modal-link-google-btn");
    if (linkBtn) {
      linkBtn.addEventListener("click", () => {
        const width = 500;
        const height = 650;
        const left = window.screen.width / 2 - width / 2;
        const top = window.screen.height / 2 - height / 2;

        const popup = window.open(
          "/api/google/auth",
          "GoogleLinkPopup",
          `width=${width},height=${height},left=${left},top=${top},status=no,resizable=yes,scrollbars=yes`,
        );

        const handleLinkMessage = (event) => {
          if (event.data && event.data.type === "google_auth_success") {
            window.removeEventListener("message", handleLinkMessage);
            showToast("Google account connected successfully!");
            hideModal();
            setTimeout(showAccountDetailsModal, 300);
          }
        };

        window.addEventListener("message", handleLinkMessage);
      });
    }

    const unlinkBtn = document.getElementById("modal-unlink-google-btn");
    if (unlinkBtn) {
      unlinkBtn.addEventListener("click", async () => {
        try {
          const ures = await fetch("/api/accounts/unlink", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ provider: "google" }),
          });
          if (ures.ok) {
            showToast("Google account unlinked successfully");
            hideModal();
            setTimeout(showAccountDetailsModal, 300);
          } else {
            showToast("Failed to unlink account", "error");
          }
        } catch (err) {
          showToast("Failed to unlink account", "error");
        }
      });
    }

    const apiBtn = document.getElementById("modal-api-shortcut-btn");
    if (apiBtn) {
      apiBtn.addEventListener("click", () => {
        hideModal();
        showAPISettings();
      });
    }

    const profileBtn = document.getElementById("modal-profile-shortcut-btn");
    if (profileBtn) {
      profileBtn.addEventListener("click", () => {
        hideModal();
        showInputModal(
          "Edit Display Name",
          "Enter new display name...",
          async (newName) => {
            try {
              const res = await fetch("/api/accounts/profile", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ display_name: newName }),
              });
              if (res.ok) {
                window.currentUserDisplayName = newName;
                showToast("Display name updated successfully!");
              } else {
                showToast("Failed to update display name", "error");
              }
            } catch (err) {
              showToast("Failed to update display name", "error");
            }
            setTimeout(showAccountDetailsModal, 300);
          },
          {
            defaultValue: window.currentUserDisplayName || "",
            maxLength: 50,
            required: true,
            label: "New Display Name",
          },
        );
      });
    }

    const backupBtn = document.getElementById("modal-backup-data-btn");
    if (backupBtn) {
      backupBtn.addEventListener("click", () => {
        window.location.href = "/api/user/backup";
      });
    }

    const deleteBtn = document.getElementById("modal-delete-account-btn");
    if (deleteBtn) {
      deleteBtn.addEventListener("click", () => {
        hideModal();
        showConfirmModal(
          "Delete Account",
          "Are you absolutely sure you want to permanently delete your account? This action is irreversible and will erase all your chats, configurations, settings, and authenticators.",
          async () => {
            try {
              const res = await fetch("/api/user/delete", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
              });
              if (res.ok) {
                showToast("Your account has been deleted.", "success");
                setTimeout(() => {
                  window.location.href = "/login";
                }, 1000);
              } else {
                const data = await res.json();
                showToast(data.error || "Failed to delete account.", "error");
              }
            } catch (err) {
              showToast("An error occurred during deletion.", "error");
            }
          },
          {
            danger: true,
            confirmText: "Delete Permanently",
          },
        );
      });
    }
  }
});

// Sidebar Toggle Logic
const button = document.querySelector("#sidebarToggleBtn");
const sidebar =
  document.querySelector(".admin-sidebar") ||
  document.querySelector(".sidebar");

if (button && sidebar) {
  button.addEventListener("click", () => {
    sidebar.classList.toggle("collapsed");

    // Smoothly rotate the chevron icon
    const icon = button.querySelector("i");
    if (icon) {
      icon.style.transform = sidebar.classList.contains("collapsed")
        ? "rotate(180deg)"
        : "rotate(0deg)";
    }
  });
}

function renderDeadlineCard(task, parentBubble) {
  if (!task || !parentBubble) return;

  const card = document.createElement("div");
  card.className = "card glass deadline-card";
  card.style.margin = "10px 0 15px 40px";
  card.style.padding = "16px";
  card.style.borderRadius = "12px";
  card.style.border = "1px solid rgba(64, 224, 208, 0.3)";
  card.style.background = "rgba(255, 255, 255, 0.03)";
  card.style.backdropFilter = "blur(10px)";
  card.style.boxShadow = "0 8px 32px 0 rgba(0, 0, 0, 0.2)";
  card.style.transition = "all 0.3s ease";
  card.style.animation = "fadeIn 0.3s ease";
  card.style.maxWidth = "500px";

  // Check if it contains subtasks
  const hasSubtasks = task.subtasks && task.subtasks.length > 0;

  if (hasSubtasks) {
    // 1. RENDER EXPANDED SUBTASK BREAKDOWN CARD
    card.innerHTML = `
      <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; cursor: pointer;" class="deadline-card-header">
        <span style="font-weight: 700; color: var(--mint); display: flex; align-items: center; gap: 8px; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px;">
          <i class="fas fa-chevron-down toggle-icon" style="transition: transform 0.2s;"></i>
          <span>${task.task_name}</span>
        </span>
        <span style="font-size: 10px; background: rgba(64, 224, 208, 0.15); color: var(--mint); padding: 2px 8px; border-radius: 20px; font-weight: 600;">
          Conf: ${Math.round(task.confidence * 100)}%
        </span>
      </div>
      <div class="deadline-card-content" style="transition: max-height 0.3s ease-out; overflow: hidden; max-height: 500px;">
        <div style="font-size: 11px; color: rgba(255, 255, 255, 0.5); display: flex; justify-content: space-between; margin-bottom: 4px; background: rgba(0,0,0,0.1); padding: 4px 8px; border-radius: 4px;">
          <span>Category: <strong>${task.category}</strong></span>
          <span>Deadline: <strong>${task.date} ${task.time}</strong></span>
          <span>Duration: <strong>${task.duration}</strong></span>
        </div>
        <div style="margin: 12px 0;">
          <div style="display: flex; justify-content: space-between; font-size: 11px; color: rgba(255,255,255,0.6); margin-bottom: 4px;">
            <span>Progress</span>
            <span class="progress-percent-val">0%</span>
          </div>
          <div style="width: 100%; height: 6px; background: rgba(255,255,255,0.1); border-radius: 3px; overflow: hidden;">
            <div class="progress-bar-fill" style="width: 0%; height: 100%; background: linear-gradient(90deg, var(--mint), #00fa9a); border-radius: 3px; transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);"></div>
          </div>
        </div>
        <div class="subtask-list-container" style="display: flex; flex-direction: column; gap: 8px; margin-bottom: 12px;"></div>
        <div class="celebration-banner" style="display: none; text-align: center; margin-top: 15px; padding: 12px; background: rgba(64, 224, 208, 0.15); border: 1px solid var(--mint); border-radius: 8px; color: #ffffff; font-weight: 700; font-size: 13px;">
          🎉 Task Completed
        </div>
      </div>
    `;

    // Collapsible Logic
    const header = card.querySelector(".deadline-card-header");
    const content = card.querySelector(".deadline-card-content");
    const icon = card.querySelector(".toggle-icon");

    header.addEventListener("click", () => {
      if (content.style.maxHeight === "0px") {
        content.style.maxHeight = "500px";
        icon.style.transform = "rotate(0deg)";
      } else {
        content.style.maxHeight = "0px";
        icon.style.transform = "rotate(-90deg)";
      }
    });

    const listContainer = card.querySelector(".subtask-list-container");

    // Render individual subtasks
    task.subtasks.forEach((sub) => {
      const item = document.createElement("label");
      item.style.display = "flex";
      item.style.alignItems = "center";
      item.style.gap = "10px";
      item.style.fontSize = "12px";
      item.style.color = "rgba(255, 255, 255, 0.85)";
      item.style.cursor = "pointer";
      item.style.padding = "6px 8px";
      item.style.borderRadius = "6px";
      item.style.background = "rgba(255,255,255,0.02)";
      item.style.border = "1px solid rgba(255,255,255,0.05)";
      item.style.transition = "all 0.2s";

      item.addEventListener("mouseenter", () => {
        item.style.background = "rgba(255,255,255,0.05)";
        item.style.border = "1px solid rgba(64, 224, 208, 0.2)";
      });
      item.addEventListener("mouseleave", () => {
        item.style.background = "rgba(255,255,255,0.02)";
        item.style.border = "1px solid rgba(255,255,255,0.05)";
      });

      const checked = sub.completed ? "checked" : "";
      const textDecoration = sub.completed ? "line-through" : "none";
      const textColor = sub.completed
        ? "rgba(255,255,255,0.4)"
        : "rgba(255,255,255,0.85)";

      // Map Priority Colors
      let prioBg = "rgba(255,255,255,0.06)";
      let prioColor = "rgba(255,255,255,0.6)";
      const prio = (sub.priority || "Medium").toLowerCase();
      if (prio === "high") {
        prioBg = "rgba(255, 107, 107, 0.15)";
        prioColor = "#ff6b6b";
      } else if (prio === "medium") {
        prioBg = "rgba(241, 196, 15, 0.15)";
        prioColor = "#f1c40f";
      } else if (prio === "low") {
        prioBg = "rgba(155, 89, 182, 0.15)";
        prioColor = "#a881d8";
      }

      // Map Difficulty Colors
      let diffBg = "rgba(255,255,255,0.06)";
      let diffColor = "rgba(255,255,255,0.6)";
      const diff = (sub.difficulty || "Medium").toLowerCase();
      if (diff === "hard") {
        diffBg = "rgba(231, 76, 60, 0.15)";
        diffColor = "#e74c3c";
      } else if (diff === "medium") {
        diffBg = "rgba(230, 126, 34, 0.15)";
        diffColor = "#e67e22";
      } else if (diff === "easy") {
        diffBg = "rgba(46, 204, 113, 0.15)";
        diffColor = "#2ecc71";
      }

      item.innerHTML = `
        <input type="checkbox" data-subtask-id="${sub.id}" ${checked} style="accent-color: var(--mint); cursor: pointer;">
        <div style="flex: 1; display: flex; align-items: flex-start; justify-content: space-between; gap: 8px;">
          <div style="display: flex; flex-direction: column; gap: 2px;">
            <span class="subtask-title" style="text-decoration: ${textDecoration}; color: ${textColor}; transition: all 0.2s; font-weight: 500;">
              ${sub.title}
            </span>
            <div style="display: flex; gap: 6px; font-size: 9px; align-items: center; flex-wrap: wrap;">
              <span style="color: ${prioColor}; background: ${prioBg}; padding: 1px 4px; border-radius: 3px; font-weight: 600; text-transform: uppercase; font-size: 8px;">${sub.priority || "Medium"}</span>
              <span style="color: ${diffColor}; background: ${diffBg}; padding: 1px 4px; border-radius: 3px; font-weight: 600; text-transform: uppercase; font-size: 8px;">${sub.difficulty || "Medium"}</span>
              ${sub.dependency ? `<span style="color: rgba(255,255,255,0.45); border-left: 1px solid rgba(255,255,255,0.15); padding-left: 6px; display: flex; align-items: center; gap: 3px;"><i class="fas fa-link" style="font-size: 7px;"></i> Needs: ${sub.dependency}</span>` : ""}
            </div>
          </div>
          <span style="font-size: 10px; color: rgba(255,255,255,0.4); display: flex; align-items: center; gap: 4px; white-space: nowrap; margin-top: 3px;">
            <i class="far fa-clock"></i> ${sub.duration || ""}
          </span>
        </div>
      `;

      const checkbox = item.querySelector('input[type="checkbox"]');
      const titleSpan = item.querySelector(".subtask-title");

      checkbox.addEventListener("change", async () => {
        try {
          checkbox.disabled = true;
          const headers = { "Content-Type": "application/json" };
          const csrfToken = getCSRFToken();
          if (csrfToken) {
            headers["X-CSRF-Token"] = csrfToken;
          }

          const res = await fetch(`/api/subtasks/${sub.id}/toggle`, {
            method: "POST",
            headers: headers,
            body: JSON.stringify({ completed: checkbox.checked }),
          });

          if (!res.ok) {
            throw new Error("Failed to update subtask");
          }

          const resData = await res.json();
          checkbox.disabled = false;

          if (typeof window.handleGamificationUpdate === "function") {
            window.handleGamificationUpdate(resData.gamification);
          }

          // Update styles
          if (checkbox.checked) {
            titleSpan.style.textDecoration = "line-through";
            titleSpan.style.color = "rgba(255,255,255,0.4)";
            showToast("Subtask completed!", "success");
          } else {
            titleSpan.style.textDecoration = "none";
            titleSpan.style.color = "rgba(255,255,255,0.85)";
            showToast("Subtask updated.");
          }

          updateCardProgress(card, resData.progress);
        } catch (err) {
          console.error(err);
          showToast(err.message || "Error updating subtask", "error");
          checkbox.checked = !checkbox.checked;
          checkbox.disabled = false;
        }
      });

      listContainer.appendChild(item);
    });

    // Compute and render initial progress
    let completedCount = task.subtasks.filter((s) => s.completed).length;
    let initialProgress = Math.round(
      (completedCount / task.subtasks.length) * 100,
    );
    updateCardProgress(card, initialProgress);
  } else {
    // 2. RENDER STANDARD ACTION BUTTON CARD
    card.innerHTML = `
      <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
        <span style="font-weight: 700; color: var(--mint); display: flex; align-items: center; gap: 6px; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px;">
          <i class="fas fa-bolt"></i> Deadline Detected
        </span>
        <span style="font-size: 10px; background: rgba(64, 224, 208, 0.15); color: var(--mint); padding: 2px 8px; border-radius: 20px; font-weight: 600;">
          Match: ${Math.round(task.confidence * 100)}%
        </span>
      </div>
      <div style="font-size: 14px; color: #ffffff; margin-bottom: 10px; font-weight: 500;">
        <span style="color: rgba(255, 255, 255, 0.6); font-size: 12px; display: block; margin-bottom: 2px;">Task Name</span>
        <span class="task-title-val">${task.task_name}</span>
      </div>
      <div style="font-size: 12px; color: rgba(255, 255, 255, 0.7); display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-bottom: 16px; background: rgba(0,0,0,0.15); padding: 8px 12px; border-radius: 8px;">
        <div><span style="color: rgba(255,255,255,0.4); font-size: 10px; display: block; margin-bottom: 1px;">Category</span><strong>${task.category}</strong></div>
        <div><span style="color: rgba(255,255,255,0.4); font-size: 10px; display: block; margin-bottom: 1px;">Deadline</span><strong>${task.date} ${task.time}</strong></div>
        <div><span style="color: rgba(255,255,255,0.4); font-size: 10px; display: block; margin-bottom: 1px;">Est. Duration</span><strong>${task.duration}</strong></div>
      </div>
      <div style="display: flex; flex-wrap: wrap; gap: 8px;">
        <button class="btn btn--mint btn--xs btn-create-task" style="flex: 1; min-width: 90px; padding: 6px 12px; font-size: 11px; border-radius: 6px;">Create Task</button>
        <button class="btn btn--secondary btn--xs btn-break-steps" style="flex: 1; min-width: 100px; padding: 6px 12px; font-size: 11px; border-radius: 6px; color: #ffffff; background: rgba(255,255,255,0.08);">Break Into Steps</button>
        <button class="btn btn--secondary btn--xs btn-generate-plan" style="flex: 1; min-width: 100px; padding: 6px 12px; font-size: 11px; border-radius: 6px; color: #ffffff; background: rgba(255,255,255,0.08);">Generate Plan</button>
        <button class="btn btn--ghost btn--xs btn-dismiss-task" style="color: #ff6b6b; flex: 1; min-width: 70px; padding: 6px 12px; font-size: 11px; border-radius: 6px;">Dismiss</button>
      </div>
    `;

    // Button Listeners
    const createBtn = card.querySelector(".btn-create-task");
    const breakBtn = card.querySelector(".btn-break-steps");
    const planBtn = card.querySelector(".btn-generate-plan");
    const dismissBtn = card.querySelector(".btn-dismiss-task");

    createBtn.addEventListener("click", async () => {
      try {
        createBtn.disabled = true;
        createBtn.textContent = "Saving...";
        const headers = { "Content-Type": "application/json" };
        const csrfToken = getCSRFToken();
        if (csrfToken) {
          headers["X-CSRF-Token"] = csrfToken;
        }

        const res = await fetch("/api/tasks/create", {
          method: "POST",
          headers: headers,
          body: JSON.stringify({
            title: task.task_name,
            category: task.category,
            deadline: `${task.date} ${task.time}`,
            duration: task.duration,
            confidence: task.confidence,
          }),
        });

        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.error || "Failed to create task");
        }

        showToast("Task created successfully!", "success");

        // Animate and collapse card
        card.style.opacity = "0";
        card.style.transform = "scale(0.95)";
        setTimeout(() => {
          card.remove();
        }, 300);
      } catch (e) {
        console.error(e);
        showToast(e.message || "Error saving task", "error");
        createBtn.disabled = false;
        createBtn.textContent = "Create Task";
      }
    });

    breakBtn.addEventListener("click", () => {
      inputEl.value = `Break this task into steps: "${task.task_name}" (Category: ${task.category}, Deadline: ${task.date} ${task.time})`;
      sendMessage();
    });

    planBtn.addEventListener("click", () => {
      inputEl.value = `Generate a detailed plan to finish the task: "${task.task_name}" by ${task.date} ${task.time}`;
      sendMessage();
    });

    dismissBtn.addEventListener("click", () => {
      card.style.opacity = "0";
      card.style.transform = "scale(0.95)";
      setTimeout(() => {
        card.remove();
      }, 300);
    });
  }

  // Append card directly after the parent bubble
  parentBubble.parentNode.insertBefore(card, parentBubble.nextSibling);
}

function updateCardProgress(card, progress) {
  const bar = card.querySelector(".progress-bar-fill");
  const label = card.querySelector(".progress-percent-val");
  const banner = card.querySelector(".celebration-banner");

  if (bar) bar.style.width = `${progress}%`;
  if (label) label.textContent = `${progress}%`;

  if (progress === 100) {
    if (banner && banner.style.display !== "block") {
      banner.style.display = "block";
      showToast("🎉 All subtasks complete! Task Completed!", "success");
      triggerConfetti();
    }
  } else {
    if (banner) banner.style.display = "none";
  }
}

function triggerConfetti() {
  const container = document.createElement("div");
  container.style.position = "fixed";
  container.style.top = "0";
  container.style.left = "0";
  container.style.width = "100vw";
  container.style.height = "100vh";
  container.style.pointerEvents = "none";
  container.style.zIndex = "99999";
  document.body.appendChild(container);

  const colors = [
    "#40e0d0",
    "#00fa9a",
    "#1e90ff",
    "#ff69b4",
    "#ffd700",
    "#ff4500",
  ];
  for (let i = 0; i < 60; i++) {
    const particle = document.createElement("div");
    const color = colors[Math.floor(Math.random() * colors.length)];
    particle.style.position = "absolute";
    particle.style.width = `${Math.random() * 8 + 6}px`;
    particle.style.height = `${Math.random() * 12 + 6}px`;
    particle.style.background = color;
    particle.style.opacity = Math.random() * 0.6 + 0.4;
    particle.style.borderRadius = "2px";

    const startX = Math.random() * window.innerWidth;
    const startY = window.innerHeight;
    particle.style.left = `${startX}px`;
    particle.style.top = `${startY}px`;
    particle.style.transform = `rotate(${Math.random() * 360}deg)`;
    container.appendChild(particle);

    const destX = startX + (Math.random() - 0.5) * 400;
    const destY = Math.random() * (window.innerHeight * 0.4);
    const duration = Math.random() * 1500 + 1000;

    const anim = particle.animate(
      [
        {
          top: `${startY}px`,
          left: `${startX}px`,
          opacity: 1,
          transform: "rotate(0deg)",
        },
        {
          top: `${destY}px`,
          left: `${destX}px`,
          opacity: 0,
          transform: `rotate(${Math.random() * 720}deg)`,
        },
      ],
      {
        duration: duration,
        easing: "cubic-bezier(0.25, 0.46, 0.45, 0.94)",
        fill: "forwards",
      },
    );

    anim.onfinish = () => particle.remove();
  }

  setTimeout(() => container.remove(), 2500);
}

// ========================================
// SMART TASK MANAGEMENT SYSTEM
// ========================================

window.fetchTasks = async function () {
  const grid = document.getElementById("tasks-grid");
  const emptyState = document.getElementById("tasks-empty-state");

  try {
    const elQ = document.getElementById("task-search-input");
    const elCat = document.getElementById("filter-category");
    const elPrio = document.getElementById("filter-priority");
    const elStat = document.getElementById("filter-status");
    const elRisk = document.getElementById("filter-risk");

    const q = elQ ? elQ.value : "";
    const category = elCat ? elCat.value : "";
    const priority = elPrio ? elPrio.value : "";
    const status = elStat ? elStat.value : "";
    const risk = elRisk ? elRisk.value : "";

    const params = new URLSearchParams();
    if (q) params.append("q", q);
    if (category) params.append("category", category);
    if (priority) params.append("priority", priority);
    if (status) params.append("status", status);
    if (risk) params.append("risk", risk);

    const res = await fetch(`/api/tasks?${params.toString()}`);
    if (!res.ok) throw new Error("Failed to fetch tasks");
    const data = await res.json();

    const tasks = data.tasks || [];

    if (grid) {
      grid.innerHTML = "";
      if (tasks.length > 0) {
        if (emptyState) emptyState.style.display = "none";
        tasks.forEach((task) => {
          grid.appendChild(createTaskCardDOM(task));
        });
      } else {
        if (emptyState) emptyState.style.display = "block";
      }
    }

    // Always update dashboard components
    if (typeof window.updateRiskDashboardOverview === "function") {
      window.updateRiskDashboardOverview(tasks);
    }
    if (typeof window.loadProductivityDashboard === "function") {
      window.loadProductivityDashboard(tasks);
    }
    if (typeof window.updateCountdownTimers === "function") {
      window.updateCountdownTimers();
    }

    // Update Panic toggle button and modal color state dynamically
    const panicToggle = document.getElementById("panic-toggle-btn");
    const panicModal = document.getElementById("panic-modal");
    if (panicToggle) {
      const activeTasks = tasks.filter(
        (t) => t.status !== "Completed" && t.status !== "Cancelled",
      );
      const hasCritical = activeTasks.some(
        (t) =>
          t.priority === "High" ||
          t.risk_level === "High" ||
          t.status === "Overdue",
      );
      if (hasCritical) {
        panicToggle.classList.remove("safe-state");
        if (panicModal) panicModal.classList.remove("safe-state");
      } else {
        panicToggle.classList.add("safe-state");
        if (panicModal) panicModal.classList.add("safe-state");
      }
    }
  } catch (err) {
    console.error(err);
    const elQ = document.getElementById("task-search-input");
    if (elQ) {
      showToast(err.message || "Error loading tasks", "error");
    }
  }
};

function createTaskCardDOM(task) {
  const card = document.createElement("div");
  card.className = "card glass";
  card.style.padding = "16px";
  card.style.display = "flex";
  card.style.flexDirection = "column";
  card.style.gap = "12px";
  card.style.position = "relative";
  card.style.transition = "transform 0.2s, box-shadow 0.2s";
  card.style.animation = "fadeIn 0.3s ease";

  // Score & priority mappings
  const score =
    task.priority_score !== undefined && task.priority_score !== null
      ? task.priority_score
      : 50;
  let prioBadgeText = "";
  let prioEmoji = "";
  let prioColor = "";
  let prioBg = "";
  if (score >= 90) {
    prioBadgeText = "Critical";
    prioEmoji = "🔴";
    prioColor = "#ff6b6b";
    prioBg = "rgba(255, 107, 107, 0.15)";
  } else if (score >= 70) {
    prioBadgeText = "High";
    prioEmoji = "🟠";
    prioColor = "#e67e22";
    prioBg = "rgba(230, 126, 34, 0.15)";
  } else if (score >= 40) {
    prioBadgeText = "Medium";
    prioEmoji = "🟡";
    prioColor = "#f1c40f";
    prioBg = "rgba(241, 196, 15, 0.15)";
  } else {
    prioBadgeText = "Low";
    prioEmoji = "🟢";
    prioColor = "#2ecc71";
    prioBg = "rgba(46, 204, 113, 0.15)";
  }

  // Risk & glow mappings
  let riskText = task.risk_level || "Safe";
  let riskBg = "rgba(46, 204, 113, 0.12)";
  let riskColor = "#2ecc71";
  let riskClass = "risk-glow-green";
  let riskEmoji = "🟢";
  if (riskText === "Critical") {
    riskBg = "rgba(231, 76, 60, 0.15)";
    riskColor = "#e74c3c";
    riskClass = "risk-glow-red";
    riskEmoji = "🔴";
  } else if (riskText === "High" || riskText === "High Risk") {
    riskBg = "rgba(230, 126, 34, 0.15)";
    riskColor = "#e67e22";
    riskClass = "risk-glow-orange";
    riskEmoji = "🟠";
  } else if (riskText === "Attention" || riskText === "Medium") {
    riskBg = "rgba(241, 196, 15, 0.15)";
    riskColor = "#f1c40f";
    riskClass = "risk-glow-yellow";
    riskEmoji = "🟡";
  } else if (riskText === "Overdue") {
    riskBg = "rgba(255,255,255,0.06)";
    riskColor = "rgba(255,255,255,0.4)";
    riskClass = "";
    riskEmoji = "⚫";
  }

  let statusColor = "#ffffff";
  let statusIcon = "fa-clock";
  if (task.status === "Completed") {
    statusColor = "var(--mint)";
    statusIcon = "fa-check-circle";
  } else if (task.status === "Overdue") {
    statusColor = "#ff6b6b";
    statusIcon = "fa-exclamation-circle";
  } else if (task.status === "In Progress") {
    statusColor = "#3498db";
    statusIcon = "fa-spinner";
  } else if (task.status === "Cancelled") {
    statusColor = "rgba(255,255,255,0.3)";
    statusIcon = "fa-times-circle";
  }

  card.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 8px;">
      <span style="font-size: 10px; background: rgba(64, 224, 208, 0.15); color: var(--mint); padding: 2px 8px; border-radius: 20px; font-weight: 600;">
        ${task.category}
      </span>
      <span style="font-size: 11px; color: ${statusColor}; font-weight: 600; display: flex; align-items: center; gap: 4px;">
        <i class="fas ${statusIcon}"></i> ${task.status}
      </span>
    </div>

    <div>
      <h3 style="margin: 4px 0; font-size: 16px; font-weight: 600; color: #ffffff;">${task.title}</h3>
      <p style="margin: 0; font-size: 12px; color: rgba(255,255,255,0.6); display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; height: 34px;">
        ${task.description || "No description provided."}
      </p>
    </div>

    <div style="display: flex; flex-wrap: wrap; gap: 8px; font-size: 9px; align-items: center;">
      <span style="color: ${prioColor}; background: ${prioBg}; padding: 2px 6px; border-radius: 4px; font-weight: 600; text-transform: uppercase;">PRIO: ${prioBadgeText} (${score}) ${prioEmoji}</span>
      <span class="${riskClass}" style="color: ${riskColor}; background: ${riskBg}; padding: 2px 6px; border-radius: 4px; font-weight: 600; text-transform: uppercase; border: 1px solid ${riskColor}33; display: inline-flex; align-items: center; gap: 2px;">RISK: ${riskText} ${riskEmoji}</span>
      <span style="color: rgba(255,255,255,0.5); font-size: 11px; margin-left: auto; display: flex; align-items: center; gap: 4px;">
        <i class="far fa-clock"></i> ${task.estimated_duration || "1 Hour"}
      </span>
    </div>

    <div style="margin: 6px 0;">
      <div style="display: flex; justify-content: space-between; font-size: 10px; color: rgba(255,255,255,0.5); margin-bottom: 4px;">
        <span>Progress (${task.progress}%)</span>
        <span>Prob: ${task.completion_probability || 100}%</span>
      </div>
      <div style="width: 100%; height: 4px; background: rgba(255,255,255,0.1); border-radius: 2px; overflow: hidden;">
        <div style="width: ${task.progress}%; height: 100%; background: var(--mint); border-radius: 2px; transition: width 0.3s ease;"></div>
      </div>
    </div>

    <!-- Suggested Recommendations -->
    ${
      task.status !== "Completed"
        ? `
      <div style="font-size: 11px; color: rgba(255,255,255,0.8); background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); padding: 8px 12px; border-radius: 6px; margin-top: 4px;">
        <div style="font-weight: 600; display: flex; align-items: center; gap: 4px; color: var(--mint); margin-bottom: 2px;">
          <i class="fas fa-lightbulb"></i> Suggested Action:
        </div>
        <div>${task.suggested_action || "Proceed at your own pace."}</div>
        ${task.risk_reason ? `<div style="font-size: 10px; color: rgba(255,255,255,0.4); margin-top: 4px;">Reason: ${task.risk_reason}</div>` : ""}
      </div>
    `
        : ""
    }

    <div style="font-size: 11px; color: rgba(255,255,255,0.4); display: flex; flex-direction: column; gap: 4px; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 10px;">
      <div style="display: flex; align-items: center; gap: 4px;">
        <i class="far fa-calendar-alt"></i> Deadline: <strong>${task.deadline || "None"}</strong>
      </div>
      ${task.deadline ? `<div class="deadline-countdown" data-deadline="${task.deadline}" style="font-weight: 600; color: var(--mint); font-size: 10px; display: flex; align-items: center; gap: 4px; margin-top: 2px;"></div>` : ""}
    </div>

    <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-top: 4px;">
      ${task.status !== "Completed" && task.status !== "Cancelled" ? `<button class="btn btn--mint btn-task-complete" style="flex: 1; padding: 4px 8px; font-size: 10px; border-radius: 4px; border: none; font-weight:600;"><i class="fas fa-check"></i> Complete</button>` : ""}
      <button class="btn btn-task-edit" style="padding: 4px 8px; font-size: 10px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.1); background: rgba(255,255,255,0.05); color: #ffffff;"><i class="fas fa-edit"></i> Edit</button>
      <button class="btn btn-task-delete" style="padding: 4px 8px; font-size: 10px; border-radius: 4px; border: 1px solid rgba(255,107,107,0.2); background: rgba(255,107,107,0.08); color: #ff6b6b;"><i class="fas fa-trash"></i></button>
    </div>

    <div style="display: flex; gap: 6px; width: 100%;">
      <button class="btn btn-task-break" style="flex: 1; padding: 4px 8px; font-size: 10px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.04); color: #ffffff;"><i class="fas fa-list-ul"></i> Break Into Steps</button>
      <button class="btn btn-task-plan" style="flex: 1; padding: 4px 8px; font-size: 10px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.04); color: #ffffff;"><i class="fas fa-compass"></i> Generate Plan</button>
    </div>

    <!-- TASK BREAKDOWN DROPDOWN -->
    ${
      task.subtasks && task.subtasks.length > 0
        ? `
      <div class="task-breakdown-dropdown" style="margin-top: 8px; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 8px; display: none;">
        <h4 style="font-size: 11px; color: rgba(255,255,255,0.5); margin: 0 0 6px 0; font-weight:600; text-align: left;">Task Breakdown (${task.subtasks.length} steps):</h4>
        <div style="display: flex; flex-direction: column; gap: 6px;">
          ${task.subtasks
            .map((s) => {
              const checkedAttr = s.completed ? "checked" : "";
              const textStyle = s.completed
                ? "text-decoration: line-through; color: rgba(255,255,255,0.4);"
                : "color: #ffffff;";
              const depBadge = s.dependency
                ? `<span style="font-size: 9px; color: #a881d8; background: rgba(168,129,216,0.12); padding: 1px 4px; border-radius: 3px; margin-left: 6px;">Prereq: ${s.dependency}</span>`
                : "";
              return `
              <div style="display: flex; align-items: center; justify-content: space-between; font-size: 11px; padding: 4px 6px; background: rgba(255,255,255,0.01); border-radius: 4px;">
                <label style="display: flex; align-items: center; gap: 6px; cursor: pointer; flex: 1; text-align: left; margin: 0;">
                  <input type="checkbox" class="subtask-checkbox-toggle" data-subtask-id="${s.id}" ${checkedAttr} style="accent-color: var(--mint); margin: 0;">
                  <span style="${textStyle}">${s.title}</span>
                  ${depBadge}
                </label>
                <span style="font-size: 9px; color: rgba(255,255,255,0.4);">${s.duration || ""}</span>
              </div>
            `;
            })
            .join("")}
        </div>
      </div>
      <button class="btn-toggle-breakdown" style="width: 100%; border: none; background: rgba(255,255,255,0.03); color: rgba(255,255,255,0.6); font-size: 10px; padding: 6px; border-radius: 4px; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 4px; margin-top: 6px; font-weight: 500;">
        <i class="fas fa-chevron-down"></i> View Breakdown (${task.subtasks.length})
      </button>
    `
        : ""
    }
  `;

  // Bind Actions
  const completeBtn = card.querySelector(".btn-task-complete");
  if (completeBtn) {
    completeBtn.addEventListener("click", async () => {
      try {
        const res = await fetch(`/api/tasks/${task.id}/complete`, {
          method: "POST",
          headers: { "X-CSRF-Token": getCSRFToken() },
        });
        if (!res.ok) throw new Error("Failed to complete task");
        const data = await res.json();
        if (typeof window.handleGamificationUpdate === "function") {
          window.handleGamificationUpdate(data.gamification);
        }
        showToast("🎉 Task Completed!", "success");
        triggerConfetti();
        window.fetchTasks();
      } catch (err) {
        showToast(err.message, "error");
      }
    });
  }

  card.querySelector(".btn-task-edit").addEventListener("click", () => {
    window.showEditTaskModal(task);
  });

  card.querySelector(".btn-task-delete").addEventListener("click", async () => {
    if (!confirm("Are you sure you want to delete this task?")) return;
    try {
      const res = await fetch(`/api/tasks/${task.id}`, {
        method: "DELETE",
        headers: { "X-CSRF-Token": getCSRFToken() },
      });
      if (!res.ok) throw new Error("Failed to delete task");
      showToast("🗑️ Task Deleted");
      window.fetchTasks();
    } catch (err) {
      showToast(err.message, "error");
    }
  });

  card.querySelector(".btn-task-break").addEventListener("click", () => {
    const chatTab = document.querySelector('.nav-tab[data-tab="tab-chat"]');
    if (chatTab) chatTab.click();
    inputEl.value = `Break this task into steps: "${task.title}" (Category: ${task.category}, Deadline: ${task.deadline || ""})`;
    sendMessage();
  });

  card.querySelector(".btn-task-plan").addEventListener("click", () => {
    const chatTab = document.querySelector('.nav-tab[data-tab="tab-chat"]');
    if (chatTab) chatTab.click();
    inputEl.value = `Generate a detailed plan to finish the task: "${task.title}" by ${task.deadline || ""}`;
    sendMessage();
  });

  // Bind Breakdown Toggle
  const toggleBreakdownBtn = card.querySelector(".btn-toggle-breakdown");
  const breakdownDropdown = card.querySelector(".task-breakdown-dropdown");
  if (toggleBreakdownBtn && breakdownDropdown) {
    toggleBreakdownBtn.addEventListener("click", () => {
      const isHidden = breakdownDropdown.style.display === "none";
      breakdownDropdown.style.display = isHidden ? "block" : "none";
      toggleBreakdownBtn.innerHTML = isHidden
        ? `<i class="fas fa-chevron-up"></i> Hide Breakdown (${task.subtasks.length})`
        : `<i class="fas fa-chevron-down"></i> View Breakdown (${task.subtasks.length})`;
    });
  }

  // Bind Subtask Checkbox Toggles
  card.querySelectorAll(".subtask-checkbox-toggle").forEach((chk) => {
    chk.addEventListener("change", async (e) => {
      const subtaskId = e.target.dataset.subtaskId;
      const completed = e.target.checked;
      try {
        const res = await fetch(`/api/subtasks/${subtaskId}/toggle`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRF-Token": getCSRFToken(),
          },
          body: JSON.stringify({ completed }),
        });
        if (!res.ok) throw new Error("Failed to toggle subtask");
        const data = await res.json();

        if (typeof window.handleGamificationUpdate === "function") {
          window.handleGamificationUpdate(data.gamification);
        }

        showToast("Subtask status updated", "success");
        if (data.is_completed) {
          triggerConfetti();
          showToast("🎉 All subtasks complete! Task Completed!", "success");
        }

        window.fetchTasks();
      } catch (err) {
        showToast(err.message, "error");
        e.target.checked = !completed;
      }
    });
  });

  return card;
}

window.showCreateTaskModal = function () {
  document.getElementById("task-modal-title").textContent = "Create Task";
  document.getElementById("task-form-id").value = "";
  document.getElementById("task-form").reset();

  const now = new Date();
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
  document.getElementById("task-form-deadline").value = now
    .toISOString()
    .slice(0, 16);

  document.getElementById("task-modal").style.display = "flex";
};

window.showEditTaskModal = function (task) {
  document.getElementById("task-modal-title").textContent = "Edit Task";
  document.getElementById("task-form-id").value = task.id;
  document.getElementById("task-form-title").value = task.title;
  document.getElementById("task-form-description").value =
    task.description || "";
  document.getElementById("task-form-category").value =
    task.category || "Other";
  document.getElementById("task-form-priority").value =
    task.priority || "Medium";
  document.getElementById("task-form-risk").value = task.risk_level || "Low";
  document.getElementById("task-form-duration").value =
    task.estimated_duration || "";
  document.getElementById("task-form-status").value = task.status || "Pending";

  if (task.deadline) {
    const dateStr = task.deadline.replace(" ", "T");
    document.getElementById("task-form-deadline").value = dateStr;
  } else {
    document.getElementById("task-form-deadline").value = "";
  }

  document.getElementById("task-modal").style.display = "flex";
};

// Bind Modal controls on init
window.addEventListener("DOMContentLoaded", () => {
  const createModalBtn = document.getElementById("btn-create-task-modal");
  const modalCloseBtn = document.getElementById("task-modal-close");
  const formCancelBtn = document.getElementById("task-form-cancel");
  const taskForm = document.getElementById("task-form");

  if (createModalBtn) {
    createModalBtn.addEventListener("click", window.showCreateTaskModal);
  }
  if (modalCloseBtn) {
    modalCloseBtn.addEventListener("click", () => {
      document.getElementById("task-modal").style.display = "none";
    });
  }
  if (formCancelBtn) {
    formCancelBtn.addEventListener("click", () => {
      document.getElementById("task-modal").style.display = "none";
    });
  }

  if (taskForm) {
    taskForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const id = document.getElementById("task-form-id").value;
      const title = document.getElementById("task-form-title").value;
      const description = document.getElementById(
        "task-form-description",
      ).value;
      const category = document.getElementById("task-form-category").value;
      const deadline = document.getElementById("task-form-deadline").value;
      const priority = document.getElementById("task-form-priority").value;
      const risk_level = document.getElementById("task-form-risk").value;
      const estimated_duration =
        document.getElementById("task-form-duration").value;
      const status = document.getElementById("task-form-status").value;

      const payload = {
        title,
        description,
        category,
        deadline,
        priority,
        risk_level,
        estimated_duration,
        status,
      };

      try {
        let res;
        if (id) {
          // Edit
          res = await fetch(`/api/tasks/${id}`, {
            method: "PUT",
            headers: {
              "Content-Type": "application/json",
              "X-CSRF-Token": getCSRFToken(),
            },
            body: JSON.stringify(payload),
          });
        } else {
          // Create
          res = await fetch("/api/tasks/create", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRF-Token": getCSRFToken(),
            },
            body: JSON.stringify(payload),
          });
        }

        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.error || "Failed to save task");
        }

        showToast(id ? "📝 Task Updated" : "✅ Task Created", "success");
        document.getElementById("task-modal").style.display = "none";
        window.fetchTasks();
      } catch (err) {
        showToast(err.message, "error");
      }
    });
  }

  // Bind Search & Filters
  const searchInput = document.getElementById("task-search-input");
  const catFilter = document.getElementById("filter-category");
  const prioFilter = document.getElementById("filter-priority");
  const statusFilter = document.getElementById("filter-status");
  const riskFilter = document.getElementById("filter-risk");
  const clearFilterBtn = document.getElementById("btn-clear-filters");

  if (searchInput) searchInput.addEventListener("input", window.fetchTasks);
  if (catFilter) catFilter.addEventListener("change", window.fetchTasks);
  if (prioFilter) prioFilter.addEventListener("change", window.fetchTasks);
  if (statusFilter) statusFilter.addEventListener("change", window.fetchTasks);
  if (riskFilter) riskFilter.addEventListener("change", window.fetchTasks);

  if (clearFilterBtn) {
    clearFilterBtn.addEventListener("click", () => {
      if (searchInput) searchInput.value = "";
      if (catFilter) catFilter.value = "";
      if (prioFilter) prioFilter.value = "";
      if (statusFilter) statusFilter.value = "";
      if (riskFilter) riskFilter.value = "";
      window.fetchTasks();
    });
  }

  // Quick To-Do List functionality
  const btnAddTodo = document.getElementById("btn-add-quick-todo");
  const todoInput = document.getElementById("quick-todo-input");
  const todoList = document.getElementById("quick-todo-list");

  if (btnAddTodo && todoInput && todoList) {
    const updateTodoStats = (todos) => {
      const total = todos.length;
      const completed = todos.filter((t) => t.completed).length;
      const pending = total - completed;

      const totalCountEl = document.getElementById("todo-total-count");
      const completedCountEl = document.getElementById("todo-completed-count");
      const pendingCountEl = document.getElementById("todo-pending-count");

      if (totalCountEl) totalCountEl.textContent = total;
      if (completedCountEl) completedCountEl.textContent = completed;
      if (pendingCountEl) pendingCountEl.textContent = pending;
    };

    const loadLocalTodos = () => {
      const saved = localStorage.getItem("quick_todos");
      if (saved) {
        todoList.innerHTML = "";
        const todos = JSON.parse(saved);
        todos.forEach((todo) => {
          todoList.appendChild(createTodoDOM(todo.text, todo.completed));
        });
        updateTodoStats(todos);
      }
    };

    const saveLocalTodos = () => {
      const todos = [];
      todoList.querySelectorAll(".todo-item").forEach((item) => {
        todos.push({
          text: item.querySelector("span").textContent,
          completed: item.querySelector('input[type="checkbox"]').checked,
        });
      });
      localStorage.setItem("quick_todos", JSON.stringify(todos));
      updateTodoStats(todos);
    };

    const createTodoDOM = (text, completed = false) => {
      const div = document.createElement("div");
      div.className = "todo-item";
      div.style.display = "flex";
      div.style.alignItems = "center";
      div.style.justifyContent = "space-between";
      div.style.padding = "10px 14px";
      div.style.background = "rgba(255,255,255,0.02)";
      div.style.border = "1px solid rgba(255,255,255,0.05)";
      div.style.borderRadius = "8px";
      div.style.transition = "background 0.2s";

      const chk = document.createElement("input");
      chk.type = "checkbox";
      chk.checked = completed;
      chk.style.accentColor = "var(--mint)";
      chk.style.cursor = "pointer";

      const span = document.createElement("span");
      span.textContent = text;
      span.style.color = "#ffffff";
      span.style.fontSize = "13px";
      if (completed) {
        span.style.textDecoration = "line-through";
        span.style.color = "rgba(255,255,255,0.4)";
      }

      chk.addEventListener("change", () => {
        if (chk.checked) {
          span.style.textDecoration = "line-through";
          span.style.color = "rgba(255,255,255,0.4)";
        } else {
          span.style.textDecoration = "";
          span.style.color = "#ffffff";
        }
        saveLocalTodos();
      });

      const delBtn = document.createElement("button");
      delBtn.className = "btn-todo-delete";
      delBtn.style.background = "transparent";
      delBtn.style.border = "none";
      delBtn.style.color = "rgba(255,107,107,0.6)";
      delBtn.style.cursor = "pointer";
      delBtn.style.fontSize = "12px";
      delBtn.innerHTML = '<i class="fas fa-trash"></i>';

      delBtn.addEventListener("click", () => {
        div.remove();
        saveLocalTodos();
      });

      const left = document.createElement("div");
      left.style.display = "flex";
      left.style.alignItems = "center";
      left.style.gap = "10px";
      left.appendChild(chk);
      left.appendChild(span);

      div.appendChild(left);
      div.appendChild(delBtn);

      return div;
    };

    btnAddTodo.addEventListener("click", () => {
      const text = todoInput.value.trim();
      if (!text) return;
      todoList.appendChild(createTodoDOM(text));
      todoInput.value = "";
      saveLocalTodos();
    });

    todoInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        btnAddTodo.click();
      }
    });

    // Check if quick_todos exists and has items, otherwise use the 4 default rows
    const saved = localStorage.getItem("quick_todos");
    let hasSavedTodos = false;
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          hasSavedTodos = true;
        }
      } catch (e) {}
    }

    if (!hasSavedTodos) {
      const defaults = [
        "📚 Complete Physics Chapter 1 revision",
        "🧪 Gather materials for Science Exhibition",
        "📝 Review exam schedule for Math midterm",
        "⏰ Set reminders for study group meeting",
      ];
      todoList.innerHTML = "";
      defaults.forEach((text) => {
        todoList.appendChild(createTodoDOM(text, false));
      });
      saveLocalTodos();
    } else {
      loadLocalTodos();
    }
  }

  // AI Smart Daily Planner
  const btnGeneratePlan = document.getElementById("btn-generate-plan");
  const btnGeneratePlanEmpty = document.getElementById(
    "btn-generate-plan-empty",
  );
  const btnRegeneratePlan = document.getElementById("btn-regenerate-plan");
  const plannerContainer = document.getElementById("planner-container");
  const plannerEmptyState = document.getElementById("planner-empty-state");
  const plannerNoTasksState = document.getElementById("planner-no-tasks-state");
  const timelineList = document.getElementById("planner-timeline-list");

  const currentFocusTitle = document.getElementById("current-focus-title");
  const currentFocusTime = document.getElementById("current-focus-time");
  const currentFocusPrioBadge = document.getElementById(
    "current-focus-prio-badge",
  );
  const btnStartFocus = document.getElementById("btn-start-current-focus");

  const upNextTitle = document.getElementById("up-next-title");
  const upNextTime = document.getElementById("up-next-time");
  const upNextWidget = document.getElementById("planner-up-next-item");

  const parseTimeToMinutes = (timeStr) => {
    if (!timeStr) return 0;
    const match = timeStr.match(/(\d+):(\d+)\s*(AM|PM)/i);
    if (!match) return 0;
    let hours = parseInt(match[1]);
    const minutes = parseInt(match[2]);
    const ampm = match[3].toUpperCase();
    if (ampm === "PM" && hours < 12) hours += 12;
    if (ampm === "AM" && hours === 12) hours = 0;
    return hours * 60 + minutes;
  };

  window.loadDailyPlan = async () => {
    try {
      const res = await fetch("/api/planner/current");
      if (!res.ok) throw new Error("Failed to load planner data");
      const data = await res.json();

      if (data.success && data.plan && data.plan.length > 0) {
        // Show container and hide empty/no tasks states
        if (plannerContainer) plannerContainer.style.display = "flex";
        if (plannerEmptyState) plannerEmptyState.style.display = "none";
        if (plannerNoTasksState) plannerNoTasksState.style.display = "none";

        // Update header buttons
        if (btnGeneratePlan) btnGeneratePlan.style.display = "none";
        if (btnRegeneratePlan) btnRegeneratePlan.style.display = "inline-flex";

        // Render timeline list
        if (timelineList) {
          timelineList.innerHTML = "";
          data.plan.forEach((item) => {
            const card = document.createElement("div");
            card.className = "todo-item"; // Reuse styling
            card.style.display = "flex";
            card.style.alignItems = "center";
            card.style.justifyContent = "space-between";
            card.style.padding = "12px 16px";
            card.style.background =
              item.type === "break"
                ? "rgba(255,255,255,0.01)"
                : "rgba(255,255,255,0.03)";
            card.style.border = "1px solid rgba(255,255,255,0.05)";
            card.style.borderRadius = "10px";

            const left = document.createElement("div");
            left.style.display = "flex";
            left.style.alignItems = "center";
            left.style.gap = "12px";

            const icon = document.createElement("i");
            if (item.type === "break") {
              icon.className = "fas fa-coffee";
              icon.style.color = "#ffb86c";
            } else if (item.type === "subtask") {
              icon.className = "fas fa-tasks";
              icon.style.color = "var(--mint)";
            } else {
              icon.className = "fas fa-clipboard-list";
              icon.style.color = "var(--mint)";
            }

            const content = document.createElement("div");
            content.style.display = "flex";
            content.style.flexDirection = "column";
            content.style.gap = "2px";

            const titleSpan = document.createElement("span");
            titleSpan.textContent = item.title;
            titleSpan.style.color = "#ffffff";
            titleSpan.style.fontSize = "14px";
            titleSpan.style.fontWeight = "500";

            const timeSpan = document.createElement("span");
            timeSpan.textContent = `${item.start_time} - ${item.end_time}`;
            timeSpan.style.color = "rgba(255,255,255,0.4)";
            timeSpan.style.fontSize = "12px";

            content.appendChild(titleSpan);
            content.appendChild(timeSpan);
            left.appendChild(icon);
            left.appendChild(content);
            card.appendChild(left);

            if (item.priority && item.type !== "break") {
              const badge = document.createElement("span");
              badge.className = "badge";
              badge.textContent = item.priority;
              badge.style.fontSize = "10px";
              badge.style.padding = "2px 8px";
              badge.style.borderRadius = "4px";
              if (item.priority === "High") {
                badge.style.background = "rgba(255, 107, 107, 0.15)";
                badge.style.color = "#ff6b6b";
                badge.style.border = "1px solid rgba(255, 107, 107, 0.3)";
              } else {
                badge.style.background = "rgba(255, 255, 255, 0.05)";
                badge.style.color = "rgba(255,255,255,0.6)";
                badge.style.border = "1px solid rgba(255,255,255,0.1)";
              }
              card.appendChild(badge);
            }

            timelineList.appendChild(card);
          });
        }

        // Calculate Current Focus & Up Next Focus items dynamically
        const now = new Date();
        const currentMinutes = now.getHours() * 60 + now.getMinutes();

        let focusIndex = -1;
        for (let i = 0; i < data.plan.length; i++) {
          const endMin = parseTimeToMinutes(data.plan[i].end_time);
          if (endMin > currentMinutes) {
            focusIndex = i;
            break;
          }
        }

        // Fallback to last item if all are completed
        if (focusIndex === -1 && data.plan.length > 0) {
          focusIndex = data.plan.length - 1;
        }

        if (focusIndex !== -1) {
          const focusItem = data.plan[focusIndex];
          if (currentFocusTitle)
            currentFocusTitle.textContent = focusItem.title;
          if (currentFocusTime)
            currentFocusTime.innerHTML = `<i class="far fa-clock"></i> ${focusItem.start_time} - ${focusItem.end_time}`;

          if (currentFocusPrioBadge) {
            if (focusItem.type === "break") {
              currentFocusPrioBadge.textContent = "Relax";
              currentFocusPrioBadge.style.background =
                "rgba(255, 184, 108, 0.15)";
              currentFocusPrioBadge.style.color = "#ffb86c";
              currentFocusPrioBadge.style.border =
                "1px solid rgba(255, 184, 108, 0.3)";
            } else {
              currentFocusPrioBadge.textContent = `${focusItem.priority || "Medium"} Priority`;
              if (focusItem.priority === "High") {
                currentFocusPrioBadge.style.background =
                  "rgba(255, 107, 107, 0.15)";
                currentFocusPrioBadge.style.color = "#ff6b6b";
                currentFocusPrioBadge.style.border =
                  "1px solid rgba(255, 107, 107, 0.3)";
              } else {
                currentFocusPrioBadge.style.background =
                  "rgba(255, 255, 255, 0.05)";
                currentFocusPrioBadge.style.color = "rgba(255,255,255,0.6)";
                currentFocusPrioBadge.style.border =
                  "1px solid rgba(255,255,255,0.1)";
              }
            }
          }

          // Up Next
          const nextIndex = focusIndex + 1;
          if (nextIndex < data.plan.length) {
            const nextItem = data.plan[nextIndex];
            if (upNextWidget) upNextWidget.style.display = "flex";
            if (upNextTitle) upNextTitle.textContent = nextItem.title;
            if (upNextTime)
              upNextTime.textContent = `${nextItem.start_time} - ${nextItem.end_time}`;
          } else {
            if (upNextWidget) upNextWidget.style.display = "none";
          }
        }
      } else {
        // No plan found. Check if tasks exist in backend list
        const tasksRes = await fetch("/api/tasks");
        const tasksData = await tasksRes.json();

        if (tasksData && tasksData.tasks && tasksData.tasks.length > 0) {
          if (plannerContainer) plannerContainer.style.display = "none";
          if (plannerEmptyState) plannerEmptyState.style.display = "block";
          if (plannerNoTasksState) plannerNoTasksState.style.display = "none";
        } else {
          if (plannerContainer) plannerContainer.style.display = "none";
          if (plannerEmptyState) plannerEmptyState.style.display = "none";
          if (plannerNoTasksState) plannerNoTasksState.style.display = "block";
        }

        if (btnGeneratePlan) btnGeneratePlan.style.display = "inline-flex";
        if (btnRegeneratePlan) btnRegeneratePlan.style.display = "none";
      }
    } catch (err) {
      console.error(err);
      showToast("⚠️ Error loading daily plan", "error");
    }
  };

  window.generateDailyPlan = async () => {
    const originalText = btnGeneratePlan ? btnGeneratePlan.innerHTML : "";
    const setGeneratingState = (generating) => {
      const btns = [btnGeneratePlan, btnGeneratePlanEmpty, btnRegeneratePlan];
      btns.forEach((btn) => {
        if (btn) {
          btn.disabled = generating;
          btn.innerHTML = generating
            ? '<i class="fas fa-spinner fa-spin"></i> Generating...'
            : btn === btnRegeneratePlan
              ? '<i class="fas fa-sync-alt"></i> Regenerate Plan'
              : '<i class="fas fa-magic"></i> Generate Today\'s Plan';
        }
      });
    };

    try {
      setGeneratingState(true);
      const byok = getBYOKConfig();
      const body = byok
        ? {
            provider: byok.provider,
            api_key: byok.api_key,
            model: byok.model,
          }
        : {};

      const res = await fetch("/api/planner/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": getCSRFToken(),
        },
        body: JSON.stringify(body),
      });

      if (!res.ok) throw new Error("Planner endpoint failed");
      const data = await res.json();

      if (data.success) {
        if (typeof window.handleGamificationUpdate === "function") {
          window.handleGamificationUpdate(data.gamification);
        }
        showToast(
          data.fallback
            ? "📋 Generated Daily Plan (Local Priority fallback)"
            : "✨ AI Daily Plan Generated!",
        );
        if (typeof window.confetti === "function") {
          window.confetti();
        }
        window.loadDailyPlan();
      } else {
        throw new Error(data.error || "Failed to generate plan");
      }
    } catch (err) {
      console.error(err);
      showToast(err.message, "error");
    } finally {
      setGeneratingState(false);
    }
  };

  if (btnGeneratePlan)
    btnGeneratePlan.addEventListener("click", window.generateDailyPlan);
  if (btnGeneratePlanEmpty)
    btnGeneratePlanEmpty.addEventListener("click", window.generateDailyPlan);
  if (btnRegeneratePlan) {
    btnRegeneratePlan.addEventListener("click", () => {
      if (
        confirm(
          "Are you sure you want to regenerate today's schedule? It will recalculate based on current priorities.",
        )
      ) {
        window.generateDailyPlan();
      }
    });
  }

  if (btnStartFocus) {
    btnStartFocus.addEventListener("click", () => {
      showToast("🚀 Session started! Focus on the current task.");
    });
  }

  window.updateCountdownTimers = () => {
    document.querySelectorAll(".deadline-countdown").forEach((el) => {
      const deadlineStr = el.dataset.deadline;
      if (!deadlineStr) return;
      const deadlineDate = new Date(deadlineStr.replace(" ", "T"));
      if (isNaN(deadlineDate)) return;

      const now = new Date();
      const diffMs = deadlineDate - now;
      if (diffMs <= 0) {
        el.innerHTML = `<span style="color: #ff6b6b;"><i class="fas fa-exclamation-triangle"></i> Overdue</span>`;
      } else {
        const days = Math.floor(diffMs / (1000 * 60 * 60 * 24));
        const hours = Math.floor(
          (diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60),
        );
        const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));

        let displayParts = [];
        if (days > 0) displayParts.push(`${days} Days`);
        if (hours > 0 || days > 0) displayParts.push(`${hours} Hours`);
        displayParts.push(`${minutes} Minutes`);

        el.innerHTML = `<i class="far fa-hourglass"></i> Due in ${displayParts.join(" ")}`;
      }
    });
  };

  window.updateRiskDashboardOverview = (tasks) => {
    const counts = { Safe: 0, Attention: 0, Critical: 0, Overdue: 0 };
    let highestPrioTask = null;
    let highestScore = -1;

    const activeTasks = (tasks || []).filter((t) => t.status !== "Completed");

    activeTasks.forEach((task) => {
      const risk = task.risk_level || "Safe";
      if (risk === "Critical") counts.Critical++;
      else if (risk === "High" || risk === "High Risk") counts.Critical++;
      else if (risk === "Attention" || risk === "Medium") counts.Attention++;
      else if (risk === "Overdue") counts.Overdue++;
      else counts.Safe++;

      const score = task.priority_score || 0;
      if (score > highestScore) {
        highestScore = score;
        highestPrioTask = task;
      }
    });

    const elSafe = document.getElementById("risk-count-safe");
    const elAttention = document.getElementById("risk-count-attention");
    const elCritical = document.getElementById("risk-count-critical");
    const elOverdue = document.getElementById("risk-count-overdue");
    const elHighestTitle = document.getElementById(
      "highest-priority-task-title",
    );
    const elBadge = document.getElementById("overall-productivity-risk-badge");

    if (elSafe) elSafe.textContent = counts.Safe;
    if (elAttention) elAttention.textContent = counts.Attention;
    if (elCritical) elCritical.textContent = counts.Critical;
    if (elOverdue) elOverdue.textContent = counts.Overdue;

    if (elHighestTitle) {
      elHighestTitle.textContent = highestPrioTask
        ? `${highestPrioTask.title} (Priority Score: ${highestScore}/100)`
        : "None";
    }

    if (elBadge) {
      let overallRisk = "Safe";
      let badgeColor = "#2ecc71";
      let badgeBg = "rgba(46, 204, 113, 0.15)";

      if (counts.Overdue > 0 || counts.Critical > 0) {
        overallRisk = "Critical";
        badgeColor = "#ff6b6b";
        badgeBg = "rgba(255, 107, 107, 0.15)";
      } else if (counts.Attention > 0) {
        overallRisk = "Attention";
        badgeColor = "#f1c40f";
        badgeBg = "rgba(241, 196, 15, 0.15)";
      }

      elBadge.textContent = overallRisk;
      elBadge.style.color = badgeColor;
      elBadge.style.background = badgeBg;
      elBadge.style.borderColor = badgeColor + "55";
    }
  };

  window.loadProductivityDashboard = async (tasks) => {
    const emptyState = document.getElementById("dashboard-empty-state");
    const mainContent = document.getElementById("dashboard-main-content");
    if (!emptyState || !mainContent) return;

    if (!tasks) tasks = [];
    emptyState.style.display = "none";
    mainContent.style.display = "flex";

    const total = tasks.length;
    const completed = tasks.filter((t) => t.status === "Completed").length;
    const pending = tasks.filter(
      (t) => t.status !== "Completed" && t.status !== "Cancelled",
    ).length;
    const critical = tasks.filter(
      (t) =>
        t.status !== "Completed" &&
        (t.risk_level === "Critical" || t.priority_score >= 90),
    ).length;
    const prodScore = total > 0 ? Math.round((completed / total) * 100) : 100;

    const activeTasks = tasks.filter(
      (t) => t.status !== "Completed" && t.status !== "Cancelled",
    );
    let avgProb = 100;
    if (activeTasks.length > 0) {
      const sum = activeTasks.reduce(
        (acc, curr) => acc + (curr.completion_probability || 0),
        0,
      );
      avgProb = Math.round(sum / activeTasks.length);
    }

    const animateStat = (id, endVal, suffix = "") => {
      const el = document.getElementById(id);
      if (!el) return;
      const prev = parseInt(el.dataset.prevVal || "0", 10);
      el.dataset.prevVal = endVal;

      let startTimestamp = null;
      const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / 250, 1);
        const val = Math.floor(progress * (endVal - prev) + prev);
        el.textContent = val + suffix;
        if (progress < 1) {
          window.requestAnimationFrame(step);
        } else {
          el.textContent = endVal + suffix;
        }
      };
      window.requestAnimationFrame(step);
    };

    animateStat("dash-total-tasks", total);
    animateStat("dash-completed-today", completed);
    animateStat("dash-pending-tasks", pending);
    animateStat("dash-critical-tasks", critical);
    animateStat("dash-productivity-score", prodScore, "%");
    animateStat("dash-completion-probability", avgProb, "%");

    let highestPrioTask = null;
    let highestScore = -1;
    activeTasks.forEach((t) => {
      const score = t.priority_score || 0;
      if (score > highestScore) {
        highestScore = score;
        highestPrioTask = t;
      }
    });

    const elHighestTask = document.getElementById("dash-highest-priority-task");
    if (elHighestTask) {
      elHighestTask.textContent = highestPrioTask
        ? `${highestPrioTask.title} (Priority Score: ${highestScore}/100)`
        : "No active tasks found. Start by creating a task!";
    }

    const elFocusTitle = document.getElementById("focus-task-title");
    const elFocusDesc = document.getElementById("focus-task-desc");
    const elFocusTime = document.getElementById("focus-task-time");
    const elFocusPrio = document.getElementById("focus-task-priority");
    const elFocusRisk = document.getElementById("focus-task-risk");
    const elFocusRec = document.getElementById("focus-task-recommendation");

    const btnFocusHighest = document.getElementById("btn-focus-highest-prio");
    const btnFocusStart = document.getElementById("btn-focus-start-working");

    if (highestPrioTask) {
      if (elFocusTitle) elFocusTitle.textContent = highestPrioTask.title;
      if (elFocusDesc)
        elFocusDesc.textContent =
          highestPrioTask.description || "No description provided.";
      if (elFocusTime)
        elFocusTime.innerHTML = `<i class="far fa-clock"></i> ${highestPrioTask.estimated_duration || "1 Hour"}`;
      if (elFocusPrio) {
        elFocusPrio.textContent = `Prio: ${highestPrioTask.priority || "Medium"} (${highestScore})`;
        let pColor = "#f1c40f";
        if (highestScore >= 90) pColor = "#ff6b6b";
        else if (highestScore >= 70) pColor = "#e67e22";
        else if (highestScore < 40) pColor = "#2ecc71";
        elFocusPrio.style.color = pColor;
        elFocusPrio.style.background = pColor + "1c";
      }
      if (elFocusRisk) {
        const risk = highestPrioTask.risk_level || "Safe";
        elFocusRisk.textContent = `Risk: ${risk}`;
        let rColor = "#2ecc71";
        if (risk === "Critical" || risk === "High Risk") rColor = "#ff6b6b";
        else if (risk === "Attention" || risk === "Medium") rColor = "#f1c40f";
        elFocusRisk.style.color = rColor;
        elFocusRisk.style.background = rColor + "1c";
      }
      if (elFocusRec)
        elFocusRec.textContent =
          highestPrioTask.suggested_action ||
          "Execute recommended focus step immediately.";
      if (btnFocusHighest) btnFocusHighest.style.display = "";
      if (btnFocusStart) btnFocusStart.style.display = "";
    } else {
      if (elFocusTitle) elFocusTitle.textContent = "All Caught Up!";
      if (elFocusDesc)
        elFocusDesc.textContent = "You have no unfinished tasks.";
      if (elFocusTime)
        elFocusTime.innerHTML = `<i class="far fa-clock"></i> 0 Min`;
      if (elFocusPrio) elFocusPrio.textContent = "--";
      if (elFocusRisk) elFocusRisk.textContent = "--";
      if (elFocusRec)
        elFocusRec.textContent =
          "Create a new task to receive optimized AI productivity recommendations.";
      if (btnFocusHighest) btnFocusHighest.style.display = "none";
      if (btnFocusStart) btnFocusStart.style.display = "none";
    }

    const safeCount = activeTasks.filter(
      (t) => (t.risk_level || "Safe") === "Safe",
    ).length;
    const attentionCount = activeTasks.filter(
      (t) => t.risk_level === "Attention" || t.risk_level === "Medium",
    ).length;
    const highCount = activeTasks.filter(
      (t) => t.risk_level === "High" || t.risk_level === "High Risk",
    ).length;
    const critCount = activeTasks.filter(
      (t) => t.risk_level === "Critical",
    ).length;
    const overdueCount = activeTasks.filter(
      (t) => t.status === "Overdue",
    ).length;

    const elSafe = document.getElementById("risk-stat-safe");
    const elAttention = document.getElementById("risk-stat-attention");
    const elHigh = document.getElementById("risk-stat-high");
    const elCrit = document.getElementById("risk-stat-critical");
    const elOverdue = document.getElementById("risk-stat-overdue");

    if (elSafe) elSafe.textContent = safeCount;
    if (elAttention) elAttention.textContent = attentionCount;
    if (elHigh) elHigh.textContent = highCount;
    if (elCrit) elCrit.textContent = critCount;
    if (elOverdue) elOverdue.textContent = overdueCount;

    const safeRatio = total > 0 ? safeCount / total : 1.0;
    const ringPercent = Math.round(safeRatio * 100);

    const elRingPercent = document.getElementById("risk-ring-percent");
    if (elRingPercent) elRingPercent.textContent = ringPercent + "%";

    const ring = document.getElementById("risk-progress-ring");
    if (ring) {
      const circ = 339.29;
      const offset = circ - circ * safeRatio;
      ring.style.strokeDashoffset = offset;
    }

    window.loadTimelineSlots();
    window.loadDeadlineMonitor(activeTasks);
    window.loadRecentActivities();
    window.loadAIInsights();
  };

  window.loadTimelineSlots = async () => {
    const list = document.getElementById("dash-timeline-list");
    if (!list) return;

    try {
      const res = await fetch("/api/planner/current");
      if (!res.ok) throw new Error("Timeline fetch failed");
      const data = await res.json();

      list.innerHTML = "";
      if (data.plan && data.plan.length > 0) {
        data.plan.forEach((slot) => {
          const card = document.createElement("div");
          card.className = "card glass";
          card.style.padding = "10px 12px";
          card.style.display = "flex";
          card.style.justifyContent = "space-between";
          card.style.alignItems = "center";
          card.style.fontSize = "12px";
          card.style.borderLeft =
            slot.type === "break"
              ? "3px solid #a881d8"
              : "3px solid var(--mint)";
          card.style.cursor = slot.id ? "pointer" : "default";
          card.style.transition = "background 0.2s";

          if (slot.id) {
            card.onclick = () => {
              if (typeof window.openEditTaskModal === "function") {
                window.openEditTaskModal(slot.id);
              }
            };
          }

          let typeEmoji = slot.type === "break" ? "☕" : "📋";
          let durationBadge = `<span style="font-size: 10px; opacity: 0.6;">${slot.start_time} - ${slot.end_time}</span>`;

          card.innerHTML = `
            <div style="display: flex; align-items: center; gap: 8px;">
              <span>${typeEmoji}</span>
              <div style="display: flex; flex-direction: column; text-align: left;">
                <strong>${slot.title}</strong>
                ${durationBadge}
              </div>
            </div>
            <span style="font-size: 10px; font-weight: 600; text-transform: uppercase; color: ${slot.priority === "High" ? "#ff6b6b" : "rgba(255,255,255,0.4)"};">${slot.priority}</span>
          `;
          list.appendChild(card);
        });
      } else {
        list.innerHTML = `
          <p style="color: rgba(255,255,255,0.5); font-size: 12px; text-align: center; padding: 20px 0; width: 100%;">
            No timeline schedule created for today. Click "Generate Plan" to optimize your time.
          </p>
        `;
      }
    } catch (err) {
      console.error(err);
    }
  };

  window.loadDeadlineMonitor = (activeTasks) => {
    const list = document.getElementById("dash-deadline-list");
    if (!list) return;

    list.innerHTML = "";
    const groups = { Overdue: [], Today: [], Tomorrow: [], "This Week": [] };
    const now = new Date();
    const todayStr = now.toISOString().slice(0, 10);

    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const tomorrowStr = tomorrow.toISOString().slice(0, 10);

    activeTasks.forEach((t) => {
      if (!t.deadline) return;
      const dDate = new Date(t.deadline.replace(" ", "T"));
      if (isNaN(dDate)) return;

      const diffMs = dDate - now;
      const dStr = t.deadline.slice(0, 10);

      if (diffMs <= 0 || t.status === "Overdue") {
        groups.Overdue.push(t);
      } else if (dStr === todayStr) {
        groups.Today.push(t);
      } else if (dStr === tomorrowStr) {
        groups.Tomorrow.push(t);
      } else if (diffMs > 0 && diffMs <= 7 * 24 * 60 * 60 * 1000) {
        groups["This Week"].push(t);
      }
    });

    let count = 0;
    for (const [groupName, items] of Object.entries(groups)) {
      if (items.length > 0) {
        count += items.length;
        const header = document.createElement("div");
        header.style.fontSize = "10px";
        header.style.fontWeight = "700";
        header.style.textTransform = "uppercase";
        header.style.color =
          groupName === "Overdue" ? "#ff6b6b" : "var(--mint)";
        header.style.marginTop = "6px";
        header.style.letterSpacing = "0.5px";
        header.textContent = groupName;
        list.appendChild(header);

        items.forEach((item) => {
          const row = document.createElement("div");
          row.style.background = "rgba(255,255,255,0.02)";
          row.style.border = "1px solid rgba(255,255,255,0.05)";
          row.style.padding = "8px 12px";
          row.style.borderRadius = "8px";
          row.style.fontSize = "12px";
          row.style.display = "flex";
          row.style.justifyContent = "space-between";
          row.style.alignItems = "center";
          row.style.cursor = "pointer";
          row.onclick = () => {
            if (typeof window.openEditTaskModal === "function") {
              window.openEditTaskModal(item.id);
            }
          };

          row.innerHTML = `
            <span>${item.title}</span>
            <div class="deadline-countdown" data-deadline="${item.deadline}" style="font-size: 10px; font-weight: 600; color: ${groupName === "Overdue" ? "#ff6b6b" : "var(--mint)"};"></div>
          `;
          list.appendChild(row);
        });
      }
    }

    if (count === 0) {
      list.innerHTML = `
        <p style="color: rgba(255,255,255,0.5); font-size: 12px; text-align: center; padding: 20px 0; width: 100%;">No active deadlines detected.</p>
      `;
    } else {
      if (typeof window.updateCountdownTimers === "function") {
        window.updateCountdownTimers();
      }
    }
  };

  window.loadRecentActivities = async () => {
    const list = document.getElementById("dash-activity-feed");
    if (!list) return;

    try {
      const res = await fetch("/api/activity/recent");
      if (!res.ok) throw new Error("Activity fetch failed");
      const data = await res.json();

      list.innerHTML = "";
      if (data.activities && data.activities.length > 0) {
        data.activities.forEach((act) => {
          const item = document.createElement("div");
          item.style.display = "flex";
          item.style.gap = "10px";
          item.style.fontSize = "12px";
          item.style.alignItems = "flex-start";
          item.style.padding = "6px 0";
          item.style.borderBottom = "1px solid rgba(255,255,255,0.04)";

          let icon = "fa-info-circle";
          let color = "rgba(255,255,255,0.4)";
          if (act.activity_type === "Task Created") {
            icon = "fa-plus-circle";
            color = "var(--mint)";
          } else if (act.activity_type === "Task Finished") {
            icon = "fa-check-circle";
            color = "#2ecc71";
          } else if (act.activity_type === "Task Deleted") {
            icon = "fa-trash-alt";
            color = "#ff6b6b";
          } else if (act.activity_type === "Subtask Completed") {
            icon = "fa-check-double";
            color = "#3498db";
          } else if (act.activity_type === "Planner Generated") {
            icon = "fa-calendar-check";
            color = "#9b59b6";
          } else if (act.activity_type === "Panic Mode Detected") {
            icon = "fa-radiation";
            color = "#e74c3c";
          } else if (act.activity_type === "Deadline Detected") {
            icon = "fa-exclamation-triangle";
            color = "#e67e22";
          }

          let timeDisplay = act.timestamp;
          try {
            const date = new Date(act.timestamp.replace(" ", "T"));
            if (!isNaN(date)) {
              timeDisplay = date.toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              });
            }
          } catch (e) {}

          item.innerHTML = `
            <i class="fas ${icon}" style="color: ${color}; margin-top: 3px; font-size: 13px;"></i>
            <div style="display: flex; flex-direction: column; flex: 1; text-align: left;">
              <span style="color: #ffffff;">${act.details}</span>
              <span style="font-size: 9px; color: rgba(255,255,255,0.4);">${timeDisplay}</span>
            </div>
          `;
          list.appendChild(item);
        });
      } else {
        list.innerHTML = `
          <p style="color: rgba(255,255,255,0.5); font-size: 12px; text-align: center; padding: 20px 0; width: 100%;">No activities logged yet.</p>
        `;
      }
    } catch (err) {
      console.error(err);
    }
  };

  window.loadAIInsights = async () => {
    const container = document.getElementById("dash-insights-container");
    if (!container) return;

    try {
      let params = new URLSearchParams();
      const byok = window.getLLMConfig ? window.getLLMConfig() : {};
      if (byok && byok.apiKey) {
        params.append("apiKey", byok.apiKey);
        params.append("provider", byok.provider);
        params.append("model", byok.model);
      }

      const res = await fetch(
        `/api/productivity/insights?${params.toString()}`,
      );
      if (!res.ok) throw new Error("Insights fetch failed");
      const data = await res.json();

      container.innerHTML = "";
      if (data.insights && data.insights.length > 0) {
        data.insights.forEach((insight) => {
          const card = document.createElement("div");
          card.style.background = "rgba(255,255,255,0.02)";
          card.style.border = "1px solid rgba(255,255,255,0.05)";
          card.style.padding = "10px 12px";
          card.style.borderRadius = "8px";
          card.style.fontSize = "12px";
          card.style.display = "flex";
          card.style.alignItems = "center";
          card.style.gap = "8px";
          card.style.textAlign = "left";

          let icon = "fa-chart-line";
          if (insight.includes("busy") || insight.includes("packed"))
            icon = "fa-calendar-day";
          else if (
            insight.includes("overdue") ||
            insight.includes("immediately")
          )
            icon = "fa-exclamation-triangle";
          else if (insight.includes("priority") || insight.includes("first"))
            icon = "fa-star";
          else if (insight.includes("prob") || insight.includes("success"))
            icon = "fa-percentage";

          card.innerHTML = `
            <i class="fas ${icon}" style="color: var(--mint); font-size: 13px; flex-shrink: 0;"></i>
            <span style="color: rgba(255,255,255,0.85);">${insight}</span>
          `;
          container.appendChild(card);
        });
      } else {
        container.innerHTML = `
          <div style="background: rgba(255,255,255,0.02); padding: 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.04); font-size: 12px;">
            <i class="fas fa-check-circle" style="color: var(--mint); margin-right: 6px;"></i> Workload cleared: no priority insights found.
          </div>
        `;
      }
    } catch (err) {
      console.error(err);
      container.innerHTML = `
        <div style="background: rgba(255,255,255,0.02); padding: 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.04); font-size: 12px;">
          <i class="fas fa-exclamation-triangle" style="color: #ff6b6b; margin-right: 6px;"></i> Failed to load AI insights.
        </div>
      `;
    }
  };

  window.triggerPanicMode = async () => {
    if (
      !confirm(
        "🚨 Are you sure you want to activate Panic Mode? This will boost all active task urgencies to Critical and set high priority rankings across the board!",
      )
    ) {
      return;
    }

    try {
      const res = await fetch("/api/panic_mode", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": getCSRFToken(),
        },
      });
      if (!res.ok) throw new Error("Panic mode endpoint failed");
      const data = await res.json();

      if (data.success) {
        showToast("🚨 PANIC MODE ACTIVATED: Backlog boosted!", "warning");

        if (typeof window.showCustomAlert === "function") {
          const stepList = data.steps.map((s) => `<li>${s}</li>`).join("");
          window.showCustomAlert({
            title: "🚨 Panic Mode Recovery Plan",
            message: `
              <div style="text-align: left; font-size: 13px;">
                <p style="color: #ff6b6b; font-weight: 600; margin-top: 0;">We sorted and prioritized all your active tasks to get you back on track. Follow this checklist:</p>
                <ul style="margin: 10px 0; padding-left: 20px; display: flex; flex-direction: column; gap: 8px; color: rgba(255,255,255,0.8);">
                  ${stepList}
                </ul>
              </div>
            `,
            confirmText: "Acknowledge",
          });
        }

        if (typeof window.fetchTasks === "function") {
          window.fetchTasks();
        }
      } else {
        showToast(data.message || "Failed to trigger panic mode.", "error");
      }
    } catch (err) {
      console.error(err);
      showToast(err.message, "error");
    }
  };

  // Add click listeners to dashboard buttons
  const bindDashboardEvents = () => {
    const btnPanicHero = document.getElementById("btn-panic-mode-hero");
    const btnPanicDash = document.getElementById("btn-panic-mode-dash");
    const btnGenPlanDash = document.getElementById("btn-generate-plan-dash");
    const btnGenPlanDashFooter = document.getElementById(
      "btn-generate-plan-dash-footer",
    );
    const btnRefreshInsights = document.getElementById(
      "btn-refresh-insights-dash",
    );
    const btnRefreshAnalysis = document.getElementById(
      "btn-refresh-analysis-dash",
    );
    const btnGlobalRefresh = document.getElementById("btn-global-refresh");

    const btnFocusHighest = document.getElementById("btn-focus-highest-prio");
    const btnFocusStart = document.getElementById("btn-focus-start-working");

    if (btnPanicHero) btnPanicHero.onclick = window.triggerPanicMode;
    if (btnPanicDash) btnPanicDash.onclick = window.triggerPanicMode;

    if (btnGenPlanDash) btnGenPlanDash.onclick = window.generateDailyPlan;
    if (btnGenPlanDashFooter)
      btnGenPlanDashFooter.onclick = window.generateDailyPlan;

    if (btnRefreshInsights) btnRefreshInsights.onclick = window.loadAIInsights;
    if (btnRefreshAnalysis) btnRefreshAnalysis.onclick = window.fetchTasks;
    if (btnGlobalRefresh) btnGlobalRefresh.onclick = window.fetchTasks;

    const handleFocusStart = () => {
      showToast("🚀 Session started! Focus on the current task.");
    };
    if (btnFocusHighest) btnFocusHighest.onclick = handleFocusStart;
    if (btnFocusStart) btnFocusStart.onclick = handleFocusStart;
  };

  // Proactive AI Coach Drawer functions and bindings
  window.loadAICoach = async () => {
    const greeting = document.getElementById("coach-greeting");
    const rec = document.getElementById("coach-top-recommendation");
    const focus = document.getElementById("coach-current-focus");
    const nextS = document.getElementById("coach-next-suggested");
    const deadline = document.getElementById("coach-upcoming-deadline");
    const motivation = document.getElementById("coach-motivation");
    const eta = document.getElementById("coach-finish-eta");

    try {
      const res = await window.fetchWithRetry("/api/coach/analyze");
      if (!res.ok) throw new Error("Coach fetch failed");
      const data = await res.json();

      if (data.success && data.coach) {
        const coach = data.coach;
        if (greeting) greeting.textContent = coach.greeting;
        if (rec) rec.textContent = coach.top_recommendation;
        if (focus) focus.textContent = coach.current_focus;
        if (nextS) nextS.textContent = coach.next_suggested_task;
        if (deadline) deadline.textContent = coach.upcoming_deadline;
        if (motivation) motivation.textContent = coach.today_motivation;
        if (eta) eta.textContent = coach.estimated_finish_time;

        window.checkSmartNotifications(coach);
      }
    } catch (err) {
      console.error("Failed to load AI Coach data:", err);
    }
  };

  window.checkSmartNotifications = async (coach) => {
    // 1. Critical Risk check
    if (coach.top_recommendation && coach.top_recommendation.startsWith("⚠️")) {
      const key = `notified_critical_${coach.current_focus}`;
      if (!sessionStorage.getItem(key)) {
        showToast(coach.top_recommendation, "warning");
        sessionStorage.setItem(key, "true");
      }
    }

    // 2. One Task Away check
    if (coach.total_active_count === 1 && coach.completed_today_count > 0) {
      const key = "notified_one_away";
      if (!sessionStorage.getItem(key)) {
        showToast("🎯 You're only one task away from today's goal!", "success");
        sessionStorage.setItem(key, "true");
      }
    }

    // 3. Ahead of Schedule check
    if (coach.avg_prob >= 90 && coach.completed_today_count >= 3) {
      const key = "notified_ahead";
      if (!sessionStorage.getItem(key)) {
        showToast("🎉 Excellent! You're ahead of schedule.", "success");
        sessionStorage.setItem(key, "true");
      }
    }

    // 4. Planned Task check
    try {
      const pRes = await fetch("/api/planner/current");
      if (pRes.ok) {
        const pData = await pRes.json();
        if (pData.plan && pData.plan.length > 0) {
          const nowStr = new Date().toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
            hour12: false,
          });
          pData.plan.forEach((slot) => {
            if (slot.start_time === nowStr && slot.type !== "break") {
              const key = `notified_planner_${slot.title}_${slot.start_time}`;
              if (!sessionStorage.getItem(key)) {
                showToast(
                  `📅 Time to begin your next planned task: ${slot.title}`,
                  "info",
                );
                sessionStorage.setItem(key, "true");
              }
            }
          });
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  // AI Coach Drawer Bindings
  const coachToggle = document.getElementById("coach-toggle-btn");
  const coachDrawer = document.getElementById("coach-drawer");
  const coachClose = document.getElementById("coach-drawer-close");
  const coachRefreshBtn = document.getElementById("btn-coach-refresh");

  if (coachToggle && coachDrawer) {
    coachToggle.addEventListener("click", () => {
      const isShowing = coachDrawer.classList.contains("show");
      if (isShowing) {
        coachDrawer.classList.remove("show");
      } else {
        coachDrawer.classList.add("show");
        window.loadAICoach();
      }
    });
  }
  if (coachClose && coachDrawer) {
    coachClose.addEventListener("click", () => {
      coachDrawer.classList.remove("show");
    });
  }
  // Click outside to close (without overlay)
  document.addEventListener("click", (e) => {
    if (coachDrawer && coachDrawer.classList.contains("show")) {
      if (
        !coachDrawer.contains(e.target) &&
        e.target !== coachToggle &&
        !coachToggle.contains(e.target)
      ) {
        coachDrawer.classList.remove("show");
      }
    }
  });
  if (coachRefreshBtn) {
    coachRefreshBtn.addEventListener("click", () => {
      window.loadAICoach();
    });
  }

  // Bind on fetch completion
  const oldFetchTasks = window.fetchTasks;
  window.fetchTasks = async (...args) => {
    await oldFetchTasks(...args);
    bindDashboardEvents();
    window.loadAICoach();
  };

  // --- 🚨 Panic Mode Client Controller ---
  const panicToggle = document.getElementById("panic-toggle-btn");
  const panicModal = document.getElementById("panic-modal");
  const panicClose = document.getElementById("panic-modal-close");
  const btnPanicRecover = document.getElementById("btn-panic-recover");

  let activePanicTasks = []; // Stored local active tasks
  let originalPanicData = null; // Original backend response data

  window.openPanicMode = async () => {
    if (!panicModal) return;
    panicModal.classList.add("show");

    // Set initial loading states
    document.getElementById("panic-stat-remaining").textContent = "...";
    document.getElementById("panic-stat-critical").textContent = "...";
    document.getElementById("panic-stat-work").textContent = "...";
    document.getElementById("panic-stat-available").textContent = "...";
    document.getElementById("panic-stat-risk").textContent = "...";
    document.getElementById("panic-stat-prob").textContent = "...";
    document.getElementById("panic-survival-value").textContent = "...";
    document.getElementById("panic-motivation-text").textContent =
      "Evaluating emergency recovery plans...";

    try {
      const response = await window.fetchWithRetry("/api/panic/analyze");
      const data = await response.json();
      
      if (data.success && data.panic) {
        originalPanicData = data.panic;
        
        // Grab task structures to simulate
        const taskResp = await window.fetchWithRetry("/api/tasks");
        const tasksData = await taskResp.json();
        const allTasks = tasksData.tasks || [];
        activePanicTasks = allTasks.filter(
          (t) => t.status !== "Completed" && t.status !== "Cancelled",
        );

        renderPanicReport(data.panic);
        renderPanicSimulator(activePanicTasks);
      } else {
        showToast("Failed to compile emergency report.", "error");
      }
    } catch (err) {
      console.error(err);
      showToast("Error establishing connection to Emergency Engine.", "error");
    }
  };

  function renderPanicReport(panic) {
    const sit = panic.situation;

    document.getElementById("panic-stat-remaining").textContent =
      sit.remaining_tasks;
    document.getElementById("panic-stat-critical").textContent =
      sit.critical_tasks;

    const workHours = Math.floor(sit.estimated_work_mins / 60);
    const workMins = sit.estimated_work_mins % 60;
    document.getElementById("panic-stat-work").textContent =
      `${workHours}h ${workMins}m`;

    const availHours = Math.floor(sit.time_available_mins / 60);
    const availMins = sit.time_available_mins % 60;
    document.getElementById("panic-stat-available").textContent =
      `${availHours}h ${availMins}m`;

    const riskEl = document.getElementById("panic-stat-risk");
    riskEl.textContent = sit.overall_risk;
    if (sit.overall_risk === "CRITICAL" || sit.overall_risk === "HIGH") {
      riskEl.style.color = "#ff3838";
    } else if (sit.overall_risk === "MEDIUM") {
      riskEl.style.color = "#ff8225";
    } else {
      riskEl.style.color = "var(--mint)";
    }

    document.getElementById("panic-stat-prob").textContent =
      `${sit.completion_probability}%`;
    document.getElementById("panic-survival-value").textContent =
      `${sit.survival_score}%`;
    document.getElementById("panic-motivation-text").textContent =
      panic.motivation;

    // Draw SVG circle
    const circle = document.getElementById("panic-survival-circle");
    if (circle) {
      const radius = 60;
      const circumference = 2 * Math.PI * radius;
      const offset = circumference - (sit.survival_score / 100) * circumference;
      circle.style.strokeDashoffset = offset;
    }

    // Render timeline
    renderPanicTimeline(panic.timeline);
  }

  function renderPanicTimeline(timeline) {
    const container = document.getElementById("panic-timeline-container");
    if (!container) return;

    if (!timeline || timeline.length === 0) {
      container.innerHTML = `<div style="text-align: center; color: rgba(255,255,255,0.4); padding: 20px; font-size: 13px;">No tasks on the emergency deck!</div>`;
      return;
    }

    container.innerHTML = timeline
      .map((item) => {
        let color = "rgba(255,255,255,0.5)";
        let border = "1px solid rgba(255,255,255,0.06)";
        let badgeBg = "rgba(255,255,255,0.05)";

        if (item.phase === "RIGHT NOW") {
          color = "#ff3838";
          border = "1px solid rgba(255, 56, 56, 0.3)";
          badgeBg = "rgba(255, 56, 56, 0.15)";
        } else if (item.phase === "NEXT") {
          color = "#ff8225";
          border = "1px solid rgba(255, 130, 37, 0.2)";
          badgeBg = "rgba(255, 130, 37, 0.1)";
        } else if (item.phase === "AFTER THAT") {
          color = "var(--mint)";
          border = "1px solid rgba(55, 230, 181, 0.2)";
          badgeBg = "rgba(55, 230, 181, 0.1)";
        }

        return `
        <div style="display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; background: rgba(255,255,255,0.01); border: ${border}; border-radius: 8px; font-size: 13px;">
          <div style="display: flex; align-items: center; gap: 12px;">
            <span style="font-size: 9px; font-weight: 800; padding: 4px 8px; border-radius: 4px; background: ${badgeBg}; color: ${color}; text-transform: uppercase; letter-spacing: 0.5px;">
              ${item.phase}
            </span>
            <span style="font-weight: 600; color: #ffffff;">${item.title}</span>
          </div>
          <span style="font-size: 11px; color: ${color}; font-weight: 700;">
            <i class="far fa-clock"></i> ${item.duration}
          </span>
        </div>
      `;
      })
      .join("");
  }

  function renderPanicSimulator(tasks) {
    const container = document.getElementById("panic-simulator-list");
    if (!container) return;

    if (tasks.length === 0) {
      container.innerHTML = `<div style="text-align: center; color: rgba(255,255,255,0.3); padding: 10px;">No tasks available to simulate.</div>`;
      return;
    }

    container.innerHTML = tasks
      .map(
        (t) => `
      <div class="panic-simulator-item" style="display: flex; align-items: center; justify-content: space-between; padding: 10px; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); border-radius: 8px; margin-bottom: 8px; transition: all 0.2s;">
        <div style="display: flex; align-items: center; gap: 10px;">
          <input type="checkbox" class="panic-task-checkbox" data-id="${t.id}" checked style="accent-color: #ff3838; width: 16px; height: 16px; cursor: pointer;" />
          <div style="display: flex; flex-direction: column;">
            <span style="font-size: 12.5px; font-weight: 600; color: #ffffff;">${t.title}</span>
            <span style="font-size: 10px; color: rgba(255,255,255,0.4);">${t.category} | ${t.estimated_duration || "45m"}</span>
          </div>
        </div>
        <span style="font-size: 10px; color: ${t.priority === "High" ? "#ff6b6b" : "rgba(255,255,255,0.5)"}; font-weight: 600; text-transform: uppercase;">
          ${t.priority}
        </span>
      </div>
    `,
      )
      .join("");

    // Add checkbox change listeners
    document.querySelectorAll(".panic-task-checkbox").forEach((cb) => {
      cb.addEventListener("change", recalculatePanicSimulator);
    });
  }

  function parseDurationToMins(durationStr) {
    if (!durationStr) return 45;
    try {
      const match = durationStr.match(/(\d+)\s*(hour|hr|min|m)/i);
      if (!match) return 45;
      const num = parseInt(match[1]);
      const unit = match[2].toLowerCase();
      if (unit.startsWith("h")) return num * 60;
      return num;
    } catch {
      return 45;
    }
  }

  function recalculatePanicSimulator() {
    // Collect unchecked task IDs
    const skips = [];
    document.querySelectorAll(".panic-task-checkbox").forEach((cb) => {
      if (!cb.checked) {
        skips.push(parseInt(cb.dataset.id));
      }
    });

    // Filter simulated active tasks
    const simActive = activePanicTasks.filter((t) => !skips.includes(t.id));

    // Run recalculations
    const remainingCount = simActive.length;
    const criticalCount = simActive.filter(
      (t) =>
        t.priority === "High" ||
        t.risk_level === "High" ||
        t.status === "Overdue",
    ).length;
    const totalWorkMins = simActive.reduce(
      (acc, t) => acc + parseDurationToMins(t.estimated_duration),
      0,
    );

    // Remaining time available stays constant from original load
    const timeAvailable = originalPanicData
      ? originalPanicData.situation.time_available_mins
      : 240;

    let prob = 100;
    if (remainingCount > 0) {
      if (totalWorkMins <= timeAvailable) {
        prob = Math.min(
          95,
          Math.round(100 - (totalWorkMins / timeAvailable) * 30),
        );
      } else {
        prob = Math.max(
          10,
          Math.round(100 - (totalWorkMins / timeAvailable) * 50),
        );
      }
    }

    let risk = "LOW";
    if (prob < 40) risk = "CRITICAL";
    else if (prob < 60) risk = "HIGH";
    else if (prob < 80) risk = "MEDIUM";

    const survival = Math.min(100, Math.max(0, Math.round(prob * 1.05)));

    // Update display values
    document.getElementById("panic-stat-remaining").textContent =
      remainingCount;
    document.getElementById("panic-stat-critical").textContent = criticalCount;

    const workHours = Math.floor(totalWorkMins / 60);
    const workMins = totalWorkMins % 60;
    document.getElementById("panic-stat-work").textContent =
      `${workHours}h ${workMins}m`;

    const riskEl = document.getElementById("panic-stat-risk");
    riskEl.textContent = risk;
    if (risk === "CRITICAL" || risk === "HIGH") {
      riskEl.style.color = "#ff3838";
    } else if (risk === "MEDIUM") {
      riskEl.style.color = "#ff8225";
    } else {
      riskEl.style.color = "var(--mint)";
    }

    document.getElementById("panic-stat-prob").textContent = `${prob}%`;
    document.getElementById("panic-survival-value").textContent =
      `${survival}%`;

    // Redraw SVG ring
    const circle = document.getElementById("panic-survival-circle");
    if (circle) {
      const radius = 60;
      const circumference = 2 * Math.PI * radius;
      const offset = circumference - (survival / 100) * circumference;
      circle.style.strokeDashoffset = offset;
    }

    // Recalculate timeline order based on skips
    const sorted = [...simActive].sort(
      (a, b) =>
        (b.priority === "High" || b.status === "Overdue") -
          (a.priority === "High" || a.status === "Overdue") ||
        (b.priority_score || 0) - (a.priority_score || 0),
    );
    const timeline = [];

    // Add active items
    sorted.forEach((t, idx) => {
      let phase = "AFTER THAT";
      if (idx === 0) phase = "RIGHT NOW";
      else if (idx === 1) phase = "NEXT";

      timeline.push({
        phase: phase,
        task_id: t.id,
        title: t.title,
        duration: t.estimated_duration || "45 min",
      });
    });

    // Add skipped items
    activePanicTasks.forEach((t) => {
      if (skips.includes(t.id)) {
        timeline.push({
          phase: "OPTIONAL",
          task_id: t.id,
          title: t.title,
          duration: "Skip Today",
        });
      }
    });

    renderPanicTimeline(timeline);

    // Dynamic simulated motivation
    let advice = "Evaluating your recovery paths...";
    if (skips.length > 0) {
      const successBoost = Math.max(5, Math.min(60, skips.length * 15));
      advice = `Skipping ${skips.length} low-priority work increases your Success Rate by ${successBoost}%. Focus exclusively on ${simActive[0] ? simActive[0].title : "remaining tasks"} first.`;
    } else {
      advice = originalPanicData
        ? originalPanicData.motivation
        : "You can still finish everything if you begin now.";
    }
    document.getElementById("panic-motivation-text").textContent = advice;
  }

  if (panicToggle) {
    panicToggle.addEventListener("click", window.openPanicMode);
  }
  if (panicClose && panicModal) {
    panicClose.addEventListener("click", () => {
      panicModal.classList.remove("show");
    });
  }
  if (btnPanicRecover) {
    btnPanicRecover.addEventListener("click", async () => {
      // Find unchecked task IDs (skips)
      const postponeTaskIds = [];
      document.querySelectorAll(".panic-task-checkbox").forEach((cb) => {
        if (!cb.checked) {
          postponeTaskIds.push(parseInt(cb.dataset.id));
        }
      });

      setStatus("sending", "⚡ Rebuilding and optimizing schedule...");
      showToast("Triggering Emergency Recovery...", "info");

      try {
        const response = await fetch("/api/panic/recover", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRF-Token": getCSRFToken(),
          },
          body: JSON.stringify({ postpone_task_ids: postponeTaskIds }),
        });

        const data = await response.json();
        if (data.success) {
          if (typeof window.handleGamificationUpdate === "function") {
            window.handleGamificationUpdate(data.gamification);
          }
          showToast(data.message, "success");
          panicModal.classList.remove("show");

          // Force a full task and planner reload!
          if (typeof window.fetchTasks === "function") {
            window.fetchTasks();
          }
          if (typeof window.loadPlannerPlan === "function") {
            window.loadPlannerPlan();
          }
        } else {
          showToast("Recovery optimization failed: " + data.error, "error");
        }
      } catch (err) {
        console.error(err);
        showToast("Error connecting to recovery gateway.", "error");
      } finally {
        setStatus("idle");
      }
    });
  }

  // Start intervals
  setInterval(window.updateCountdownTimers, 60000);

  // Hero Mock metrics cycler
  const mockStates = [
    {
      score: "94/100 🔴",
      risk: "Critical Risk",
      riskClass: "risk-glow-red",
      riskColor: "#e74c3c",
      riskBg: "rgba(231, 76, 60, 0.15)",
      scoreColor: "#ff6b6b",
      scoreBg: "rgba(255, 107, 107, 0.15)",
      prob: "84%",
      probWidth: "84%",
    },
    {
      score: "78/100 🟠",
      risk: "High Risk",
      riskClass: "risk-glow-orange",
      riskColor: "#e67e22",
      riskBg: "rgba(230, 126, 34, 0.15)",
      scoreColor: "#e67e22",
      scoreBg: "rgba(230, 126, 34, 0.15)",
      prob: "72%",
      probWidth: "72%",
    },
    {
      score: "52/100 🟡",
      risk: "Attention",
      riskClass: "risk-glow-yellow",
      riskColor: "#f1c40f",
      riskBg: "rgba(241, 196, 15, 0.15)",
      scoreColor: "#f1c40f",
      scoreBg: "rgba(241, 196, 15, 0.15)",
      prob: "48%",
      probWidth: "48%",
    },
    {
      score: "28/100 🟢",
      risk: "Safe",
      riskClass: "risk-glow-green",
      riskColor: "#2ecc71",
      riskBg: "rgba(46, 204, 113, 0.15)",
      scoreColor: "#2ecc71",
      scoreBg: "rgba(46, 204, 113, 0.15)",
      prob: "95%",
      probWidth: "95%",
    },
  ];
  let currentMockState = 0;
  setInterval(() => {
    const elScore = document.getElementById("hero-mock-score");
    const elRisk = document.getElementById("hero-mock-risk");
    const elProb = document.getElementById("hero-mock-prob");
    const elProbBar = document.getElementById("hero-mock-prob-bar");
    if (!elScore && !elRisk && !elProb && !elProbBar) return;

    currentMockState = (currentMockState + 1) % mockStates.length;
    const state = mockStates[currentMockState];

    if (elScore) {
      elScore.textContent = state.score;
      elScore.style.color = state.scoreColor;
      elScore.style.background = state.scoreBg;
      elScore.style.borderColor = state.scoreColor + "55";
    }
    if (elRisk) {
      elRisk.textContent = state.risk;
      elRisk.className = state.riskClass;
      elRisk.style.color = state.riskColor;
      elRisk.style.background = state.riskBg;
      elRisk.style.borderColor = state.riskColor + "55";
    }
    if (elProb) {
      elProb.textContent = state.prob;
    }
    if (elProbBar) {
      elProbBar.style.width = state.probWidth;
    }
  }, 1000);

  window.openRegisterCustomModelModal = () => {
    document.getElementById('customModelProvider').value = 'custom';
    document.getElementById('customModelIdInput').value = '';
    document.getElementById('customModelDisplayNameInput').value = '';
    document.getElementById('customModelDescriptionInput').value = '';
    document.getElementById('customModelContextInput').value = '128000';
    document.getElementById('customModelCapChat').checked = true;
    document.getElementById('customModelCapReasoning').checked = false;
    document.getElementById('customModelCapVision').checked = false;
    document.getElementById('customModelCapAudio').checked = false;
    document.getElementById('customModelCapFunc').checked = false;
    document.getElementById('customModelCapStream').checked = true;
    document.getElementById('registerCustomModelModal').classList.add('show');
  };

  window.closeModalCustom = () => {
    document.getElementById('registerCustomModelModal').classList.remove('show');
  };

  window.submitRegisterCustomModel = async () => {
    const provider = document.getElementById('customModelProvider').value;
    const modelId = document.getElementById('customModelIdInput').value.trim();
    const displayName = document.getElementById('customModelDisplayNameInput').value.trim();
    const description = document.getElementById('customModelDescriptionInput').value.trim();
    const contextWindow = parseInt(document.getElementById('customModelContextInput').value) || 128000;
    
    if (!modelId || !displayName) {
      showToast("Model ID and Display Name are required.", "error");
      return;
    }
    
    const features = {
      supports_chat: document.getElementById('customModelCapChat').checked ? 1 : 0,
      supports_reasoning: document.getElementById('customModelCapReasoning').checked ? 1 : 0,
      supports_vision: document.getElementById('customModelCapVision').checked ? 1 : 0,
      supports_audio: document.getElementById('customModelCapAudio').checked ? 1 : 0,
      supports_function_calling: document.getElementById('customModelCapFunc').checked ? 1 : 0,
      supports_streaming: document.getElementById('customModelCapStream').checked ? 1 : 0,
    };
    
    try {
      const response = await fetch('/api/admin/models/custom', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          provider: provider,
          model_id: modelId,
          display_name: displayName,
          description: description,
          context_window: contextWindow,
          features: features
        })
      });
      
      const data = await response.json();
      if (response.ok && data.success) {
        showToast(`Successfully registered custom model "${displayName}".`, "success");
        window.closeModalCustom();
        if (typeof loadDynamicModels === "function") {
          await loadDynamicModels();
        }
        if (typeof populateAPISettingsDropdowns === "function") {
          await populateAPISettingsDropdowns();
        }
      } else {
        showToast(data.error || 'Failed to register custom model.', "error");
      }
    } catch (err) {
      console.error("Error registering custom model:", err);
      showToast("Failed to register custom model: " + err.message, "error");
    }
  };

  // Load gamification stats on startup
  if (typeof window.loadGamificationStats === "function") {
    window.loadGamificationStats();
  }
});

// --- Gamification System ---
window.celebrateLevelUp = function (newLevel) {
  return new Promise((resolve) => {
    const modal = document.createElement("div");
    modal.className = "mint-custom-modal level-up-celebration-modal";
    modal.style.background = "rgba(10, 10, 10, 0.85)";
    modal.style.backdropFilter = "blur(12px)";
    modal.style.zIndex = "99999";
    modal.innerHTML = `
      <div class="mint-custom-modal-content level-up-content" style="text-align: center; max-width: 400px; padding: 40px 24px; border: 2px solid var(--mint); box-shadow: 0 0 30px rgba(55, 230, 181, 0.3); position: relative; overflow: hidden; animation: modal-pulse 2s infinite alternate;">
        <!-- Glowing effect -->
        <div style="position: absolute; top:-50%; left:-50%; width:200%; height:200%; background: radial-gradient(circle, rgba(55,230,181,0.15) 0%, transparent 60%); pointer-events: none; animation: rotate-glow 15s linear infinite;"></div>

        <div style="font-size: 70px; margin-bottom: 20px; filter: drop-shadow(0 0 15px var(--mint)); animation: bounce-emoji 1s ease infinite alternate;">🎉</div>

        <h2 style="margin: 0 0 8px 0; font-size: 28px; font-weight: 900; background: linear-gradient(135deg, var(--mint), #00d2ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-transform: uppercase; letter-spacing: 1px;">
          Level Up!
        </h2>

        <p style="margin: 0 0 24px 0; font-size: 15px; color: rgba(255,255,255,0.8);">
          Congratulations! You have reached <strong style="color: var(--mint); font-size: 18px;">Level ${newLevel}</strong>!
        </p>

        <div style="display: inline-flex; align-items: center; justify-content: center; width: 100px; height: 100px; border-radius: 50%; background: rgba(55,230,181,0.1); border: 4px solid var(--mint); font-size: 42px; font-weight: 900; color: var(--mint); text-shadow: 0 0 10px rgba(55,230,181,0.5); margin-bottom: 24px;">
          ${newLevel}
        </div>

        <div class="mint-custom-modal-actions" style="margin-top: 0; display: flex; justify-content: center; width: 100%;">
          <button class="btn btn--mint mint-custom-modal-btn-confirm" style="padding: 10px 32px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; box-shadow: 0 4px 15px rgba(55, 230, 181, 0.4);">
            Awesome!
          </button>
        </div>
      </div>
    `;
    document.body.appendChild(modal);

    // Add styling elements to document head
    if (!document.getElementById("level-up-animations")) {
      const style = document.createElement("style");
      style.id = "level-up-animations";
      style.innerHTML = `
        @keyframes bounce-emoji {
          from { transform: translateY(0) scale(1); }
          to { transform: translateY(-10px) scale(1.1); }
        }
        @keyframes rotate-glow {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        @keyframes modal-pulse {
          from { box-shadow: 0 0 25px rgba(55, 230, 181, 0.25); }
          to { box-shadow: 0 0 35px rgba(55, 230, 181, 0.45); }
        }
      `;
      document.head.appendChild(style);
    }

    // Force reflow and show
    modal.offsetHeight;
    modal.classList.add("show");

    const confirmBtn = modal.querySelector(".mint-custom-modal-btn-confirm");
    confirmBtn.focus();

    const close = () => {
      modal.classList.remove("show");
      setTimeout(() => {
        modal.remove();
        resolve();
      }, 200);
    };

    confirmBtn.addEventListener("click", close);
    modal.addEventListener("click", (e) => {
      if (e.target === modal) close();
    });

    const keyHandler = (e) => {
      if (e.key === "Enter" || e.key === "Escape") {
        e.preventDefault();
        document.removeEventListener("keydown", keyHandler);
        close();
      }
    };
    document.addEventListener("keydown", keyHandler);
  });
};

window.handleGamificationUpdate = function (gamification) {
  if (!gamification) return;

  // Reload stats to reflect new progress
  window.loadGamificationStats();

  // Show toast for XP gained
  if (gamification.xp_gained > 0) {
    showToast(
      `+${gamification.xp_gained} XP: ${gamification.reason}`,
      "success",
    );
  }

  // Level up celebration
  if (gamification.level_up) {
    setTimeout(() => {
      window.celebrateLevelUp(gamification.new_level);
      if (typeof triggerConfetti === "function") {
        triggerConfetti();
      }
    }, 500);
  }

  // New badges earned
  if (gamification.new_badges && gamification.new_badges.length > 0) {
    gamification.new_badges.forEach((badge, idx) => {
      setTimeout(
        () => {
          showToast(`🏆 New Badge: ${badge.badge_name}!`, "success");
        },
        1000 + idx * 1500,
      );
    });
  }
};

window.loadGamificationStats = async function () {
  try {
    const res = await fetch("/api/gamification/stats");
    const data = await res.json();
    if (!data.success) return;
    const stats = data.stats;

    // Update Analytics Tab elements if present
    const elLevelText = document.getElementById("gam-level-text");
    if (elLevelText) elLevelText.textContent = stats.level;

    const elLevelBadge = document.getElementById("gam-level-badge");
    if (elLevelBadge) elLevelBadge.textContent = stats.level;

    const elXpText = document.getElementById("gam-xp-text");
    if (elXpText)
      elXpText.textContent = `${stats.xp_in_level} / ${stats.xp_needed} XP`;

    const elStreakText = document.getElementById("gam-streak-text");
    if (elStreakText) elStreakText.textContent = stats.streak;

    const elNextLevel = document.getElementById("gam-next-level");
    if (elNextLevel) elNextLevel.textContent = stats.level + 1;

    const elXpPct = document.getElementById("gam-xp-percent");
    if (elXpPct) elXpPct.textContent = `${stats.progress_pct}%`;

    const elXpBar = document.getElementById("gam-xp-bar");
    if (elXpBar) elXpBar.style.width = `${stats.progress_pct}%`;

    const elAnStreak = document.getElementById("an-streak");
    if (elAnStreak) elAnStreak.textContent = `${stats.streak} days`;

    // Also update analytics tab an-gam-* elements (separate IDs to avoid duplicate ID bug)
    const _s = stats;
    const _set = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.textContent = val;
    };
    _set("an-gam-level-text", _s.level);
    _set("an-gam-streak-text", _s.streak);
    _set("an-gam-next-level", _s.level + 1);
    _set("an-gam-xp-percent", `${_s.progress_pct}%`);
    _set("an-gam-xp-text", `${_s.xp_in_level} / ${_s.xp_needed} XP`);
    const elAnGamBadge = document.getElementById("an-gam-level-badge");
    if (elAnGamBadge) elAnGamBadge.textContent = _s.level;
    const elAnGamBar = document.getElementById("an-gam-xp-bar");
    if (elAnGamBar) elAnGamBar.style.width = `${_s.progress_pct}%`;
    const elAnGamBadges = document.getElementById("an-gam-badges-container");
    if (elAnGamBadges) {
      if (_s.badges && _s.badges.length > 0) {
        elAnGamBadges.innerHTML = _s.badges
          .map(
            (b) =>
              `<div class="glass" style="padding:8px 12px;border-radius:8px;display:flex;align-items:center;gap:8px;border:1px solid rgba(55,230,181,0.3);background:rgba(55,230,181,0.05);min-width:140px;" title="${b.badge_description}"><span style="font-size:20px;">${b.icon}</span><div><div style="font-size:11px;font-weight:bold;color:#fff;">${b.badge_name}</div><div style="font-size:9px;color:rgba(255,255,255,0.6);">${b.badge_description}</div></div></div>`,
          )
          .join("");
      } else {
        elAnGamBadges.innerHTML =
          '<div style="color:rgba(255,255,255,0.3);font-size:12px;width:100%;text-align:center;">No badges earned yet. Complete tasks to earn badges!</div>';
      }
    }

    const elBadgesContainer = document.getElementById("gam-badges-container");
    if (elBadgesContainer) {
      if (stats.badges && stats.badges.length > 0) {
        elBadgesContainer.innerHTML = stats.badges
          .map(
            (b) => `
          <div class="glass" style="padding: 8px 12px; border-radius: 8px; display: flex; align-items: center; gap: 8px; border: 1px solid rgba(55,230,181,0.3); background: rgba(55,230,181,0.05); min-width: 140px;" title="${b.badge_description}">
            <span style="font-size: 20px;">${b.icon}</span>
            <div style="text-align: left;">
              <div style="font-size: 11px; font-weight: bold; color: #ffffff; white-space: nowrap;">${b.badge_name}</div>
              <div style="font-size: 9px; color: rgba(255,255,255,0.6); max-width: 120px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${b.badge_description}</div>
            </div>
          </div>
        `,
          )
          .join("");
      } else {
        elBadgesContainer.innerHTML = `<div style="color:rgba(255,255,255,0.3); font-size:12px; width:100%; text-align:center;">No badges earned yet. Complete tasks, generate plans, and stay productive to earn badges!</div>`;
      }
    }

    // Update Hero Banner Widget elements if present
    const elHeroLevel = document.getElementById("hero-gam-level");
    if (elHeroLevel) elHeroLevel.textContent = `Lvl ${stats.level}`;

    const elHeroXpText = document.getElementById("hero-gam-xp-text");
    if (elHeroXpText)
      elHeroXpText.textContent = `${stats.xp_in_level} / ${stats.xp_needed} XP`;

    const elHeroXpPct = document.getElementById("hero-gam-xp-pct");
    if (elHeroXpPct) elHeroXpPct.textContent = `${stats.progress_pct}%`;

    const elHeroXpBar = document.getElementById("hero-gam-xp-bar");
    if (elHeroXpBar) elHeroXpBar.style.width = `${stats.progress_pct}%`;
  } catch (err) {
    console.error("Error loading gamification stats:", err);
  }
};
