
// Scope localStorage per logged-in user to prevent sharing API keys/settings
(function() {
  const originalGet = Storage.prototype.getItem;
  const originalSet = Storage.prototype.setItem;
  const originalRemove = Storage.prototype.removeItem;

  const prefixableKeys = [
    'apiProvider', 'apiOpenAIKey', 'apiOpenAIModel',
    'apiGeminiKey', 'apiGeminiModel',
    'apiAnthropicKey', 'apiAnthropicModel',
    'apiGroqKey', 'apiGroqModel',
    'apiOpenRouterKey', 'apiOpenRouterModel',
    'apiMistralKey', 'apiMistralModel',
    'chatboxModel', 'chatDraft',
    'theme', 'autoTheme',
    'mint_custom_playlists'
  ];

  function getPrefixedKey(key) {
    const user = window.currentUser || '';
    if (user && prefixableKeys.includes(key)) {
      return `${user}_${key}`;
    }
    return key;
  }

  Storage.prototype.getItem = function(key) {
    return originalGet.call(this, getPrefixedKey(key));
  };

  Storage.prototype.setItem = function(key, value) {
    return originalSet.call(this, getPrefixedKey(key), value);
  };

  Storage.prototype.removeItem = function(key) {
    return originalRemove.call(this, getPrefixedKey(key));
  };
})();

function getProviderLogoHtml(provider, size = 16) {
  provider = (provider || '').toLowerCase();
  if (provider === 'openai') {
    return `<svg class="brand-logo-svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="${size}" height="${size}" fill="#10a37f" style="vertical-align: middle; flex-shrink: 0;">
      <path d="M21.74 11.53c0-.36-.07-.72-.2-1.06-.1-.28-.27-.53-.48-.74l.01-.01c-.13-.15-.29-.27-.47-.36.21-.49.31-1.02.28-1.54-.03-.49-.16-.97-.39-1.4-.24-.46-.6-.84-1.03-1.11-.43-.27-.93-.41-1.43-.41-.33 0-.66.06-.97.17-.18-.17-.4-.3-.64-.38-.34-.58-.84-1.02-1.45-1.27-.6-.24-1.26-.29-1.89-.13a3.85 3.85 0 0 0-1.89 1.1c-.2-.03-.4-.05-.61-.05-1.04 0-2.04.41-2.77 1.15A3.94 3.94 0 0 0 4.7 8.3c-.6.31-1.07.82-1.34 1.44a3.88 3.88 0 0 0 .1 3.52 3.86 3.86 0 0 0 .37.5c-.15.22-.24.47-.28.74-.15.48-.19.98-.12 1.48.06.49.23.96.49 1.38.26.43.62.77 1.05 1 .43.23.91.36 1.4.37.28 0 .56-.04.83-.12.16.14.35.25.56.32.4.52.93.9 1.54 1.1.6.2 1.25.21 1.86.04a3.84 3.84 0 0 0 2-.95c.21.05.42.08.64.08 1.04 0 2.04-.41 2.77-1.15.74-.73 1.15-1.73 1.15-2.77 0-.25-.03-.5-.08-.74.19-.15.35-.34.46-.56.45-.4.77-.92.93-1.5.17-.57.19-1.18.06-1.76zm-8.87 8.1c-.6.28-1.27.32-1.89.12-.6-.2-1.12-.6-1.49-1.13l3.66-2.11c.21-.12.38-.29.5-.5.12-.21.18-.45.18-.69V10.2l2.3 1.33c.09.05.17.13.23.22.06.09.09.2.09.31v4.25c0 .64-.26 1.25-.71 1.7-.45.45-1.06.71-1.7.71a2.38 2.38 0 0 1-1.11-.29zm-7.66-3.8c-.3-.53-.42-1.16-.32-1.77.1-.6.38-1.16.82-1.56l3.66 2.11c.2.12.44.18.68.18s.48-.06.69-.18l4.43-2.56v2.66c0 .1.03.2.08.29a.57.57 0 0 0 .23.23l-3.69 2.13c-.56.32-1.2.45-1.84.36a2.41 2.41 0 0 1-1.58-.91 2.38 2.38 0 0 1-.36-1.84c.1-.64.44-1.22.93-1.63zM4.64 7.68c.28-.6.76-1.07 1.36-1.33.6-.26 1.27-.3 1.89-.1l3.66 2.11c.21.12.38.29.5.5s.18.45.18.69v5.12L9.93 13.4c-.09-.05-.17-.13-.23-.22a.58.58 0 0 1-.09-.31V8.62c0-.64.26-1.25.71-1.7a2.4 2.4 0 0 1 2.81-.42zm7.66 2.5l-3.66-2.11c-.2-.12-.44-.18-.68-.18s-.48.06-.69.18l-4.43 2.56v-2.66c0-.1-.03-.2-.08-.29a.57.57 0 0 0-.23-.23l3.69-2.13a2.39 2.39 0 0 1 3.42.55 2.41 2.41 0 0 1 .36 1.84c-.1.64-.44 1.22-.93 1.63zm3.76-2.5c.3.53.42 1.16.32 1.77-.1.6-.38 1.16-.82 1.56l-3.66-2.11a1.36 1.36 0 0 0-1.37 0l-4.43 2.56V8.8c0-.1-.03-.2-.08-.29a.57.57 0 0 0-.23-.23l3.69-2.13c.56-.32 1.2-.45 1.84-.36a2.41 2.41 0 0 1 1.58.91 2.38 2.38 0 0 1 .36 1.84c-.1.64-.44 1.22-.93 1.63zm2.3 8.1c-.28.6-.76 1.07-1.36 1.33a2.43 2.43 0 0 1-1.89.1l-3.66-2.11c-.21-.12-.38-.29-.5-.5a1.36 1.36 0 0 1-.18-.69V9.82l2.3 1.33c.09.05.17.13.23.22.06.09.09.2.09.31v4.25c0 .64-.26 1.25-.71 1.7a2.4 2.4 0 0 1-2.81.42z"/>
    </svg>`;
  }
  if (provider === 'gemini') {
    return `<svg class="brand-logo-svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="${size}" height="${size}" style="vertical-align: middle; flex-shrink: 0;">
      <path fill="#4285F4" d="M12 2C12 2 12 7.5 6.5 7.5C12 7.5 12 13 12 13C12 13 12 7.5 17.5 7.5C12 7.5 12 2 12 2Z"/>
      <path fill="#ea4335" d="M19 13C19 13 19 15.5 16.5 15.5C19 15.5 19 18 19 18C19 18 19 15.5 21.5 15.5C19 15.5 19 13 19 13Z"/>
    </svg>`;
  }
  if (provider === 'anthropic') {
    return `<svg class="brand-logo-svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="${size}" height="${size}" fill="#cc5843" style="vertical-align: middle; flex-shrink: 0;">
      <path d="M12 2c-.8 0-1.5.7-1.5 1.5v6.3l-4.5-4.5c-.6-.6-1.5-.6-2.1 0s-.6 1.5 0 2.1l4.5 4.5H2c-.8 0-1.5.7-1.5 1.5S1.2 15 2 15h6.4l-4.5 4.5c-.6.6-.6 1.5 0 2.1.3.3.7.4 1.1.4.4 0 .8-.1 1.1-.4l4.5-4.5v6.4c0 .8.7 1.5 1.5 1.5s1.5-.7 1.5-1.5v-6.4l4.5 4.5c.3.3.7.4 1.1.4.4 0 .8-.1 1.1-.4.6-.6.6-1.5 0-2.1l-4.5-4.5H22c.8 0 1.5-.7 1.5-1.5S22.8 12 22 12h-6.4l4.5-4.5c.6-.6.6-1.5 0-2.1s-1.5-.6-2.1 0l-4.5 4.5V3.5C13.5 2.7 12.8 2 12 2z"/>
    </svg>`;
  }
  if (provider === 'groq') {
    return `<svg class="brand-logo-svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="${size}" height="${size}" fill="#eb5757" style="vertical-align: middle; flex-shrink: 0;">
      <path d="M19.5 2.5L3.5 12.5H11.5L9.5 21.5L20.5 10.5H12.5L19.5 2.5Z"/>
    </svg>`;
  }
  if (provider === 'openrouter') {
    return `<svg class="brand-logo-svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="${size}" height="${size}" fill="#7c3aed" style="vertical-align: middle; flex-shrink: 0;">
      <path d="M12 2L2 7v10l10 5 10-5V7L12 2zm0 2.8l7.6 3.8v6.8L12 19.2l-7.6-3.8V8.6L12 4.8zm0 2.8c-2.4 0-4.4 2-4.4 4.4s2 4.4 4.4 4.4 4.4-2 4.4-4.4-2-4.4-4.4-4.4z"/>
    </svg>`;
  }
  if (provider === 'mistral') {
    return `<svg class="brand-logo-svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="${size}" height="${size}" fill="#ff7000" style="vertical-align: middle; flex-shrink: 0;">
      <path d="M2 4h4v12h4V8l4 6 4-6v8h4V4h-4l-4 6-4-6H2z"/>
    </svg>`;
  }
  return '';
}

// DOM Elements
const messagesEl = document.getElementById('messages');
const inputEl = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const statusText = document.getElementById('status-text');
const statusDot = document.getElementById('status-dot');
const typingIndicator = document.getElementById('typing-indicator');
const charCount = document.getElementById('char-count');
const messageCount = document.getElementById('message-count');
const themeToggle = document.getElementById('theme-toggle');
const themeIcon = document.getElementById('theme-icon');
const searchBtn = document.getElementById('search-btn');
const searchPanel = document.getElementById('search-panel');
const searchInput = document.getElementById('search-input');
const searchClose = document.getElementById('search-close');
const clearBtn = document.getElementById('clear-btn');
const exportBtn = document.getElementById('export-btn');
const voiceBtn = document.getElementById('voice-btn');
const shortcuts = document.getElementById('shortcuts');
const timeDisplay = document.getElementById('time-display');
const weatherDisplay = document.getElementById('weather-display');
const weatherTemp = document.getElementById('weather-temp');
const weatherIcon = weatherDisplay.querySelector('i');
const panel = document.querySelector('.panel');
const historyToggle = document.getElementById('history-toggle');
const historyPanel = document.getElementById('history-panel');
const recentChats = document.getElementById('recent-chats');
const newChatBtn = document.getElementById('new-chat-btn');
const hoverPanel = document.getElementById('hover-panel');
const emojiBtn = document.getElementById('emoji-btn');
const emojiPicker = document.getElementById('emoji-picker');
const emojiGrid = document.getElementById('emoji-grid');
const emojiCategories = document.querySelectorAll('.emoji-category');

// State
let inFlight = false;
let messageHistory = [];
let currentTheme = localStorage.getItem('theme') || 'dark';
let autoTheme = localStorage.getItem('autoTheme') === 'true';
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
  smileys: ['😀', '😃', '😄', '😁', '😆', '😅', '🤣', '😂', '🙂', '🙃', '😉', '😊', '😇', '🥰', '😍', '🤩', '😘', '😗', '😚', '😙', '😋', '😛', '😜', '🤪', '😝', '🤑', '🤗', '🤭', '🤫', '🤔', '🤐', '🤨', '😐', '😑', '😶', '😏', '😒', '🙄', '😬', '🤥'],
  people: ['👶', '🧒', '👦', '👧', '🧑', '👱', '👨', '🧔', '👩', '🧓', '👴', '👵', '🙍', '🙎', '🙅', '🙆', '💁', '🙋', '🧏', '🙇', '🤦', '🤷', '👮', '🕵️', '💂', '👷', '🤴', '👸', '👳', '👲', '🧕', '🤵', '👰', '🤰', '🤱', '👼', '🎅', '🤶', '🦸', '🦹'],
  nature: ['🐶', '🐱', '🐭', '🐹', '🐰', '🦊', '🐻', '🐼', '🐨', '🐯', '🦁', '🐮', '🐷', '🐽', '🐸', '🐵', '🙈', '🙉', '🙊', '🐒', '🐔', '🐧', '🐦', '🐤', '🐣', '🐥', '🦆', '🦅', '🦉', '🦇', '🐺', '🐗', '🐴', '🦄', '🐝', '🐛', '🦋', '🐌', '🐞', '🐜'],
  food: ['🍎', '🍐', '🍊', '🍋', '🍌', '🍉', '🍇', '🍓', '🍈', '🍒', '🍑', '🥭', '🍍', '🥥', '🥝', '🍅', '🍆', '🥑', '🥦', '🥬', '🥒', '🌶️', '🌽', '🥕', '🧄', '🧅', '🥔', '🍠', '🥐', '🍞', '🥖', '🥨', '🧀', '🥚', '🍳', '🧈', '🥞', '🧇', '🥓', '🥩'],
  activities: ['⚽', '🏀', '🏈', '⚾', '🥎', '🎾', '🏐', '🏉', '🥏', '🎱', '🪀', '🏓', '🏸', '🏒', '🏑', '🥍', '🏏', '🪃', '🥅', '⛳', '🪁', '🏹', '🎣', '🤿', '🥊', '🥋', '🎽', '🛹', '🛷', '⛸️', '🥌', '🎿', '⛷️', '🏂', '🪂', '🏋️', '🤼', '🤸', '⛹️', '🤺'],
  travel: ['🚗', '🚕', '🚙', '🚌', '🚎', '🏎️', '🚓', '🚑', '🚒', '🚐', '🛻', '🚚', '🚛', '🚜', '🏍️', '🛵', '🚲', '🛴', '🛹', '🛼', '🚁', '🛸', '✈️', '🛩️', '🛫', '🛬', '🪂', '💺', '🚀', '🛰️', '🚢', '⛵', '🚤', '🛥️', '🛳️', '⛴️', '🚂', '🚃', '🚄', '🚅'],
  objects: ['⌚', '📱', '📲', '💻', '⌨️', '🖥️', '🖨️', '🖱️', '🖲️', '🕹️', '🗜️', '💽', '💾', '💿', '📀', '📼', '📷', '📸', '📹', '🎥', '📽️', '🎞️', '📞', '☎️', '📟', '📠', '📺', '📻', '🎙️', '🎚️', '🎛️', '🧭', '⏱️', '⏲️', '⏰', '🕰️', '⌛', '⏳', '📡', '🔋'],
  symbols: ['❤️', '🧡', '💛', '💚', '💙', '💜', '🖤', '🤍', '🤎', '💔', '❣️', '💕', '💞', '💓', '💗', '💖', '💘', '💝', '💟', '☮️', '✝️', '☪️', '🕉️', '☸️', '✡️', '🔯', '🕎', '☯️', '☦️', '🛐', '⛎', '♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏']
};

// Modal elements
const modalOverlay = document.getElementById('modal-overlay');
const modal = document.getElementById('modal');
const modalTitle = document.getElementById('modal-title');
const modalBody = document.getElementById('modal-body');
const modalFooter = document.getElementById('modal-footer');
const modalClose = document.getElementById('modal-close');

// Theme selector elements
const themeSelector = document.getElementById('theme-selector');
const themeClose = document.getElementById('theme-close');
const themeOptions = document.querySelectorAll('.theme-option');
const autoThemeCheckbox = document.getElementById('auto-theme');
const createThemeBtn = document.getElementById('create-theme-btn');
const customThemesList = document.getElementById('custom-themes-list');
const customThemesContainer = document.getElementById('custom-themes-container');

// Simple theme creator elements
const themeCreatorOverlay = document.getElementById('theme-creator-overlay');
const themeCreator = document.getElementById('theme-creator');
const creatorClose = document.getElementById('creator-close');
const creatorCancel = document.getElementById('creator-cancel');
const creatorSave = document.getElementById('creator-save');
const themeNameInput = document.getElementById('theme-name');
const themePreview = document.getElementById('theme-preview');

