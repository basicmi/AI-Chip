(() => {
  "use strict";
  const root = document.querySelector("[data-evidence-workbench]");
  if (!root) return;
  const $ = selector => root.querySelector(selector);
  const ui = {
    claims: $("[data-ew-claims]"), graph: $("[data-ew-graph]"), triage: $("[data-ew-triage]"), aging: $("[data-ew-aging]"),
    status: $("[data-ew-status]"), provenance: $("[data-ew-provenance]"),
    search: $("[data-ew-search]"), topic: $("[data-ew-topic]"),
    publisher: $("[data-ew-publisher]"), relationship: $("[data-ew-relationship]"),
    ageFilter: $("[data-ew-age-filter]"), stateFilter: $("[data-ew-state-filter]"),
    results: $("[data-ew-results]"), empty: $("[data-ew-empty]"),
    count: $("[data-ew-result-count]"), summary: $("[data-ew-summary]")
  };
  let claimData = null, graphData = null, triageData = null, agingData = null;
  const MAX_BYTES = 12 * 1024 * 1024;
  const element = (tag, cls = "", text) => {
    const node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text !== undefined) node.textContent = String(text);
    return node;
  };
  const safeUrl = value => {
    if (typeof value !== "string") return null;
    try {
      const url = new URL(value);
      return url.protocol === "https:" && !url.username && !url.password ? url.href : null;
    } catch (_) { return null; }
  };
  const status = (message, error = false) => {
    ui.status.textContent = message;
    ui.status.classList.toggle("is-error", error);
  };
  const clear = () => {
    claimData = null;
    graphData = null;
    triageData = null;
    agingData = null;
    root.dispatchEvent(new CustomEvent("ew-clear-review"));
    ui.claims.value = "";
    ui.graph.value = "";
    ui.triage.value = "";
    ui.aging.value = "";
    ui.search.value = "";
    ui.topic.replaceChildren(element("option", "", "All topics"));
    ui.publisher.replaceChildren(element("option", "", "All publishers"));
    ui.topic.firstChild.value = "";
    ui.publisher.firstChild.value = "";
    ui.relationship.value = "";
    ui.ageFilter.value = "";
    ui.stateFilter.value = "";
    $("[data-ew-aging-panel]").hidden = true;
    [ui.search, ui.topic, ui.publisher, ui.relationship, ui.ageFilter, ui.stateFilter].forEach(node => { node.disabled = true; });
    ui.provenance.hidden = true;
    ui.results.replaceChildren();
    ui.empty.hidden = false;
    ui.count.textContent = "0";
    ui.summary.textContent = "No review candidates loaded.";
    ["claims", "sources", "duplicates", "conflicts"].forEach(key => {
      $("[data-ew-stat='" + key + "']").textContent = "—";
    });
    status("Choose a Claim JSON file to begin.");
  };
  const validateClaims = data => {
    if (!data || data.schema_version !== "1.0" || !Array.isArray(data.claims) ||
        data.claims.length > 10000 || data.claim_count !== data.claims.length) {
      throw new Error("Expected PR #90 Claim JSON v1.0 with consistent claim_count (up to 10,000).");
    }
    const ids = new Set();
    for (const claim of data.claims) {
      if (!claim || typeof claim.claim_id !== "string" || ids.has(claim.claim_id) ||
          !claim.statement || typeof claim.statement !== "string" ||
          claim.review_status !== "unverified_candidate" || !safeUrl(claim.source?.url)) {
        throw new Error("Invalid, duplicate or already-approved Claim record.");
      }
      ids.add(claim.claim_id);
    }
    return data;
  };
  const validateGraph = (graph, claims) => {
    if (!graph || graph.schema_version !== "1.0" || !Array.isArray(graph.nodes) ||
        !Array.isArray(graph.edges) || !Array.isArray(graph.duplicate_clusters) ||
        !Array.isArray(graph.scoped_comparisons) || graph.input_claim_count !== claims.claims.length ||
        graph.summary?.independently_verified_claims !== 0) {
      throw new Error("Evidence Graph is invalid, mismatched or makes unsupported verification claims.");
    }
    const ids = new Set(claims.claims.map(item => item.claim_id));
    const graphClaims = graph.nodes.filter(item => item?.type === "claim_candidate");
    if (graphClaims.length !== ids.size ||
        graphClaims.some(item => !ids.has(item.claim_id) || item.review_status !== "unverified_candidate")) {
      throw new Error("Evidence Graph Claim IDs do not match the Claim report.");
    }
    for (const group of [...graph.duplicate_clusters, ...graph.scoped_comparisons]) {
      if (!Array.isArray(group?.claim_ids) || group.claim_ids.some(id => !ids.has(id)) ||
          group.independently_verified === true || group.independent_corroboration === true) {
        throw new Error("Evidence Graph relationships reference unknown claims or claim unsupported verification.");
      }
    }
    return graph;
  };
  const validateTriage = (data, claims) => {
    if (!data || data.schema_version !== "1.0" ||
        data.ranking_method !== "transparent_rule_based_v1" ||
        data.score_is_truth_confidence !== false ||
        data.summary?.automatically_verified !== 0 ||
        data.summary?.input_claims !== claims.claims.length ||
        !Array.isArray(data.queue)) {
      throw new Error("Triage JSON has incompatible version, claim counts or confidence policy.");
    }
    const ids = new Set(claims.claims.map(item => item.claim_id));
    const seen = new Set();
    for (const group of data.queue) {
      if (!group || !Array.isArray(group.related_claim_ids) ||
          group.related_claim_ids.length === 0 ||
          !ids.has(group.claim_id) || !Number.isFinite(group.score) ||
          group.review_status !== "unverified_candidate") {
        throw new Error("Invalid triage group or review status.");
      }
      for (const id of group.related_claim_ids) {
        if (!ids.has(id) || seen.has(id)) throw new Error("Invalid or repeated triage Claim ID.");
        seen.add(id);
      }
    }
    return data;
  };
  const VALID_REVIEW_STATES = new Set(["pending", "needs_more_evidence", "rejected", "accepted_for_evidence_attachment"]);
  const VALID_ALERTS = new Set(["within_7d", "overdue_7d", "overdue_14d", "overdue_30d", "follow_up_needed", "handled"]);
  const validateAging = (data, claims) => {
    if (!data || data.schema_version !== "1.0" || data.state_is_approval !== false ||
        data.observation_state !== "cache_persisted" ||
        !Array.isArray(data.claim_aging) || !Array.isArray(data.aging_backlog) ||
        !Array.isArray(data.queue) ||
        !data.summary || data.summary.tracked_current_claims !== claims.claims.length ||
        data.summary.tracked_backlog_claims !== data.claim_aging.length ||
        data.summary.unknown_first_seen_if_cache_reset !== true ||
        data.summary.backlog_not_observed_this_run !== data.claim_aging.length - claims.claims.length) {
      throw new Error("Incompatible review state snapshot or backlog counts.");
    }
    const currentIds = new Set(claims.claims.map(claim => claim.claim_id));
    const ids = new Set();
    for (const entry of data.claim_aging) {
      if (!entry || typeof entry.claim_id !== "string" || ids.has(entry.claim_id) ||
          typeof entry.observed_this_run !== "boolean" ||
          entry.observed_this_run !== currentIds.has(entry.claim_id) ||
          !Number.isSafeInteger(entry.days_since_first_seen) || entry.days_since_first_seen < 0 ||
          !VALID_REVIEW_STATES.has(entry.review_state) ||
          !VALID_ALERTS.has(entry.alert_level) || entry.review_is_factual_verification !== false ||
          !Number.isFinite(Date.parse(entry.first_seen_at)) ||
          !Number.isFinite(Date.parse(entry.last_seen_at)) ||
          Date.parse(entry.first_seen_at) > Date.parse(entry.last_seen_at)) {
        throw new Error("Malformed or contradictory persisted review state entry.");
      }
      ids.add(entry.claim_id);
    }
    if ([...currentIds].some(id => !ids.has(id))) throw new Error("Review snapshot missing current Claim IDs.");
    const pendingIds = new Set(data.claim_aging.filter(row =>
      row.review_state === "pending" || row.review_state === "needs_more_evidence").map(row => row.claim_id));
    const seenPending = new Set();
    for (const row of data.aging_backlog) {
      if (!row || !pendingIds.has(row.claim_id) || seenPending.has(row.claim_id)) {
        throw new Error("Unresolved backlog references invalid or handled claim IDs.");
      }
      seenPending.add(row.claim_id);
    }
    if (seenPending.size !== pendingIds.size) throw new Error("Unresolved backlog is incomplete.");
    for (const state of VALID_REVIEW_STATES) {
      const actual = data.claim_aging.filter(row => row.review_state === state).length;
      if (data.summary.review_states?.[state] !== actual) throw new Error("Review state summary is inconsistent.");
    }
    return data;
  };
  const renderBacklog = () => {
    const panel = $("[data-ew-aging-panel]");
    panel.hidden = !agingData;
    if (!agingData) return;
    const entries = agingData.claim_aging;
    const active = entries.filter(x => x.review_state === "pending" || x.review_state === "needs_more_evidence");
    const count = key => $("[data-ew-aging-count='" + key + "']");
    count("tracked").textContent = String(entries.length);
    count("seven").textContent = String(active.filter(x => x.days_since_first_seen >= 7).length);
    count("fourteen").textContent = String(active.filter(x => x.days_since_first_seen >= 14).length);
    count("thirty").textContent = String(active.filter(x => x.days_since_first_seen >= 30).length);
    $("[data-ew-aging-meta]").textContent =
      "Snapshot " + (agingData.generated_at || "unknown") +
      " · First observed in a best-effort Actions cache; eviction or changed Claim IDs can reset age. " +
      "These are operational review states, never verified facts.";
    const list = $("[data-ew-historical-list]");
    const historical = entries.filter(x => !x.observed_this_run);
    historical.sort((a,b) => b.days_since_first_seen - a.days_since_first_seen ||
      a.claim_id.localeCompare(b.claim_id));
    list.replaceChildren();
    for (const item of historical.slice(0, 100)) {
      const row = element("div", "ew-backlog-row");
      row.append(element("strong", "", item.claim_id));
      row.append(element("span", "", item.days_since_first_seen + " days · " + item.review_state +
        " · last observed " + item.last_seen_at));
      const url = safeUrl(item.source_url);
      if (url) {
        const link = element("a", "", "Original source ↗");
        link.href = url; link.target = "_blank"; link.rel = "noopener noreferrer";
        row.append(link);
      }
      list.append(row);
    }
    if (!historical.length) list.append(element("p", "", "No historical claims absent from this run."));
    $("[data-ew-historical-summary]").textContent =
      "Showing " + Math.min(100, historical.length) + " / " + historical.length +
      " previously observed records (historical details require their original Claim report).";
  };
  const readJson = async file => {
    if (!file || file.size === 0 || file.size > MAX_BYTES) {
      throw new Error("JSON files must be non-empty and at most 12 MiB.");
    }
    return JSON.parse(await file.text());
  };
  const makeRelations = () => {
    const map = new Map();
    if (!graphData) return map;
    const add = (id, kind, group) => {
      const row = map.get(id) || { duplicates: [], comparisons: [], conflicts: [] };
      row[kind].push(group);
      map.set(id, row);
    };
    for (const group of graphData.duplicate_clusters) {
      group.claim_ids.forEach(id => add(id, "duplicates", group));
    }
    for (const group of graphData.scoped_comparisons) {
      group.claim_ids.forEach(id => {
        add(id, "comparisons", group);
        if (group.status === "possible_specification_conflict") add(id, "conflicts", group);
      });
    }
    return map;
  };
  const addTag = (tags, text) => tags.append(element("span", "compat-tag", text));
  const renderCard = (claim, rel) => {
    const card = element("article", "model-support-card");
    const head = element("div", "model-support-card-head");
    const left = element("div");
    left.append(element("p", "compat-vendor",
      (claim.source?.publisher || claim.source?.source_name || "Unknown source") + " · " + (claim.topic || "unclassified")));
    left.append(element("h3", "", claim.statement));
    head.append(left, element("span", "status-pill", "Unverified · review required"));
    card.append(head);
    const tags = element("div", "compat-tags");
    addTag(tags, claim.claim_type || "unclassified");
    if (claim.value !== null && claim.value !== undefined) {
      addTag(tags, String(claim.value) + " " + (claim.unit || "unit unknown"));
    }
    if (claim.scope?.text) addTag(tags, claim.scope.text);
    const aging = agingData?.claim_aging.find(item => item.claim_id === claim.claim_id);
    if (aging) {
      addTag(tags, aging.days_since_first_seen + " days in review queue");
      addTag(tags, aging.review_state.replaceAll("_", " ") + " (workflow only)");
      if (aging.alert_level !== "within_7d" && aging.alert_level !== "handled")
        addTag(tags, "Aging alert: " + aging.alert_level);
    }
    (claim.qualifiers || []).slice(0, 5).forEach(value => addTag(tags, value));
    if (rel?.duplicates.length) addTag(tags, "Exact wording duplicate (not corroboration)");
    if (rel?.conflicts.length) addTag(tags, "Possible specification conflict");
    if (rel?.comparisons.length && !rel.conflicts.length) addTag(tags, "Reviewer-scoped comparison");
    card.append(tags);
    card.append(element("p", "compat-limitations", "Evidence excerpt: " + (claim.evidence_quote || claim.statement)));
    const meta = element("p", "compat-evidence-meta");
    const url = safeUrl(claim.source?.url);
    const sourceLink = element(url ? "a" : "span", "", "Open original source ↗");
    if (url) {
      sourceLink.href = url;
      sourceLink.target = "_blank";
      sourceLink.rel = "noopener noreferrer";
    }
    meta.append(sourceLink, element("span", "", " · Published " + (claim.source?.published_at || "unknown") +
      " · " + (claim.source?.evidence_scope || "scope unclassified")));
    card.append(meta);
    const details = element("details", "compat-details");
    details.append(element("summary", "", "Claim ID, evidence and review steps"));
    details.append(element("p", "", "Claim ID: " + claim.claim_id));
    details.append(element("p", "", "Extraction: " + (claim.extraction?.method || "unknown") +
      " · confidence " + (claim.extraction?.confidence || "unknown") + " (not a truth rating)"));
    (rel?.duplicates || []).forEach(group => details.append(element("p", "",
      "Exact statement duplicates: " + group.claim_ids.join(", ") + ". Not independent corroboration.")));
    (rel?.comparisons || []).forEach(group => details.append(element("p", "",
      "Reviewer context: " + group.subject_key + " / " + group.metric_key + " / " +
      group.context_key + " · " + group.status + " · not automatically verified.")));
    const gates = element("ul", "compat-evidence-list");
    (claim.review_gates || []).slice(0, 8).forEach(gate => gates.append(element("li", "", gate)));
    details.append(gates);
    card.append(details);
    const review = element("button", "text-button", "Review this claim");
    review.type = "button";
    review.dataset.ewReviewClaim = claim.claim_id;
    review.addEventListener("click", () => root.dispatchEvent(new CustomEvent("ew-select-claim", {detail: {claim}})));
    card.append(review);
    return card;
  };
  const render = () => {
    if (!claimData) return;
    const relations = makeRelations();
    const query = ui.search.value.trim().toLowerCase();
    const topic = ui.topic.value, publisher = ui.publisher.value, relationship = ui.relationship.value;
    const agingMap = new Map((agingData?.claim_aging || []).map(entry => [entry.claim_id, entry]));
    const age = ui.ageFilter.value, reviewState = ui.stateFilter.value;
    const matches = claimData.claims.filter(claim => {
      const rel = relations.get(claim.claim_id);
      const record = agingMap.get(claim.claim_id);
      if (reviewState && record?.review_state !== reviewState) return false;
      if (age && (!record || record.days_since_first_seen <
        (age === "overdue_30d" ? 30 : age === "overdue_14d" ? 14 : 7))) return false;
      if (topic && claim.topic !== topic) return false;
      if (publisher && (claim.source?.publisher || claim.source?.source_name || "Unknown source") !== publisher) return false;
      if (relationship === "duplicates" && !rel?.duplicates.length) return false;
      if (relationship === "conflicts" && !rel?.conflicts.length) return false;
      if (relationship === "comparisons" && !rel?.comparisons.length) return false;
      if (relationship === "standalone" && rel && (rel.duplicates.length || rel.comparisons.length)) return false;
      const haystack = [claim.statement, claim.topic, claim.claim_type, claim.unit,
        claim.source?.publisher, claim.source?.url, claim.evidence_quote].filter(Boolean).join(" ").toLowerCase();
      return !query || haystack.includes(query);
    });
    const priorities = new Map();
    if (triageData) {
      for (const group of triageData.queue) {
        for (const id of group.related_claim_ids) priorities.set(id, group.score);
      }
      matches.sort((a,b) => (priorities.get(b.claim_id) ?? -1) - (priorities.get(a.claim_id) ?? -1) ||
        a.claim_id.localeCompare(b.claim_id));
    }
    ui.results.replaceChildren(...matches.slice(0, 250).map(item => renderCard(item, relations.get(item.claim_id))));
    ui.count.textContent = String(matches.length);
    ui.summary.textContent = "Showing " + Math.min(250, matches.length) + " of " + matches.length +
      " matches (250-card display limit)";
    ui.empty.hidden = matches.length > 0;
    if (!matches.length) ui.empty.replaceChildren(element("strong", "", "No matching claims"),
      element("p", "", "Try different filters or check the uploaded report."));
  };
  const options = (select, values, label) => {
    select.replaceChildren();
    const all = element("option", "", "All " + label);
    all.value = "";
    select.append(all);
    [...new Set(values.filter(value => typeof value === "string" && value.trim()))].sort().forEach(value => {
      const option = element("option", "", value);
      option.value = value;
      select.append(option);
    });
  };
  const load = async () => {
    if (!ui.claims.files.length) { clear(); return; }
    status("Reading local artifacts…");
    try {
      const claims = validateClaims(await readJson(ui.claims.files[0]));
      const graph = ui.graph.files.length ? validateGraph(await readJson(ui.graph.files[0]), claims) : null;
      const triage = ui.triage.files.length ? validateTriage(await readJson(ui.triage.files[0]), claims) : null;
      const aging = ui.aging.files.length ? validateAging(await readJson(ui.aging.files[0]), claims) : null;
      claimData = claims;
      graphData = graph;
      triageData = triage;
      agingData = aging;
      root.dispatchEvent(new CustomEvent("ew-clear-review"));
      options(ui.topic, claims.claims.map(item => item.topic), "topics");
      options(ui.publisher, claims.claims.map(item => item.source?.publisher || item.source?.source_name || "Unknown source"), "publishers");
      [ui.search, ui.topic, ui.publisher, ui.relationship].forEach(node => { node.disabled = false; });
      [ui.ageFilter, ui.stateFilter].forEach(node => { node.disabled = !aging; node.value = ""; });
      renderBacklog();
      ui.search.value = "";
      ui.relationship.value = "";
      const sources = new Set(claims.claims.map(item => safeUrl(item.source.url)).filter(Boolean));
      $("[data-ew-stat='claims']").textContent = String(claims.claims.length);
      $("[data-ew-stat='sources']").textContent = String(sources.size);
      $("[data-ew-stat='duplicates']").textContent = graph ? String(graph.duplicate_clusters.length) : "—";
      $("[data-ew-stat='conflicts']").textContent = graph ?
        String(graph.scoped_comparisons.filter(item => item.status === "possible_specification_conflict").length) : "—";
      ui.provenance.textContent = "Claims generated " + (claims.generated_at || "unknown") +
        " · " + (graph ? "Graph generated " + (graph.generated_at || "unknown") :
          "No graph loaded: duplicate/conflict filters are unavailable") +
        " · " + (triage ? "Sorted by review urgency, not truth confidence" : "Default source order") +
        " · " + (aging ? "Persistent review snapshot loaded (not factual verification)" : "No aging snapshot loaded") +
        " · All candidates stay unverified. Files remain in this browser session.";
      ui.provenance.hidden = false;
      status("Artifacts loaded locally. Nothing was uploaded or approved.");
      render();
    } catch (error) {
      claimData = null;
      graphData = null;
      triageData = null;
      agingData = null;
      $("[data-ew-aging-panel]").hidden = true;
      root.dispatchEvent(new CustomEvent("ew-clear-review"));
      ui.results.replaceChildren();
      ui.empty.hidden = false;
      ["claims", "sources", "duplicates", "conflicts"].forEach(key => {
        $("[data-ew-stat='" + key + "']").textContent = "—";
      });
      [ui.search, ui.topic, ui.publisher, ui.relationship, ui.ageFilter, ui.stateFilter].forEach(node => { node.disabled = true; });
      ui.count.textContent = "0";
      status("Cannot load review artifact: " + error.message, true);
    }
  };
  ui.claims.addEventListener("change", load);
  ui.graph.addEventListener("change", load);
  ui.triage.addEventListener("change", load);
  ui.aging.addEventListener("change", load);
  ui.search.addEventListener("input", render);
  [ui.topic, ui.publisher, ui.relationship, ui.ageFilter, ui.stateFilter].forEach(node => node.addEventListener("change", render));
  $("[data-ew-reset]").addEventListener("click", clear);
  $("[data-ew-clear-filters]").addEventListener("click", () => {
    ui.search.value = ""; ui.topic.value = ""; ui.publisher.value = ""; ui.relationship.value = "";
    ui.ageFilter.value = ""; ui.stateFilter.value = "";
    render();
  });
  clear();
})();