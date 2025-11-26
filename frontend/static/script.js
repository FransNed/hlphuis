async function api(path, method='GET', body=null) {
  const opts = { method, headers: {} };
  if (body !== null) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(path, opts);
  return res.json();
}

let currentUserId = null;

document.getElementById('login-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;
  const r = await api('/api/login', 'POST', { email, password });
  const out = document.getElementById('login-result');
  if (r.ok) {
    out.textContent = 'Ingelogd als ' + (r.email || r.id);
    currentUserId = r.id;
    if (r.is_admin) {
      // redirect admin to admin UI
      window.location = '/admin.html';
      return;
    }
    // non-admin: show lesson form and profile
    document.getElementById('form-section').style.display = 'block';
    document.getElementById('profile-section').style.display = 'block';
    loadUsers().then(()=>{
      try { document.getElementById('user_select').value = currentUserId; } catch(e){}
    });
    loadLessons();
    loadProfile();
  } else {
    out.textContent = 'Login fout: ' + (r.error || 'onbekend');
  }
});

document.getElementById('lesson-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const date = document.getElementById('date').value;
  const customer_name = document.getElementById('customer_name').value;
  const amount = document.getElementById('amount').value;
  const out = document.getElementById('form-result');
  // Validate date format YYYY-MM-DD (type=date helps, but validate anyway)
  const dateRe = /^\d{4}-\d{2}-\d{2}$/;
  if (!dateRe.test(date)) {
    out.textContent = 'Datum ongeldig. Gebruik formaat YYYY-MM-DD.';
    return;
  }
  // Validate amount
  const num = parseFloat(amount);
  if (Number.isNaN(num)) {
    out.textContent = 'Bedrag ongeldig. Vul een getal in.';
    return;
  }

  const user_select = document.getElementById('user_select');
  const user_id = user_select && user_select.value ? parseInt(user_select.value) : undefined;
  const r = await api('/api/lessons', 'POST', { date, customer_name, amount: num, user_id });
  if (r.ok) {
    out.textContent = 'Opgeslagen, id=' + r.id;
    loadLessons();
  } else {
    out.textContent = 'Fout: ' + (r.error || 'onbekend');
  }
});

async function loadUsers() {
  try {
    const r = await api('/api/users_simple');
    if (r.ok && Array.isArray(r.users)) {
      const sel = document.getElementById('user_select');
      if (!sel) return;
      sel.innerHTML = '';
      r.users.forEach(u => {
        const opt = document.createElement('option');
        opt.value = u.id;
        opt.textContent = u.name || u.username;
        sel.appendChild(opt);
      });
      // if currentUserId is set, try to select it
      if (typeof currentUserId === 'number') {
        try { sel.value = currentUserId; } catch(e){}
      }
    }
  } catch (e) {}
}

async function loadLessons() {
  const r = await api('/api/lessons');
  const list = document.getElementById('lessons-list');
  list.innerHTML = '';
    if (r.ok && Array.isArray(r.lessons)) {
    r.lessons.forEach(l => {
      const li = document.createElement('li');
      li.textContent = `${l.date} — ${l.customer_name} — €${l.amount} ${l.user_name ? '— ' + l.user_name : ''}`;
      list.appendChild(li);
    });
  }
}

async function loadProfile() {
  if (!currentUserId) return;
  try {
    const r = await api('/api/users/' + currentUserId);
    if (r.ok && r.user) {
      document.getElementById('p_email').value = r.user.email || '';
      document.getElementById('p_name').value = r.user.name || '';
      document.getElementById('p_description').value = r.user.description || '';
    }
  } catch(e){}
}

document.getElementById('p_save') && document.getElementById('p_save').addEventListener('click', async () => {
  if (!currentUserId) return;
  const email = document.getElementById('p_email').value;
  const name = document.getElementById('p_name').value;
  const description = document.getElementById('p_description').value;
  const r = await api('/api/users/' + currentUserId, 'PUT', { email, name, description });
  if (r.ok) {
    alert('Profiel opgeslagen');
  } else {
    alert('Fout: ' + (r.error||'onbekend'));
  }
});

document.getElementById('profile-password-form') && document.getElementById('profile-password-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  if (!currentUserId) return;
  const oldp = document.getElementById('old_password').value;
  const newp = document.getElementById('new_password').value;
  const r = await api('/api/users/' + currentUserId + '/password', 'POST', { old_password: oldp, new_password: newp });
  if (r.ok) {
    alert('Wachtwoord gewijzigd');
  } else {
    alert('Fout: ' + (r.error||'onbekend'));
  }
});

// try load on open (will work if public endpoint)
loadLessons().catch(()=>{});
