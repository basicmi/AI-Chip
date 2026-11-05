(() => {
  const root = document.querySelector("[data-compatibility-explorer]");
  if (!root) return;

  const source = root.dataset.source;
  const search = root.querySelector("[data-filter-search]");
  const platformFilter = root.querySelector("[data-filter-platform]");
  const layerFilter = root.querySelector("[data-filter-layer]");
  const statusFilter = root.querySelector("[data-filter-status]");
  const sortFilter = root.querySelector("[data-filter-sort]");
  const resetButton = root.querySelector("[data-filter-reset]");
  const results = root.querySelector("[data-results]");
  const count = root.querySelector("[data-result-count]");
  const cards = root.querySelector("[data-result-cards]");
  const state = root.querySelector("[data-load-state]");
  const statusLabels = {
    upstream_supported: "Upstream supported",
    vendor_plugin_supported: "Vendor plugin",
    vendor_framework: "Vendor framework",
    experimental: "Experimental",
    in_progress: "In progress",
    needs_review: "Needs review",
    vendor_reported: "Vendor reported"
  };
  const layerLabels = {
    framework: "Framework",
    compiler: "Compiler",
    kernel_dsl: "Kernel DSL",
    operator_library: "Operator library",
    serving: "Serving",
    communication: "Communication",
    runtime: "Runtime",
    model_porting: "Model porting",
    benchmark: "Benchmark",
    other: "Other"
  };
  let database = null;

  const make = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = String(text);
    return node;
  };
  const safeUrl = (value) => {
    try {
      const url = new URL(value, window.location.href);
      return url.protocol === "https:" || url.protocol === "http:" ? url.href : null;
    } catch (_) { return null; }
  };
  const addOption = (select, value, label) => {
    const option = make("option", "", label);
    option.value = value;
    select.append(option);
  };
  const searchableText = (entry, platform) => [
    platform.vendor, platform.name, ...(platform.hardware_scope || []),
    ...(platform.vendor_stack || []), entry.project, entry.layer, entry.status,
    entry.hardware_scope, JSON.stringify(entry.versions || {}), entry.limitations,
    ...(entry.evidence || []).map((item) => item.claim)
  ].join(" ").toLowerCase();

  const buildFilters = () => {
    const platforms = [...database.platforms].sort((a, b) => a.vendor.localeCompare(b.vendor));
    platforms.forEach((item) => addOption(platformFilter, item.id, item.vendor + " · " + item.name));
    const layers = [...new Set(database.integrations.map((item) => item.layer))].sort();
    layers.forEach((layer) => addOption(layerFilter, layer, layerLabels[layer] || layer));
    Object.keys(statusLabels).forEach((status) => addOption(statusFilter, status, statusLabels[status]));
  };

  const updateStats = () => {
    const documented = database.integrations.filter((item) =>
      ["upstream_supported", "vendor_plugin_supported", "vendor_framework"].includes(item.status)).length;
    const review = database.integrations.filter((item) =>
      ["experimental", "in_progress", "needs_review"].includes(item.status)).length;
    root.querySelector('[data-stat="platforms"]').textContent = database.platforms.length;
    root.querySelector('[data-stat="integrations"]').textContent = database.integrations.length;
    root.querySelector('[data-stat="documented"]').textContent = documented;
    root.querySelector('[data-stat="review"]').textContent = review;
    // Dataset metadata lives in the page heading, outside the explorer root.
    const databaseVersion = document.querySelector("[data-database-version]");
    const lastReviewed = document.querySelector("[data-last-reviewed]");
    if (!databaseVersion || !lastReviewed) {
      throw new Error("Compatibility page metadata elements are missing.");
    }
    databaseVersion.textContent = database.database_version || "Current snapshot";
    lastReviewed.textContent = database.last_reviewed || "Not specified";
  };

  const renderVersions = (versions) => {
    const list = make("dl", "compat-versions");
    Object.entries(versions || {}).forEach(([key, value]) => {
      const row = make("div", "compat-version-row");
      row.append(make("dt", "", key.replaceAll("_", " ")));
      row.append(make("dd", "", String(value)));
      list.append(row);
    });
    return list;
  };

  const renderCard = (entry, platform) => {
    const card = make("article", "compat-card");
    const top = make("div", "compat-card-top");
    const titleGroup = make("div", "compat-card-title");
    titleGroup.append(make("p", "compat-vendor", platform.vendor + " · " + platform.name));
    const projectLink = make("a", "compat-project", entry.project);
    const href = safeUrl(entry.project_url);
    if (href) {
      projectLink.href = href;
      projectLink.target = "_blank";
      projectLink.rel = "noopener noreferrer";
    }
    titleGroup.append(projectLink);
    top.append(titleGroup);
    top.append(make("span", "status-pill status-" + entry.status, statusLabels[entry.status] || entry.status));
    card.append(top);

    card.append(make("p", "compat-hardware", entry.hardware_scope));
    const tags = make("div", "compat-tags");
    tags.append(make("span", "compat-tag", layerLabels[entry.layer] || entry.layer));
    tags.append(make("span", "compat-tag", entry.maintainer_type.replaceAll("_", " ")));
    tags.append(make("span", "compat-confidence", "Evidence confidence: " + entry.confidence));
    card.append(tags);

    if (entry.versions && Object.keys(entry.versions).length) {
      card.append(make("h4", "compat-subheading", "Version pins"));
      card.append(renderVersions(entry.versions));
    }

    const details = make("details", "compat-details");
    const summary = make("summary", "", "Limitations & source evidence");
    details.append(summary);
    details.append(make("p", "compat-limitations", entry.limitations || "No limitations recorded."));
    const evidenceList = make("ul", "compat-evidence-list");
    (entry.evidence || []).forEach((evidence) => {
      const item = make("li", "");
      const link = make("a", "", evidence.claim || evidence.type);
      const evidenceUrl = safeUrl(evidence.url);
      if (evidenceUrl) {
        link.href = evidenceUrl;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
      }
      item.append(link);
      item.append(make("span", "compat-evidence-meta", (evidence.type || "source") + " · checked " + (evidence.checked_at || "date unavailable")));
      evidenceList.append(item);
    });
    details.append(evidenceList);
    card.append(details);
    return card;
  };

  const render = () => {
    const query = search.value.trim().toLowerCase();
    const platformId = platformFilter.value;
    const layer = layerFilter.value;
    const status = statusFilter.value;
    const filtered = database.integrations.filter((entry) => {
      const platform = database.platforms.find((item) => item.id === entry.platform_id);
      if (!platform) return false;
      if (platformId && entry.platform_id !== platformId) return false;
      if (layer && entry.layer !== layer) return false;
      if (status && entry.status !== status) return false;
      return !query || searchableText(entry, platform).includes(query);
    });

    filtered.sort((a, b) => {
      const pa = database.platforms.find((item) => item.id === a.platform_id);
      const pb = database.platforms.find((item) => item.id === b.platform_id);
      if (sortFilter.value === "project") return a.project.localeCompare(b.project);
      return (pa.vendor + a.project).localeCompare(pb.vendor + b.project);
    });

    cards.replaceChildren();
    filtered.forEach((entry) => {
      const platform = database.platforms.find((item) => item.id === entry.platform_id);
      cards.append(renderCard(entry, platform));
    });
    const message = filtered.length + " of " + database.integrations.length + " integration records";
    results.textContent = message;
    count.textContent = String(filtered.length);
    cards.hidden = filtered.length === 0;
    root.querySelector("[data-empty-state]").hidden = filtered.length !== 0;
  };

  const reset = () => {
    search.value = "";
    platformFilter.value = "";
    layerFilter.value = "";
    statusFilter.value = "";
    sortFilter.value = "vendor";
    render();
  };

  [search, platformFilter, layerFilter, statusFilter, sortFilter].forEach((control) => {
    control.addEventListener(control === search ? "input" : "change", render);
  });
  resetButton.addEventListener("click", reset);

  fetch(source, { headers: { "Accept": "application/json" } })
    .then((response) => {
      if (!response.ok) throw new Error("The compatibility data could not be loaded (HTTP " + response.status + ").");
      return response.json();
    })
    .then((data) => {
      if (!data || !Array.isArray(data.platforms) || !Array.isArray(data.integrations)) {
        throw new Error("The compatibility data has an unexpected structure.");
      }
      database = data;
      buildFilters();
      updateStats();
      state.hidden = true;
      render();
    })
    .catch((error) => {
      state.classList.add("is-error");
      state.textContent = error.message + " Open the raw JSON dataset on GitHub to inspect the current snapshot.";
      const link = make("a", "", "View compatibility.json");
      link.href = "https://github.com/basicmi/AI-Chip/blob/master/data/compatibility.json";
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      state.append(document.createTextNode(" "));
      state.append(link);
    });
})();
