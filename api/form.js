// Receives every form on the Rebels Garage site (quotes and messages) and emails it through Resend.
// Settings (Vercel > Project > Settings > Environment Variables):
//   RESEND_API_KEY  required. From resend.com > API Keys.
//   FORM_TO         optional. Where submissions go. Default troy@twofourmedia.com.
//   FORM_FROM       optional. Sender. Default uses Resend's shared address until
//                   therebelsgarage.com is verified in Resend, then set it to
//                   "The Rebels Garage <website@therebelsgarage.com>" and FORM_TO to info@rebelsauto.us.

const FORM_NAMES = {
  quote: 'Quote request',
  contact: 'Website message',

};

const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

module.exports = async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ ok: false, error: 'POST only' });

  let body = req.body;
  if (typeof body === 'string') {
    try { body = JSON.parse(body); } catch { return res.status(400).json({ ok: false, error: 'Bad request' }); }
  }
  const form = String(body?.form || 'lead');
  const fields = Array.isArray(body?.fields) ? body.fields.slice(0, 80) : [];

  // Spam trap: real people never see or fill the "company_site" field.
  if (fields.some(([k, v]) => k === 'company_site' && String(v).trim())) return res.status(200).json({ ok: true });

  const clean = fields
    .filter(([k]) => k !== 'company_site')
    .map(([k, v]) => [String(k).slice(0, 200), String(v ?? '').slice(0, 5000)]);
  const get = (name) => (clean.find(([k]) => k.toLowerCase() === name) || [])[1] || '';

  const email = get('email');
  const name = get('name') || [get('first name'), get('last name')].filter(Boolean).join(' ');
  const who = form === 'quote' ? `${name || get('phone')}${get('vehicle') ? ' (' + get('vehicle') + ')' : ''}: ${get('service')}` : (name || get('email') || 'website visitor');
  const label = FORM_NAMES[form] || 'Website form';

  const key = process.env.RESEND_API_KEY;
  if (!key) return res.status(503).json({ ok: false, error: 'Form email is not set up yet' });

  const rows = clean
    .filter(([, v]) => v.trim())
    .map(([k, v]) => `<tr><td style="padding:8px 12px;border:1px solid #ddd;vertical-align:top;font-weight:600;width:38%">${esc(k)}</td><td style="padding:8px 12px;border:1px solid #ddd;white-space:pre-wrap">${esc(v)}</td></tr>`)
    .join('');
  const text = clean.filter(([, v]) => v.trim()).map(([k, v]) => `${k}: ${v}`).join('\n\n');
  const page = String(body?.page || '').slice(0, 300);

  const r = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: { Authorization: `Bearer ${key}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      from: process.env.FORM_FROM || 'Rebels Garage Website <onboarding@resend.dev>',
      to: (process.env.FORM_TO || 'troy@twofourmedia.com').split(',').map((s) => s.trim()),
      reply_to: /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email) ? email : undefined,
      subject: `${label}: ${who}`,
      html: `<h2 style="font-family:Arial,sans-serif">${esc(label)}</h2><table style="border-collapse:collapse;font-family:Arial,sans-serif;font-size:14px">${rows}</table><p style="font-family:Arial,sans-serif;color:#888;font-size:12px">Sent from therebelsgarage.com${esc(page || '')}</p>`,
      text: `${label}\n\n${text}\n\nSent from therebelsgarage.com${page || ''}`,
    }),
  });
  if (!r.ok) {
    console.error('Resend error', r.status, await r.text());
    return res.status(502).json({ ok: false, error: 'Email send failed' });
  }
  console.log('form sent', form, who);
  return res.status(200).json({ ok: true });
}
