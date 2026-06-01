// LuxeStay Main JavaScript

document.addEventListener('DOMContentLoaded', function () {

  // Auto-dismiss flash messages
  setTimeout(() => {
    document.querySelectorAll('.flash').forEach(f => {
      f.style.transition = 'opacity 0.4s, transform 0.4s';
      f.style.opacity = '0';
      f.style.transform = 'translateX(120%)';
      setTimeout(() => f.remove(), 400);
    });
  }, 5000);

  // Sidebar hamburger toggle
  const hamburger = document.getElementById('hamburger');
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebarOverlay');
  if (hamburger && sidebar) {
    hamburger.addEventListener('click', () => {
      sidebar.classList.toggle('open');
      if (overlay) overlay.classList.toggle('show');
    });
  }
  if (overlay) {
    overlay.addEventListener('click', () => {
      sidebar.classList.remove('open');
      overlay.classList.remove('show');
    });
  }

  // Notification bell
  const notifBtn = document.getElementById('notifBtn');
  const notifDropdown = document.getElementById('notifDropdown');
  if (notifBtn && notifDropdown) {
    notifBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      notifDropdown.classList.toggle('open');
      if (notifDropdown.classList.contains('open')) loadNotifications();
    });
    document.addEventListener('click', () => notifDropdown.classList.remove('open'));
    notifDropdown.addEventListener('click', e => e.stopPropagation());
    // Poll every 30s
    setInterval(loadNotifications, 30000);
    loadNotifications();
  }

  // Image upload preview
  const imageInput = document.getElementById('imageInput');
  const imagePreview = document.getElementById('imagePreview');
  const uploadArea = document.getElementById('uploadArea');
  if (imageInput && imagePreview) {
    imageInput.addEventListener('change', function () {
      if (this.files && this.files[0]) {
        const reader = new FileReader();
        reader.onload = e => {
          imagePreview.querySelector('img').src = e.target.result;
          imagePreview.style.display = 'block';
        };
        reader.readAsDataURL(this.files[0]);
      }
    });
    if (uploadArea) {
      uploadArea.addEventListener('click', () => imageInput.click());
      uploadArea.addEventListener('dragover', e => { e.preventDefault(); uploadArea.style.borderColor = 'var(--gold)'; });
      uploadArea.addEventListener('dragleave', () => uploadArea.style.borderColor = '');
      uploadArea.addEventListener('drop', e => {
        e.preventDefault();
        uploadArea.style.borderColor = '';
        if (e.dataTransfer.files[0]) {
          imageInput.files = e.dataTransfer.files;
          imageInput.dispatchEvent(new Event('change'));
        }
      });
    }
  }

  // Availability checker
  const checkInInput = document.getElementById('check_in');
  const checkOutInput = document.getElementById('check_out');
  const roomIdInput = document.getElementById('room_id_hidden');
  const availCheck = document.getElementById('availCheck');
  const excludeId = document.getElementById('exclude_reservation_id');

  function checkAvailability() {
    if (!checkInInput || !checkOutInput || !roomIdInput || !availCheck) return;
    const ci = checkInInput.value, co = checkOutInput.value, rid = roomIdInput.value;
    if (!ci || !co || !rid) return;
    const exc = excludeId ? excludeId.value : '';
    fetch(`/customer/api/check-availability?room_id=${rid}&check_in=${ci}&check_out=${co}&exclude_id=${exc}`)
      .then(r => r.json())
      .then(data => {
        availCheck.classList.add('show');
        if (data.available) {
          availCheck.className = 'avail-check show ok';
          availCheck.innerHTML = '<i class="fas fa-check-circle"></i> ' + data.message;
        } else {
          availCheck.className = 'avail-check show fail';
          availCheck.innerHTML = '<i class="fas fa-times-circle"></i> ' + data.message;
        }
        updateNights();
      })
      .catch(() => {});
  }

  if (checkInInput) checkInInput.addEventListener('change', checkAvailability);
  if (checkOutInput) checkOutInput.addEventListener('change', checkAvailability);

  // Night counter
  function updateNights() {
    const nightsDisplay = document.getElementById('nightsDisplay');
    const totalDisplay = document.getElementById('totalDisplay');
    const pricePerNight = parseFloat(document.getElementById('price_per_night')?.value || 0);
    if (!checkInInput || !checkOutInput || !nightsDisplay) return;
    const ci = new Date(checkInInput.value), co = new Date(checkOutInput.value);
    if (ci && co && co > ci) {
      const nights = Math.round((co - ci) / (1000 * 60 * 60 * 24));
      nightsDisplay.textContent = nights + ' night' + (nights !== 1 ? 's' : '');
      if (totalDisplay && pricePerNight) {
        totalDisplay.textContent = '₱' + (nights * pricePerNight).toLocaleString('en-PH', { minimumFractionDigits: 2 });
      }
    } else {
      nightsDisplay.textContent = '—';
      if (totalDisplay) totalDisplay.textContent = '—';
    }
  }
  if (checkInInput) checkInInput.addEventListener('change', updateNights);
  if (checkOutInput) checkOutInput.addEventListener('change', updateNights);

  // Confirm delete modals
  document.querySelectorAll('[data-confirm]').forEach(btn => {
    btn.addEventListener('click', function (e) {
      if (!confirm(this.dataset.confirm)) e.preventDefault();
    });
  });

  // Modal open/close
  document.querySelectorAll('[data-modal-open]').forEach(btn => {
    btn.addEventListener('click', () => {
      const modal = document.getElementById(btn.dataset.modalOpen);
      if (modal) modal.classList.add('open');
    });
  });
  document.querySelectorAll('[data-modal-close]').forEach(btn => {
    btn.addEventListener('click', () => {
      const modal = document.getElementById(btn.dataset.modalClose);
      if (modal) modal.classList.remove('open');
    });
  });
  document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', function (e) {
      if (e.target === this) this.classList.remove('open');
    });
  });

  // Filter tabs
  document.querySelectorAll('.filter-tab[data-filter]').forEach(tab => {
    tab.addEventListener('click', function () {
      const url = new URL(window.location);
      url.searchParams.set('status', this.dataset.filter);
      window.location = url.toString();
    });
  });

  // Print receipt
  const printBtn = document.getElementById('printReceipt');
  if (printBtn) printBtn.addEventListener('click', () => window.print());
});

function loadNotifications() {
  fetch('/admin/api/notifications')
    .then(r => r.json())
    .then(data => {
      const badge = document.getElementById('notifCount');
      const list = document.getElementById('notifList');
      if (badge) {
        badge.textContent = data.count;
        badge.style.display = data.count > 0 ? 'flex' : 'none';
      }
      if (list) {
        if (data.notifications.length === 0) {
          list.innerHTML = '<div class="notif-empty"><i class="fas fa-bell-slash" style="display:block;font-size:28px;margin-bottom:8px;"></i>No pending notifications</div>';
        } else {
          list.innerHTML = data.notifications.map(n => `
            <a href="/admin/reservations/${n.id}" class="notif-item" style="display:block;text-decoration:none;">
              <div class="notif-item-title">${n.ref} — ${n.name}</div>
              <div class="notif-item-sub">${n.room} &middot; ${n.created_at}</div>
            </a>
          `).join('');
        }
      }
    }).catch(() => {});
}
