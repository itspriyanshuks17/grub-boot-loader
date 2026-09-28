const ACCESS_KEY = atob('aW50ZXJuc0BtcWkyMDI1');
const LOCKED = ['marquardt', 'mq'];
let pendingTheme = null;

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

function verifyKey() {
  const val = document.getElementById('key-input').value.trim();
  if (val === ACCESS_KEY) {
    document.getElementById('key-modal').classList.remove('open');
    showUnlocked(pendingTheme);
  } else {
    document.getElementById('key-error').textContent = 'Invalid access key. Please try again.';
    document.getElementById('key-input').focus();
  }
}

function showUnlocked(theme) {
  const names = { marquardt: 'Classic', mq: 'MQ' };
  document.getElementById('unlock-msg').textContent =
    'Access granted for the ' + (names[theme] || theme) + ' theme. Use the command below after cloning the repo:';
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
  }
}

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') document.querySelectorAll('.modal-overlay.open').forEach(m => m.classList.remove('open'));
  if (e.key === 'Enter' && document.getElementById('key-modal').classList.contains('open')) verifyKey();
});

function copy(btn) {
  const text = btn.dataset.text || btn.previousElementSibling.textContent.trim();
  navigator.clipboard.writeText(text).then(() => {
    btn.textContent = 'Copied!';
    btn.classList.add('copied');
    setTimeout(() => { btn.textContent = 'Copy'; btn.classList.remove('copied'); }, 2000);
  });
}
