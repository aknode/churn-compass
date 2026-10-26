async function start() {
  const [s, sch, c] = await Promise.all([
    api("/api/summary"),
    api("/api/schema"),
    api("/api/cohort"),
  ]);
  const m = s.test[s.selected_model];
  $("#metrics").innerHTML = [
    ["Dataset rows", fmt(s.rows)],
    ["Test ROC AUC", fmt(m.roc_auc, 3)],
    ["Test average precision", fmt(m.average_precision, 3)],
    ["Decision threshold", fmt(s.threshold, 3)],
  ]
    .map(
      ([a, b]) =>
        '<div class="card"><div class="label">' +
        a +
        '</div><div class="metric">' +
        b +
        "</div></div>",
    )
    .join("");
  $("#benchmark").innerHTML = table(
    Object.entries(s.test).map(([model, m]) => ({
      model,
      ROC_AUC: m.roc_auc,
      AP: m.average_precision,
      precision: m.precision,
      recall: m.recall,
    })),
  );
  const max = Math.max(...s.importance.map((r) => r.ap_drop), 0.001);
  $("#importance").innerHTML = s.importance
    .slice(0, 7)
    .map(
      (r) =>
        "<div>" +
        esc(r.feature) +
        " <small>" +
        fmt(r.ap_drop, 4) +
        '</small></div><div class="bar"><i style="width:' +
        Math.max(0, (r.ap_drop / max) * 100) +
        '%"></i></div>',
    )
    .join("");
  $("#cohort").innerHTML = table(c);
  $("#notes").innerHTML =
    "<p>Selected model: <b>" +
    esc(s.selected_model) +
    "</b> · Train / validation / test: " +
    Object.values(s.split).join(" / ") +
    "</p>" +
    s.limitations.map((n) => '<p class="muted">' + esc(n) + "</p>").join("");
  $("#pr").innerHTML = lineChart(s.pr_curve, "recall", "precision");
  $("#fields").innerHTML = sch.features
    .map(
      (k) =>
        '<div><label for="f-' +
        k +
        '">' +
        esc(k) +
        "</label>" +
        (sch.options[k]
          ? '<select id="f-' +
            k +
            '" name="' +
            k +
            '">' +
            sch.options[k]
              .map((v) => "<option>" + esc(v) + "</option>")
              .join("") +
            "</select>"
          : '<input id="f-' +
            k +
            '" name="' +
            k +
            '" type="number" min="0" step="any" value="' +
            { tenure: 12, MonthlyCharges: 70, TotalCharges: 840 }[k] +
            '" required>') +
        "</div>",
    )
    .join("");
}
$("#predict").onsubmit = async (e) => {
  e.preventDefault();
  try {
    const data = Object.fromEntries(new FormData(e.target));
    const r = (await post("/api/predict", { customers: [data] }))
      .predictions[0];
    $("#prediction").innerHTML =
      '<div class="notice"><strong>' +
      pct(r.risk_score) +
      " estimated churn risk</strong><br>" +
      (r.flagged ? "Flagged for review" : "Below review threshold") +
      " · Threshold " +
      fmt(r.threshold, 3) +
      "</div>";
  } catch (e) {
    error(e);
  }
};
$("#batch").onclick = async () => {
  try {
    const f = $("#csv").files[0];
    if (!f) throw Error("Choose a CSV first.");
    $("#batch").disabled = true;
    const r = await fetch("/api/predict-csv", {
      method: "POST",
      headers: { "Content-Type": "text/csv" },
      body: f,
    });
    if (!r.ok) throw Error((await r.json()).detail);
    const url = URL.createObjectURL(await r.blob());
    const a = document.createElement("a");
    a.href = url;
    a.download = "churn_predictions.csv";
    a.click();
    URL.revokeObjectURL(url);
    $("#batch-status").textContent = "Predictions downloaded.";
  } catch (e) {
    error(e);
  } finally {
    $("#batch").disabled = false;
  }
};
start().catch(error);
