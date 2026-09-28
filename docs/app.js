const ACCESS_KEY = atob('aW50ZXJuc0BtcWkyMDI1');
const LOCKED_THEMES = ['marquardt', 'mq'];
const THEME_NAMES = { marquardt: 'Classic', mq: 'MQ', aurora: 'Aurora', ember: 'Ember', glacier: 'Glacier', neon: 'Neon' };
let pendingTheme = null;
let selectedInstallTheme = null;

/* ── Theme cards (preview section) ── */
function selectTheme(card) {
  document.querySelectorAll('.theme-card').forEach(c => c.classList.remove('active'));
  card.classList.add('active');
}

function promptKey(card) {
  pendingTheme = card.dataset.theme;
  document.getElementById('key-input').value = '';
  document.getElementById('key-error').textContent = '';
  document.getElementById('key-modal').classList.add('open');
  setTimeout(() => document.getElementById('key-input').focus(), 100);
}

/* ── Installer picker ── */
function pickTheme(btn, theme) {
  applyPick(btn, theme);
}

function pickThemeLocked(btn, theme) {
  pendingTheme = theme;
  pendingBtn = btn;
  document.getElementById('key-input').value = '';
  document.getElementById('key-error').textContent = '';
  document.getElementById('key-modal').classList.add('open');
  setTimeout(() => document.getElementById('key-input').focus(), 100);
}

let pendingBtn = null;

function applyPick(btn, theme) {
  selectedInstallTheme = theme;
  document.querySelectorAll('.pick-btn').forEach(b => b.classList.remove('selected'));
  if (btn) btn.classList.add('selected');

  const name = THEME_NAMES[theme] || theme;
  const cmd = 'sudo ./install.sh --theme ' + theme;

  // Update step 3 command
  const cmdEl = document.getElementById('install-cmd');
  if (cmdEl) cmdEl.textContent = cmd;

  // Update terminal preview
  const term = document.getElementById('term-preview');
  if (term) {
    term.innerHTML =
      'Selected theme: <span style="color:var(--accent2)">' + name + '</span>\n\n' +
      '$ ' + cmd + '\n\n' +
      'Installing theme: <span style="color:var(--accent2)">' + theme + '</span>\n' +
      'Done! Reboot to see your theme. <span class="cursor">_</span>';
  }

  // Show banner
  const banner = document.getElementById('installer-banner');
  const bannerText = document.getElementById('installer-banner-text');
  if (banner && bannerText) {
    bannerText.textContent = '✔ Theme selected: ' + name + ' — step 3 command updated below.';
    banner.style.display = 'flex';
  }
}

function clearPick() {
  selectedInstallTheme = null;
  document.querySelectorAll('.pick-btn').forEach(b => b.classList.remove('selected'));
  const cmdEl = document.getElementById('install-cmd');
  if (cmdEl) cmdEl.textContent = 'sudo ./install.sh';
  const term = document.getElementById('term-preview');
  if (term) {
    term.innerHTML =
      'Available themes:\n' +
      '  1) aurora\n' +
      '  2) ember\n' +
      '  3) glacier\n' +
      '  4) classic  [access key required]\n' +
      '  5) mq       [access key required]\n' +
      '  6) neon\n\n' +
      'Select a theme [1-6]: <span class="cursor">_</span>';
  }
  const banner = document.getElementById('installer-banner');
  if (banner) banner.style.display = 'none';
}

/* ── Access key modal ── */
function verifyKey() {
  const val = document.getElementById('key-input').value.trim();
  if (val === ACCESS_KEY) {
    document.getElementById('key-modal').classList.remove('open');
    // came from installer picker
    if (pendingBtn) {
      applyPick(pendingBtn, pendingTheme);
      pendingBtn = null;
    } else {
      // came from theme preview card
      showUnlocked(pendingTheme);
    }
  } else {
    document.getElementById('key-error').textContent = 'Invalid access key. Please try again.';
    document.getElementById('key-input').focus();
  }
}

function showUnlocked(theme) {
  const name = THEME_NAMES[theme] || theme;
  document.getElementById('unlock-msg').textContent =
    'Access granted for the ' + name + ' theme. Use the command below after cloning the repo:';
  document.getElementById('unlock-cmd').textContent = 'sudo ./install.sh --theme ' + theme;
  document.getElementById('unlock-modal').classList.add('open');
  const card = document.querySelector('[data-theme="' + theme + '"]');
  if (card) {
    document.querySelectorAll('.theme-card').forEach(c => c.classList.remove('active'));
    card.classList.add('active');
  }
}

function closeModal(e) {
  if (e.target.classList.contains('modal-overlay')) {
    e.target.classList.remove('open');
    pendingBtn = null;
  }
}

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-overlay.open').forEach(m => m.classList.remove('open'));
    pendingBtn = null;
  }
  if (e.key === 'Enter' && document.getElementById('key-modal').classList.contains('open')) verifyKey();
});

/* ── Copy button ── */
function copy(btn) {
  const text = btn.dataset.text || btn.previousElementSibling.textContent.trim();
  navigator.clipboard.writeText(text).then(() => {
    btn.textContent = 'Copied!';
    btn.classList.add('copied');
    setTimeout(() => { btn.textContent = 'Copy'; btn.classList.remove('copied'); }, 2000);
  });
}
