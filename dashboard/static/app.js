// Tripline Dashboard Client Interactivity
document.addEventListener('DOMContentLoaded', () => {
  // 1. Copy to clipboard
  document.querySelectorAll('[data-copy]').forEach(el => {
    el.addEventListener('click', (e) => {
      e.preventDefault();
      const text = el.getAttribute('data-copy');
      if (text) {
        navigator.clipboard.writeText(text).then(() => {
          const original = el.innerText;
          el.innerText = 'Copied!';
          el.classList.add('copied');
          setTimeout(() => {
            el.innerText = original;
            el.classList.remove('copied');
          }, 1500);
        });
      }
    });
  });

  // 2. Client-side search in Receipts and Runs tables
  const searchInput = document.querySelector('[data-table-search]');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      const q = e.target.value.toLowerCase().trim();
      const rows = document.querySelectorAll('table.data-table tbody tr');
      rows.forEach(row => {
        const text = row.innerText.toLowerCase();
        row.style.display = text.includes(q) ? '' : 'none';
      });
    });
  }

  // 3. Filter chips in table toolbar
  document.querySelectorAll('[data-filter-group]').forEach(group => {
    const chips = group.querySelectorAll('.filter-chip');
    chips.forEach(chip => {
      chip.addEventListener('click', () => {
        chips.forEach(c => c.classList.remove('active'));
        chip.classList.add('active');
        const filterVal = chip.getAttribute('data-filter') || 'all';
        const targetCol = chip.getAttribute('data-col');
        const rows = document.querySelectorAll('table.data-table tbody tr');
        rows.forEach(row => {
          if (filterVal === 'all') {
            row.style.display = '';
          } else {
            const cell = targetCol ? row.querySelector(`[data-cell="${targetCol}"]`) : null;
            const text = (cell ? cell.innerText : row.innerText).toLowerCase();
            row.style.display = text.includes(filterVal.toLowerCase()) ? '' : 'none';
          }
        });
      });
    });
  });

  // 4. One-time dismissable banner
  const banner = document.getElementById('info-banner');
  const bannerClose = document.getElementById('banner-close');
  if (banner && bannerClose) {
    if (localStorage.getItem('tripline_banner_dismissed') === '1') {
      banner.style.display = 'none';
    } else {
      banner.style.display = 'flex';
      bannerClose.addEventListener('click', () => {
        banner.style.display = 'none';
        localStorage.setItem('tripline_banner_dismissed', '1');
      });
    }
  }

  // 5. Relative timestamps
  document.querySelectorAll('[data-timestamp]').forEach(el => {
    const raw = el.getAttribute('data-timestamp');
    if (!raw || raw === '—') return;
    try {
      const date = new Date(raw);
      if (isNaN(date.getTime())) return;
      const now = new Date();
      const diffSec = Math.floor((now - date) / 1000);
      if (diffSec < 60) el.innerText = 'just now';
      else if (diffSec < 3600) el.innerText = `${Math.floor(diffSec / 60)}m ago`;
      else if (diffSec < 86400) el.innerText = `${Math.floor(diffSec / 3600)}h ago`;
      else el.innerText = `${Math.floor(diffSec / 86400)}d ago`;
      el.title = date.toISOString();
    } catch (err) {}
  });

  // 6. Sign Up Modal Controls
  const signupModal = document.getElementById('signup-modal');
  const openModalBtn = document.getElementById('open-signup-modal-btn');
  const closeModalBtn = document.getElementById('close-signup-modal-btn');

  if (signupModal && openModalBtn) {
    openModalBtn.addEventListener('click', (e) => {
      // If we are not already on /signup, open the quick modal!
      if (window.location.pathname !== '/signup') {
        e.preventDefault();
        signupModal.style.display = 'flex';
      }
    });

    if (closeModalBtn) {
      closeModalBtn.addEventListener('click', () => {
        signupModal.style.display = 'none';
      });
    }

    signupModal.addEventListener('click', (e) => {
      if (e.target === signupModal) {
        signupModal.style.display = 'none';
      }
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && signupModal.style.display === 'flex') {
        signupModal.style.display = 'none';
      }
    });
  }

  // 7. Modal Sign Up AJAX Submission
  const modalForm = document.getElementById('modal-signup-form');
  if (modalForm) {
    modalForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const submitBtn = modalForm.querySelector('button[type="submit"]');
      const originalText = submitBtn.innerHTML;
      submitBtn.innerHTML = 'Generating Credentials...';
      submitBtn.disabled = true;

      const payload = {
        name: document.getElementById('modal-name')?.value || 'Agent Developer',
        email: document.getElementById('modal-email')?.value || 'dev@tripline.local',
        agent_stack: document.getElementById('modal-stack')?.value || 'MCP Server'
      };

      try {
        const res = await fetch('/signup', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.status === 'success') {
          const formBody = document.getElementById('modal-form-body');
          const successBody = document.getElementById('modal-success-body');
          const msg = document.getElementById('modal-success-msg');
          const apiKey = document.getElementById('modal-api-key');
          if (formBody && successBody) {
            formBody.style.display = 'none';
            successBody.style.display = 'block';
            if (msg) msg.innerText = `Registered: ${data.registration.name} (${data.registration.reg_id})`;
            if (apiKey) apiKey.innerText = data.registration.api_key;
          }
        }
      } catch (err) {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
        alert('Registration error. Please try again.');
      }
    });
  }

  // 8. Segmented Control in Page Form
  document.querySelectorAll('[data-segmented]').forEach(seg => {
    const options = seg.querySelectorAll('.segment-option');
    options.forEach(opt => {
      opt.addEventListener('click', () => {
        options.forEach(o => o.classList.remove('active'));
        opt.classList.add('active');
        const radio = opt.querySelector('input[type="radio"]');
        if (radio) radio.checked = true;
      });
    });
  });

  // 9. GitHub Quick Fill Button
  const ghQuickBtn = document.getElementById('github-quick-btn');
  if (ghQuickBtn) {
    ghQuickBtn.addEventListener('click', () => {
      const nameInput = document.getElementById('name');
      const emailInput = document.getElementById('email');
      const ghInput = document.getElementById('github');
      if (nameInput) nameInput.value = 'Agent Builder (@agent-dev)';
      if (emailInput) emailInput.value = 'builder@flowstate.ai';
      if (ghInput) ghInput.value = 'https://github.com/agent-dev/mcp-agent';
      ghQuickBtn.innerHTML = '<span>Prefilled with GitHub Developer Profile ✓</span>';
      ghQuickBtn.style.borderColor = 'var(--allow)';
      ghQuickBtn.style.color = 'var(--allow)';
    });
  }
});