// Simple color pickers
const colorPrimary = document.getElementById('color-primary');
const colorBg0 = document.getElementById('color-bg0');
const colorBg1 = document.getElementById('color-bg1');
const colorFg = document.getElementById('color-fg');

// API Settings Elements
const apiSettingsBtn = document.getElementById('api-settings-btn');
const apiSettingsOverlay = document.getElementById('api-settings-overlay');
const apiSettingsClose = document.getElementById('api-settings-close');
const apiSettingsCancel = document.getElementById('api-settings-cancel');
const apiSettingsSave = document.getElementById('api-settings-save');
const apiSettingsReset = document.getElementById('api-settings-reset');
const apiProviderSelect = document.getElementById('api-provider');
const apiOpenAIKeyInput = document.getElementById('api-openai-key');
const apiOpenAIModelSelect = document.getElementById('api-openai-model');
const apiGeminiKeyInput = document.getElementById('api-gemini-key');
const apiGeminiModelSelect = document.getElementById('api-gemini-model');
const openaiKeyCard = document.getElementById('openai-key-card');
const geminiKeyCard = document.getElementById('gemini-key-card');

// Initialize theme
async function initTheme() {
  // 1. Immediately apply localStorage theme first (instant UI, no blank flash or loading block!)
  try {
    currentTheme = localStorage.getItem('theme') || 'dark';
    autoTheme = localStorage.getItem('autoTheme') === 'true';
    if (autoTheme) {
      detectSystemTheme();
    } else if (currentTheme.startsWith('custom_')) {
      applyCustomTheme(currentTheme);
    } else {
      applyTheme(currentTheme);
    }
    updateThemeIcon();
    updateThemeSelector();
  } catch (e) {
    console.error('Initial theme apply error:', e);
  }

  // 2. Concurrently load and sync with the backend database in the background
  loadThemeFromBackend().then((backendLoaded) => {
    if (backendLoaded) {
      if (autoTheme) {
        detectSystemTheme();
      } else if (currentTheme.startsWith('custom_')) {
        applyCustomTheme(currentTheme);
      } else {
        applyTheme(currentTheme);
      }
      updateThemeIcon();
      updateThemeSelector();
      console.log('Theme synchronized with database:', currentTheme);
    }
  }).catch(error => {
    console.error('Non-blocking theme sync failed:', error);
  });
}

// Load theme from backend
async function loadThemeFromBackend() {
  try {
    const response = await fetch('/api/theme');
    const data = await response.json();
    
    if (data.theme) {
      currentTheme = data.theme;
      // Update localStorage to match backend
      localStorage.setItem('theme', currentTheme);
    }
    
    if (data.auto_theme !== undefined) {
      autoTheme = data.auto_theme;
      localStorage.setItem('autoTheme', autoTheme.toString());
    }
    
    if (data.custom_themes) {
      customThemes = data.custom_themes;
    }
    
    return true;
  } catch (error) {
    console.log('Backend theme load failed, using localStorage fallback');
    // Fallback to localStorage if backend fails
    currentTheme = localStorage.getItem('theme') || 'dark';
    autoTheme = localStorage.getItem('autoTheme') === 'true';
    return false;
  }
}

// Apply theme
function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  currentTheme = theme;
}

// Update theme icon
function updateThemeIcon() {
  const iconMap = {
    'dark': 'fas fa-moon',
    'light': 'fas fa-sun',
    'mint': 'fas fa-leaf',
    'ocean': 'fas fa-water',
    'sunset': 'fas fa-sun',
    'forest': 'fas fa-tree'
  };
  themeIcon.className = iconMap[currentTheme] || 'fas fa-palette';
}

// Detect system theme
function detectSystemTheme() {
  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    applyTheme('dark');
  } else {
    applyTheme('light');
  }
}

// Toggle theme (now opens selector)
function toggleTheme() {
  showThemeSelector();
}

// Show theme selector
function showThemeSelector() {
  themeSelectorVisible = true;
  themeSelector.classList.add('show');
  updateThemeSelector();
}

// Hide theme selector
function hideThemeSelector() {
  themeSelectorVisible = false;
  themeSelector.classList.remove('show');
}

// Update theme selector UI
function updateThemeSelector() {
  themeOptions.forEach(option => {
    option.classList.toggle('active', option.dataset.theme === currentTheme);
  });
  autoThemeCheckbox.checked = autoTheme;
  updateCustomThemesList();
}

// Load custom themes
async function loadCustomThemes() {
  try {
    const response = await fetch('/api/theme');
    const data = await response.json();
    customThemes = data.custom_themes || {};
    updateCustomThemesList();
  } catch (error) {
    console.error('Failed to load custom themes:', error);
  }
}

// Update custom themes list
function updateCustomThemesList() {
  const hasCustomThemes = Object.keys(customThemes).length > 0;
  customThemesList.style.display = hasCustomThemes ? 'block' : 'none';
  
  customThemesContainer.innerHTML = '';
  
  Object.entries(customThemes).forEach(([themeId, theme]) => {
    const item = document.createElement('div');
    item.className = 'custom-theme-item';
    
    const span = document.createElement('span');
    span.style.color = 'var(--fg)';
    span.style.cursor = 'pointer';
    span.textContent = `🎨 ${sanitizeHTML(theme.name)}`;
    span.onclick = () => setTheme(sanitizeHTML(themeId));
    
    const button = document.createElement('button');
    button.className = 'custom-theme-delete';
    button.title = 'Delete theme';
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
    showToast('Theme creator not available', 'error');
    return;
  }
  themeCreatorVisible = true;
  themeCreatorOverlay.classList.add('show');
  hideThemeSelector();
  resetThemeCreator();
}

function hideThemeCreator() {
  themeCreatorVisible = false;
  if (themeCreatorOverlay) {
    themeCreatorOverlay.classList.remove('show');
  }
}

function resetThemeCreator() {
  if (themeNameInput) themeNameInput.value = '';
  if (colorPrimary) colorPrimary.value = '#37e6b5';
  if (colorBg0) colorBg0.value = '#0b0f14';
  if (colorBg1) colorBg1.value = '#0f1620';
  if (colorFg) colorFg.value = '#e9fbf5';
  updatePreview();
}

function updatePreview() {
  if (!themePreview) return;
  const primary = colorPrimary?.value || '#37e6b5';
  const bg = colorBg1?.value || '#0f1620';
  const fg = colorFg?.value || '#e9fbf5';
  
  themePreview.style.setProperty('--preview-primary', primary);
  themePreview.style.setProperty('--preview-bg', bg);
  themePreview.style.setProperty('--preview-fg', fg);
}

// Hex to RGB converter
function hexToRgb(hex) {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result ? {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16)
  } : { r: 55, g: 230, b: 181 };
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
  root.style.setProperty('--custom-primary', colors.primary);
  root.style.setProperty('--custom-primary-dark', primaryDark);
  root.style.setProperty('--custom-primary-darker', primaryDarker);
  root.style.setProperty('--custom-bg0', colors.bg0);
  root.style.setProperty('--custom-bg1', colors.bg1);
  root.style.setProperty('--custom-fg', colors.fg);
  root.style.setProperty('--custom-muted', colors.muted);
  root.style.setProperty('--custom-glass', glass);
  root.style.setProperty('--custom-border', border);
  root.style.setProperty('--custom-shadow', shadow);
  
  root.setAttribute('data-theme', themeId);
}

// Adjust brightness helper
function adjustBrightness(hex, percent) {
  const rgb = hexToRgb(hex);
  const factor = 1 + percent / 100;
  
  const r = Math.min(255, Math.max(0, Math.round(rgb.r * factor)));
  const g = Math.min(255, Math.max(0, Math.round(rgb.g * factor)));
  const b = Math.min(255, Math.max(0, Math.round(rgb.b * factor)));
  
  return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
}

async function saveCustomTheme() {
  const name = themeNameInput?.value?.trim();
  if (!name) {
    showToast('Please enter a theme name', 'error');
    return;
  }
  
  const colors = {
    primary: colorPrimary?.value || '#37e6b5',
    bg0: colorBg0?.value || '#0b0f14',
    bg1: colorBg1?.value || '#0f1620',
    fg: colorFg?.value || '#e9fbf5',
    muted: '#a6b7b2'
  };
  
  try {
    const response = await fetch('/api/custom-theme', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, colors })
    });
    
    const data = await response.json();
    
    if (response.ok) {
      await loadCustomThemes();
      hideThemeCreator();
      showToast(`Theme "${name}" created!`);
      setTimeout(() => setTheme(data.theme_id), 300);
    } else {
      showToast(data.error || 'Failed to save theme', 'error');
    }
  } catch (error) {
    showToast('Failed to save theme', 'error');
  }
}

// Delete custom theme
async function deleteCustomTheme(themeId) {
  try {
    const response = await fetch('/api/custom-theme', {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ theme_id: themeId })
    });
    
    if (response.ok) {
      delete customThemes[themeId];
      updateCustomThemesList();
      
      // Switch to default theme if current theme was deleted
      if (currentTheme === themeId) {
        setTheme('dark');
      }
      
      showToast('Theme deleted successfully');
    } else {
      showToast('Failed to delete theme', 'error');
    }
  } catch (error) {
    console.error('Delete theme error:', error);
    showToast('Failed to delete theme', 'error');
  }
}

// Set theme
async function setTheme(theme) {
  try {
    // Update backend first
    const response = await fetch('/api/theme', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ theme, auto_theme: false })
    });
    
    if (response.ok) {
      currentTheme = theme;
      autoTheme = false;
      
      // Update localStorage to match backend
      localStorage.setItem('theme', theme);
      localStorage.setItem('autoTheme', 'false');
      
      // Apply theme
      if (theme.startsWith('custom_')) {
        applyCustomTheme(theme);
      } else {
        applyTheme(theme);
      }
      
      updateThemeIcon();
      updateThemeSelector();
      
      const themeName = theme.startsWith('custom_') ? customThemes[theme]?.name || 'Custom' : theme;
      showToast(`Theme changed to ${themeName}`);
    } else {
      throw new Error('Backend theme update failed');
    }
  } catch (error) {
    console.error('Theme change error:', error);
    showToast('Failed to change theme', 'error');
  }
}

// Toggle auto theme
async function toggleAutoTheme() {
  autoTheme = !autoTheme;
  
  try {
    // Update backend
    const response = await fetch('/api/theme', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ theme: currentTheme, auto_theme: autoTheme })
    });
    
    if (response.ok) {
      // Update localStorage to match backend
      localStorage.setItem('autoTheme', autoTheme.toString());
      
      if (autoTheme) {
        detectSystemTheme();
        showToast('Auto theme enabled');
        
        // Listen for system theme changes
        if (window.matchMedia) {
          window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', detectSystemTheme);
        }
      } else {
        showToast('Auto theme disabled');
        if (window.matchMedia) {
          window.matchMedia('(prefers-color-scheme: dark)').removeEventListener('change', detectSystemTheme);
        }
      }
      
      updateThemeIcon();
      updateThemeSelector();
    } else {
      // Revert on failure
      autoTheme = !autoTheme;
      showToast('Failed to update auto theme setting', 'error');
    }
  } catch (error) {
    // Revert on error
    autoTheme = !autoTheme;
    console.error('Auto theme toggle error:', error);
    showToast('Failed to update auto theme setting', 'error');
  }
}

// Format timestamp
function formatTime(timestamp) {
  try {
    if (timestamp && typeof timestamp === 'string') {
      // Safely transform SQLite 'YYYY-MM-DD HH:MM:SS' format to standard ISO-8601 'YYYY-MM-DDTHH:MM:SSZ'
      let cleanTimestamp = timestamp.trim().replace(' ', 'T');
      if (!cleanTimestamp.includes('Z') && !cleanTimestamp.includes('+') && !cleanTimestamp.includes('-')) {
        cleanTimestamp += 'Z'; // SQLite CURRENT_TIMESTAMP is UTC
      }
      const date = new Date(cleanTimestamp);
      if (!isNaN(date.getTime())) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      }
    }
    const date = timestamp ? new Date(timestamp) : new Date();
    if (!isNaN(date.getTime())) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    return '';
  } catch (e) {
    console.error('Error formatting time:', e);
    return '';
  }
}

// Create a message bubble element (without side-effects or direct DOM appending)
function createMessageElement(text, who = 'ai', timestamp = null, messageId = null) {
  const div = document.createElement('div');
  div.className = who === 'user' ? 'bubble bubble--user' : 'bubble bubble--ai';
  div.setAttribute('data-message-id', messageId || Date.now());
  
  const content = document.createElement('div');
  content.className = 'bubble__content';
  
  const p = document.createElement('p');
  // If text already contains HTML formatting from backend, use it directly
  if (text.includes('<') && text.includes('>')) {
    p.innerHTML = text;
  } else {
    p.innerHTML = formatMessage(text);
  }
  content.appendChild(p);
  
  // Store raw text for copying
  div.setAttribute('data-raw-text', text);
  
  // Ellipsis menu trigger button
  const menuBtn = document.createElement('button');
  menuBtn.className = 'bubble__menu-btn';
  menuBtn.title = 'Message Actions';
  menuBtn.innerHTML = '<i class="fas fa-bars"></i>';
  
  // Custom dropdown panel
  const actionsDropdown = document.createElement('div');
  actionsDropdown.className = 'bubble__actions-dropdown';
  
  menuBtn.onclick = (e) => {
    e.stopPropagation();
    document.querySelectorAll('.bubble__actions-dropdown').forEach(dropdown => {
      if (dropdown !== actionsDropdown) dropdown.classList.remove('show');
    });
    actionsDropdown.classList.toggle('show');
  };
  
  const copyBtn = document.createElement('button');
  copyBtn.className = 'bubble__action';
  copyBtn.innerHTML = '<i class="fas fa-copy"></i><span>Copy</span>';
  copyBtn.onclick = (e) => {
    e.stopPropagation();
    copyMessage(text);
    actionsDropdown.classList.remove('show');
  };
  actionsDropdown.appendChild(copyBtn);
  
  if (who === 'ai') {
    const likeBtn = document.createElement('button');
    likeBtn.className = 'bubble__action';
    likeBtn.innerHTML = '<i class="far fa-thumbs-up"></i><span>Like</span>';
    likeBtn.onclick = (e) => {
      e.stopPropagation();
      toggleReaction(likeBtn, 'like');
      actionsDropdown.classList.remove('show');
    };
    
    const regenerateBtn = document.createElement('button');
    regenerateBtn.className = 'bubble__action';
    regenerateBtn.innerHTML = '<i class="fas fa-redo"></i><span>Retry</span>';
    regenerateBtn.onclick = (e) => {
      e.stopPropagation();
      regenerateResponse(div);
      actionsDropdown.classList.remove('show');
    };
    
    actionsDropdown.appendChild(likeBtn);
    actionsDropdown.appendChild(regenerateBtn);
  } else {
    const editBtn = document.createElement('button');
    editBtn.className = 'bubble__action';
    editBtn.innerHTML = '<i class="fas fa-edit"></i><span>Edit</span>';
    editBtn.onclick = (e) => {
      e.stopPropagation();
      editMessage(div);
      actionsDropdown.classList.remove('show');
    };
    actionsDropdown.appendChild(editBtn);
  }
  
  div.appendChild(menuBtn);
  div.appendChild(actionsDropdown);
  
  const t = document.createElement('time');
  const timeStr = formatTime(timestamp);
  t.textContent = who === 'user' ? `you • ${timeStr}` : `ai • ${timeStr}`;
  
  div.appendChild(content);
  div.appendChild(t);
  
  return div;
}

// Push message to chat panel
function pushMessage(text, who = 'ai', timestamp = null, messageId = null) {
  const div = createMessageElement(text, who, timestamp, messageId);
  messagesEl.appendChild(div);
  
  // Store in history
  messageHistory.push({ text, who, timestamp: timestamp || new Date().toISOString(), id: div.getAttribute('data-message-id') });
  
  smoothScrollToBottom();
}

