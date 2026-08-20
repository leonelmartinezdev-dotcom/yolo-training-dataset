const api = {
  async getClasses() {
    const res = await fetch("/api/classes");
    return res.json();
  },

  async getImages() {
    const res = await fetch("/api/images");
    return res.json();
  },

  async getAnnotations(filename) {
    const res = await fetch(`/api/annotations/${encodeURIComponent(filename)}`);
    if (!res.ok) throw new Error(`Failed to load annotations for ${filename}`);
    return res.json();
  },

  async saveAnnotations(filename, boxes) {
    const res = await fetch(`/api/annotations/${encodeURIComponent(filename)}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ boxes }),
    });
    if (!res.ok) throw new Error(`Failed to save annotations for ${filename}`);
    return res.json();
  },

  async exportDataset(trainPct, valPct, testPct) {
    const res = await fetch("/api/export", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ train_pct: trainPct, val_pct: valPct, test_pct: testPct }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail ? JSON.stringify(err.detail) : "Export failed");
    }
    return res.json();
  },
};
