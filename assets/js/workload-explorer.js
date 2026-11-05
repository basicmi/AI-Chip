(() => {
  const root = document.querySelector("[data-workload-explorer]");
  if (!root) return;
  const $ = (selector) => root.querySelector(selector);
  const search = $("[data-workload-search]");
  const kind = $("[data-workload-kind]");
  const platform = $("[data-workload-platform]");
  const status = $("[data-workload-status]");
  const cards = $("[data-workload-cards]");
  const load = $("[data-workload-load]");
  const labels = {
    integration_only: "Integration documented",
    vendor_reported: "Vendor reported",
    workload_tested: "Workload tested",
    benchmark_reported: "Benchmark reported",
    independently_benchmarked: "Independently benchmarked"
  };
  const categories = {
    llm_inference: "LLM inference",
    llm_training: "LLM training",
    model_porting: "Model porting",
    multimodal_inference: "Multimodal",
    retrieval: "Embedding & retrieval",
    generative_inference: "Generative inference",
    edge_inference: "Edge inference"
  };
  let db, compat, platformMap, integrationMap;
  const el = (tag, cls, value) => { const n = document.createElement(tag); if (cls) n.className = cls; if (value !== undefined) n.textContent = value; return n; };
  const option = (select, value, label) => { const n = el("option", "", label); n.value = value; select.append(n); };
  const safeUrl = (value) => { try { const u = new URL(value); return ["https:", "http:"].includes(u.protocol) ? u.href : null; } catch (_) { return null; } };
  const link = (url, label) => { const n = el("a", "", label); const href = safeUrl(url); if (href) { n.href = href; n.target = "_blank"; n.rel = "noopener noreferrer"; } return n; };
  const addTag = (parent, value) => parent.append(el("span", "compat-tag", value));
  const renderCatalog = () => {
    const target = document.querySelector("[data-workload-catalog]");
    db.workloads.forEach(w => {
      const card = el("article", "workload-definition-card");
      card.append(el("p", "eyebrow", categories[w.category] || w.category));
      card.append(el("h3", "", w.name));
      card.append(el("p", "workload-definition-description", w.description));
      const dims = el("div", "workload-definition-list");
      dims.append(el("strong", "", "Pin these dimensions"));
      const list = el("ul", "");
      w.key_dimensions.forEach(x => list.append(el("li", "", x)));
      dims.append(list);
      card.append(dims);
      const metrics = el("div", "workload-definition-list");
      metrics.append(el("strong", "", "Report these metrics"));
      const metricList = el("p", "workload-metric-list", w.metrics_to_report.join(" · "));
      metrics.append(metricList);
      card.append(metrics);
      target.append(card);
    });
  };
  const renderPath = path => {
    const p = platformMap.get(path.platform_id), w = db.workloads.find(x => x.id === path.workload_id);
    const card = el("article", "workload-path-card");
    const head = el("div", "workload-path-head");
    const title = el("div", "");
    title.append(el("p", "compat-vendor", p.vendor + " · " + p.name));
    title.append(el("h3", "", w.name));
    head.append(title);
    head.append(el("span", "status-pill status-" + path.status, labels[path.status] || path.status));
    card.append(head);
    card.append(el("p", "workload-path-scope", path.scope));
    const tags = el("div", "compat-tags");
    addTag(tags, categories[w.category] || w.category);
    path.integration_ids.forEach(id => {
      const i = integrationMap.get(id);
      if (i) addTag(tags, i.project + " · " + i.layer);
    });
    card.append(tags);
    const details = el("details", "compat-details");
    details.append(el("summary", "", "Configuration, limits & source integrations"));
    if (Object.keys(path.configuration || {}).length) {
      const config = el("dl", "compat-versions");
      Object.entries(path.configuration).forEach(([k,v]) => {
        const row = el("div", "compat-version-row");
        row.append(el("dt", "", k.replaceAll("_", " ")));
        row.append(el("dd", "", String(v)));
        config.append(row);
      });
      details.append(config);
    }
    details.append(el("p", "compat-limitations", path.limitations));
    const sourceList = el("ul", "compat-evidence-list");
    path.integration_ids.forEach(id => {
      const i = integrationMap.get(id);
      if (!i) return;
      const item = el("li", "");
      item.append(link(i.project_url, i.project + " — " + (labels[i.status] || i.status)));
      item.append(el("span", "compat-evidence-meta", "Checked " + i.last_checked + " · " + i.confidence + " confidence"));
      (i.evidence || []).forEach(ev => {
        const evidenceItem = el("div", "compat-evidence-meta");
        evidenceItem.append(link(ev.url, ev.claim + " · " + ev.checked_at));
        item.append(evidenceItem);
      });
      sourceList.append(item);
    });
    details.append(sourceList);
    if (path.metrics?.length) {
      details.append(el("h4", "compat-subheading", "Reported metrics"));
      path.metrics.forEach(m => details.append(el("p", "compat-limitations", m.name + ": " + m.value + " " + m.unit + " — " + m.evidence_type)));
    } else {
      details.append(el("p", "compat-evidence-meta", "No workload-specific performance measurements recorded."));
    }
    card.append(details);
    return card;
  };
  const render = () => {
    const q = search.value.trim().toLowerCase();
    const selectedKind = kind.value, selectedPlatform = platform.value, selectedStatus = status.value;
    const filtered = db.paths.filter(path => {
      if (selectedKind && path.workload_id !== selectedKind) return false;
      if (selectedPlatform && path.platform_id !== selectedPlatform) return false;
      if (selectedStatus && path.status !== selectedStatus) return false;
      const p = platformMap.get(path.platform_id), w = db.workloads.find(x => x.id === path.workload_id);
      const integrations = path.integration_ids.map(id => integrationMap.get(id)).filter(Boolean);
      const haystack = [p.vendor,p.name,w.name,w.description,path.scope,path.limitations,...integrations.map(i => i.project)].join(" ").toLowerCase();
      return !q || haystack.includes(q);
    });
    cards.replaceChildren(...filtered.map(renderPath));
    $("[data-workload-result-count]").textContent = String(filtered.length);
    $("[data-workload-result-summary]").textContent = filtered.length + " of " + db.paths.length + " candidate paths · no implied performance ranking";
    $("[data-workload-empty]").hidden = filtered.length > 0;
  };
  const reset = () => { search.value = ""; kind.value = ""; platform.value = ""; status.value = ""; render(); };
  [search,kind,platform,status].forEach(c => c.addEventListener(c === search ? "input" : "change", render));
  $("[data-workload-reset]").addEventListener("click", reset);
  Promise.all([
    fetch(root.dataset.source).then(r => { if (!r.ok) throw new Error("Workload data request failed: " + r.status); return r.json(); }),
    fetch(root.dataset.compatSource).then(r => { if (!r.ok) throw new Error("Compatibility data request failed: " + r.status); return r.json(); })
  ]).then(([workloads, compatibility]) => {
    db = workloads; compat = compatibility;
    platformMap = new Map(compat.platforms.map(p => [p.id,p]));
    integrationMap = new Map(compat.integrations.map(i => [i.id,i]));
    const byId = new Map(db.workloads.map(w => [w.id,w]));
    db.workloads.forEach(w => option(kind,w.id,w.name));
    compat.platforms.forEach(p => option(platform,p.id,p.vendor + " · " + p.name));
    Object.entries(labels).forEach(([k,v]) => option(status,k,v));
    const counts = [
      ["workloads",db.workloads.length],
      ["paths",db.paths.length],
      ["integration",db.paths.filter(p => p.status === "integration_only").length],
      ["vendor",db.paths.filter(p => p.status === "vendor_reported").length]
    ];
    counts.forEach(([key,value]) => { const n = document.querySelector('[data-workload-stat="' + key + '"]'); if (n) n.textContent = value; });
    document.querySelector("[data-workload-version]").textContent = db.database_version;
    document.querySelector("[data-workload-reviewed]").textContent = db.last_reviewed;
    renderCatalog();
    load.hidden = true;
    render();
  }).catch(error => { load.classList.add("is-error"); load.textContent = error.message; });
})();