// Sanitize HTML to prevent XSS
function sanitizeHTML(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

// Format message text (enhanced markdown support with XSS protection)
function formatMessage(text) {
  // Sanitize input first
  if (typeof text !== 'string') {
    text = String(text || '');
  }
  
  // Check if text contains image HTML (from backend image generation) - validate it's safe
  if (text.includes('<img src="data:image/')) {
    // Only allow data URLs for images, sanitize the rest
    const imgRegex = /<img src="data:image\/[^"]*"[^>]*>/g;
    const safeImages = text.match(imgRegex) || [];
    const textWithoutImages = text.replace(imgRegex, '__IMAGE_PLACEHOLDER__');
    let sanitizedText = sanitizeHTML(textWithoutImages);
    safeImages.forEach(img => {
      sanitizedText = sanitizedText.replace('__IMAGE_PLACEHOLDER__', img);
    });
    return sanitizedText;
  }
  
  // For any HTML content, sanitize first then apply safe formatting
  text = sanitizeHTML(text);
  
  // Apply markdown formatting to plain text
  let formatted = text;
  
  // Headers (must come before other formatting) - Compact spacing
  formatted = formatted.replace(/^#### (.*$)/gm, '<h4 style="color: var(--mint); margin: 8px 0 4px 0; font-size: 1.1em;">$1</h4>');
  formatted = formatted.replace(/^### (.*$)/gm, '<h3 style="color: var(--mint); margin: 10px 0 5px 0; font-size: 1.2em;">$1</h3>');
  formatted = formatted.replace(/^## (.*$)/gm, '<h2 style="color: var(--mint); margin: 12px 0 6px 0; font-size: 1.3em;">$1</h2>');
  formatted = formatted.replace(/^# (.*$)/gm, '<h1 style="color: var(--mint); margin: 15px 0 8px 0; font-size: 1.4em;">$1</h1>');
  
  // Code blocks - Compact spacing
  formatted = formatted.replace(/```([\s\S]*?)```/g, '<pre style="background: rgba(255,255,255,0.1); padding: 8px; border-radius: 4px; margin: 6px 0; overflow-x: auto; font-size: 0.9em;"><code>$1</code></pre>');
  
  // Inline code
  formatted = formatted.replace(/`([^`]+)`/g, '<code style="background: rgba(255,255,255,0.1); padding: 1px 3px; border-radius: 2px; font-family: monospace; font-size: 0.9em;">$1</code>');
  
  // Bold text
  formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong style="color: var(--mint); font-weight: 600;">$1</strong>');
  
  // Italic text
  formatted = formatted.replace(/\*([^*]+)\*/g, '<em style="font-style: italic; color: rgba(255,255,255,0.9);">$1</em>');
  
  // Lists - Enhanced number formatting with compact spacing
  formatted = formatted.replace(/^(\d+)\. (.+)$/gm, '<li style="margin: 2px 0; color: rgba(255,255,255,0.9); display: flex; align-items: flex-start;"><span style="color: var(--mint); font-weight: 600; min-width: 24px; background: rgba(255,255,255,0.1); border-radius: 50%; width: 20px; height: 20px; display: flex; align-items: center; justify-content: center; font-size: 0.8em; margin-right: 8px; flex-shrink: 0;">$1</span><span style="flex: 1;">$2</span></li>');
  formatted = formatted.replace(/^[*-] (.+)$/gm, '<li style="margin: 2px 0; color: rgba(255,255,255,0.9); display: flex; align-items: flex-start;"><span style="color: var(--mint); margin-right: 8px; font-weight: bold;">•</span><span style="flex: 1;">$2</span></li>');
  
  // Wrap consecutive list items in ul - Compact spacing
  formatted = formatted.replace(/((<li[^>]*>.*<\/li>\s*)+)/g, '<ul style="margin: 6px 0; padding-left: 0; list-style: none;">$1</ul>');
  
  // Line breaks - More compact
  formatted = formatted.replace(/\n\n/g, '<br>');
  formatted = formatted.replace(/\n/g, '<br>');
  
  return formatted;
}

// Smooth scroll to bottom
function smoothScrollToBottom() {
  messagesEl.scrollTo({
    top: messagesEl.scrollHeight,
    behavior: 'smooth'
  });
}

// Copy message to clipboard
async function copyMessage(text) {
  try {
    // Clean the text by removing HTML tags using DOM parser for safety
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = text;
    const cleanText = tempDiv.textContent || tempDiv.innerText || '';
    
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(cleanText);
      showToast('Message copied to clipboard!');
    } else {
      // Fallback for older browsers (deprecated API)
      console.warn('Using deprecated document.execCommand for clipboard access');
      const textArea = document.createElement('textarea');
      textArea.value = cleanText;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      showToast('Message copied to clipboard!');
    }
  } catch (err) {
    console.error('Failed to copy:', err);
    showToast('Failed to copy message', 'error');
  }
}

// Toggle reaction
function toggleReaction(btn, type) {
  const icon = btn.querySelector('i');
  const span = btn.querySelector('span');
  const isActive = btn.classList.contains('active');
  
  if (isActive) {
    icon.className = `far fa-thumbs-${type === 'like' ? 'up' : 'down'}`;
    btn.classList.remove('active');
    span.textContent = type === 'like' ? 'Like' : 'Dislike';
    showToast('Reaction removed');
  } else {
    icon.className = `fas fa-thumbs-${type === 'like' ? 'up' : 'down'}`;
    btn.classList.add('active');
    span.textContent = type === 'like' ? 'Liked' : 'Disliked';
    showToast(`Message ${type === 'like' ? 'liked' : 'disliked'}!`);
  }
}

// Show toast notification
function showToast(message, type = 'success') {
  const toast = document.createElement('div');
  toast.className = `toast toast--${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);
  
  setTimeout(() => {
    toast.classList.add('toast--show');
  }, 100);
  
  setTimeout(() => {
    toast.classList.remove('toast--show');
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// Set status indicator
function setStatus(state, message = null) {
  const states = {
    sending: { text: 'Thinking…', color: 'var(--mint)', pulse: true },
    error: { text: 'Error', color: 'crimson', pulse: false },
    idle: { text: 'Idle', color: 'rgba(255,255,255,0.55)', pulse: false },
    ratelimit: { text: 'Rate Limited', color: 'orange', pulse: false }
  };
  
  const config = states[state] || states.idle;
  statusText.textContent = message || config.text;
  statusDot.style.background = config.color;
  statusDot.style.animation = config.pulse ? 'pulse 1.5s infinite' : 'none';
}

// Show/hide typing indicator
function showTyping(show = true) {
  typingIndicator.style.display = show ? 'block' : 'none';
  if (show) smoothScrollToBottom();
}

// Update character count
function updateCharCount() {
  const length = inputEl.value.length;
  charCount.textContent = `${length}/2000`;
  charCount.style.color = length > 1800 ? 'var(--error)' : 'var(--muted)';
  
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
  return token ? token.getAttribute('content') : null;
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

  inFlight = true;
  setStatus('sending');
  showTyping(true);
  pushMessage(userMessage, 'user');
  
  // Reset input immediately
  inputEl.value = '';
  inputEl.focus();
  localStorage.removeItem('chatDraft'); // Clear draft
  updateCharCount();

  try {
    console.log('Sending message length:', userMessage.length);
    
    // Prepare headers with location if available
    const headers = { 'Content-Type': 'application/json' };
    
    // Add CSRF token if available
    const csrfToken = getCSRFToken();
    if (csrfToken) {
      headers['X-CSRF-Token'] = csrfToken;
    }
    
    // Validate and add location headers
    if (window.userLocation && 
        typeof window.userLocation.lat === 'number' && 
        typeof window.userLocation.lon === 'number') {
      headers['X-User-Latitude'] = window.userLocation.lat.toString();
      headers['X-User-Longitude'] = window.userLocation.lon.toString();
    }
    
    const requestBody = { message: sanitizeHTML(userMessage) };
    const byok = getBYOKConfig();
    if (byok) {
      requestBody.provider = byok.provider;
      requestBody.api_key = byok.api_key;
      requestBody.model = byok.model;
    }

    const res = await fetch('/chat', {
      method: 'POST',
      headers: headers,
      body: JSON.stringify(requestBody)
    });
    
    if (!res.ok) {
      if (res.status === 429) {
        setStatus('ratelimit', 'Rate limited - please wait');
        showToast('Too many messages. Please wait before sending another.', 'warning');
        return;
      }
      const errorData = await res.json().catch(() => ({ error: 'Unknown error' }));
      throw new Error(errorData.error || `Server error ${res.status}`);
    }

    const data = await res.json();
    
    const aiText = data.reply || 'No response';
    pushMessage(aiText, 'ai', data.timestamp);
    updateMessageCount(data.message_count);
    setStatus('idle');
    
    // Update session ID and refresh recent chats if new session
    if (data.session_id && data.session_id !== currentSessionId) {
      currentSessionId = data.session_id;
      updateRecentChats();
    }
    
  } catch (err) {
    console.error('Chat error:', err);
    const errorMsg = err.message.includes('Failed to fetch') 
      ? 'Connection error - please check your internet' 
      : err.message;
    pushMessage(`⚠️ ${errorMsg}`, 'ai');
    setStatus('error');
    showToast('Failed to send message', 'error');
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
  historyPanel.classList.toggle('hidden', !historyVisible);
}



// Load chat session
async function loadChatSession(sessionId) {
  try {
    // Validate URL and add CSRF protection
    const loadUrl = `/api/sessions/${encodeURIComponent(sessionId)}/load`;
    if (!isValidURL(new URL(loadUrl, window.location.origin).href)) {
      throw new Error('Invalid session ID');
    }
    
    const headers = { 'Content-Type': 'application/json' };
    const csrfToken = getCSRFToken();
    if (csrfToken) {
      headers['X-CSRF-Token'] = csrfToken;
    }
    
    const response = await fetch(loadUrl, { 
      method: 'POST',
      headers: headers
    });
    const data = await response.json();
    
    if (!response.ok) {
      showToast('Failed to load chat session', 'error');
      return;
    }
    
    currentSessionId = sessionId;
    messageHistory = [...data.messages]; // Correctly set once (no duplicate pushes)
    
    // Clear current messages
    messagesEl.innerHTML = '';
    
    // Use Document Fragment to append all elements in a single DOM operation - HUGE performance boost!
    const fragment = document.createDocumentFragment();
    data.messages.forEach(msg => {
      const msgId = msg.id || 'msg_' + Math.random().toString(36).substr(2, 9);
      const div = createMessageElement(msg.text, msg.who, msg.timestamp, msgId);
      fragment.appendChild(div);
    });
    
    messagesEl.appendChild(fragment);
    
    updateMessageCount(messageHistory.length);
    updateRecentChats(); // Update to show active session
    smoothScrollToBottom();
    showToast('Chat session loaded');
  } catch (error) {
    console.error('Failed to load chat session:', error);
    showToast('Failed to load chat session', 'error');
  }
}

// Start new chat
async function startNewChat() {
  try {
    // Add CSRF protection
    const headers = { 'Content-Type': 'application/json' };
    const csrfToken = getCSRFToken();
    if (csrfToken) {
      headers['X-CSRF-Token'] = csrfToken;
    }
    
    const response = await fetch('/api/new-session', { 
      method: 'POST',
      headers: headers
    });
    
    if (response.ok) {
      currentSessionId = null;
      messageHistory = [];
      messagesEl.innerHTML = '';
      updateMessageCount(0);
      
      // Add welcome message
      pushMessage('Welcome — ask me anything. I have context memory and can help with various tasks!', 'ai');
      
      // Update recent chats
      updateRecentChats();
      showToast('New chat started');
    }
  } catch (error) {
    console.error('Failed to start new chat:', error);
    showToast('Failed to start new chat', 'error');
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
  const adjustedX = (x + panelWidth > window.innerWidth) ? x - panelWidth : x;
  const adjustedY = (y + panelHeight > window.innerHeight) ? y - panelHeight : y;
  
  hoverPanel.style.left = adjustedX + 'px';
  hoverPanel.style.top = adjustedY + 'px';
  hoverPanel.classList.add('show');
}

// Hide context panel
function hideHoverPanel() {
  hoverPanel.classList.remove('show');
  hoverPanelTarget = null;
}

// Modal System Functions
function showModal(title, content, buttons = []) {
  modalTitle.textContent = title;
  modalBody.innerHTML = content;
  modalFooter.innerHTML = '';
  
  if (!buttons || buttons.length === 0) {
    modalFooter.style.display = 'none';
  } else {
    modalFooter.style.display = 'flex';
    buttons.forEach(btn => {
      const button = document.createElement('button');
      button.className = `btn ${btn.class || 'btn--secondary'}`;
      button.textContent = btn.text;
      button.onclick = btn.onclick;
      modalFooter.appendChild(button);
    });
  }
  
  const closeBtn = document.getElementById('modal-close');
  if (closeBtn) closeBtn.style.display = 'flex';
  
  modalOverlay.classList.add('show');
  
  // Focus first input if exists
  const firstInput = modalBody.querySelector('input, textarea');
  if (firstInput) {
    setTimeout(() => firstInput.focus(), 100);
  }
}

function hideModal() {
  modalOverlay.classList.remove('show');
}

function showConfirmModal(title, message, onConfirm, options = {}) {
  const iconClass = options.danger ? 'fas fa-exclamation-triangle' : 'fas fa-question-circle';
  const confirmClass = options.danger ? 'btn--danger' : 'btn--mint';
  const confirmText = options.confirmText || 'Confirm';
  
  const content = `
    <div class="modal--confirm ${options.danger ? 'danger' : ''}">
      <div class="modal-icon">
        <i class="${iconClass}"></i>
      </div>
      <div class="modal-message">${message}</div>
      ${options.submessage ? `<div class="modal-submessage">${options.submessage}</div>` : ''}
    </div>
  `;
  
  showModal(title, content, [
    {
      text: 'Cancel',
      class: 'btn--secondary',
      onclick: hideModal
    },
    {
      text: confirmText,
      class: confirmClass,
      onclick: () => {
        hideModal();
        onConfirm();
      }
    }
  ]);
}

function showInputModal(title, placeholder, onSubmit, options = {}) {
  const inputType = options.textarea ? 'textarea' : 'input';
  const inputClass = options.textarea ? 'form-input form-textarea' : 'form-input';
  const defaultValue = options.defaultValue || '';
  
  const content = `
    <div class="form-group">
      <label class="form-label">${options.label || title}</label>
      <${inputType} 
        id="modal-input" 
        class="${inputClass}" 
        placeholder="${placeholder}"
        maxlength="${options.maxLength || 100}"
        ${options.required ? 'required' : ''}
      >${defaultValue}</${inputType}>
      <div id="modal-input-error" class="form-error" style="display: none;"></div>
    </div>
  `;
  
  showModal(title, content, [
    {
      text: 'Cancel',
      class: 'btn--secondary',
      onclick: hideModal
    },
    {
      text: options.submitText || 'Save',
      class: 'btn--mint',
      onclick: () => {
        const input = document.getElementById('modal-input');
        const value = input.value.trim();
        const errorEl = document.getElementById('modal-input-error');
        
        // Validation
        if (options.required && !value) {
          errorEl.textContent = 'This field is required';
          errorEl.style.display = 'block';
          input.focus();
          return;
        }
        
        if (options.maxLength && value.length > options.maxLength) {
          errorEl.textContent = `Maximum ${options.maxLength} characters allowed`;
          errorEl.style.display = 'block';
          input.focus();
          return;
        }
        
        hideModal();
        onSubmit(value);
      }
    }
  ]);
}

// Handle hover panel actions
function handleHoverAction(action) {
  if (!hoverPanelTarget) {
    console.warn('No hover panel target set');
    return;
  }
  
  // Validate action parameter
  const validActions = ['duplicate', 'rename', 'copy', 'export', 'delete'];
  if (!validActions.includes(action)) {
    console.error('Invalid action:', action);
    showToast('Invalid action', 'error');
    return;
  }
  
  switch (action) {
    case 'duplicate':
      duplicateChatSession(hoverPanelTarget);
      break;
    case 'rename':
      showRenameModal(hoverPanelTarget);
      break;
    case 'copy':
      copySessionMessages(hoverPanelTarget);
      break;
    case 'export':
      exportSingleChat(hoverPanelTarget);
      break;
    case 'delete':
      showDeleteModal(hoverPanelTarget);
      break;
    default:
      console.error('Unhandled action:', action);
      showToast('Action not implemented', 'error');
  }
  
  hoverPanel.classList.remove('show');
  hoverPanelTarget = null;
}

// Modal-based rename function
function showRenameModal(sessionId) {
  showInputModal(
    'Rename Chat',
    'Enter new chat title...',
    (newTitle) => renameChatSessionWithTitle(sessionId, newTitle),
    {
      label: 'Chat Title',
      maxLength: 100,
      required: true,
      submitText: 'Rename'
    }
  );
}

// Modal-based delete confirmation
function showDeleteModal(sessionId) {
  showConfirmModal(
    'Delete Chat',
    'Are you sure you want to delete this chat?',
    () => deleteChatSession(sessionId),
    {
      danger: true,
      confirmText: 'Delete',
      submessage: 'This action cannot be undone.'
    }
  );
}

// Modal-based message edit
function showEditMessageModal(bubbleElement) {
  const rawText = bubbleElement.getAttribute('data-raw-text') || '';
  
  showInputModal(
    'Edit Message',
    'Edit your message...',
    (newText) => editMessageRequest(bubbleElement, newText),
    {
      label: 'Message Content',
      defaultValue: rawText,
      maxLength: 2000,
      required: true,
      textarea: true,
      submitText: 'Update'
    }
  );
}



// Copy session messages
async function copySessionMessages(sessionId) {
  try {
    const response = await fetch(`/api/sessions/${encodeURIComponent(sessionId)}/copy`);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Copy failed' }));
      throw new Error(errorData.error || 'Copy failed');
    }
    
    const data = await response.json();
    
    if (data.success && data.formatted_text) {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(data.formatted_text);
      } else {
        console.warn('Using deprecated document.execCommand for clipboard access - consider upgrading packages');
        const textArea = document.createElement('textarea');
        textArea.value = data.formatted_text;
        textArea.style.position = 'fixed';
        textArea.style.opacity = '0';
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
      }
      showToast(`Copied ${data.message_count || 0} messages!`);
    } else {
      throw new Error('No content to copy');
    }
  } catch (error) {
    console.error('Copy messages error:', error);
    showToast(error.message || 'Failed to copy messages', 'error');
  }
}

// Regenerate last AI response (keyboard shortcut)
async function regenerateLastResponse() {
  const aiBubbles = messagesEl.querySelectorAll('.bubble--ai');
  if (aiBubbles.length === 0) {
    showToast('No AI responses to regenerate', 'warning');
    return;
  }
  
  const lastAiBubble = aiBubbles[aiBubbles.length - 1];
  await regenerateResponse(lastAiBubble);
}

// Edit user message
function editMessage(bubbleElement) {
  if (inFlight) {
    showToast('Please wait for current request to complete', 'warning');
    return;
  }
  
  showEditMessageModal(bubbleElement);
}

// Send edit message request
async function editMessageRequest(bubbleElement, newText) {
  try {
    inFlight = true;
    setStatus('sending', 'Editing message...');
    showTyping(true);
    
    const messageId = bubbleElement.getAttribute('data-message-id');
    
    // Add CSRF protection
    const headers = { 'Content-Type': 'application/json' };
    const csrfToken = getCSRFToken();
    if (csrfToken) {
      headers['X-CSRF-Token'] = csrfToken;
    }
    
    const requestBody = {
      message_id: sanitizeHTML(messageId),
      new_text: sanitizeHTML(newText)
    };
    const byok = getBYOKConfig();
    if (byok) {
      requestBody.provider = byok.provider;
      requestBody.api_key = byok.api_key;
      requestBody.model = byok.model;
    }

    const response = await fetch('/edit-message', {
      method: 'POST',
      headers: headers,
      body: JSON.stringify(requestBody)
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Edit failed' }));
      throw new Error(errorData.error || 'Edit failed');
    }
    
    const data = await response.json();
    
    // Update user message
    const userContent = bubbleElement.querySelector('.bubble__content p');
    if (userContent) {
      userContent.innerHTML = formatMessage(data.user_message);
      bubbleElement.setAttribute('data-raw-text', data.user_message);
    }
    
    // Find and update the corresponding AI response
    const nextBubble = bubbleElement.nextElementSibling;
    if (nextBubble && nextBubble.classList.contains('bubble--ai')) {
      const aiContent = nextBubble.querySelector('.bubble__content p');
      if (aiContent) {
        aiContent.innerHTML = formatMessage(data.ai_reply);
        nextBubble.setAttribute('data-raw-text', data.ai_reply);
        
        // Update timestamp
        const timeElement = nextBubble.querySelector('time');
        if (timeElement) {
          timeElement.textContent = `ai • ${formatTime(data.timestamp)}`;
        }
      }
    }
    
    setStatus('idle');
    showToast('Message edited successfully!');
    
  } catch (error) {
    console.error('Edit error:', error);
    setStatus('error');
    showToast(error.message || 'Failed to edit message', 'error');
  } finally {
    showTyping(false);
    inFlight = false;
  }
}

// Regenerate AI response
async function regenerateResponse(bubbleElement) {
  if (inFlight) {
    showToast('Please wait for current request to complete', 'warning');
    return;
  }
  
  // Validate bubble element
  if (!bubbleElement || !bubbleElement.querySelector) {
    console.error('Invalid bubble element for regeneration');
    showToast('Cannot regenerate: invalid message element', 'error');
    return;
  }
  
  const content = bubbleElement.querySelector('.bubble__content p');
  if (!content) {
    console.error('Cannot find message content for regeneration');
    showToast('Cannot regenerate: message content not found', 'error');
    return;
  }
  
  try {
    inFlight = true;
    setStatus('sending', 'Regenerating...');
    showTyping(true);
    
    // Store original content safely
    const originalText = content.innerHTML;
    content.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Regenerating response...';
    
    // Add CSRF protection
    const headers = { 'Content-Type': 'application/json' };
    const csrfToken = getCSRFToken();
    if (csrfToken) {
      headers['X-CSRF-Token'] = csrfToken;
    }
    
    const requestBody = { message_id: bubbleElement.getAttribute('data-message-id') };
    const byok = getBYOKConfig();
    if (byok) {
      requestBody.provider = byok.provider;
      requestBody.api_key = byok.api_key;
      requestBody.model = byok.model;
    }

    const response = await fetch('/regenerate', {
      method: 'POST',
      headers: headers,
      body: JSON.stringify(requestBody)
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
      throw new Error(errorData.error || `HTTP ${response.status}`);
    }
    
    const data = await response.json();
    
    // Update the bubble with new response (safely formatted)
    const sanitizedReply = sanitizeHTML(data.reply || 'No response');
    content.innerHTML = formatMessage(sanitizedReply);
    bubbleElement.setAttribute('data-raw-text', data.reply || '');
    
    // Update timestamp
    const timeElement = bubbleElement.querySelector('time');
    if (timeElement) {
      timeElement.textContent = `ai • ${formatTime(data.timestamp)}`;
    }
    
    setStatus('idle');
    showToast('Response regenerated successfully!');
    
  } catch (error) {
    console.error('Regenerate error:', error);
    
    // Restore original content on error
    if (content && originalText) {
      content.innerHTML = originalText;
    }
    
    setStatus('error');
    showToast(error.message || 'Failed to regenerate response', 'error');
  } finally {
    showTyping(false);
    inFlight = false;
  }
}

// Copy current chat messages
async function copyCurrentChatMessages() {
  if (!currentSessionId) {
    showToast('No active chat to copy', 'warning');
    return;
  }
  
  try {
    // Get current messages from DOM
    const bubbles = messagesEl.querySelectorAll('.bubble');
    let formattedText = '';
    
    bubbles.forEach(bubble => {
      const isUser = bubble.classList.contains('bubble--user');
      const sender = isUser ? 'You' : 'AI';
      const rawText = bubble.getAttribute('data-raw-text') || bubble.querySelector('p').textContent;
      formattedText += `${sender}: ${rawText}\n\n`;
    });
    
    if (formattedText.trim()) {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(formattedText.trim());
      } else {
        // Fallback (deprecated API)
        console.warn('Using deprecated document.execCommand for clipboard access');
        const textArea = document.createElement('textarea');
        textArea.value = formattedText.trim();
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
      }
      showToast(`Copied ${bubbles.length} messages from current chat!`);
    } else {
      showToast('No messages to copy', 'warning');
    }
  } catch (error) {
    console.error('Copy error:', error);
    showToast('Failed to copy messages', 'error');
  }
}



// Export single chat
async function exportSingleChat(sessionId) {
  try {
    // Validate session ID format
    if (!sessionId || typeof sessionId !== 'string') {
      throw new Error('Invalid session ID');
    }
    
    const response = await fetch(`/api/sessions/${encodeURIComponent(sessionId)}`);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Export failed' }));
      throw new Error(errorData.error || 'Export failed');
    }
    
    const data = await response.json();
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chat-${sessionId.substring(0, 8)}.json`; // Truncate for filename
    a.click();
    URL.revokeObjectURL(url);
    showToast('Chat exported successfully');
  } catch (error) {
    console.error('Export error:', error);
    showToast('Failed to export chat', 'error');
  }
}

// Rename chat session with title
async function renameChatSessionWithTitle(sessionId, newTitle) {
  // Validate and sanitize input
  const trimmedTitle = newTitle.trim();
  if (trimmedTitle.length > 100) {
    showToast('Title too long (max 100 characters)', 'error');
    return;
  }
  
  // Remove potentially dangerous characters
  const sanitizedTitle = trimmedTitle.replace(/[<>"'&]/g, '');
  
  if (!sanitizedTitle) {
    showToast('Invalid title after sanitization', 'error');
    return;
  }
  
  try {
    const response = await fetch(`/api/sessions/${encodeURIComponent(sessionId)}/title`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: sanitizedTitle })
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Rename failed' }));
      throw new Error(errorData.error || 'Rename failed');
    }
    
    updateRecentChats();
    showToast('Chat renamed successfully');
  } catch (error) {
    console.error('Failed to rename chat:', error);
    showToast(error.message || 'Failed to rename chat', 'error');
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
      throw new Error('Invalid session ID');
    }
    
    const headers = { 'Content-Type': 'application/json' };
    const csrfToken = getCSRFToken();
    if (csrfToken) {
      headers['X-CSRF-Token'] = csrfToken;
    }
    
    const response = await fetch(duplicateUrl, { 
      method: 'POST',
      headers: headers
    });
    const data = await response.json();
    
    if (response.ok) {
      updateRecentChats();
      showToast('Chat duplicated successfully');
      
      // Load the duplicated chat
      setTimeout(() => {
        loadChatSession(data.new_session_id);
      }, 500);
    } else {
      showToast('Failed to duplicate chat', 'error');
    }
  } catch (error) {
    showToast('Failed to duplicate chat', 'error');
  }
}

// Delete chat session
async function deleteChatSession(sessionId) {
  try {
    // Validate URL and add CSRF protection
    const deleteUrl = `/api/sessions/${encodeURIComponent(sessionId)}`;
    if (!isValidURL(new URL(deleteUrl, window.location.origin).href)) {
      throw new Error('Invalid session ID');
    }
    
    const headers = { 'Content-Type': 'application/json' };
    const csrfToken = getCSRFToken();
    if (csrfToken) {
      headers['X-CSRF-Token'] = csrfToken;
    }
    
    const response = await fetch(deleteUrl, { 
      method: 'DELETE',
      headers: headers
    });
    
    if (response.ok) {
      // If deleting current session, start new chat
      if (sessionId === currentSessionId) {
        await startNewChat();
      }
      updateRecentChats();
      showToast('Chat deleted successfully');
    } else {
      showToast('Failed to delete chat', 'error');
    }
  } catch (error) {
    console.error('Failed to delete chat:', error);
    showToast('Failed to delete chat', 'error');
  }
}

// Update recent chats display (optimized with document fragment)
async function updateRecentChats() {
  try {
    // Append a unique cache-buster timestamp parameter to prevent browser caching of GET requests
    const response = await fetch('/api/sessions?t=' + Date.now());
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const data = await response.json();
    
    recentChats.innerHTML = '';
    
    if (!data.sessions || data.sessions.length === 0) {
      recentChats.innerHTML = '<div class="chat-empty"><i class="fas fa-comments"></i>No recent chats</div>';
      return;
    }
    
    // Use document fragment for better performance
    const fragment = document.createDocumentFragment();
    
    data.sessions.forEach(session => {
      const chatItem = document.createElement('div');
      chatItem.className = 'chat-item';
      chatItem.title = 'Click to load chat session';
      if (session.id === currentSessionId) {
        chatItem.classList.add('active');
      }
      
      // Click to load session
      chatItem.onclick = () => loadChatSession(session.id);
      
      // Right-click event for action panel
      chatItem.addEventListener('contextmenu', (e) => {
        e.preventDefault();
        showHoverPanel(e, session.id);
      });
      
      const title = document.createElement('div');
      title.className = 'chat-item__title';
      title.textContent = session.title || 'Untitled Chat';
      
      const preview = document.createElement('div');
      preview.className = 'chat-item__preview';
      preview.textContent = session.preview || 'No preview available';
      
      const time = document.createElement('div');
      time.className = 'chat-item__time';
      time.textContent = formatTime(session.timestamp);
      
      chatItem.appendChild(title);
      chatItem.appendChild(preview);
      chatItem.appendChild(time);
      fragment.appendChild(chatItem);
    });
    
    recentChats.appendChild(fragment);
  } catch (error) {
    console.error('Failed to load chat sessions:', error);
    recentChats.innerHTML = '<p style="color: var(--error); text-align: center; padding: 20px;">Failed to load chats</p>';
  }
}

// Clear chat history with modal confirmation
async function clearHistory() {
  showConfirmModal(
    'Clear History',
    'Are you sure you want to clear all chat history?',
    async () => {
      try {
        // Add CSRF protection
        const headers = { 'Content-Type': 'application/json' };
        const csrfToken = getCSRFToken();
        if (csrfToken) {
          headers['X-CSRF-Token'] = csrfToken;
        }
        
        const res = await fetch('/clear-history', { 
          method: 'POST',
          headers: headers
        });
        if (res.ok) {
          messagesEl.innerHTML = '';
          messageHistory = [];
          currentSessionId = null;
          updateMessageCount(0);
          updateRecentChats();
          showToast('All chat history cleared');
          
          // Clear local storage
          localStorage.removeItem('chatDraft');
          
          // Add welcome message
          pushMessage('All chat history cleared. Starting fresh!', 'ai');
        }
      } catch (err) {
        showToast('Failed to clear history', 'error');
      }
    },
    {
      danger: true,
      confirmText: 'Clear All',
      submessage: 'This will remove all messages from the current session.'
    }
  );
}

// Clear all data function with modal confirmation
async function clearAllData() {
  showConfirmModal(
    'Clear All Data',
    'This will permanently delete ALL chat data including sessions.',
    async () => {
      try {
        // Clear all data via backend
        // Add CSRF protection
        const headers = { 'Content-Type': 'application/json' };
        const csrfToken = getCSRFToken();
        if (csrfToken) {
          headers['X-CSRF-Token'] = csrfToken;
        }
        
        const res = await fetch('/clear-all-data', { 
          method: 'POST',
          headers: headers
        });
        
        if (!res.ok) {
          const errorData = await res.json().catch(() => ({ error: 'Clear failed' }));
          throw new Error(errorData.error || 'Clear failed');
        }
        
        // Clear UI
        messagesEl.innerHTML = '';
        messageHistory = [];
        currentSessionId = null;
        updateMessageCount(0);
        updateRecentChats();
        
        // Clear specific localStorage items instead of all
        const keysToRemove = ['chatDraft', 'theme'];
        keysToRemove.forEach(key => localStorage.removeItem(key));
        
        showToast('All data cleared successfully!');
        pushMessage('All data cleared. Fresh start!', 'ai');
        
      } catch (err) {
        console.error('Clear all data error:', err);
        showToast(err.message || 'Failed to clear all data', 'error');
      }
    },
    {
      danger: true,
      confirmText: 'Delete All',
      submessage: 'This action cannot be undone.'
    }
  );
}

// Export chat history
async function exportChat() {
  try {
    const res = await fetch('/export-chat');
    const data = await res.json();
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chat-export-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
    
    showToast('Chat exported successfully');
  } catch (err) {
    showToast('Failed to export chat', 'error');
  }
}

// Search messages (improved with null checks)
function searchMessages() {
  const query = searchInput.value.toLowerCase().trim();
  const bubbles = messagesEl.querySelectorAll('.bubble');
  
  bubbles.forEach(bubble => {
    const textElement = bubble.querySelector('p');
    if (!textElement) {
      console.warn('Message bubble missing text element');
      return;
    }
    
    const text = textElement.textContent.toLowerCase();
    const match = !query || text.includes(query);
    bubble.style.display = match ? 'block' : 'none';
    
    if (match && query) {
      bubble.classList.add('highlight');
    } else {
      bubble.classList.remove('highlight');
    }
  });
}

// Voice input (if supported)
function initVoiceInput() {
  if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';
    
    recognition.onstart = () => {
      isListening = true;
      voiceBtn.classList.add('listening');
      voiceBtn.innerHTML = '<i class="fas fa-stop"></i>';
      setStatus('sending', 'Listening...');
    };
    
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      inputEl.value = transcript;
      updateCharCount();
    };
    
    recognition.onend = () => {
      isListening = false;
      voiceBtn.classList.remove('listening');
      voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
      setStatus('idle');
    };
    
    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      showToast('Voice recognition failed', 'error');
      // Properly handle the error state
      isListening = false;
      voiceBtn.classList.remove('listening');
      voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
      setStatus('idle');
    };
  } else {
    voiceBtn.style.display = 'none';
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
  hour: '2-digit', 
  minute: '2-digit', 
  second: '2-digit',
  hour12: true 
});

function updateTime() {
  const now = new Date();
  timeDisplay.textContent = timeFormatter.format(now);
}

// Get weather data
async function updateWeather(location = 'London') {
  try {
    const response = await fetch(`/weather?city=${encodeURIComponent(location)}`);
    const data = await response.json();
    
    if (data.error) {
      weatherTemp.textContent = '22°C';
      weatherIcon.className = 'fas fa-sun';
      return;
    }
    
    weatherTemp.textContent = `${data.temperature}°C`;
    
    // Enhanced icon mapping based on OpenWeatherMap icons
    const iconMap = {
      'Clear': 'fas fa-sun',
      'Clouds': 'fas fa-cloud',
      'Rain': 'fas fa-cloud-rain',
      'Drizzle': 'fas fa-cloud-drizzle',
      'Thunderstorm': 'fas fa-bolt',
      'Snow': 'fas fa-snowflake',
      'Mist': 'fas fa-smog',
      'Fog': 'fas fa-smog',
      'Haze': 'fas fa-smog'
    };
    
    weatherIcon.className = iconMap[data.condition] || 'fas fa-sun';
    weatherIcon.title = `${data.description} in ${data.location}`;
    
    // Store current weather data for chat context
    window.currentWeather = data;
    
  } catch (error) {
    console.error('Weather update error:', error);
    weatherTemp.textContent = '22°C';
    weatherIcon.className = 'fas fa-sun';
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
          const weatherData = await getWeatherByCoordinates(latitude, longitude);
          if (weatherData && !weatherData.error) {
            weatherTemp.textContent = `${weatherData.temperature}°C`;
            const iconMap = {
              'Clear': 'fas fa-sun',
              'Clouds': 'fas fa-cloud',
              'Rain': 'fas fa-cloud-rain',
              'Drizzle': 'fas fa-cloud-drizzle',
              'Thunderstorm': 'fas fa-bolt',
              'Snow': 'fas fa-snowflake',
              'Mist': 'fas fa-smog',
              'Fog': 'fas fa-smog',
              'Haze': 'fas fa-smog'
            };
            weatherIcon.className = iconMap[weatherData.condition] || 'fas fa-sun';
            weatherIcon.title = `${weatherData.description} in ${weatherData.location}`;
            window.currentWeather = weatherData;
          } else {
            // Fallback to default location
            updateWeather('London');
          }
        } catch (error) {
          console.error('Location weather error:', error);
          updateWeather('London');
        }
      },
      (error) => {
        console.log('Geolocation denied, using default location');
        updateWeather('London');
      },
      { timeout: 5000, enableHighAccuracy: false }
    );
  } else {
    // Geolocation not supported, use default
    updateWeather('London');
  }
  
  // Update time every second
  setInterval(updateTime, 1000);
  
  // Update weather every 10 minutes
  setInterval(() => {
    if (window.currentWeather && window.currentWeather.location !== 'Your Location') {
      // Re-get location weather if we have real location data
      getUserLocationWeather();
    } else {
      updateWeather('London');
    }
  }, 600000);
}

// Weather-specific functions
async function getWeatherForecast(location, days = 5) {
  try {
    const response = await fetch(`/api/weather/forecast?location=${encodeURIComponent(location)}&days=${days}`);
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Forecast error:', error);
    return null;
  }
}

async function searchCities(query) {
  try {
    const response = await fetch(`/api/weather/search?q=${encodeURIComponent(query)}`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const data = await response.json();
    return data.cities || [];
  } catch (error) {
    console.error('City search error:', error);
    return [];
  }
}

async function getWeatherByCoordinates(lat, lon) {
  try {
    const response = await fetch(`/api/weather/coordinates?lat=${lat}&lon=${lon}`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Coordinates weather error:', error);
    return null;
  }
}

// Weather icon mapping (moved to module level for performance)
const WEATHER_ICON_MAP = {
  'Clear': 'fas fa-sun',
  'Clouds': 'fas fa-cloud',
  'Rain': 'fas fa-cloud-rain',
  'Drizzle': 'fas fa-cloud-drizzle',
  'Thunderstorm': 'fas fa-bolt',
  'Snow': 'fas fa-snowflake',
  'Mist': 'fas fa-smog',
  'Fog': 'fas fa-smog',
  'Haze': 'fas fa-smog'
};

// Get user's location and update weather
function getUserLocationWeather() {
  console.log('Location button clicked');
  
  if (!navigator.geolocation) {
    showToast('Geolocation not supported by this browser', 'error');
    return;
  }
  
  // Check if we're on HTTPS (required for geolocation)
  if (location.protocol !== 'https:' && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
    showToast('Location access requires HTTPS', 'warning');
    return;
  }
  
  showToast('Requesting location access...', 'info');
  
  navigator.geolocation.getCurrentPosition(
    async (position) => {
      console.log('Location obtained:', position.coords);
      const { latitude, longitude } = position.coords;
      
      // Validate coordinates
      if (typeof latitude !== 'number' || typeof longitude !== 'number' ||
          latitude < -90 || latitude > 90 || longitude < -180 || longitude > 180) {
        showToast('Invalid location coordinates', 'error');
        return;
      }
      
      // Store user location globally
      window.userLocation = { lat: latitude, lon: longitude };
      
      try {
        const weatherData = await getWeatherByCoordinates(latitude, longitude);
        if (weatherData && !weatherData.error) {
          weatherTemp.textContent = `${weatherData.temperature}°C`;
          weatherIcon.className = WEATHER_ICON_MAP[weatherData.condition] || 'fas fa-sun';
          weatherIcon.title = `${weatherData.description} in ${weatherData.location}`;
          window.currentWeather = weatherData;
          showToast(`Weather updated for ${weatherData.location}`);
        } else {
          showToast('Failed to get weather data', 'error');
        }
      } catch (error) {
        console.error('Location weather error:', error);
        showToast('Failed to get location weather', 'error');
      }
    },
    (error) => {
      console.error('Geolocation error:', error);
      let message = 'Location access failed';
      
      switch(error.code) {
        case error.PERMISSION_DENIED:
          message = 'Location access denied by user';
          break;
        case error.POSITION_UNAVAILABLE:
          message = 'Location information unavailable';
          break;
        case error.TIMEOUT:
          message = 'Location request timed out';
          break;
      }
      
      showToast(message, 'warning');
    },
    { 
      timeout: 10000,
      enableHighAccuracy: true,
      maximumAge: 300000 // 5 minutes
    }
  );
}

// Set weather API key
async function setWeatherApiKey(apiKey) {
  try {
    const response = await fetch('/api/weather/set-key', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_key: apiKey })
    });
    
    const data = await response.json();
    
    if (response.ok) {
      showToast('Weather API key set successfully!');
      updateWeather(); // Refresh weather with new key
      return true;
    } else {
      showToast(data.error || 'Failed to set API key', 'error');
      return false;
    }
  } catch (error) {
    showToast('Failed to set API key', 'error');
    return false;
  }
}

// Modal event listeners
modalClose.addEventListener('click', hideModal);
modalOverlay.addEventListener('click', (e) => {
  if (e.target === modalOverlay) {
    hideModal();
  }
});

// Event Listeners
sendBtn.addEventListener('click', sendMessage);
if (themeToggle) themeToggle.addEventListener('click', toggleTheme);

// Theme selector events
themeClose.addEventListener('click', hideThemeSelector);
autoThemeCheckbox.addEventListener('change', toggleAutoTheme);
createThemeBtn.addEventListener('click', showThemeCreator);

themeOptions.forEach(option => {
  option.addEventListener('click', () => {
    const theme = option.dataset.theme;
    setTheme(theme);
  });
});

// Simple event listeners
if (creatorClose) creatorClose.addEventListener('click', hideThemeCreator);
if (creatorCancel) creatorCancel.addEventListener('click', hideThemeCreator);
if (creatorSave) creatorSave.addEventListener('click', saveCustomTheme);
if (createThemeBtn) createThemeBtn.addEventListener('click', showThemeCreator);

// Color picker events
if (colorPrimary) colorPrimary.addEventListener('input', updatePreview);
if (colorBg0) colorBg0.addEventListener('input', updatePreview);
if (colorBg1) colorBg1.addEventListener('input', updatePreview);
if (colorFg) colorFg.addEventListener('input', updatePreview);

// Close on overlay click
if (themeCreatorOverlay) {
  themeCreatorOverlay.addEventListener('click', (e) => {
    if (e.target === themeCreatorOverlay) hideThemeCreator();
  });
}

// Test function for debugging
window.testThemeCreator = function() {
  console.log('Test function called');
  showThemeCreator();
};

// Close theme selector on outside click
document.addEventListener('click', (e) => {
  if (themeSelectorVisible && !themeSelector.contains(e.target) && (!themeToggle || !themeToggle.contains(e.target))) {
    hideThemeSelector();
  }
});
clearBtn.addEventListener('click', clearHistory);

// Add clear all data button functionality
document.addEventListener('DOMContentLoaded', () => {
  // Add clear all button if it doesn't exist
  if (!document.getElementById('clear-all-btn')) {
    const clearAllBtn = document.createElement('button');
    clearAllBtn.id = 'clear-all-btn';
    clearAllBtn.className = 'btn btn--danger btn--sm';
    clearAllBtn.style.padding = '4px 8px';
    clearAllBtn.style.fontSize = '12px';
    clearAllBtn.style.height = '32px';
    clearAllBtn.innerHTML = '<i class="fas fa-trash-alt"></i> Clear All';
    clearAllBtn.title = 'Clear all chat data and sessions';
    clearAllBtn.onclick = clearAllData;
    
    // Add to sidebar header controls (next to new-chat-btn)
    const sidebarHeader = document.querySelector('.sidebar-header');
    if (sidebarHeader) {
      // Find or create wrapper to align them nicely
      let btnGroup = sidebarHeader.querySelector('.sidebar-header-buttons');
      if (!btnGroup) {
        btnGroup = document.createElement('div');
        btnGroup.className = 'sidebar-header-buttons';
        btnGroup.style.display = 'flex';
        btnGroup.style.gap = '8px';
        btnGroup.style.alignItems = 'center';
        
        const newChat = document.getElementById('new-chat-btn');
        if (newChat) {
          newChat.parentNode.insertBefore(btnGroup, newChat);
          btnGroup.appendChild(newChat);
        }
      }
      btnGroup.appendChild(clearAllBtn);
    }
  }
});
exportBtn.addEventListener('click', exportChat);
voiceBtn.addEventListener('click', toggleVoice);
historyToggle.addEventListener('click', toggleHistory);
const sidebarToggleBtn = document.getElementById('sidebar-toggle-btn');
if (sidebarToggleBtn) {
  sidebarToggleBtn.addEventListener('click', toggleHistory);
}
const sidebarCloseBtn = document.getElementById('sidebar-close-btn');
if (sidebarCloseBtn) {
  sidebarCloseBtn.addEventListener('click', toggleHistory);
}
newChatBtn.addEventListener('click', startNewChat);
document.getElementById('location-btn').addEventListener('click', getUserLocationWeather);
emojiBtn.addEventListener('click', toggleEmojiPicker);

// Context panel events - no hover logic needed

hoverPanel.addEventListener('click', (e) => {
  e.preventDefault();
  e.stopPropagation();
  const menuItem = e.target.closest('.panel-item');
  if (menuItem && menuItem.dataset.action) {
    handleHoverAction(menuItem.dataset.action);
  }
});

// Hide context panel on click outside or scroll
document.addEventListener('click', (e) => {
  if (!hoverPanel.contains(e.target)) {
    hideHoverPanel();
  }
  
  // Hide emoji picker when clicking outside
  if (!emojiPicker.contains(e.target) && !emojiBtn.contains(e.target)) {
    hideEmojiPicker();
  }
  
  // Hide theme selector when clicking outside
  if (themeSelectorVisible && !themeSelector.contains(e.target) && (!themeToggle || !themeToggle.contains(e.target))) {
    hideThemeSelector();
  }
  
  // Hide bubble actions dropdowns when clicking outside
  if (!e.target.closest('.bubble__menu-btn') && !e.target.closest('.bubble__actions-dropdown')) {
    document.querySelectorAll('.bubble__actions-dropdown').forEach(dropdown => {
      dropdown.classList.remove('show');
    });
  }
});

document.addEventListener('scroll', () => {
  hideHoverPanel();
  hideEmojiPicker();
});



// Search functionality
searchBtn.addEventListener('click', () => {
  searchPanel.style.display = searchPanel.style.display === 'none' ? 'flex' : 'none';
  if (searchPanel.style.display === 'flex') {
    searchInput.focus();
  } else {
    searchInput.value = '';
    searchMessages();
  }
});

searchClose.addEventListener('click', () => {
  searchPanel.style.display = 'none';
  searchInput.value = '';
  searchMessages();
});

searchInput.addEventListener('input', searchMessages);

// Input events
inputEl.addEventListener('input', updateCharCount);
inputEl.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
  if (e.ctrlKey || e.metaKey) {
    switch (e.key) {
      case 'k':
        e.preventDefault();
        if (shortcuts) {
          shortcuts.style.display = shortcuts.style.display === 'none' ? 'block' : 'none';
        }
        break;
      case 'l':
        e.preventDefault();
        clearHistory();
        break;
      case 'd':
        if (e.shiftKey) {
          e.preventDefault();
          clearAllData();
        }
        break;
      case 'e':
        e.preventDefault();
        exportChat();
        break;
      case 'f':
        e.preventDefault();
        searchBtn.click();
        break;
      case 'c':
        if (e.shiftKey) {
          e.preventDefault();
          copyCurrentChatMessages();
        }
        break;
      case 'r':
        e.preventDefault();
        regenerateLastResponse();
        break;
      case 'w':
        e.preventDefault();
        getUserLocationWeather();
        break;
      case 'u':
        if (e.shiftKey) {
          e.preventDefault();
          // Use a more user-friendly modal instead of prompt
          showToast('API key setting moved to settings panel', 'info');
        }
        break;
      case 't':
        e.preventDefault();
        showThemeSelector();
        break;
      case 't':
        e.preventDefault();
        showThemeSelector();
        break;
    }
  } else if (e.key === 'Escape') {
    // Close panels in priority order
    if (modalOverlay.classList.contains('show')) {
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
      searchPanel.style.display = 'none';
      shortcuts.style.display = 'none';
      searchInput.value = '';
      searchMessages();
    }
  }
});



// Initialize on load
window.addEventListener('load', async () => {
  try {
    // Initialize theme system first (loads custom themes from backend)
    await initTheme();
    
    // Then initialize other components
    initVoiceInput();
    initWeatherTime();
    initEmojiPicker();
    initAPISettings();
    updateCharCount();
    updateMessageCount(0);
    if (currentSessionId) {
      await loadChatSession(currentSessionId);
    } else {
      updateRecentChats();
    }

    inputEl.focus();
    setStatus('idle');
    
    // Set current year
    document.getElementById('year').textContent = new Date().getFullYear();
    
    console.log('App initialized successfully');
  } catch (error) {
    console.error('App initialization error:', error);
    // Ensure basic functionality works even if theme loading fails
    setStatus('idle');
    inputEl.focus();
  }
});

// Auto-save draft
let draftTimer;
inputEl.addEventListener('input', () => {
  clearTimeout(draftTimer);
  draftTimer = setTimeout(() => {
    localStorage.setItem('chatDraft', inputEl.value);
  }, 500);
});

// Restore draft on load
window.addEventListener('load', () => {
  const draft = localStorage.getItem('chatDraft');
  if (draft) {
    inputEl.value = draft;
    updateCharCount();
  }
});

// Clear draft on send - integrate into existing sendMessage function
// This is handled within the sendMessage function itself

// Emoji Picker Functions
function initEmojiPicker() {
  populateEmojiGrid('smileys');
  
  // Category click handlers
  emojiCategories.forEach(category => {
    category.addEventListener('click', () => {
      emojiCategories.forEach(c => c.classList.remove('active'));
      category.classList.add('active');
      populateEmojiGrid(category.dataset.category);
    });
  });
}

function populateEmojiGrid(category) {
  const emojis = emojiData[category] || emojiData.smileys;
  emojiGrid.innerHTML = '';
  
  emojis.forEach(emoji => {
    const button = document.createElement('button');
    button.className = 'emoji-item';
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
  emojiPicker.classList.toggle('show', emojiPickerVisible);
  
  if (emojiPickerVisible) {
    // Position picker relative to composer area
    const composer = document.querySelector('.composer');
    const rect = composer.getBoundingClientRect();
    
    let left = rect.right - 320;
    let bottom = window.innerHeight - rect.top + 10;
    
    if (left < 10) {
      left = 10;
    }
    
    emojiPicker.style.left = left + 'px';
    emojiPicker.style.bottom = bottom + 'px';
  }
}

function hideEmojiPicker() {
  emojiPickerVisible = false;
  emojiPicker.classList.remove('show');
}

// Remove deprecated fetchWeather function - replaced with getUserLocationWeather
// This function used alert() which is not recommended for production

// API Settings (BYOK) Modal State & Functions
let apiSettingsVisible = false;

function getBYOKConfig() {
  const select = document.getElementById('chatbox-model-select');
  if (!select) return null;

  const val = select.value;
  if (!val) return null;

  const parts    = val.split(':');
  const provider = parts[0];
  const model    = parts.slice(1).join(':');

  const keyMap = {
    openai:     'apiOpenAIKey',
    gemini:     'apiGeminiKey',
    anthropic:  'apiAnthropicKey',
    groq:       'apiGroqKey',
    openrouter: 'apiOpenRouterKey',
    mistral:    'apiMistralKey',
  };

  const apiKey = (localStorage.getItem(keyMap[provider] || '') || '').trim();
  return { provider, api_key: apiKey, model };
}

function initAPISettings() {
  if (!apiSettingsBtn) return;
  
  // Show settings
  apiSettingsBtn.addEventListener('click', () => {
    showAccountDetailsModal('api');
  });
  
  // Toggle password eye visibility for all key fields
  document.querySelectorAll('#api-settings .toggle-password-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const input = btn.previousElementSibling;
      const icon = btn.querySelector('i');
      if (input.type === 'password') {
        input.type = 'text';
        icon.className = 'far fa-eye-slash';
      } else {
        input.type = 'password';
        icon.className = 'far fa-eye';
      }
    });
  });
  
  // Update visibility of provider cards on provider select change
  apiProviderSelect.addEventListener('change', updateAPIKeyCards);
  
  // Close / Cancel click
  document.getElementById('api-settings-close').addEventListener('click', hideAPISettings);
  apiSettingsCancel.addEventListener('click', hideAPISettings);
  
  // Save button
  apiSettingsSave.addEventListener('click', () => {
    const provider = apiProviderSelect.value;
    const openaiKey = apiOpenAIKeyInput.value.trim();
    const openaiModel = apiOpenAIModelSelect.value;
    const geminiKey = apiGeminiKeyInput.value.trim();
    const geminiModel = apiGeminiModelSelect.value;
    
    const anthropicKey = document.getElementById('api-anthropic-key').value.trim();
    const anthropicModel = document.getElementById('api-anthropic-model').value;
    const groqKey = document.getElementById('api-groq-key').value.trim();
    const groqModel = document.getElementById('api-groq-model').value;
    const openrouterKey = document.getElementById('api-openrouter-key').value.trim();
    const openrouterModel = document.getElementById('api-openrouter-model').value;
    const mistralKey = document.getElementById('api-mistral-key').value.trim();
    const mistralModel = document.getElementById('api-mistral-model').value;
    
    // Simple key format validations
    if (provider === 'openai' && openaiKey && !openaiKey.startsWith('sk-')) {
      showToast('Warning: OpenAI key usually starts with sk-', 'warning');
    }
    if (provider === 'gemini' && geminiKey && !geminiKey.startsWith('AIzaSy')) {
      showToast('Warning: Gemini key usually starts with AIzaSy', 'warning');
    }
    
    localStorage.setItem('apiProvider', provider);
    localStorage.setItem('apiOpenAIKey', openaiKey);
    localStorage.setItem('apiOpenAIModel', openaiModel);
    localStorage.setItem('apiGeminiKey', geminiKey);
    localStorage.setItem('apiGeminiModel', geminiModel);
    
    localStorage.setItem('apiAnthropicKey', anthropicKey);
    localStorage.setItem('apiAnthropicModel', anthropicModel);
    localStorage.setItem('apiGroqKey', groqKey);
    localStorage.setItem('apiGroqModel', groqModel);
    localStorage.setItem('apiOpenRouterKey', openrouterKey);
    localStorage.setItem('apiOpenRouterModel', openrouterModel);
    localStorage.setItem('apiMistralKey', mistralKey);
    localStorage.setItem('apiMistralModel', mistralModel);
    
    hideAPISettings();
    showToast('API Key settings saved successfully!');
    // Notify model-selector badge to refresh
    document.dispatchEvent(new CustomEvent('apikeysSaved'));
  });
  
  // Reset button
  apiSettingsReset.addEventListener('click', () => {
    const keysToRemove = [
      'apiProvider', 'apiOpenAIKey', 'apiOpenAIModel', 'apiGeminiKey', 'apiGeminiModel',
      'apiAnthropicKey', 'apiAnthropicModel', 'apiGroqKey', 'apiGroqModel',
      'apiOpenRouterKey', 'apiOpenRouterModel', 'apiMistralKey', 'apiMistralModel'
    ];
    keysToRemove.forEach(k => localStorage.removeItem(k));
    
    apiProviderSelect.value = 'default';
    apiOpenAIKeyInput.value = '';
    apiOpenAIModelSelect.value = 'gpt-4o-mini';
    apiGeminiKeyInput.value = '';
    apiGeminiModelSelect.value = 'gemini-1.5-flash';
    
    document.getElementById('api-anthropic-key').value = '';
    document.getElementById('api-anthropic-model').value = 'claude-3-5-sonnet-20241022';
    document.getElementById('api-groq-key').value = '';
    document.getElementById('api-groq-model').value = 'llama3-8b-8192';
    document.getElementById('api-openrouter-key').value = '';
    document.getElementById('api-openrouter-model').value = 'meta-llama/llama-3-8b-instruct:free';
    document.getElementById('api-mistral-key').value = '';
    document.getElementById('api-mistral-model').value = 'mistral-small-latest';
    
    updateAPIKeyCards();
    hideAPISettings();
    showToast('API configurations reset to Server Default', 'info');
    document.dispatchEvent(new CustomEvent('apikeysSaved'));
  });
}

function updateAPIKeyCards() {
  const provider = apiProviderSelect.value;
  openaiKeyCard.style.display = provider === 'openai' ? 'block' : 'none';
  geminiKeyCard.style.display = provider === 'gemini' ? 'block' : 'none';
  document.getElementById('anthropic-key-card').style.display = provider === 'anthropic' ? 'block' : 'none';
  document.getElementById('groq-key-card').style.display = provider === 'groq' ? 'block' : 'none';
  document.getElementById('openrouter-key-card').style.display = provider === 'openrouter' ? 'block' : 'none';
  document.getElementById('mistral-key-card').style.display = provider === 'mistral' ? 'block' : 'none';
}

function showAPISettings() {
  apiSettingsOverlay.classList.add('show');
  apiSettingsVisible = true;
}

function hideAPISettings() {
  apiSettingsOverlay.classList.remove('show');
  apiSettingsVisible = false;
}

// ── Toolbar menu & model-selector orchestration ────────────────
document.addEventListener('DOMContentLoaded', () => {
  const toolbarMenuBtn    = document.getElementById('toolbar-menu-btn');
  const toolbarDropdown   = document.getElementById('toolbar-dropdown');
  const chatboxModelSelect = document.getElementById('chatbox-model-select');
  const modelKeyBadge     = document.getElementById('model-key-badge');

  function updateModelKeyBadge() {
    if (!modelKeyBadge || !chatboxModelSelect) return;

    const val      = chatboxModelSelect.value;
    const provider = val ? val.split(':')[0] : '';

    const keyMap = {
      openai:     'apiOpenAIKey',
      gemini:     'apiGeminiKey',
      anthropic:  'apiAnthropicKey',
      groq:       'apiGroqKey',
      openrouter: 'apiOpenRouterKey',
      mistral:    'apiMistralKey',
    };

    const storageKey = keyMap[provider];
    const savedKey   = storageKey ? (localStorage.getItem(storageKey) || '').trim() : '';

    if (savedKey) {
      modelKeyBadge.className = 'model-key-badge model-key-badge--ok';
      modelKeyBadge.title = `✓ API key configured for ${provider}`;
    } else {
      modelKeyBadge.className = 'model-key-badge model-key-badge--warn';
      modelKeyBadge.title = `⚠ No API key for ${provider} — open ☰ → API Settings`;
    }
  }

  if (chatboxModelSelect) {
    // Restore saved model — fall back to first option if stale value
    const stored = localStorage.getItem('chatboxModel') || '';
    const optionExists = stored && chatboxModelSelect.querySelector(`option[value="${stored}"]`);
    chatboxModelSelect.value = optionExists ? stored : chatboxModelSelect.options[0].value;
    // Persist the resolved selection
    localStorage.setItem('chatboxModel', chatboxModelSelect.value);
    updateModelKeyBadge();

    chatboxModelSelect.addEventListener('change', () => {
      localStorage.setItem('chatboxModel', chatboxModelSelect.value);
      updateModelKeyBadge();

      const val      = chatboxModelSelect.value;
      const provider = val.split(':')[0];
      const model    = val.split(':').slice(1).join(':');
      const keyMap   = {
        openai:     'apiOpenAIKey',
        gemini:     'apiGeminiKey',
        anthropic:  'apiAnthropicKey',
        groq:       'apiGroqKey',
        openrouter: 'apiOpenRouterKey',
        mistral:    'apiMistralKey',
      };
      const hasKey = !!(localStorage.getItem(keyMap[provider] || '') || '').trim();
      if (hasKey) {
        showToast(`Model → ${model}`, 'success');
      } else {
        showToast(`⚠ No ${provider} key — open ☰ → API Settings`, 'warning');
      }
    });
  }

  // Re-check badge whenever API Settings saves new keys
  document.addEventListener('apikeysSaved', updateModelKeyBadge);

  // ── CUSTOM MODEL SEARCHER CONTROLLER ──────────────────────────
  const modelSearcher = document.getElementById('custom-model-searcher');
  const modelPillTrigger = document.getElementById('model-pill-trigger');
  const selectedModelDisplay = document.getElementById('selected-model-display');
  const modelSearcherDropdown = document.getElementById('model-searcher-dropdown');
  const modelSearcherInput = document.getElementById('model-searcher-input');
  const modelSearcherClear = document.getElementById('model-searcher-clear');
  const modelSearcherList = document.getElementById('model-searcher-list');
  const fetchLiveModelsBtn = document.getElementById('fetch-live-models-btn');
  const addCustomModelBtn = document.getElementById('add-custom-model-btn');

  if (modelSearcher && chatboxModelSelect) {
    // 1. Sync displaying selected model name
    function syncSelectedModelDisplay() {
      const selectedOpt = chatboxModelSelect.options[chatboxModelSelect.selectedIndex];
      if (selectedOpt) {
        const val = chatboxModelSelect.value || '';
        const provider = val.split(':')[0] || '';
        modelPillTrigger.dataset.provider = provider;
        
        const cleanText = selectedOpt.textContent.replace(/^[\p{Emoji}\p{Extended_Pictographic}]\s*/u, '').trim();
        const logoHtml = getProviderLogoHtml(provider, 14);
        
        selectedModelDisplay.innerHTML = `${logoHtml} <span style="margin-left: 6px;">${cleanText}</span>`;
      }
    }

    // 2. Populate list items from native select
    function buildModelSearcherList(filterText = '') {
      modelSearcherList.innerHTML = '';
      const query = filterText.toLowerCase().trim();

      // Read current options grouped by optgroups
      const groups = chatboxModelSelect.querySelectorAll('optgroup');
      let totalVisible = 0;

      groups.forEach(group => {
        const groupLabel = group.label;
        const options = group.querySelectorAll('option');
        
        // Filter options in this group
        const matchedOptions = Array.from(options).filter(opt => {
          return opt.textContent.toLowerCase().includes(query) || opt.value.toLowerCase().includes(query);
        });

        if (matchedOptions.length > 0) {
          // Add group title
          const titleDiv = document.createElement('div');
          titleDiv.className = 'model-searcher-group-title';
          titleDiv.textContent = groupLabel;
          modelSearcherList.appendChild(titleDiv);

          // Add items
          matchedOptions.forEach(opt => {
            const itemDiv = document.createElement('div');
            const isActive = chatboxModelSelect.value === opt.value;
            itemDiv.className = `model-searcher-item ${isActive ? 'active' : ''}`;
            
            const provider = opt.value.split(':')[0];
            const logoHtml = getProviderLogoHtml(provider, 14);
            const cleanText = opt.textContent.replace(/^[\p{Emoji}\p{Extended_Pictographic}]\s*/u, '').trim();
            
            const textSpan = document.createElement('span');
            textSpan.style.display = 'flex';
            textSpan.style.alignItems = 'center';
            textSpan.style.gap = '8px';
            textSpan.innerHTML = `${logoHtml} <span>${cleanText}</span>`;
            itemDiv.appendChild(textSpan);

            const providerSpan = document.createElement('span');
            providerSpan.className = 'item-provider';
            providerSpan.textContent = provider;
            itemDiv.appendChild(providerSpan);

            // Click selects option
            itemDiv.addEventListener('click', () => {
              chatboxModelSelect.value = opt.value;
              chatboxModelSelect.dispatchEvent(new Event('change'));
              syncSelectedModelDisplay();
              closeDropdown();
            });

            modelSearcherList.appendChild(itemDiv);
            totalVisible++;
          });
        }
      });

      // Show/Hide custom register button if input looks like a potential custom model
      if (query.includes(':') && query.split(':')[1].length > 1) {
        addCustomModelBtn.style.display = 'flex';
        addCustomModelBtn.title = `Add "${query}" as a custom model option`;
      } else {
        addCustomModelBtn.style.display = 'none';
      }

      // If no results, show empty status
      if (totalVisible === 0) {
        const emptyDiv = document.createElement('div');
        emptyDiv.style.padding = '20px 12px';
        emptyDiv.style.textAlign = 'center';
        emptyDiv.style.color = 'var(--muted)';
        emptyDiv.style.fontSize = '12px';
        emptyDiv.textContent = 'No matching models. Type "provider:model" to add a custom one!';
        modelSearcherList.appendChild(emptyDiv);
      }
    }

    // Toggle dropdown
    function toggleDropdown(e) {
      if (e) e.stopPropagation();
      const isOpen = modelSearcherDropdown.classList.contains('show');
      if (isOpen) {
        closeDropdown();
      } else {
        document.querySelectorAll('.toolbar-dropdown, .bubble__actions-dropdown').forEach(d => d.classList.remove('show'));
        modelSearcherDropdown.classList.add('show');
        modelPillTrigger.querySelector('i').className = 'fas fa-chevron-down';
        modelSearcherInput.focus();
        buildModelSearcherList(modelSearcherInput.value);
      }
    }

    function closeDropdown() {
      modelSearcherDropdown.classList.remove('show');
      modelPillTrigger.querySelector('i').className = 'fas fa-chevron-up';
    }

    // Close on click outside
    document.addEventListener('click', (e) => {
      if (!modelSearcher.contains(e.target)) {
        closeDropdown();
      }
    });

    modelPillTrigger.addEventListener('click', toggleDropdown);

    // Filter input events
    modelSearcherInput.addEventListener('input', (e) => {
      const val = e.target.value;
      modelSearcherClear.style.display = val ? 'flex' : 'none';
      buildModelSearcherList(val);
    });

    modelSearcherClear.addEventListener('click', () => {
      modelSearcherInput.value = '';
      modelSearcherClear.style.display = 'none';
      buildModelSearcherList('');
      modelSearcherInput.focus();
    });

    // Add Custom Model Registration
    addCustomModelBtn.addEventListener('click', () => {
      const customString = modelSearcherInput.value.trim();
      const parts = customString.split(':');
      if (parts.length < 2 || !parts[0] || !parts[1]) {
        showToast('Please type custom model as "provider:name" (e.g. openai:my-gpt)', 'warning');
        return;
      }
      
      const provider = parts[0].toLowerCase();
      const modelName = parts.slice(1).join(':');

      // Create dynamic option
      const newOpt = document.createElement('option');
      newOpt.value = customString;
      newOpt.textContent = `⚙️ Custom: ${modelName}`;

      // Find or create "Custom Models" optgroup in native select
      let customGroup = Array.from(chatboxModelSelect.querySelectorAll('optgroup')).find(g => g.label.includes('Custom Registered'));
      if (!customGroup) {
        customGroup = document.createElement('optgroup');
        customGroup.label = '⚙️ Custom Registered Models';
        chatboxModelSelect.appendChild(customGroup);
      }

      // Check if already exists
      const existing = chatboxModelSelect.querySelector(`option[value="${customString}"]`);
      if (existing) {
        chatboxModelSelect.value = customString;
      } else {
        customGroup.appendChild(newOpt);
        chatboxModelSelect.value = customString;
      }

      chatboxModelSelect.dispatchEvent(new Event('change'));
      syncSelectedModelDisplay();
      closeDropdown();
      showToast(`Registered custom model: ${modelName}`, 'success');
      
      // Reset input
      modelSearcherInput.value = '';
      modelSearcherClear.style.display = 'none';
    });

    // Fetch Live Models via Backend Proxy API
    fetchLiveModelsBtn.addEventListener('click', async () => {
      const activeOpt = chatboxModelSelect.options[chatboxModelSelect.selectedIndex];
      if (!activeOpt) return;
      const provider = chatboxModelSelect.value.split(':')[0];

      const keyMap = {
        openai:     'apiOpenAIKey',
        gemini:     'apiGeminiKey',
        anthropic:  'apiAnthropicKey',
        groq:       'apiGroqKey',
        openrouter: 'apiOpenRouterKey',
        mistral:    'apiMistralKey',
      };
      
      const storageKey = keyMap[provider];
      const savedKey = storageKey ? (localStorage.getItem(storageKey) || '').trim() : '';

      if (!savedKey) {
        showToast(`No API key saved for ${provider}! Click ☰ → API Settings to configure.`, 'warning');
        return;
      }

      fetchLiveModelsBtn.disabled = true;
      fetchLiveModelsBtn.querySelector('span').textContent = 'Fetching...';
      fetchLiveModelsBtn.querySelector('i').className = 'fas fa-spinner fa-spin';

      try {
        const resp = await fetch('/api/fetch-models', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ provider, api_key: savedKey })
        });

        const result = await resp.json();
        if (result.error) {
          showToast(`Fetch error: ${result.error}`, 'error');
        } else if (result.models && result.models.length > 0) {
          let liveGroup = Array.from(chatboxModelSelect.querySelectorAll('optgroup')).find(g => g.label === `📡 Live API: ${provider}`);
          if (!liveGroup) {
            liveGroup = document.createElement('optgroup');
            liveGroup.label = `📡 Live API: ${provider}`;
            chatboxModelSelect.appendChild(liveGroup);
          } else {
            liveGroup.innerHTML = '';
          }

          result.models.forEach(m => {
            const optVal = `${provider}:${m}`;
            if (!chatboxModelSelect.querySelector(`option[value="${optVal}"]`)) {
              const opt = document.createElement('option');
              opt.value = optVal;
              opt.textContent = `📡 ${m}`;
              liveGroup.appendChild(opt);
            }
          });

          buildModelSearcherList(modelSearcherInput.value);
          showToast(`Loaded ${result.models.length} live models from ${provider}!`, 'success');
        } else {
          showToast('No models returned from API.', 'warning');
        }
      } catch (err) {
        showToast(`API Connection failed: ${err.message}`, 'error');
      } finally {
        fetchLiveModelsBtn.disabled = false;
        fetchLiveModelsBtn.querySelector('span').textContent = 'Fetch Live Models';
        fetchLiveModelsBtn.querySelector('i').className = 'fas fa-sync-alt';
      }
    });

    setTimeout(() => {
      syncSelectedModelDisplay();
      chatboxModelSelect.addEventListener('change', syncSelectedModelDisplay);
    }, 100);
  }

  // ── Toolbar dropdown ──────────────────────────────────────────
  if (toolbarMenuBtn && toolbarDropdown) {
    toolbarMenuBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      document.querySelectorAll('.bubble__actions-dropdown').forEach(d => d.classList.remove('show'));
      // Close profile dropdown
      const profileDropdown = document.getElementById('profile-dropdown');
      if (profileDropdown) profileDropdown.style.display = 'none';
      toolbarDropdown.classList.toggle('show');
    });

    toolbarDropdown.querySelectorAll('.btn').forEach(btn => {
      btn.addEventListener('click', () => toolbarDropdown.classList.remove('show'));
    });

    document.addEventListener('click', (e) => {
      if (!toolbarDropdown.contains(e.target) && !toolbarMenuBtn.contains(e.target)) {
        toolbarDropdown.classList.remove('show');
      }
    });
  }

  // ── Profile dropdown & Account Modal ──────────────────────────
  const profileMenuBtn  = document.getElementById('profile-menu-btn');
  const profileDropdown = document.getElementById('profile-dropdown');
  const profileAccountBtn = document.getElementById('profile-account-btn');

  if (profileMenuBtn && profileDropdown) {
    profileMenuBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      document.querySelectorAll('.bubble__actions-dropdown').forEach(d => d.classList.remove('show'));
      if (toolbarDropdown) toolbarDropdown.classList.remove('show');
      
      const isOpen = profileDropdown.style.display === 'flex';
      profileDropdown.style.display = isOpen ? 'none' : 'flex';
    });

    profileDropdown.querySelectorAll('.btn, a').forEach(item => {
      item.addEventListener('click', () => {
        profileDropdown.style.display = 'none';
      });
    });

    document.addEventListener('click', (e) => {
      if (!profileDropdown.contains(e.target) && !profileMenuBtn.contains(e.target)) {
        profileDropdown.style.display = 'none';
      }
    });
  }

  if (profileAccountBtn) {
    profileAccountBtn.addEventListener('click', showAccountDetailsModal);
  }

  const navProfileBtn = document.getElementById('nav-profile-btn');
  if (navProfileBtn) {
    navProfileBtn.addEventListener('click', showAccountDetailsModal);
  }

  // Handle Account Modal
  async function showAccountDetailsModal(initialTab = 'profile') {
    if (typeof initialTab !== 'string') {
      initialTab = 'profile';
    }
    const username = window.currentUser || 'Guest';
    const displayName = window.currentUserDisplayName || 'Not Set';
    const avatarChar = username.charAt(0).toUpperCase();

    const contentHtml = `
      <div class="account-modal-container" style="display: flex; flex-direction: column; gap: 15px; min-height: 380px;">
        <!-- Tab switch capsule -->
        <div class="mfa-tabs-switcher" style="margin-bottom: 20px; display: flex; background: rgba(0, 0, 0, 0.3); border-radius: var(--radius-md); padding: 4px; border: 1px solid var(--border); position: relative;">
          <button class="mfa-tab-btn" id="modal-tab-profile" style="flex: 1; border: none; background: none; padding: 8px 12px; font-size: 13px; font-weight: 600; color: var(--muted); cursor: pointer; z-index: 2; transition: color 0.3s ease; display: flex; align-items: center; justify-content: center; gap: 8px;">
            <i class="fas fa-user"></i> Profile
          </button>
          <button class="mfa-tab-btn" id="modal-tab-api" style="flex: 1; border: none; background: none; padding: 8px 12px; font-size: 13px; font-weight: 600; color: var(--muted); cursor: pointer; z-index: 2; transition: color 0.3s ease; display: flex; align-items: center; justify-content: center; gap: 8px;">
            <i class="fas fa-key"></i> API Keys
          </button>
          <button class="mfa-tab-btn" id="modal-tab-integrations" style="flex: 1; border: none; background: none; padding: 8px 12px; font-size: 13px; font-weight: 600; color: var(--muted); cursor: pointer; z-index: 2; transition: color 0.3s ease; display: flex; align-items: center; justify-content: center; gap: 8px;">
            <i class="fas fa-plug"></i> Integrations
          </button>
          <div id="modal-toggle-slider" style="position: absolute; top: 4px; bottom: 4px; left: 4px; width: calc(33.333% - 5px); background: var(--mint); border-radius: calc(var(--radius-md) - 2px); z-index: 1; transition: transform 0.3s cubic-bezier(0.25, 0.8, 0.25, 1); box-shadow: 0 4px 12px rgba(55, 230, 181, 0.3);"></div>
        </div>

        <!-- Profile Section -->
        <div id="modal-sect-profile" class="modal-tab-section" style="display: block;">
          <div style="text-align: center; margin-bottom: 20px;">
            <div id="modal-profile-avatar-container" style="position: relative; width: 80px; height: 80px; margin: 0 auto 12px auto; cursor: pointer; border-radius: 50%; overflow: hidden; border: 2px solid var(--mint); box-shadow: 0 4px 14px rgba(55, 230, 181, 0.3); display: flex; align-items: center; justify-content: center; background: rgba(255,255,255,0.03);">
              <span id="modal-avatar-char" style="font-size: 2.2em; font-weight: 700; color: var(--fg);">${avatarChar}</span>
              <img id="modal-avatar-img" style="display: none; width: 100%; height: 100%; object-fit: cover;" />
            </div>
            <h3 style="margin: 0; font-size: 1.4em; color: var(--fg); font-weight: 600;">${username}</h3>
            <p style="margin: 4px 0 0 0; font-size: 0.9em; color: var(--muted);">Display Name: <strong id="modal-display-name-text" style="color: var(--mint);">${displayName}</strong></p>
          </div>

          <!-- Actions -->
          <div style="display: flex; flex-direction: column; gap: 10px;">
            <button id="modal-change-name-btn" class="btn btn--ghost btn--sm" style="width: 100%; display: flex; align-items: center; justify-content: center; gap: 8px; border: 1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.02); padding: 8px 12px; border-radius: 8px;">
              <i class="fas fa-user-edit"></i> Edit Display Name
            </button>
            <button id="modal-upload-pic-btn" class="btn btn--ghost btn--sm" style="width: 100%; display: flex; align-items: center; justify-content: center; gap: 8px; border: 1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.02); padding: 8px 12px; border-radius: 8px;">
              <i class="fas fa-upload"></i> Upload Custom Avatar
            </button>
            <button id="modal-google-pic-btn" class="btn btn--ghost btn--sm" style="width: 100%; display: flex; align-items: center; justify-content: center; gap: 8px; border: 1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.02); padding: 8px 12px; border-radius: 8px; display: none;">
              <i class="fab fa-google"></i> Set to Google Avatar
            </button>
            <button id="modal-remove-pic-btn" class="btn btn--ghost btn--sm btn--danger" style="width: 100%; display: flex; align-items: center; justify-content: center; gap: 8px; padding: 8px 12px; border-radius: 8px; display: none;">
              <i class="fas fa-trash-alt"></i> Remove Avatar
            </button>
          </div>
          <input type="file" id="modal-avatar-file-input" style="display: none;" accept="image/*" />
        </div>

        <!-- API Keys Section -->
        <div id="modal-sect-api" class="modal-tab-section" style="display: none; max-height: 50vh; overflow-y: auto; padding-right: 4px;">
          <!-- API Settings Inputs Container -->
          <div id="modal-api-inputs-container"></div>
        </div>

        <!-- Integrations Section -->
        <div id="modal-sect-integrations" class="modal-tab-section" style="display: none;">
          <!-- Connected Addons Cards Grid -->
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;" id="modal-integrations-grid">
            <!-- Google Card -->
            <div class="card glass" style="padding: 12px; display: flex; flex-direction: column; align-items: center; text-align: center; border-radius: var(--radius-md); border: 1px solid var(--border); transition: all 0.2s;" id="m-int-google-card">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="28" height="28" style="margin-bottom: 6px;"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22c-.22-.67-.35-1.37-.35-2.09l.81 1.46z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/></svg>
              <span style="font-weight: 700; font-size: 12px; margin-bottom: 2px;">Google</span>
              <span style="font-size: 10px; margin-bottom: 6px; font-weight: 600;" id="m-int-google-status">Disconnected</span>
              <button class="btn btn--ghost btn--xs" id="m-int-google-btn" style="padding: 2px 6px; font-size: 10px;">Connect</button>
            </div>

            <!-- Location Card -->
            <div class="card glass" style="padding: 12px; display: flex; flex-direction: column; align-items: center; text-align: center; border-radius: var(--radius-md); border: 1px solid var(--border); transition: all 0.2s;" id="m-int-location-card">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="28" height="28" style="margin-bottom: 6px;"><path fill="#EA4335" d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg>
              <span style="font-weight: 700; font-size: 12px; margin-bottom: 2px;">Location</span>
              <span style="font-size: 10px; margin-bottom: 6px; font-weight: 600;" id="m-int-location-status">Disconnected</span>
              <button class="btn btn--ghost btn--xs" id="m-int-location-btn" style="padding: 2px 6px; font-size: 10px;">Enable</button>
            </div>
          </div>
        </div>
      </div>
    `;

    showModal('Account Center', contentHtml, []);

    const modalClose = document.getElementById('modal-close');
    if (modalClose) modalClose.style.display = 'none';

    const tabProfileBtn = document.getElementById('modal-tab-profile');
    const tabApiBtn = document.getElementById('modal-tab-api');
    const tabIntegrationsBtn = document.getElementById('modal-tab-integrations');

    const sectProfile = document.getElementById('modal-sect-profile');
    const sectApi = document.getElementById('modal-sect-api');
    const sectIntegrations = document.getElementById('modal-sect-integrations');

    const switchTab = (tab) => {
      tabProfileBtn.style.color = 'var(--muted)';
      tabApiBtn.style.color = 'var(--muted)';
      tabIntegrationsBtn.style.color = 'var(--muted)';
      
      tabProfileBtn.classList.remove('active');
      tabApiBtn.classList.remove('active');
      tabIntegrationsBtn.classList.remove('active');
      sectProfile.style.display = 'none';
      sectApi.style.display = 'none';
      sectIntegrations.style.display = 'none';

      const slider = document.getElementById('modal-toggle-slider');

      if (tab === 'profile') {
        tabProfileBtn.classList.add('active');
        tabProfileBtn.style.color = 'var(--bg-0)';
        sectProfile.style.display = 'block';
        if (slider) slider.style.transform = 'translateX(0%)';
      } else if (tab === 'api') {
        tabApiBtn.classList.add('active');
        tabApiBtn.style.color = 'var(--bg-0)';
        sectApi.style.display = 'block';
        if (slider) slider.style.transform = 'translateX(100%)';
        initTabApiKeys();
      } else if (tab === 'integrations') {
        tabIntegrationsBtn.classList.add('active');
        tabIntegrationsBtn.style.color = 'var(--bg-0)';
        sectIntegrations.style.display = 'block';
        if (slider) slider.style.transform = 'translateX(200%)';
        refreshModalIntegrations();
      }
    };

    tabProfileBtn.addEventListener('click', () => switchTab('profile'));
    tabApiBtn.addEventListener('click', () => switchTab('api'));
    tabIntegrationsBtn.addEventListener('click', () => switchTab('integrations'));

    // --- Tab Profile Setup ---
    const updateModalAvatarDisplay = () => {
      const avatarCharSpan = document.getElementById('modal-avatar-char');
      const avatarImg = document.getElementById('modal-avatar-img');
      const removeBtn = document.getElementById('modal-remove-pic-btn');
      
      if (window.currentUserProfilePic) {
        avatarImg.src = window.currentUserProfilePic;
        avatarImg.style.display = 'block';
        avatarCharSpan.style.display = 'none';
        if (removeBtn) removeBtn.style.display = 'flex';
      } else {
        avatarImg.style.display = 'none';
        avatarCharSpan.style.display = 'block';
        if (removeBtn) removeBtn.style.display = 'none';
      }
    };
    updateModalAvatarDisplay();

    // Check if google is linked to show Google Avatar option
    try {
      const resp = await fetch('/api/user/integrations');
      if (resp.ok) {
        const data = await resp.json();
        if (data.success && data.integrations.google.connected) {
          const googlePicBtn = document.getElementById('modal-google-pic-btn');
          if (googlePicBtn) {
            googlePicBtn.style.display = 'flex';
            googlePicBtn.onclick = async () => {
              try {
                const meResp = await fetch('/api/google/me');
                if (meResp.ok) {
                  const meData = await meResp.json();
                  const picture = meData.picture;
                  if (picture) {
                    const updateResp = await fetch('/api/accounts/profile', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ profile_pic: picture })
                    });
                    if (updateResp.ok) {
                      window.currentUserProfilePic = picture;
                      updateModalAvatarDisplay();
                      if (typeof window.updateHeaderAvatar === 'function') {
                        window.updateHeaderAvatar(picture);
                      }
                      showToast('Avatar set to Google profile picture!', 'success');
                    } else {
                      showToast('Failed to update profile picture', 'error');
                    }
                  } else {
                    showToast('No profile picture found on your Google Account', 'warning');
                  }
                } else {
                  showToast('Failed to retrieve Google profile data', 'error');
                }
              } catch (err) {
                showToast('Failed to retrieve Google profile data', 'error');
              }
            };
          }
        }
      }
    } catch (e) {
      console.warn(e);
    }

    // Hidden input file handler
    const fileInput = document.getElementById('modal-avatar-file-input');
    const uploadBtn = document.getElementById('modal-upload-pic-btn');
    if (uploadBtn && fileInput) {
      uploadBtn.addEventListener('click', () => fileInput.click());
      fileInput.addEventListener('change', () => {
        const file = fileInput.files[0];
        if (file) {
          if (file.size > 1024 * 1024 * 2) {
            showToast('Image size exceeds 2MB limit', 'warning');
            return;
          }
          const reader = new FileReader();
          reader.onload = async (e) => {
            const base64 = e.target.result;
            try {
              const resp = await fetch('/api/accounts/profile', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ profile_pic: base64 })
              });
              if (resp.ok) {
                window.currentUserProfilePic = base64;
                updateModalAvatarDisplay();
                if (typeof window.updateHeaderAvatar === 'function') {
                  window.updateHeaderAvatar(base64);
                }
                showToast('Profile picture uploaded successfully!', 'success');
              } else {
                showToast('Failed to upload profile picture', 'error');
              }
            } catch (err) {
              showToast('Failed to upload profile picture', 'error');
            }
          };
          reader.readAsDataURL(file);
        }
      });
    }

    // Remove avatar handler
    const removeBtn = document.getElementById('modal-remove-pic-btn');
    if (removeBtn) {
      removeBtn.addEventListener('click', async () => {
        try {
          const resp = await fetch('/api/accounts/profile', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ profile_pic: null })
          });
          if (resp.ok) {
            window.currentUserProfilePic = '';
            updateModalAvatarDisplay();
            if (typeof window.updateHeaderAvatar === 'function') {
              window.updateHeaderAvatar(null);
            }
            showToast('Profile picture removed successfully', 'info');
          } else {
            showToast('Failed to remove profile picture', 'error');
          }
        } catch (err) {
          showToast('Failed to remove profile picture', 'error');
        }
      });
    }

    // Change display name handler
    const changeNameBtn = document.getElementById('modal-change-name-btn');
    if (changeNameBtn) {
      changeNameBtn.addEventListener('click', () => {
        hideModal();
        showInputModal(
          'Edit Display Name',
          'Enter new display name...',
          async (newName) => {
            try {
              const res = await fetch('/api/accounts/profile', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ display_name: newName })
              });
              if (res.ok) {
                window.currentUserDisplayName = newName;
                document.getElementById('modal-display-name-text').textContent = newName;
                showToast('Display name updated successfully!');
              } else {
                showToast('Failed to update display name', 'error');
              }
            } catch (err) {
              showToast('Failed to update display name', 'error');
            }
            setTimeout(() => showAccountDetailsModal('profile'), 300);
          },
          {
            defaultValue: window.currentUserDisplayName || '',
            maxLength: 50,
            required: true,
            label: 'New Display Name'
          }
        );
      });
    }

    // --- Tab API Keys Setup ---
    function initTabApiKeys() {
      const apiInputsContainer = document.getElementById('modal-api-inputs-container');
      if (!apiInputsContainer || apiInputsContainer.children.length > 0) return;

      const apiModalBody = document.querySelector('#api-settings-overlay .modal-body');
      if (apiModalBody) {
        apiInputsContainer.innerHTML = apiModalBody.innerHTML;
        
        apiInputsContainer.querySelectorAll('.toggle-password-btn').forEach(btn => {
          btn.addEventListener('click', () => {
            const input = btn.previousElementSibling;
            const icon = btn.querySelector('i');
            if (input.type === 'password') {
              input.type = 'text';
              icon.className = 'far fa-eye-slash';
            } else {
              input.type = 'password';
              icon.className = 'far fa-eye';
            }
          });
        });
        
        const provSelect = apiInputsContainer.querySelector('#api-provider');
        provSelect.value = localStorage.getItem('apiProvider') || 'default';
        
        const keyFields = {
          'api-openai-key': 'apiOpenAIKey',
          'api-openai-model': 'apiOpenAIModel',
          'api-gemini-key': 'apiGeminiKey',
          'api-gemini-model': 'apiGeminiModel',
          'api-anthropic-key': 'apiAnthropicKey',
          'api-anthropic-model': 'apiAnthropicModel',
          'api-groq-key': 'apiGroqKey',
          'api-groq-model': 'apiGroqModel',
          'api-openrouter-key': 'apiOpenRouterKey',
          'api-openrouter-model': 'apiOpenRouterModel',
          'api-mistral-key': 'apiMistralKey',
          'api-mistral-model': 'apiMistralModel'
        };
        
        for (const [id, storageKey] of Object.entries(keyFields)) {
          const el = apiInputsContainer.querySelector('#' + id);
          if (el) el.value = localStorage.getItem(storageKey) || '';
        }
        
        const btnRow = document.createElement('div');
        btnRow.style = "display: flex; gap: 10px; margin-top: 20px;";
        btnRow.innerHTML = `
          <button class="btn btn--secondary btn--sm" id="modal-api-reset" style="flex: 1;">Reset</button>
          <button class="btn btn--mint btn--sm" id="modal-api-save" style="flex: 1;">Save Keys</button>
        `;
        apiInputsContainer.appendChild(btnRow);
        
        const updateModalKeyCards = () => {
          const provider = provSelect.value;
          apiInputsContainer.querySelectorAll('.api-key-card').forEach(card => card.style.display = 'none');
          const activeCard = apiInputsContainer.querySelector(`#${provider}-key-card`) || apiInputsContainer.querySelector(`#api-${provider}-key-card`) || apiInputsContainer.querySelector(`[id*="${provider}-key-card"]`);
          if (activeCard) activeCard.style.display = 'block';
        };
        
        provSelect.addEventListener('change', updateModalKeyCards);
        updateModalKeyCards();
        
        apiInputsContainer.querySelector('#modal-api-save').addEventListener('click', () => {
          localStorage.setItem('apiProvider', provSelect.value);
          for (const [id, storageKey] of Object.entries(keyFields)) {
            const el = apiInputsContainer.querySelector('#' + id);
            if (el) localStorage.setItem(storageKey, el.value.trim());
          }
          showToast('API Key settings saved successfully!');
          document.dispatchEvent(new CustomEvent('apikeysSaved'));
        });
        
        apiInputsContainer.querySelector('#modal-api-reset').addEventListener('click', () => {
          Object.values(keyFields).concat(['apiProvider']).forEach(k => localStorage.removeItem(k));
          provSelect.value = 'default';
          for (const id of Object.keys(keyFields)) {
            const el = apiInputsContainer.querySelector('#' + id);
            if (el) el.value = '';
          }
          updateModalKeyCards();
          showToast('API configurations reset to default', 'info');
          document.dispatchEvent(new CustomEvent('apikeysSaved'));
        });
      }
    }

    // --- Tab Integrations Setup ---
    async function refreshModalIntegrations() {
      try {
        const resp = await fetch('/api/user/integrations');
        const data = await resp.json();
        if (data.success) {
          const ints = data.integrations;
          
          // Google Card
          const gStatus = document.getElementById('m-int-google-status');
          const gBtn = document.getElementById('m-int-google-btn');
          if (ints.google.connected) {
            gStatus.textContent = "Connected";
            gStatus.style.color = "var(--mint)";
            gBtn.textContent = "Disconnect";
            gBtn.className = "btn btn--ghost btn--xs btn--danger";
            gBtn.onclick = () => toggleModalIntegration('google', 'disconnect');
            const googlePicBtn = document.getElementById('modal-google-pic-btn');
            if (googlePicBtn) googlePicBtn.style.display = 'flex';
          } else {
            gStatus.textContent = "Disconnected";
            gStatus.style.color = "var(--muted)";
            gBtn.textContent = "Connect";
            gBtn.className = "btn btn--ghost btn--xs";
            gBtn.onclick = () => connectGoogleModal();
            const googlePicBtn = document.getElementById('modal-google-pic-btn');
            if (googlePicBtn) googlePicBtn.style.display = 'none';
          }

          // Drive Card and Calendar Card removed

          // Location Card
          const lStatus = document.getElementById('m-int-location-status');
          const lBtn = document.getElementById('m-int-location-btn');
          if (ints.location.connected) {
            lStatus.textContent = "Active";
            lStatus.style.color = "var(--mint)";
            lBtn.textContent = "Disable";
            lBtn.className = "btn btn--ghost btn--xs btn--danger";
            lBtn.onclick = () => toggleModalIntegration('location', 'disconnect');
          } else {
            lStatus.textContent = "Inactive";
            lStatus.style.color = "var(--muted)";
            lBtn.textContent = "Enable";
            lBtn.className = "btn btn--ghost btn--xs";
            lBtn.onclick = () => enableModalLocation();
          }
        }
      } catch (e) {
        console.error("Failed to load integrations in modal", e);
      }
    }

    async function toggleModalIntegration(provider, action, value = 'active') {
      try {
        const resp = await fetch('/api/user/integrations/toggle', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ provider, action, value })
        });
        const data = await resp.json();
        if (data.success) {
          showToast(`${provider} integration updated!`);
          refreshModalIntegrations();
        } else {
          showToast(data.error || "Integration update failed", 'error');
        }
      } catch (e) {
        showToast("Integration toggle request error", 'error');
      }
    }

    function connectGoogleModal() {
      const width = 500;
      const height = 650;
      const left = (window.screen.width / 2) - (width / 2);
      const top = (window.screen.height / 2) - (height / 2);
      
      const popup = window.open('/api/google/auth', 'GoogleLinkPopup', `width=${width},height=${height},left=${left},top=${top},status=no,resizable=yes,scrollbars=yes`);
      
      const handleLinkMessage = (event) => {
        if (event.data && event.data.type === 'google_auth_success') {
          window.removeEventListener('message', handleLinkMessage);
          showToast('Google account connected successfully!');
          refreshModalIntegrations();
        }
      };
      window.addEventListener('message', handleLinkMessage);
    }

    function enableModalLocation() {
      if (!navigator.geolocation) {
        showToast("Geolocation is not supported by your browser", 'error');
        return;
      }
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const lat = position.coords.latitude;
          const lon = position.coords.longitude;
          toggleModalIntegration('location', 'connect', `${lat.toFixed(4)}, ${lon.toFixed(4)}`);
        },
        (error) => {
          showToast("Location permission failed", 'error');
        }
      );
    }

    // Select initial tab
    switchTab(initialTab);
  }
});

// Sidebar Toggle Logic
const button = document.querySelector('#sidebarToggleBtn');
const sidebar = document.querySelector('.admin-sidebar') || document.querySelector('.sidebar');

if (button && sidebar) {
  button.addEventListener('click', () => {
    sidebar.classList.toggle('collapsed');
    
    // Smoothly rotate the chevron icon
    const icon = button.querySelector('i');
    if (icon) {
      icon.style.transform = sidebar.classList.contains('collapsed') 
        ? 'rotate(180deg)' 
        : 'rotate(0deg)';
    }
  });
}