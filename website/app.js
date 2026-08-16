const API_BASE = (window.HERMES_API_BASE || '').replace(/\/$/, '');
const api = (path) => `${API_BASE}${path}`;

const $ = (id) => document.getElementById(id);
const healthDot = $('health-dot');
const healthTitle = $('health-title');
const healthDetail = $('health-detail');
const serviceCount = $('service-count');
const chatLog = $('chat-log');
const chatForm = $('chat-form');
const chatInput = $('chat-input');
const sendBtn = $('send-btn');
const chatError = $('chat-error');

function setHealth(state, title, detail) {
  healthDot.className = `health-dot ${state}`;
  healthTitle.textContent = title;
  healthDetail.textContent = detail;
}

async function refreshHealth() {
  setHealth('', 'Checking backend…', 'Connecting to the Hermes gateway.');
  try {
    const [healthResponse, servicesResponse] = await Promise.all([
      fetch(api('/health?deep=false'), {headers: {'Accept': 'application/json'}}),
      fetch(api('/v1/services'), {headers: {'Accept': 'application/json'}})
    ]);
    if (!healthResponse.ok) throw new Error(`Health endpoint returned HTTP ${healthResponse.status}`);
    const health = await healthResponse.json();
    const services = servicesResponse.ok ? await servicesResponse.json() : null;
    const count = services?.count ?? health?.services_by_tier ? Object.values(health.services_by_tier).reduce((a,b) => a+b, 0) : '—';
    serviceCount.textContent = `${count} registered services`;
    setHealth(health.status === 'healthy' ? 'good' : 'bad', health.status === 'healthy' ? 'Backend online' : `Backend ${health.status}`, `Gateway v${health.version || 'unknown'} · ${health.uptime_seconds ?? 0}s uptime`);
  } catch (error) {
    serviceCount.textContent = 'Gateway unavailable';
    setHealth('bad', 'Backend offline', 'Start the Hermes Docker stack, then refresh this panel.');
  }
}

function addBubble(role, text) {
  const el = document.createElement('div');
  el.className = `bubble ${role}`;
  const label = document.createElement('span');
  label.className = 'bubble-label';
  label.textContent = role === 'user' ? 'You' : 'Hermes';
  const p = document.createElement('p');
  p.textContent = text;
  el.append(label, p);
  chatLog.appendChild(el);
  chatLog.scrollTop = chatLog.scrollHeight;
}

function showError(message) {
  chatError.hidden = !message;
  chatError.textContent = message || '';
}

async function sendMessage(message) {
  const nativeLanguage = $('native-language').value;
  const targetLanguage = $('target-language').value;
  addBubble('user', message);
  showError('');
  sendBtn.disabled = true;
  sendBtn.textContent = 'Thinking…';

  try {
    const response = await fetch(api('/v1/chat'), {
      method: 'POST',
      headers: {'Content-Type': 'application/json', 'Accept': 'application/json'},
      body: JSON.stringify({
        user_id: 'web-demo-user',
        message,
        session_context: {
          client: 'hermes-web',
          native_language: nativeLanguage,
          target_language: targetLanguage,
          level: 'beginner'
        }
      })
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const msg = data?.error?.message || data?.detail || `Hermes returned HTTP ${response.status}`;
      throw new Error(msg);
    }
    const reply = data?.response?.message || data?.message || data?.reply || data?.output || data?.result?.message || data?.data?.message;
    if (!reply) throw new Error('The backend responded, but no tutor message was found in the response payload. Check /docs for the current API contract.');
    addBubble('ai', String(reply));
  } catch (error) {
    showError(`Live tutor request failed: ${error.message}. The UI is connected to the real API; no fake response was generated.`);
  } finally {
    sendBtn.disabled = false;
    sendBtn.innerHTML = 'Send <span>↗</span>';
    chatInput.focus();
  }
}

chatForm.addEventListener('submit', (event) => {
  event.preventDefault();
  const message = chatInput.value.trim();
  if (!message) return;
  chatInput.value = '';
  sendMessage(message);
});
$('refresh-health').addEventListener('click', refreshHealth);
refreshHealth();

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => navigator.serviceWorker.register('/sw.js').catch(() => {}));
}
