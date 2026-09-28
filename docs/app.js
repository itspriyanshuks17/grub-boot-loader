function copy(btn) {
  const text = btn.dataset.text || btn.previousElementSibling.textContent.trim();
  navigator.clipboard.writeText(text).then(() => {
    btn.textContent = 'Copied!';
    btn.classList.add('copied');
    setTimeout(() => { btn.textContent = 'Copy'; btn.classList.remove('copied'); }, 2000);
  });
}

function selectTheme(card) {
  document.querySelectorAll('.theme-card').forEach(c => c.classList.remove('active'));
  card.classList.add('active');
}
