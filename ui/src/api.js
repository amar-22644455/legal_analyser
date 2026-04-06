export async function postJson(url, body) {
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });

  const text = await response.text();
  let data = {};

  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = { detail: text };
    }
  }

  if (!response.ok) {
    throw new Error(data.detail || data.message || 'Request failed');
  }
  return data;
}

export async function getJson(url) {
  const response = await fetch(url);
  const text = await response.text();
  let data = {};

  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = { detail: text };
    }
  }

  if (!response.ok) {
    throw new Error(data.detail || data.message || 'Request failed');
  }
  return data;
}

export async function postFormData(url, formData) {
  const response = await fetch(url, {
    method: 'POST',
    // ⚠️ CRITICAL: Do NOT set the 'Content-Type' header here!
    // The browser automatically sets it to 'multipart/form-data' 
    // and calculates the required boundary when you pass a FormData object.
    body: formData
  });

  const text = await response.text();
  let data = {};

  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = { detail: text };
    }
  }

  if (!response.ok) {
    throw new Error(data.detail || data.message || 'Upload failed');
  }
  return data;
}
