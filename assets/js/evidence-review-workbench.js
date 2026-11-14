(() => {
  "use strict";
  const root = document.querySelector("[data-evidence-workbench]");
  if (!root) return;
  const $ = selector => root.querySelector(selector);
  const ui = {
    claims: $("[data-ew-claims]"), graph: $("[data-ew-graph]"),
    status: $("[data-ew-status]"), provenance: $("[data-ew-provenance]"),
    search: $("[data-ew-search]"), topic: $("[data-ew-topic]"),
    publisher: $("[data-ew-publisher]"), relationship: $("[data-ew-relationship]"),
    results: $("[data-ew-results]"), empty: $("[data-ew-empty]"),
    count: $("[data-ew-result-count]"), summary: $("[data-ew-summary]")
  };
  let claimData = null, graphData = null;
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
    root.dispatchEvent(new CustomEvent("ew-clear-review"));
    ui.claims.value = "";
    ui.graph.value = "";
    ui.search.value = "";
    ui.topic.replaceChildren(element("option", "", "All topics"));
    ui.publisher.replaceChildren(element("option", "", "All publishers"));
    ui.topic.firstChild.value = "";
    ui.publisher.firstChild.value = "";
    ui.relationship.value = "";
    [ui.search, ui.topic, ui.publisher, ui.relationship].forEach(node => { node.disabled = true; });
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
    const matches = claimData.claims.filter(claim => {
      const rel = relations.get(claim.claim_id);
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
      claimData = claims;
      graphData = graph;
      root.dispatchEvent(new CustomEvent("ew-clear-review"));
      options(ui.topic, claims.claims.map(item => item.topic), "topics");
      options(ui.publisher, claims.claims.map(item => item.source?.publisher || item.source?.source_name || "Unknown source"), "publishers");
      [ui.search, ui.topic, ui.publisher, ui.relationship].forEach(node => { node.disabled = false; });
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
        " · All candidates stay unverified. Files remain in this browser session.";
      ui.provenance.hidden = false;
      status("Artifacts loaded locally. Nothing was uploaded or approved.");
      render();
    } catch (error) {
      claimData = null;
      graphData = null;
      root.dispatchEvent(new CustomEvent("ew-clear-review"));
      ui.results.replaceChildren();
      ui.empty.hidden = false;
      ["claims", "sources", "duplicates", "conflicts"].forEach(key => {
        $("[data-ew-stat='" + key + "']").textContent = "—";
      });
      [ui.search, ui.topic, ui.publisher, ui.relationship].forEach(node => { node.disabled = true; });
      ui.count.textContent = "0";
      status("Cannot load review artifact: " + error.message, true);
    }
  };
  ui.claims.addEventListener("change", load);
  ui.graph.addEventListener("change", load);
  ui.search.addEventListener("input", render);
  [ui.topic, ui.publisher, ui.relationship].forEach(node => node.addEventListener("change", render));
  $("[data-ew-reset]").addEventListener("click", clear);
  $("[data-ew-clear-filters]").addEventListener("click", () => {
    ui.search.value = ""; ui.topic.value = ""; ui.publisher.value = ""; ui.relationship.value = "";
    render();
  });
  clear();
})();