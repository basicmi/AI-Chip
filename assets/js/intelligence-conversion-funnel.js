(() => {
  const root = document.querySelector("[data-conversion-funnel]");
  if (!root) return;
  const input = root.querySelector("[data-cf-files]");
  const status = root.querySelector("[data-cf-status]");
  const clear = root.querySelector("[data-cf-clear]");
  const historyPanel = root.querySelector("[data-cf-history-panel]");
  const detailPanel = root.querySelector("[data-cf-detail-panel]");
  const history = root.querySelector("[data-cf-history]");
  const select = root.querySelector("[data-cf-select]");
  const details = root.querySelector("[data-cf-details]");
  const MAX_BYTES = 5 * 1024 * 1024;
  const MAX_FILES = 20;
  const stat = key => root.querySelector('[data-cf-stat="' + key + '"]');
  let snapshots = [];

  const integer = value => Number.isSafeInteger(value) && value >= 0;
  const rateText = item => item.rate === null ? "N/A" : (100 * item.rate).toFixed(1) + "%";
  const cell = value => {
    const node = document.createElement("td");
    node.textContent = String(value);
    return node;
  };
  const validate = data => {
    if (!data || data.schema_version !== "1.0" || !data.policy ||
        data.policy.read_only !== true ||
        data.policy.formal_factual_verification_performed !== false ||
        data.policy.automatic_registry_writes !== false ||
        data.policy.accepted_for_evidence_attachment_is_final_approval !== false ||
        !data.metrics || !Array.isArray(data.stages) ||
        !Array.isArray(data.integration_receipts)) {
      throw Error("Snapshot schema or read-only policy is invalid.");
    }
    const m = data.metrics;
    const countKeys = ["discovery_candidates","candidates_with_claims","claims_extracted",
      "triage_groups","duplicate_claims_collapsed","persistent_review_backlog",
      "human_decisions_recorded","accepted_for_evidence_attachment",
      "eligible_claims_not_integrated","integrated_claims","integration_receipts"];
    for (const key of countKeys) if (!integer(m[key])) throw Error("Invalid count: " + key);
    if (!m.review_states || !["pending","needs_more_evidence","rejected",
      "accepted_for_evidence_attachment"].every(key => integer(m.review_states[key]))) {
      throw Error("Review-state counts are missing or invalid.");
    }
    const states = Object.values(m.review_states).reduce((a,b) => a+b, 0);
    if (states !== m.persistent_review_backlog ||
        m.human_decisions_recorded !== states - m.review_states.pending ||
        m.accepted_for_evidence_attachment !== m.review_states.accepted_for_evidence_attachment ||
        m.integrated_claims + m.eligible_claims_not_integrated !== m.accepted_for_evidence_attachment ||
        m.integration_receipts < m.integrated_claims ||
        m.integration_receipts !== data.integration_receipts.length) {
      throw Error("Review and integration counts do not reconcile.");
    }
    for (const [key, numerator, denominator] of [
      ["decision_coverage",m.human_decisions_recorded,m.persistent_review_backlog],
      ["acceptance_rate_among_decisions",m.accepted_for_evidence_attachment,m.human_decisions_recorded],
      ["integration_coverage",m.integrated_claims,m.accepted_for_evidence_attachment]
    ]) {
      const row = m[key];
      if (!row || row.numerator !== numerator || row.denominator !== denominator ||
          (row.rate !== null && (typeof row.rate !== "number" || row.rate < 0 || row.rate > 1)) ||
          row.rate !== (denominator ? Math.round(numerator / denominator * 10000) / 10000 : null)) {
        throw Error("Invalid rate denominator or arithmetic: " + key);
      }
    }
    if (!data.source_timestamps ||
        !["discovery","claims","triage","review_state"].every(key =>
          typeof data.source_timestamps[key] === "string" && !Number.isNaN(Date.parse(data.source_timestamps[key])))) {
      throw Error("Source timestamps are missing.");
    }
    if (typeof data.generated_at !== "string" || Number.isNaN(Date.parse(data.generated_at))) {
      throw Error("Invalid snapshot timestamp.");
    }
    if (!data.integration_receipts.every(x => x && typeof x.claim_id === "string" &&
        typeof x.target_registry === "string" && typeof x.target_record_id === "string" &&
        typeof x.merged_pr_url === "string")) {
      throw Error("Integration receipt fields are malformed.");
    }
    if (m.integrated_claims !== new Set(data.integration_receipts.map(x => x.claim_id)).size) {
      throw Error("Unique integrated Claim count does not match receipts.");
    }
    return data;
  };
  const reset = () => {
    snapshots = [];
    input.value = "";
    history.replaceChildren();
    select.replaceChildren();
    details.replaceChildren();
    ["candidates","claims","decisions","integrated"].forEach(key => stat(key).textContent = "—");
    historyPanel.hidden = true;
    detailPanel.hidden = true;
    status.textContent = "No conversion snapshots loaded.";
    status.classList.remove("is-error");
  };
  const render = () => {
    const latest = snapshots[snapshots.length - 1];
    stat("candidates").textContent = latest.metrics.discovery_candidates.toLocaleString();
    stat("claims").textContent = latest.metrics.claims_extracted.toLocaleString();
    stat("decisions").textContent = latest.metrics.human_decisions_recorded.toLocaleString();
    stat("integrated").textContent = latest.metrics.integrated_claims.toLocaleString();
    history.replaceChildren();
    for (const row of snapshots) {
      const m = row.metrics;
      const tr = document.createElement("tr");
      [new Date(row.generated_at).toISOString().slice(0,10),
       m.discovery_candidates,m.claims_extracted,m.persistent_review_backlog,
       m.human_decisions_recorded,rateText(m.decision_coverage),
       m.accepted_for_evidence_attachment,m.integrated_claims,
       rateText(m.integration_coverage)].forEach(value => tr.append(cell(value)));
      history.append(tr);
    }
    select.replaceChildren();
    snapshots.forEach((row,index) => {
      const option = document.createElement("option");
      option.value = String(index);
      option.textContent = new Date(row.generated_at).toISOString();
      select.append(option);
    });
    historyPanel.hidden = false;
    detailPanel.hidden = false;
    inspect();
  };
  const inspect = () => {
    const row = snapshots[Number(select.value)] || snapshots[snapshots.length - 1];
    if (!row) return;
    const m = row.metrics;
    details.replaceChildren();
    const list = document.createElement("ul");
    const lines = [
      "Discovery candidates: " + m.discovery_candidates,
      "Candidates yielding Claims: " + m.candidates_with_claims,
      "Extracted Claim candidates: " + m.claims_extracted,
      "Triage groups: " + m.triage_groups + " (exact-text duplicates collapsed: " + m.duplicate_claims_collapsed + ")",
      "Persistent review backlog: " + m.persistent_review_backlog,
      "Pending: " + m.review_states.pending,
      "Needs more evidence: " + m.review_states.needs_more_evidence,
      "Rejected: " + m.review_states.rejected,
      "Accepted for evidence attachment: " + m.review_states.accepted_for_evidence_attachment,
      "Decision coverage: " + rateText(m.decision_coverage),
      "Acceptance rate among recorded decisions: " + rateText(m.acceptance_rate_among_decisions),
      "Claims with merged integration receipts: " + m.integrated_claims,
      "Eligible Claims not integrated: " + m.eligible_claims_not_integrated,
      "Integration coverage: " + rateText(m.integration_coverage)
    ];
    lines.forEach(value => {
      const li = document.createElement("li");
      li.textContent = value;
      list.append(li);
    });
    const note = document.createElement("p");
    note.textContent = row.policy.interpretation;
    details.append(list,note);
  };
  input.addEventListener("change", async () => {
    try {
      const files = Array.from(input.files || []);
      if (!files.length || files.length > MAX_FILES) throw Error("Select between 1 and " + MAX_FILES + " JSON snapshots.");
      const values = [];
      for (const file of files) {
        if (!file.size || file.size > MAX_BYTES) throw Error("Each snapshot must be nonempty and no larger than 5 MiB.");
        values.push(validate(JSON.parse(await file.text())));
      }
      values.sort((a,b) => Date.parse(a.generated_at) - Date.parse(b.generated_at));
      const timestamps = values.map(x => Date.parse(x.generated_at));
      if (new Set(timestamps).size !== timestamps.length) throw Error("Duplicate snapshot timestamps are not allowed.");
      snapshots = values;
      status.classList.remove("is-error");
      status.textContent = "Loaded " + values.length + " validated read-only conversion snapshot(s).";
      render();
    } catch (error) {
      reset();
      status.classList.add("is-error");
      status.textContent = "Cannot load conversion snapshots: " + error.message;
    }
  });
  select.addEventListener("change",inspect);
  clear.addEventListener("click",reset);
})();
