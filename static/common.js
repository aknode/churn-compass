const $ = (s) => document.querySelector(s);
const esc = (s) =>
  String(s ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
function error(e) {
  const a = $("#error");
  a.textContent = e.message || String(e);
  a.style.display = "block";
}
async function api(url, options = {}) {
  const r = await fetch(url, options);
  if (!r.ok) {
    let t;
    try {
      t = await r.json();
    } catch {
      t = { detail: r.statusText };
    }
    throw Error(
      typeof t.detail === "string" ? t.detail : JSON.stringify(t.detail),
    );
  }
  return r.json();
}
const post = (url, data) =>
  api(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
const fmt = (n, d = 0) =>
  Number(n).toLocaleString("en-GB", { maximumFractionDigits: d });
const pct = (n) => fmt(n * 100, 1) + "%";
function table(rows) {
  if (!rows.length) return '<p class="muted">No matching records.</p>';
  const keys = Object.keys(rows[0]);
  return (
    '<div class="scroll"><table><thead><tr>' +
    keys.map((k) => "<th>" + esc(k.replaceAll("_", " ")) + "</th>").join("") +
    "</tr></thead><tbody>" +
    rows
      .map(
        (r) =>
          "<tr>" +
          keys
            .map(
              (k) =>
                "<td>" +
                esc(typeof r[k] === "number" ? fmt(r[k], 3) : r[k]) +
                "</td>",
            )
            .join("") +
          "</tr>",
      )
      .join("") +
    "</tbody></table></div>"
  );
}
function lineChart(rows, x, y) {
  if (!rows.length) return "";
  const w = 700,
    h = 210,
    p = 35,
    vals = rows.map((r) => Number(r[y])),
    max = Math.max(...vals, 1),
    min = Math.min(...vals, 0);
  let numeric = typeof rows[0][x] === "number";
  let pts = vals.map((v, i) => [
    p +
      (numeric ? Number(rows[i][x]) : i / Math.max(1, vals.length - 1)) *
        (w - 2 * p),
    h - p - ((v - min) / (max - min)) * (h - 2 * p),
  ]);
  return (
    '<svg class="chart" role="img" aria-label="' +
    esc(y) +
    ' trend" viewBox="0 0 ' +
    w +
    " " +
    h +
    '"><line x1="35" y1="175" x2="665" y2="175" stroke="#cbd6ce"/><polyline fill="none" stroke="#146b55" stroke-width="3" points="' +
    pts.map((a) => a.join(",")).join(" ") +
    '"/>' +
    (numeric
      ? [0, 0.25, 0.5, 0.75, 1]
          .map(
            (v) =>
              '<text x=\"' +
              (35 + v * 630) +
              '\" y=\"200\" text-anchor=\"middle\">' +
              v +
              "</text>",
          )
          .join("")
      : rows
          .map((r, i) =>
            i % Math.max(1, Math.ceil(rows.length / 6)) === 0
              ? '<text x="' +
                pts[i][0] +
                '" y="200" text-anchor="middle">' +
                esc(numeric ? fmt(r[x], 2) : r[x]) +
                "</text>"
              : "",
          )
          .join("")) +
    '<text x="5" y="18">' +
    fmt(max, 0) +
    "</text></svg>"
  );
}
