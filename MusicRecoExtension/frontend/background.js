/**
 * Background Service Worker
 * 
 * Handles extension icon clicks and manages SoundCloud tab activation.
 * 
 * Behavior:
 * - If current tab is SoundCloud: Toggle the sidebar
 * - If another SoundCloud tab exists: Switch to it and toggle sidebar
 * - Otherwise: Open a new SoundCloud tab
 */

chrome.action.onClicked.addListener((tab) => {
  // Check if current tab is SoundCloud
  if (tab.url && tab.url.includes("soundcloud.com")) {
      // Toggle sidebar on current SoundCloud tab
      chrome.tabs.sendMessage(tab.id, { action: 'toggleSidebar' });
  } else {
      // Look for any existing SoundCloud tab
      chrome.tabs.query({url: "*://*.soundcloud.com/*"}, (tabs) => {
          if (tabs && tabs.length > 0) {
              // Found a SoundCloud tab - switch to it
              const scTab = tabs[0];
              chrome.tabs.update(scTab.id, {active: true});
              chrome.windows.update(scTab.windowId, {focused: true});
              chrome.tabs.sendMessage(scTab.id, { action: 'toggleSidebar' });
          } else {
              // No SoundCloud tab found - open a new one
              chrome.tabs.create({ url: "https://soundcloud.com" });
          }
      });
  }
});
