async function api(path, method='GET', body=null) {
  const opts = { method, headers: {} };
  if (body !== null) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(path, opts);
  return res.json();
}

document.getElementById('login-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const username = document.getElementById('username').value;
  const password = document.getElementById('password').value;
  const r = await api('/api/login', 'POST', { username, password });
  const out = document.getElementById('login-result');
  if (r.ok) {
    out.textContent = 'Ingelogd als ' + r.username;
    document.getElementById('form-section').style.display = 'block';
    loadLessons();
  } else {
    out.textContent = 'Login fout: ' + (r.error || 'onbekend');
  }
});

document.getElementById('lesson-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const date = document.getElementById('date').value;
  const customer_name = document.getElementById('customer_name').value;
  const amount = document.getElementById('amount').value;
  const r = await api('/api/lessons', 'POST', { date, customer_name, amount });
  const out = document.getElementById('form-result');
  if (r.ok) {
    out.textContent = 'Opgeslagen, id=' + r.id;
    loadLessons();
  } else {
    out.textContent = 'Fout: ' + (r.error || 'onbekend');
  }
});

async function loadLessons() {
  const r = await api('/api/lessons');
  const list = document.getElementById('lessons-list');
  list.innerHTML = '';
  if (r.ok && Array.isArray(r.lessons)) {
    r.lessons.forEach(l => {
      const li = document.createElement('li');
      li.textContent = `${l.date} — ${l.customer_name} — €${l.amount}`;
      list.appendChild(li);
    });
  }
}

// try load on open (will work if public endpoint)
loadLessons().catch(()=>{});
