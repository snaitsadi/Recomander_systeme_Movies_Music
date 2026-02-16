/**
 * Sidebar Popup Script
 * 
 * Handles the extension popup UI interactions.
 * Sends messages to content scripts to toggle the sidebar.
 */

document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('toggleBtn');
  if (btn) {
    btn.addEventListener('click', () => {
      // Send message to active tab's content script
      chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
        if (tabs[0]?.id) {
          chrome.tabs.sendMessage(tabs[0].id, {action: 'toggleSidebar'});
        }
      });
    });
  }
});
