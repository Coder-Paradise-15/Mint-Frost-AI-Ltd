/**
 * Premium Dual-Source Music Player - Frontend Controller
 * Powered strictly by HTML5 Native Audio & Secure Backend APIs.
 * Supporting Restriction-Free YouTube Stream Extraction & Jamendo Indie Music.
 */

document.addEventListener('DOMContentLoaded', () => {
  console.log("[Music Player] DOMContentLoaded fired. Setting up Dual Playback Controller.");

  // DOM Elements
  const jamendoPanel = document.getElementById('jamendo-panel');
  const jamendoPanelBackdrop = document.getElementById('jamendo-panel-backdrop');
  const jamendoBtn = document.getElementById('jamendo-btn');
  const jamendoPanelClose = document.getElementById('jamendo-panel-close');
  const jamendoPanelTitle = document.getElementById('jamendo-panel-title-text');
  const jamendoSearchInput = document.getElementById('jamendo-search-input');
  const jamendoSearchClear = document.getElementById('jamendo-search-clear');
  const jamendoResultsList = document.getElementById('jamendo-results-list');
  const jamendoStatusMsg = document.getElementById('jamendo-status-msg');

  // Sidebar Nav Elements
  const navItemHome = document.getElementById('nav-item-home');
  const navItemLibrary = document.getElementById('nav-item-library');
  const navItemPlaylists = document.getElementById('nav-item-playlists');
  const sidebarPlaylistsList = document.getElementById('sidebar-playlists-list');

  // Search Filter Elements
  const filterPills = document.querySelectorAll('.filter-pill');

  // Player Footer UI Elements
  const jamendoPlayBtn = document.getElementById('jamendo-play-btn');
  const jamendoShuffleBtn = document.getElementById('jamendo-shuffle-btn');
  const jamendoPrevBtn = document.getElementById('jamendo-prev-btn');
  const jamendoNextBtn = document.getElementById('jamendo-next-btn');
  const jamendoRepeatBtn = document.getElementById('jamendo-repeat-btn');
  const jamendoPlayerTitle = document.getElementById('jamendo-player-title');
  const jamendoPlayerAuthor = document.getElementById('jamendo-player-author');
  const jamendoPlayerThumbnail = document.getElementById('jamendo-player-thumbnail');
  const jamendoProgressBar = document.getElementById('jamendo-progress-bar');
  const jamendoProgress = document.getElementById('jamendo-progress');
  const jamendoCurrentTime = document.getElementById('jamendo-current-time');
  const jamendoDuration = document.getElementById('jamendo-duration');
  const jamendoVisualizer = document.getElementById('jamendo-visualizer');
  const jamendoVolumeBar = document.getElementById('jamendo-volume-bar');
  const jamendoVolumeLevel = document.getElementById('jamendo-volume-level');
  const jamendoVolumeIcon = document.getElementById('jamendo-volume-icon');

  // Player Engine Elements
  const nativeAudio = document.getElementById('music-audio-player');

  // Controller State Variables
  let currentSource = 'youtube'; // Default source is Mainstream (YouTube)
  let currentPlayingTrack = null;
  let progressInterval = null;
  let searchTimeout = null;
  let isShuffle = false;
  let isRepeat = false;
  let currentPlaylistTracks = [];
  let activeSearchFilter = 'tracks'; // 'tracks', 'artists', 'playlists'

  // 1. Initialize Player defaults
  if (nativeAudio) {
    nativeAudio.volume = 0.8; // Default 80% volume
    if (jamendoVolumeLevel) jamendoVolumeLevel.style.width = '80%';
    console.log("[Music Player] Default volume initialized to 80%.");
  }

  // 2. Toggle Sidebar Panel Drawer (Centered Popout Modal)
  if (jamendoBtn) {
    jamendoBtn.addEventListener('click', (e) => {
      e.preventDefault();
      console.log("[Music Player] Centered popout panel opened.");
      jamendoPanel.classList.add('show');
      if (jamendoPanelBackdrop) jamendoPanelBackdrop.classList.add('show');
      const dropdown = document.getElementById('toolbar-dropdown');
      if (dropdown) dropdown.classList.remove('show');
    });
  }

  if (jamendoPanelClose) {
    jamendoPanelClose.addEventListener('click', () => {
      jamendoPanel.classList.remove('show');
      if (jamendoPanelBackdrop) jamendoPanelBackdrop.classList.remove('show');
    });
  }



  if (jamendoPanelBackdrop) {
    jamendoPanelBackdrop.addEventListener('click', () => {
      jamendoPanel.classList.remove('show');
      jamendoPanelBackdrop.classList.remove('show');
      console.log("[Music Player] Panel closed via backdrop click.");
    });
  }



  // 4. Bind HTML5 Audio Player Events
  if (nativeAudio) {
    nativeAudio.addEventListener('play', () => {
      if (jamendoPlayBtn) jamendoPlayBtn.innerHTML = '<i class="fas fa-pause"></i>';
      if (jamendoVisualizer) jamendoVisualizer.classList.add('active');
      startProgressPolling();
    });

    nativeAudio.addEventListener('pause', () => {
      if (jamendoPlayBtn) jamendoPlayBtn.innerHTML = '<i class="fas fa-play"></i>';
      if (jamendoVisualizer) jamendoVisualizer.classList.remove('active');
      stopProgressPolling();
    });

    nativeAudio.addEventListener('ended', () => {
      if (jamendoPlayBtn) jamendoPlayBtn.innerHTML = '<i class="fas fa-play"></i>';
      if (jamendoVisualizer) jamendoVisualizer.classList.remove('active');
      stopProgressPolling();
      if (jamendoProgress) jamendoProgress.style.width = '0%';
      if (jamendoCurrentTime) jamendoCurrentTime.textContent = '0:00';

      console.log("[Music Player] Audio track ended.");
      if (isRepeat) {
        nativeAudio.currentTime = 0;
        nativeAudio.play();
        console.log("[Music Player] Repeating current track.");
      } else {
        playNextTrack(); // Automatically play next track!
      }
    });

    nativeAudio.addEventListener('error', (e) => {
      console.error("[Music Player] Native Audio Stream playback error:", e);
      if (jamendoVisualizer) jamendoVisualizer.classList.remove('active');
      stopProgressPolling();
      showToast("Audio stream failed to buffer. Please try another track.", "error");
    });
  }

  // 5. Playback Progress Scrubber Polling
  function startProgressPolling() {
    stopProgressPolling(); // Clear existing
    progressInterval = setInterval(() => {
      if (nativeAudio && !isNaN(nativeAudio.duration)) {
        const current = nativeAudio.currentTime;
        const duration = nativeAudio.duration;
        
        if (duration > 0) {
          const pct = (current / duration) * 100;
          if (jamendoProgress) jamendoProgress.style.width = `${pct}%`;
          if (jamendoCurrentTime) jamendoCurrentTime.textContent = formatTime(current);
          if (jamendoDuration) jamendoDuration.textContent = formatTime(duration);
        }
      }
    }, 500);
  }

  function stopProgressPolling() {
    if (progressInterval) {
      clearInterval(progressInterval);
      progressInterval = null;
    }
  }

  // Helper to format seconds to M:SS
  function formatTime(seconds) {
    if (isNaN(seconds) || seconds === undefined) return '0:00';
    const minutes = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${minutes}:${secs < 10 ? '0' : ''}${secs}`;
  }

  // 6. Time Seeking Scrub
  if (jamendoProgressBar) {
    jamendoProgressBar.addEventListener('click', (e) => {
      if (nativeAudio && !isNaN(nativeAudio.duration)) {
        const rect = jamendoProgressBar.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const width = rect.width;
        const pct = clickX / width;
        const duration = nativeAudio.duration;
        
        if (duration > 0) {
          const seekTime = pct * duration;
          nativeAudio.currentTime = seekTime;
          if (jamendoProgress) jamendoProgress.style.width = `${pct * 100}%`;
          if (jamendoCurrentTime) jamendoCurrentTime.textContent = formatTime(seekTime);
          console.log("[Music Player] Seek requested to:", formatTime(seekTime));
        }
      }
    });
  }

  // 7. Volume Level adjustment
  if (jamendoVolumeBar) {
    jamendoVolumeBar.addEventListener('click', (e) => {
      if (nativeAudio) {
        const rect = jamendoVolumeBar.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const width = rect.width;
        const pct = Math.max(0, Math.min(1, clickX / width));
        const volume = Math.round(pct * 100);
        
        nativeAudio.volume = pct;
        if (jamendoVolumeLevel) jamendoVolumeLevel.style.width = `${pct * 100}%`;
        
        // Update Icons based on levels
        if (volume === 0) {
          jamendoVolumeIcon.className = 'fas fa-volume-mute';
        } else if (volume < 40) {
          jamendoVolumeIcon.className = 'fas fa-volume-down';
        } else {
          jamendoVolumeIcon.className = 'fas fa-volume-up';
        }
        console.log("[Music Player] Volume adjusted to:", volume);
      }
    });
  }

  // 8. Circular Play / Pause toggle click
  if (jamendoPlayBtn) {
    jamendoPlayBtn.addEventListener('click', () => {
      if (!currentPlayingTrack || !nativeAudio) {
        showToast("Please search and select a song first!", "info");
        return;
      }
      
      if (nativeAudio.paused) {
        nativeAudio.play();
      } else {
        nativeAudio.pause();
      }
    });
  }

  // 8.1 Advanced playback controls (Shuffle, Repeat, Next, Prev)
  if (jamendoShuffleBtn) {
    jamendoShuffleBtn.addEventListener('click', () => {
      isShuffle = !isShuffle;
      jamendoShuffleBtn.classList.toggle('active', isShuffle);
      console.log("[Music Player] Shuffle toggled:", isShuffle);
    });
  }

  if (jamendoRepeatBtn) {
    jamendoRepeatBtn.addEventListener('click', () => {
      isRepeat = !isRepeat;
      jamendoRepeatBtn.classList.toggle('active', isRepeat);
      console.log("[Music Player] Repeat toggled:", isRepeat);
    });
  }

  if (jamendoNextBtn) {
    jamendoNextBtn.addEventListener('click', () => {
      playNextTrack();
    });
  }

  if (jamendoPrevBtn) {
    jamendoPrevBtn.addEventListener('click', () => {
      playPrevTrack();
    });
  }

  // Helper to play next track
  function playNextTrack() {
    if (currentPlaylistTracks.length === 0 || !currentPlayingTrack) return;
    
    let currentIndex = currentPlaylistTracks.findIndex(t => t.id === currentPlayingTrack.id);
    if (currentIndex === -1) return;
    
    let nextIndex;
    if (isShuffle) {
      nextIndex = Math.floor(Math.random() * currentPlaylistTracks.length);
    } else {
      nextIndex = currentIndex + 1;
      if (nextIndex >= currentPlaylistTracks.length) {
        nextIndex = isRepeat ? 0 : currentPlaylistTracks.length - 1; // loop if repeat is on, else stay at last
      }
    }
    
    const nextTrack = currentPlaylistTracks[nextIndex];
    if (nextTrack) {
      const row = document.querySelector(`.jamendo-track-row[data-video-id="${nextTrack.id}"]`);
      playTrack(nextTrack, row);
    }
  }

  // Helper to play previous track
  function playPrevTrack() {
    if (currentPlaylistTracks.length === 0 || !currentPlayingTrack) return;
    
    let currentIndex = currentPlaylistTracks.findIndex(t => t.id === currentPlayingTrack.id);
    if (currentIndex === -1) return;
    
    let prevIndex = currentIndex - 1;
    if (prevIndex < 0) {
      prevIndex = isRepeat ? currentPlaylistTracks.length - 1 : 0;
    }
    
    const prevTrack = currentPlaylistTracks[prevIndex];
    if (prevTrack) {
      const row = document.querySelector(`.jamendo-track-row[data-video-id="${prevTrack.id}"]`);
      playTrack(prevTrack, row);
    }
  }

  // 9. Search Input Scraper triggering
  if (jamendoSearchInput) {
    jamendoSearchInput.addEventListener('input', (e) => {
      const query = e.target.value.trim();
      
      if (query.length > 0) {
        jamendoSearchClear.style.display = 'flex';
      } else {
        jamendoSearchClear.style.display = 'none';
        clearSearchResults();
        return;
      }

      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => {
        performSearch(query);
      }, 300);
    });

    jamendoSearchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        clearTimeout(searchTimeout);
        const query = jamendoSearchInput.value.trim();
        if (query) performSearch(query);
      }
    });
  }

  if (jamendoSearchClear) {
    jamendoSearchClear.addEventListener('click', () => {
      jamendoSearchInput.value = '';
      jamendoSearchClear.style.display = 'none';
      clearSearchResults();
    });
  }

  function clearSearchResults() {
    jamendoResultsList.innerHTML = `
      <div class="jamendo-empty-state">
        <i class="fab fa-youtube" style="font-size: 48px; color: var(--mint); opacity: 0.15;"></i>
        <p>Search over millions of mainstream tracks restriction-free!</p>
      </div>
    `;
  }

  // 10. Fetch search results from Flask Backend
  async function performSearch(query) {
    if (!query) return;

    if (jamendoStatusMsg) {
      jamendoStatusMsg.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Searching Mainstream Library...`;
      jamendoStatusMsg.style.display = 'block';
    }

    // Advanced search option query suffix engineering
    let processedQuery = query;
    if (activeSearchFilter === 'artists') {
      processedQuery = `${query} songs`;
    } else if (activeSearchFilter === 'playlists') {
      processedQuery = `${query} playlist full album`;
    }

    console.log("[Music Player] Searching mainstream secure backend for:", processedQuery);

    const apiEndpoint = '/api/youtube/search';

    try {
      const response = await fetch(`${apiEndpoint}?q=${encodeURIComponent(processedQuery)}`);
      const results = await response.json();

      if (jamendoStatusMsg) jamendoStatusMsg.style.display = 'none';
      console.log("[Music Player] parsed:", results.length, "items");
      renderSearchResults(results);
    } catch (err) {
      console.error("[Music Player] Search request error:", err);
      if (jamendoStatusMsg) jamendoStatusMsg.style.display = 'none';
      showToast("Failed to fetch search results.", "error");
    }
  }

  function renderSearchResults(results) {
    currentPlaylistTracks = results || [];
    if (!results || results.length === 0) {
      jamendoResultsList.innerHTML = `
        <div class="jamendo-empty-state">
          <i class="fas fa-search-minus" style="font-size: 32px; color: var(--muted); margin-bottom: 12px;"></i>
          <p>No results found. Try another search terms!</p>
        </div>
      `;
      return;
    }

    jamendoResultsList.innerHTML = '';
    results.forEach(track => {
      const row = document.createElement('div');
      row.className = 'jamendo-track-row animate-fade-in';
      row.dataset.videoId = track.id;

      row.innerHTML = `
        <img class="track-thumb" src="${track.thumbnail || 'data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 24 24\' width=\'40\' height=\'40\'%3E%3Crect width=\'100%25\' height=\'100%25\' fill=\'%231f2c3d\'/%3E%3C/svg%3E'}" alt="Thumb" loading="lazy">
        <div class="track-metadata">
          <div class="track-title" title="${track.title}">${track.title}</div>
          <div class="track-author">${track.author}</div>
        </div>
        <div class="track-row-actions" style="display: flex; align-items: center; gap: 12px; margin-left: auto;">
          <div class="track-duration">${track.duration}</div>
          <button class="add-to-pl-trigger" title="Add to Playlist" style="background: none; border: none; color: #888888; cursor: pointer; padding: 4px; display: flex; align-items: center; justify-content: center; transition: all 0.2s ease;">
            <i class="fas fa-plus" style="font-size: 11px;"></i>
          </button>
        </div>
      `;

      row.addEventListener('click', () => {
        playTrack(track, row);
      });

      const addBtn = row.querySelector('.add-to-pl-trigger');
      addBtn.addEventListener('click', (e) => {
        showAddToPlaylistMenu(track, e, addBtn);
      });

      jamendoResultsList.appendChild(row);
    });
  }

  // 11. Play Selected Track (Dual-Source Coordination)
  async function playTrack(track, clickedRow) {
    console.log("[Music Player] Play requested for track. ID:", track.id, "Title:", track.title);

    if (!nativeAudio) return;

    // Highlight row
    document.querySelectorAll('.jamendo-track-row').forEach(r => r.classList.remove('playing-row'));
    if (clickedRow) clickedRow.classList.add('playing-row');

    // Update Footer Player interface metadata
    if (jamendoPlayerTitle) jamendoPlayerTitle.textContent = track.title;
    if (jamendoPlayerAuthor) jamendoPlayerAuthor.textContent = track.author;
    if (jamendoPlayerThumbnail) jamendoPlayerThumbnail.src = track.thumbnail || 'data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 24 24\' width=\'40\' height=\'40\'%3E%3Crect width=\'100%25\' height=\'100%25\' fill=\'%231f2c3d\'/%3E%3C/svg%3E';
    if (jamendoDuration) jamendoDuration.textContent = track.duration;

    // Trigger metadata slide animations
    jamendoPlayerTitle.classList.remove('animate-fade-in');
    jamendoPlayerAuthor.classList.remove('animate-fade-in');
    jamendoPlayerThumbnail.classList.remove('animate-scale-in');
    void jamendoPlayerTitle.offsetWidth; // Trigger DOM reflow
    jamendoPlayerTitle.classList.add('animate-fade-in');
    jamendoPlayerAuthor.classList.add('animate-fade-in');
    jamendoPlayerThumbnail.classList.add('animate-scale-in');

    // Update large central dashboard banner elements if they exist
    const dbCover = document.getElementById('dashboard-large-cover');
    const dbTitle = document.getElementById('dashboard-banner-title');
    const dbAuthor = document.getElementById('dashboard-banner-author');
    
    if (dbCover) {
      dbCover.src = track.thumbnail || 'data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 24 24\' width=\'200\' height=\'200\'%3E%3Crect width=\'100%25\' height=\'100%25\' fill=\'%231f2c3d\'/%3E%3Cpath d=\'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 14.5v-9l6 4.5-6 4.5z\' fill=\'%2337e6b5\'/%3E%3C/svg%3E';
      dbCover.classList.remove('animate-scale-in');
      void dbCover.offsetWidth; // Trigger reflow
      dbCover.classList.add('animate-scale-in');
    }
    
    if (dbTitle) {
      dbTitle.textContent = track.title;
      dbTitle.classList.remove('animate-fade-in');
      void dbTitle.offsetWidth; // Trigger reflow
      dbTitle.classList.add('animate-fade-in');
    }
    
    if (dbAuthor) {
      dbAuthor.textContent = track.author;
      dbAuthor.classList.remove('animate-fade-in');
      void dbAuthor.offsetWidth; // Trigger reflow
      dbAuthor.classList.add('animate-fade-in');
    }

    currentPlayingTrack = track;

    // YouTube mainstream tracks require server-side signature/stream URL resolution
    if (jamendoStatusMsg) {
      jamendoStatusMsg.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Resolving direct audio stream... This may take a few seconds.`;
      jamendoStatusMsg.style.display = 'block';
    }
    
    const playIcon = jamendoPlayBtn.innerHTML;
    if (jamendoPlayBtn) jamendoPlayBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

    try {
      const response = await fetch(`/api/youtube/stream?video_id=${track.id}`);
      const data = await response.json();

      if (jamendoStatusMsg) jamendoStatusMsg.style.display = 'none';
      
      if (data.url) {
        nativeAudio.src = data.url;
        nativeAudio.play();
        console.log("[Music Player] Mainstream audio stream loaded successfully.");
      } else {
        console.error("[Music Player] Failed to resolve stream link:", data.error);
        if (jamendoPlayBtn) jamendoPlayBtn.innerHTML = playIcon;
        showToast("Failed to resolve stream link. Please try another song.", "error");
      }
    } catch (err) {
      console.error("[Music Player] YouTube stream resolution failed:", err);
      if (jamendoStatusMsg) jamendoStatusMsg.style.display = 'none';
      if (jamendoPlayBtn) jamendoPlayBtn.innerHTML = playIcon;
      showToast("Server error during stream resolution.", "error");
    }
  }

  // --- Spotify-like Sidebar Navigations & Search Filters ---

  const curatedPlaylists = [
    { name: "Lofi Coding Session", query: "Lofi Hip Hop chill study beats" },
    { name: "Retro Synthwave", query: "80s Retro Synthwave instrumental" },
    { name: "Top Hit Songs", query: "Billboard hot 100 hit songs" },
    { name: "Peaceful Acoustic", query: "Acoustic pop guitar covers" }
  ];

  const libraryTracks = [
    { id: "60ItHLz5WEA", title: "Faded", author: "Alan Walker", duration: "3:32", thumbnail: "https://i.ytimg.com/vi/60ItHLz5WEA/hqdefault.jpg" },
    { id: "7wtfhZwyrcc", title: "Believer", author: "Imagine Dragons", duration: "3:36", thumbnail: "https://i.ytimg.com/vi/7wtfhZwyrcc/hqdefault.jpg" },
    { id: "W8a4sUabCUo", title: "Dandelions", author: "Ruth B.", duration: "3:53", thumbnail: "https://i.ytimg.com/vi/W8a4sUabCUo/hqdefault.jpg" },
    { id: "4NRXx6U8ABQ", title: "Blinding Lights", author: "The Weeknd", duration: "3:21", thumbnail: "https://i.ytimg.com/vi/4NRXx6U8ABQ/hqdefault.jpg" }
  ];

  // Custom Playlists Persistence Utilities
  function getCustomPlaylists() {
    const data = localStorage.getItem('mint_custom_playlists');
    return data ? JSON.parse(data) : [];
  }

  function saveCustomPlaylists(playlists) {
    localStorage.setItem('mint_custom_playlists', JSON.stringify(playlists));
  }

  function setActiveSidebarNav(navId) {
    document.querySelectorAll('.sidebar-nav-item').forEach(item => {
      if (item.id === navId) {
        item.classList.add('active');
      } else {
        item.classList.remove('active');
      }
    });
    // Remove active state from sidebar playlist items
    document.querySelectorAll('.sidebar-playlist-item').forEach(el => el.classList.remove('active'));
  }

  function initSidebarPlaylists() {
    if (!sidebarPlaylistsList) return;
    sidebarPlaylistsList.innerHTML = '';

    // 1. Render Curated Playlists
    curatedPlaylists.forEach((pl, idx) => {
      const btn = document.createElement('button');
      btn.className = 'sidebar-playlist-item';
      btn.innerHTML = `<i class="far fa-compass" style="margin-right: 8px; color: #888888;"></i> <span>${pl.name}</span>`;
      btn.addEventListener('click', () => {
        document.querySelectorAll('.sidebar-playlist-item').forEach(el => el.classList.remove('active'));
        document.querySelectorAll('.sidebar-nav-item').forEach(item => item.classList.remove('active'));
        btn.classList.add('active');

        if (jamendoSearchInput) {
          jamendoSearchInput.value = pl.name;
          if (jamendoSearchClear) jamendoSearchClear.style.display = 'flex';
        }
        
        setActiveFilter('playlists');
        performSearch(pl.query);
      });
      sidebarPlaylistsList.appendChild(btn);
    });

    // 2. Render Custom Playlists
    const customPlaylists = getCustomPlaylists();
    customPlaylists.forEach(pl => {
      const itemContainer = document.createElement('div');
      itemContainer.className = 'sidebar-playlist-item-container';
      itemContainer.style.display = 'flex';
      itemContainer.style.alignItems = 'center';
      itemContainer.style.justifyContent = 'space-between';
      itemContainer.style.width = '100%';

      const btn = document.createElement('button');
      btn.className = 'sidebar-playlist-item';
      btn.style.flex = '1';
      btn.innerHTML = `<i class="fas fa-list-ul" style="margin-right: 8px; color: var(--mint);"></i> <span style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 105px; display: inline-block;">${pl.name}</span>`;
      btn.addEventListener('click', () => {
        document.querySelectorAll('.sidebar-playlist-item').forEach(el => el.classList.remove('active'));
        document.querySelectorAll('.sidebar-nav-item').forEach(item => item.classList.remove('active'));
        btn.classList.add('active');

        renderCustomPlaylistView(pl);
      });

      // Custom Context Menu trigger on right click
      btn.addEventListener('contextmenu', (e) => {
        showContextMenu(pl, e);
      });

      const delBtn = document.createElement('button');
      delBtn.className = 'delete-playlist-btn';
      delBtn.title = "Delete Playlist";
      delBtn.innerHTML = `<i class="far fa-trash-alt"></i>`;
      delBtn.style.background = 'none';
      delBtn.style.border = 'none';
      delBtn.style.color = '#555555';
      delBtn.style.cursor = 'pointer';
      delBtn.style.padding = '4px 8px';
      delBtn.style.fontSize = '11px';
      delBtn.style.transition = 'all 0.2s ease';
      
      delBtn.addEventListener('mouseenter', () => delBtn.style.color = 'var(--error)');
      delBtn.addEventListener('mouseleave', () => delBtn.style.color = '#555555');
      delBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        showMintConfirm("Delete Playlist", `Are you sure you want to delete the playlist "${pl.name}"? This action cannot be undone.`, (confirmed) => {
          if (confirmed) {
            const playlists = getCustomPlaylists();
            const updated = playlists.filter(p => p.id !== pl.id);
            saveCustomPlaylists(updated);
            initSidebarPlaylists();
            
            // Re-render home landing page if deleted playlist was selected
            const activeSidebarItem = document.querySelector('.sidebar-playlist-item.active');
            if (activeSidebarItem && activeSidebarItem.textContent.trim() === pl.name) {
              if (navItemHome) navItemHome.click();
            } else if (navItemPlaylists && document.querySelector('.sidebar-nav-item.active') === navItemPlaylists) {
              navItemPlaylists.click();
            }

            showToast(`Deleted playlist "${pl.name}"`, "info");
          }
        });
      });

      itemContainer.appendChild(btn);
      itemContainer.appendChild(delBtn);
      sidebarPlaylistsList.appendChild(itemContainer);
    });

    // Wire empty space context menu trigger on empty list click
    sidebarPlaylistsList.addEventListener('contextmenu', (e) => {
      if (e.target === sidebarPlaylistsList) {
        showEmptySidebarContextMenu(e);
      }
    });
  }

  function renderCustomPlaylistView(pl) {
    currentPlaylistTracks = pl.tracks || [];
    
    jamendoResultsList.innerHTML = `
      <div class="playlist-view-header" style="padding: 12px 4px; border-bottom: 1px solid rgba(255,255,255,0.05); margin-bottom: 16px; display: flex; flex-direction: column; gap: 4px;">
        <div style="display: flex; align-items: center; gap: 8px;">
          <i class="fas fa-music" style="color: var(--mint); font-size: 14px;"></i>
          <span style="font-size: 14px; font-weight: 700; color: #ffffff;">${pl.name}</span>
          <span style="font-size: 11px; color: #888888; margin-left: 6px;">(${pl.tracks.length} songs)</span>
        </div>
        <p style="margin: 0; font-size: 11px; color: #666666;">Your personal custom playlist compilation.</p>
      </div>
    `;

    if (pl.tracks.length === 0) {
      jamendoResultsList.innerHTML += `
        <div class="jamendo-empty-state" style="padding: 40px 0;">
          <i class="fas fa-folder-open" style="font-size: 32px; color: var(--muted); margin-bottom: 12px;"></i>
          <p style="font-size: 12px; color: #888888;">This playlist is empty.</p>
          <p style="font-size: 11px; color: #555555; margin-top: 4px;">Search for songs, click the "+" icon to populate it!</p>
        </div>
      `;
      return;
    }

    pl.tracks.forEach((track, index) => {
      const row = document.createElement('div');
      row.className = 'jamendo-track-row animate-fade-in';
      row.dataset.videoId = track.id;
      if (currentPlayingTrack && currentPlayingTrack.id === track.id) {
        row.classList.add('playing-row');
      }

      row.innerHTML = `
        <img class="track-thumb" src="${track.thumbnail || 'data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 24 24\' width=\'40\' height=\'40\'%3E%3Crect width=\'100%25\' height=\'100%25\' fill=\'%231f2c3d\'/%3E%3C/svg%3E'}" alt="Thumb" loading="lazy">
        <div class="track-metadata">
          <div class="track-title" title="${track.title}">${track.title}</div>
          <div class="track-author">${track.author}</div>
        </div>
        <div class="track-row-actions" style="display: flex; align-items: center; gap: 12px; margin-left: auto;">
          <div class="track-duration">${track.duration}</div>
          <button class="remove-from-pl-btn" title="Remove from Playlist" style="background: none; border: none; color: #888888; cursor: pointer; padding: 4px; display: flex; align-items: center; justify-content: center; transition: all 0.2s ease;">
            <i class="fas fa-times" style="font-size: 11px;"></i>
          </button>
        </div>
      `;

      row.addEventListener('click', () => {
        playTrack(track, row);
      });

      const removeBtn = row.querySelector('.remove-from-pl-btn');
      removeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        showMintConfirm("Remove Song", `Remove "${track.title}" from your playlist "${pl.name}"?`, (confirmed) => {
          if (confirmed) {
            const playlists = getCustomPlaylists();
            const activePl = playlists.find(p => p.id === pl.id);
            if (activePl) {
              activePl.tracks = activePl.tracks.filter(t => t.id !== track.id);
              saveCustomPlaylists(playlists);
              renderCustomPlaylistView(activePl);
              initSidebarPlaylists();
              showToast(`Removed song from "${pl.name}"`, "info");
            }
          }
        });
      });

      jamendoResultsList.appendChild(row);
    });
  }

  // Create a global absolute-positioned "Add to Playlist" popover menu
  let addToPlaylistMenu = document.getElementById('add-to-playlist-menu');
  if (!addToPlaylistMenu) {
    addToPlaylistMenu = document.createElement('div');
    addToPlaylistMenu.id = 'add-to-playlist-menu';
    addToPlaylistMenu.className = 'add-to-playlist-menu custom-scrollbar';
    document.body.appendChild(addToPlaylistMenu);
  }

  function showAddToPlaylistMenu(track, event, triggerBtn) {
    event.stopPropagation();
    
    // Close any open menu
    addToPlaylistMenu.style.display = 'none';

    // Get current custom playlists
    const customPlaylists = getCustomPlaylists();
    if (customPlaylists.length === 0) {
      addToPlaylistMenu.innerHTML = `
        <div style="padding: 8px 12px; color: #888888; font-size: 11px; text-align: center; line-height: 1.4;">
          No custom playlists.<br>Create one in the sidebar!
        </div>
      `;
    } else {
      addToPlaylistMenu.innerHTML = '';
      customPlaylists.forEach(pl => {
        const item = document.createElement('button');
        item.className = 'add-to-playlist-menu-item';
        item.innerHTML = `<i class="fas fa-list" style="font-size: 10px; color: #888888;"></i> <span>${pl.name}</span>`;
        item.addEventListener('click', (e) => {
          e.stopPropagation();
          addTrackToPlaylist(track, pl.id);
          addToPlaylistMenu.style.display = 'none';
        });
        addToPlaylistMenu.appendChild(item);
      });
    }

    // Position the dropdown near the clicked button (adjusting for body CSS zoom level)
    const zoom = getZoomFactor();
    const rect = triggerBtn.getBoundingClientRect();
    addToPlaylistMenu.style.top = `${rect.bottom / zoom + 4}px`;
    // Align right side of menu with right side of button
    addToPlaylistMenu.style.left = `${(rect.right - 160) / zoom}px`;
    addToPlaylistMenu.style.display = 'block';

    // Click outside to close
    const closeMenu = (e) => {
      if (!addToPlaylistMenu.contains(e.target) && e.target !== triggerBtn) {
        addToPlaylistMenu.style.display = 'none';
        document.removeEventListener('click', closeMenu);
      }
    };
    setTimeout(() => {
      document.addEventListener('click', closeMenu);
    }, 10);
  }

  function addTrackToPlaylist(track, playlistId) {
    const playlists = getCustomPlaylists();
    const pl = playlists.find(p => p.id === playlistId);
    if (pl) {
      // Check if track already exists in playlist
      if (pl.tracks.some(t => t.id === track.id)) {
        showToast(`"${track.title}" is already in "${pl.name}"!`, "info");
        return;
      }
      pl.tracks.push(track);
      saveCustomPlaylists(playlists);
      showToast(`Added "${track.title}" to "${pl.name}"!`, "success");
    }
  }

  // Bind Sidebar Nav Click Events
  if (navItemHome) {
    navItemHome.addEventListener('click', () => {
      setActiveSidebarNav('nav-item-home');
      if (jamendoSearchInput) {
        jamendoSearchInput.value = '';
        if (jamendoSearchClear) jamendoSearchClear.style.display = 'none';
      }
      clearSearchResults();
    });
  }

  if (navItemLibrary) {
    navItemLibrary.addEventListener('click', () => {
      setActiveSidebarNav('nav-item-library');
      currentPlaylistTracks = libraryTracks;
      jamendoResultsList.innerHTML = `
        <div class="library-header" style="padding: 12px 4px; border-bottom: 1px solid rgba(255,255,255,0.05); margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
          <i class="fas fa-heart" style="color: var(--mint); font-size: 14px;"></i>
          <span style="font-size: 13px; font-weight: 700; color: #ffffff;">Your Curated Library Queue</span>
        </div>
      `;
      libraryTracks.forEach(track => {
        const row = document.createElement('div');
        row.className = 'jamendo-track-row animate-fade-in';
        row.dataset.videoId = track.id;
        if (currentPlayingTrack && currentPlayingTrack.id === track.id) {
          row.classList.add('playing-row');
        }

        row.innerHTML = `
          <img class="track-thumb" src="${track.thumbnail}" alt="Thumb" loading="lazy">
          <div class="track-metadata">
            <div class="track-title" title="${track.title}">${track.title}</div>
            <div class="track-author">${track.author}</div>
          </div>
          <div class="track-row-actions" style="display: flex; align-items: center; gap: 12px; margin-left: auto;">
            <div class="track-duration">${track.duration}</div>
            <button class="add-to-pl-trigger" title="Add to Playlist" style="background: none; border: none; color: #888888; cursor: pointer; padding: 4px; display: flex; align-items: center; justify-content: center; transition: all 0.2s ease;">
              <i class="fas fa-plus" style="font-size: 11px;"></i>
            </button>
          </div>
        `;

        row.addEventListener('click', () => {
          playTrack(track, row);
        });

        const addBtn = row.querySelector('.add-to-pl-trigger');
        addBtn.addEventListener('click', (e) => {
          showAddToPlaylistMenu(track, e, addBtn);
        });

        jamendoResultsList.appendChild(row);
      });
    });
  }

  if (navItemPlaylists) {
    navItemPlaylists.addEventListener('click', () => {
      setActiveSidebarNav('nav-item-playlists');
      
      const customPlaylists = getCustomPlaylists();
      
      jamendoResultsList.innerHTML = `
        <div class="playlists-header" style="padding: 12px 4px; border-bottom: 1px solid rgba(255,255,255,0.05); margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
          <i class="fas fa-list-ul" style="color: var(--mint); font-size: 14px;"></i>
          <span style="font-size: 13px; font-weight: 700; color: #ffffff;">Curated Compilations</span>
        </div>
        <div class="playlist-cards-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 12px; padding: 4px; margin-bottom: 24px;">
          ${curatedPlaylists.map((pl, idx) => `
            <div class="playlist-card curated animate-fade-in" data-index="${idx}" style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); border-radius: 8px; padding: 16px; cursor: pointer; transition: all 0.2s ease; display: flex; flex-direction: column; gap: 8px;">
               <div style="width: 36px; height: 36px; border-radius: 6px; background: rgba(55,230,181,0.08); display: flex; align-items: center; justify-content: center; color: var(--mint);">
                 <i class="far fa-compass" style="font-size: 14px;"></i>
               </div>
               <h4 style="margin: 0; font-size: 12px; font-weight: 600; color: #ffffff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${pl.name}</h4>
               <p style="margin: 0; font-size: 10px; color: #888888;">Tap to stream compilation</p>
            </div>
          `).join('')}
        </div>

        <div class="playlists-header" style="padding: 12px 4px; border-bottom: 1px solid rgba(255,255,255,0.05); margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
          <i class="fas fa-folder-open" style="color: var(--mint); font-size: 14px;"></i>
          <span style="font-size: 13px; font-weight: 700; color: #ffffff;">Your Custom Playlists</span>
        </div>
        <div class="playlist-cards-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 12px; padding: 4px;">
          ${customPlaylists.length === 0 ? `
            <div style="grid-column: 1 / -1; padding: 24px 0; text-align: center; color: #888888; font-size: 12px;">
              No custom playlists created. Create one in the sidebar!
            </div>
          ` : customPlaylists.map((pl) => `
            <div class="playlist-card custom-pl-card animate-fade-in" data-playlist-id="${pl.id}" style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); border-radius: 8px; padding: 16px; cursor: pointer; transition: all 0.2s ease; display: flex; flex-direction: column; gap: 8px;">
               <div style="width: 36px; height: 36px; border-radius: 6px; background: rgba(55,230,181,0.08); display: flex; align-items: center; justify-content: center; color: var(--mint);">
                 <i class="fas fa-list-ul" style="font-size: 14px;"></i>
               </div>
               <h4 style="margin: 0; font-size: 12px; font-weight: 600; color: #ffffff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${pl.name}</h4>
               <p style="margin: 0; font-size: 10px; color: #888888;">${pl.tracks.length} tracks</p>
            </div>
          `).join('')}
        </div>
      `;

      // Event listeners for curated cards
      document.querySelectorAll('.playlist-card.curated').forEach(card => {
        card.addEventListener('mouseenter', () => {
          card.style.background = 'rgba(255,255,255,0.06)';
          card.style.borderColor = 'rgba(55, 230, 181, 0.2)';
        });
        card.style.transition = 'all 0.2s ease';
        card.addEventListener('mouseleave', () => {
          card.style.background = 'rgba(255,255,255,0.02)';
          card.style.borderColor = 'rgba(255,255,255,0.05)';
        });
        card.addEventListener('click', () => {
          const idx = parseInt(card.dataset.index);
          const pl = curatedPlaylists[idx];
          
          if (jamendoSearchInput) {
            jamendoSearchInput.value = pl.name;
            if (jamendoSearchClear) jamendoSearchClear.style.display = 'flex';
          }
          setActiveFilter('playlists');
          performSearch(pl.query);
        });
      });

      // Event listeners for custom playlist cards
      document.querySelectorAll('.playlist-card.custom-pl-card').forEach(card => {
        card.addEventListener('mouseenter', () => {
          card.style.background = 'rgba(255,255,255,0.06)';
          card.style.borderColor = 'rgba(55, 230, 181, 0.2)';
        });
        card.style.transition = 'all 0.2s ease';
        card.addEventListener('mouseleave', () => {
          card.style.background = 'rgba(255,255,255,0.02)';
          card.style.borderColor = 'rgba(255,255,255,0.05)';
        });
        card.addEventListener('click', () => {
          const plId = card.dataset.playlistId;
          const playlists = getCustomPlaylists();
          const targetPl = playlists.find(p => p.id === plId);
          if (targetPl) {
            // Find sidebar button matching and highlight
            document.querySelectorAll('.sidebar-playlist-item').forEach(el => {
              if (el.textContent.trim() === targetPl.name) el.classList.add('active');
              else el.classList.remove('active');
            });
            renderCustomPlaylistView(targetPl);
          }
        });
        card.addEventListener('contextmenu', (e) => {
          e.preventDefault();
          const plId = card.dataset.playlistId;
          const playlists = getCustomPlaylists();
          const targetPl = playlists.find(p => p.id === plId);
          if (targetPl) {
            showContextMenu(targetPl, e);
          }
        });
      });
    });
  }

  // Add Custom Playlist button functionality
  const addPlaylistBtn = document.querySelector('.add-playlist-btn');
  if (addPlaylistBtn) {
    addPlaylistBtn.addEventListener('click', () => {
      showMintPrompt("Create Playlist", "", "Enter playlist name...", (playlistName) => {
        if (playlistName && playlistName.trim()) {
          const name = playlistName.trim();
          const playlists = getCustomPlaylists();
          
          // Check duplicates
          if (playlists.some(p => p.name.toLowerCase() === name.toLowerCase())) {
            showToast(`A playlist named "${name}" already exists!`, "info");
            return;
          }

          const newPl = {
            id: 'pl_' + Date.now(),
            name: name,
            tracks: []
          };
          playlists.push(newPl);
          saveCustomPlaylists(playlists);
          initSidebarPlaylists();
          showToast(`Playlist "${name}" created!`, "success");
        }
      });
    });
  }

  // Search Filter Pills click events
  function setActiveFilter(filterName) {
    activeSearchFilter = filterName;
    filterPills.forEach(pill => {
      if (pill.dataset.filter === filterName) {
        pill.classList.add('active');
      } else {
        pill.classList.remove('active');
      }
    });
  }

  if (filterPills) {
    filterPills.forEach(pill => {
      pill.addEventListener('click', () => {
        const filter = pill.dataset.filter;
        setActiveFilter(filter);
        
        // Auto trigger search if input is not empty
        const query = jamendoSearchInput.value.trim();
        if (query) {
          performSearch(query);
        }
      });
    });
  }

  // Initialize curated sidebar list items on load
  initSidebarPlaylists();

  // --- Right-Click Custom Action Context Menu ---

  let contextMenu = document.getElementById('custom-context-menu');
  if (!contextMenu) {
    contextMenu = document.createElement('div');
    contextMenu.id = 'custom-context-menu';
    contextMenu.className = 'custom-context-menu';
    document.body.appendChild(contextMenu);
  }

  // Custom Glassmorphic Prompt Dialog popup (replaces browser's native prompt)
  function showMintPrompt(title, defaultValue, placeholder, callback) {
    let customModal = document.getElementById('mint-custom-modal');
    if (!customModal) {
      customModal = document.createElement('div');
      customModal.id = 'mint-custom-modal';
      customModal.className = 'mint-custom-modal';
      document.body.appendChild(customModal);
    }
    
    customModal.innerHTML = `
      <div class="mint-custom-modal-content">
        <h3 class="mint-custom-modal-title">${title}</h3>
        <input type="text" class="mint-custom-modal-input" placeholder="${placeholder}" value="${defaultValue}">
        <div class="mint-custom-modal-actions">
          <button class="mint-custom-modal-btn mint-custom-modal-btn-cancel" id="mint-prompt-cancel">Cancel</button>
          <button class="mint-custom-modal-btn mint-custom-modal-btn-confirm" id="mint-prompt-confirm">Save</button>
        </div>
      </div>
    `;
    
    const input = customModal.querySelector('.mint-custom-modal-input');
    const cancelBtn = customModal.querySelector('#mint-prompt-cancel');
    const confirmBtn = customModal.querySelector('#mint-prompt-confirm');
    
    customModal.classList.add('show');
    input.focus();
    input.select();
    
    const handleConfirm = () => {
      const val = input.value.trim();
      customModal.classList.remove('show');
      callback(val);
    };
    
    const handleCancel = () => {
      customModal.classList.remove('show');
      callback(null);
    };
    
    confirmBtn.addEventListener('click', handleConfirm);
    cancelBtn.addEventListener('click', handleCancel);
    
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        handleConfirm();
      } else if (e.key === 'Escape') {
        handleCancel();
      }
    });
  }

  // Custom Glassmorphic Confirm Dialog popup (replaces browser's native confirm)
  function showMintConfirm(title, message, callback) {
    let customModal = document.getElementById('mint-custom-modal');
    if (!customModal) {
      customModal = document.createElement('div');
      customModal.id = 'mint-custom-modal';
      customModal.className = 'mint-custom-modal';
      document.body.appendChild(customModal);
    }
    
    customModal.innerHTML = `
      <div class="mint-custom-modal-content">
        <h3 class="mint-custom-modal-title">${title}</h3>
        <p class="mint-custom-modal-message" style="font-size: 12px; color: #aaaaaa; margin: 4px 0 12px 0; line-height: 1.5; text-align: left;">${message}</p>
        <div class="mint-custom-modal-actions">
          <button class="mint-custom-modal-btn mint-custom-modal-btn-cancel" id="mint-confirm-cancel">Cancel</button>
          <button class="mint-custom-modal-btn mint-custom-modal-btn-confirm" id="mint-confirm-ok">OK</button>
        </div>
      </div>
    `;
    
    const cancelBtn = customModal.querySelector('#mint-confirm-cancel');
    const okBtn = customModal.querySelector('#mint-confirm-ok');
    
    customModal.classList.add('show');
    okBtn.focus();
    
    const handleOk = () => {
      customModal.classList.remove('show');
      document.removeEventListener('keydown', handleKeyDown);
      callback(true);
    };
    
    const handleCancel = () => {
      customModal.classList.remove('show');
      document.removeEventListener('keydown', handleKeyDown);
      callback(false);
    };
    
    okBtn.addEventListener('click', handleOk);
    cancelBtn.addEventListener('click', handleCancel);
    
    const handleKeyDown = (e) => {
      if (customModal.classList.contains('show')) {
        if (e.key === 'Enter') {
          e.preventDefault();
          handleOk();
        } else if (e.key === 'Escape') {
          e.preventDefault();
          handleCancel();
        }
      }
    };
    
    document.addEventListener('keydown', handleKeyDown);
  }

  function downloadPlaylist(pl) {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(pl, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `${pl.name.replace(/\s+/g, '_')}_playlist.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
    showToast(`Exported "${pl.name}" successfully!`, "success");
  }

  function uploadPlaylist() {
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = '.json';
    fileInput.style.display = 'none';
    
    fileInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (!file) return;
      
      const reader = new FileReader();
      reader.onload = (event) => {
        try {
          const pl = JSON.parse(event.target.result);
          
          if (!pl.name || !Array.isArray(pl.tracks)) {
            showToast("Invalid playlist JSON format.", "error");
            return;
          }
          
          const playlists = getCustomPlaylists();
          pl.id = 'pl_' + Date.now();
          
          let name = pl.name;
          let counter = 1;
          while (playlists.some(p => p.name.toLowerCase() === name.toLowerCase())) {
            name = `${pl.name} (${counter++})`;
          }
          pl.name = name;
          
          playlists.push(pl);
          saveCustomPlaylists(playlists);
          initSidebarPlaylists();
          showToast(`Imported playlist "${pl.name}"!`, "success");
        } catch (err) {
          showToast("Failed to parse JSON file.", "error");
        }
      };
      reader.readAsText(file);
    });
    
    document.body.appendChild(fileInput);
    fileInput.click();
    fileInput.remove();
  }

  function addTracksToPlaylist(pl) {
    if (jamendoSearchInput) {
      jamendoSearchInput.value = '';
      jamendoSearchInput.placeholder = `Search tracks for "${pl.name}"...`;
      jamendoSearchInput.focus();
      setActiveFilter('tracks');
      showToast(`Search for songs and click "+" to add them to "${pl.name}"!`, "info");
    }
  }

  function renamePlaylist(pl) {
    showMintPrompt("Rename Playlist", pl.name, "Enter playlist name...", (newName) => {
      if (newName && newName.trim()) {
        const name = newName.trim();
        const playlists = getCustomPlaylists();
        
        // Exclude current playlist from duplicate check
        if (playlists.some(p => p.id !== pl.id && p.name.toLowerCase() === name.toLowerCase())) {
          showToast(`A playlist named "${name}" already exists!`, "info");
          return;
        }
        
        // Find and update
        const targetPl = playlists.find(p => p.id === pl.id);
        if (targetPl) {
          const oldName = targetPl.name;
          targetPl.name = name;
          saveCustomPlaylists(playlists);
          initSidebarPlaylists();
          
          // Re-render header if it's currently selected
          const activeSidebarItem = document.querySelector('.sidebar-playlist-item.active');
          if (activeSidebarItem && activeSidebarItem.textContent.trim() === oldName) {
            // Find updated item and activate
            document.querySelectorAll('.sidebar-playlist-item').forEach(el => {
              if (el.textContent.trim() === name) el.classList.add('active');
            });
            renderCustomPlaylistView(targetPl);
          }
          
          showToast(`Playlist renamed to "${name}"!`, "success");
        }
      }
    });
  }

  function showContextMenu(pl, event) {
    event.preventDefault();
    event.stopPropagation();
    
    contextMenu.style.display = 'none';
    if (addToPlaylistMenu) addToPlaylistMenu.style.display = 'none';
    
    contextMenu.innerHTML = `
      <button class="context-menu-item" id="ctx-add-tracks">
        <i class="fas fa-plus" style="color: var(--mint);"></i> Add Tracks
      </button>
      <button class="context-menu-item" id="ctx-rename">
        <i class="fas fa-edit" style="color: var(--mint);"></i> Rename Playlist
      </button>
      <button class="context-menu-item" id="ctx-create-ctx">
        <i class="fas fa-plus-circle" style="color: var(--mint);"></i> Create Playlist
      </button>
      <div class="context-menu-divider"></div>
      <button class="context-menu-item" id="ctx-download">
        <i class="fas fa-download"></i> Export (Download)
      </button>
      <button class="context-menu-item" id="ctx-upload">
        <i class="fas fa-upload"></i> Import (Upload)
      </button>
      <div class="context-menu-divider"></div>
      <button class="context-menu-item danger" id="ctx-delete">
        <i class="far fa-trash-alt"></i> Delete Playlist
      </button>
    `;
    
    contextMenu.querySelector('#ctx-add-tracks').addEventListener('click', () => {
      addTracksToPlaylist(pl);
      contextMenu.style.display = 'none';
    });
    
    contextMenu.querySelector('#ctx-rename').addEventListener('click', () => {
      renamePlaylist(pl);
      contextMenu.style.display = 'none';
    });

    contextMenu.querySelector('#ctx-create-ctx').addEventListener('click', () => {
      if (addPlaylistBtn) addPlaylistBtn.click();
      contextMenu.style.display = 'none';
    });
    
    contextMenu.querySelector('#ctx-download').addEventListener('click', () => {
      downloadPlaylist(pl);
      contextMenu.style.display = 'none';
    });
    
    contextMenu.querySelector('#ctx-upload').addEventListener('click', () => {
      uploadPlaylist();
      contextMenu.style.display = 'none';
    });
    
    contextMenu.querySelector('#ctx-delete').addEventListener('click', () => {
      contextMenu.style.display = 'none';
      showMintConfirm("Delete Playlist", `Are you sure you want to delete the playlist "${pl.name}"? This action cannot be undone.`, (confirmed) => {
        if (confirmed) {
          const playlists = getCustomPlaylists();
          const updated = playlists.filter(p => p.id !== pl.id);
          saveCustomPlaylists(updated);
          initSidebarPlaylists();
          
          // Re-render home landing page if deleted playlist was selected
          const activeSidebarItem = document.querySelector('.sidebar-playlist-item.active');
          if (activeSidebarItem && activeSidebarItem.textContent.trim() === pl.name) {
            if (navItemHome) navItemHome.click();
          } else if (navItemPlaylists && document.querySelector('.sidebar-nav-item.active') === navItemPlaylists) {
            navItemPlaylists.click();
          }

          showToast(`Deleted playlist "${pl.name}"`, "info");
        }
      });
    });
    
    // Position menu at cursor viewport coordinates (adjusting for body CSS zoom level)
    const zoom = getZoomFactor();
    contextMenu.style.top = `${event.clientY / zoom}px`;
    contextMenu.style.left = `${event.clientX / zoom}px`;
    contextMenu.style.display = 'block';
  }

  // Helper to retrieve the current CSS zoom level of the document body
  function getZoomFactor() {
    const zoomVal = window.getComputedStyle(document.body).zoom;
    return zoomVal ? parseFloat(zoomVal) : 0.675;
  }

  function showEmptySidebarContextMenu(event) {
    event.preventDefault();
    event.stopPropagation();
    
    contextMenu.style.display = 'none';
    if (addToPlaylistMenu) addToPlaylistMenu.style.display = 'none';
    
    contextMenu.innerHTML = `
      <button class="context-menu-item" id="ctx-create-pl">
        <i class="fas fa-plus" style="color: var(--mint);"></i> Create Playlist
      </button>
      <button class="context-menu-item" id="ctx-import-pl">
        <i class="fas fa-upload"></i> Import Playlist (JSON)
      </button>
    `;
    
    contextMenu.querySelector('#ctx-create-pl').addEventListener('click', () => {
      if (addPlaylistBtn) addPlaylistBtn.click();
      contextMenu.style.display = 'none';
    });
    
    contextMenu.querySelector('#ctx-import-pl').addEventListener('click', () => {
      uploadPlaylist();
      contextMenu.style.display = 'none';
    });
    
    // Position menu at cursor viewport coordinates (adjusting for body CSS zoom level)
    const zoom = getZoomFactor();
    contextMenu.style.top = `${event.clientY / zoom}px`;
    contextMenu.style.left = `${event.clientX / zoom}px`;
    contextMenu.style.display = 'block';
  }

  // Global dismiss listeners to prevent popups from sticking
  document.addEventListener('click', (e) => {
    if (contextMenu && !contextMenu.contains(e.target)) {
      contextMenu.style.display = 'none';
    }
    if (addToPlaylistMenu && !addToPlaylistMenu.contains(e.target) && !e.target.closest('.add-to-pl-trigger')) {
      addToPlaylistMenu.style.display = 'none';
    }
  });

  document.addEventListener('contextmenu', (e) => {
    // Dismiss existing menus on right-clicking elsewhere
    if (contextMenu && !contextMenu.contains(e.target)) {
      contextMenu.style.display = 'none';
    }
  });

  // Automatically dismiss active menus on window/document scrolls
  document.addEventListener('scroll', () => {
    if (contextMenu) contextMenu.style.display = 'none';
  }, { passive: true });

  // Dismiss dropdowns on tracks results container scroll (extremely premium local scrolling cleanup)
  const resultsScrollContainer = document.getElementById('jamendo-results-list');
  if (resultsScrollContainer) {
    resultsScrollContainer.addEventListener('scroll', () => {
      if (addToPlaylistMenu) addToPlaylistMenu.style.display = 'none';
      if (contextMenu) contextMenu.style.display = 'none';
    });
  }

  // Helper for displaying notifications
  function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast toast--show toast--${type}`;
    toast.style.position = 'fixed';
    toast.style.top = '20px';
    toast.style.right = '20px';
    toast.style.zIndex = '150000';
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => {
      toast.classList.remove('toast--show');
      setTimeout(() => toast.remove(), 400);
    }, 3000);
  }

  // Auto-load Curated Library Queue on page initialization to avoid blank/empty player states
  if (navItemLibrary) {
    navItemLibrary.click();
    console.log("[Music Player] Auto-initialized list view to Library Queue on page load.");
  }
});
