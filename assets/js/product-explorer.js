(() => {
  const root = document.querySelector("[data-product-explorer]");
  if (!root) return;

  const source = root.dataset.source;
  const search = root.querySelector("[data-product-search]");
  const companyFilter = root.querySelector("[data-product-company]");
  const typeFilter = root.querySelector("[data-product-type]");
  const availabilityFilter = root.querySelector("[data-product-availability]");
  const precisionFilter = root.querySelector("[data-product-precision]");
  const resetButton = root.querySelector("[data-product-reset]");
  const results = root.querySelector("[data-product-results]");
  const empty = root.querySelector("[data-product-empty]");
  const count = root.querySelector("[data-product-count]");
  const compareCount = root.querySelector("[data-product-compare-count]");
  const compareNote = root.querySelector("[data-product-compare-note]");
  const compareEmpty = root.querySelector("[data-product-compare-empty]");
  const compareTable = root.querySelector("[data-product-compare-table]");
  const compareClear = root.querySelector("[data-product-compare-clear]");
  const version = document.querySelector("[data-product-version]");
  const reviewed = document.querySelector("[data-product-reviewed]");
  const selected = new Set();
  const topicLabels = {
    product_identity: "Product identity",
    architecture: "Architecture",
    process_node: "Process node",
    compute: "Compute",
    memory_capacity: "Memory capacity",
    memory_bandwidth: "Memory bandwidth",
    interconnect: "Interconnect",
    power: "Power",
    software_support: "Software support",
    availability: "Availability",
    deployment: "Deployment",
    performance: "Performance",
    memory_type: "Memory type",
    packaging: "Packaging",
    die_count: "Die count",
    form_factor: "Form factor",
    system_scale: "System scale",
    networking: "Networking",
    thermal: "Thermal",
    other: "Other"
  };
  const statusLabels = {
    announced: "Announced",
    sampling: "Sampling",
    shipping: "Shipping",
    production: "In production",
    roadmap: "Roadmap",
    discontinued: "Discontinued",
    unknown: "Status unknown"
  };
  const topicOrder = ["memory_capacity", "memory_bandwidth", "compute", "interconnect", "power"];
  let database = null;
  let products = [];

  const make = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = String(text);
    return node;
  };

  const safeUrl = (value) => {
    try {
      const url = new URL(value, window.location.href);
      return url.protocol === "https:" || url.protocol === "http:" ? url.href : "";
    } catch (_) {
      return "";
    }
  };

  const addLink = (parent, value, label, className) => {
    const href = safeUrl(value);
    if (!href) return;
    const link = make("a", className || "", label);
    link.href = href;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    parent.append(link);
  };

  const formatValue = (claim) => {
    if (claim.value === undefined || claim.value === null) return "—";
    return [claim.value, claim.unit].filter(Boolean).join(" ");
  };

  const contextLabel = (claim) => {
    const context = claim.metric_context || {};
    return [
      context.precision,
      context.sparsity && context.sparsity !== "not_applicable" ? context.sparsity.replaceAll("_", " ") : "",
      context.measurement_scope,
      context.metric_type
    ].filter(Boolean).join(" · ");
  };

  const claimForTopic = (product, topic) => product.claims.find(claim => claim.topic === topic);
  const keyClaims = (product) => {
    const picked = [];
    for (const topic of topicOrder) {
      const matches = product.claims.filter(claim => claim.topic === topic);
      if (topic === "compute") picked.push(...matches.slice(0, 2));
      else if (matches.length) picked.push(matches[0]);
    }
    return picked.slice(0, 6);
  };

  const populate = (select, values, labelFor = value => value) => {
    const first = select.options[0];
    select.replaceChildren(first);
    values.forEach(value => {
      const option = document.createElement("option");
      option.value = value.value;
      option.textContent = labelFor(value.label);
      select.append(option);
    });
  };

  const buildCard = (product) => {
    const card = make("article", "product-card");
    const head = make("div", "product-card-head");
    const vendor = make("div", "product-vendor");
    if (product.company.logo_url && safeUrl(product.company.logo_url)) {
      const logo = make("img", "product-vendor-logo");
      logo.src = safeUrl(product.company.logo_url);
      logo.alt = product.company.display_name;
      logo.loading = "lazy";
      vendor.append(logo);
    }
    const vendorText = make("div", "product-vendor-copy");
    vendorText.append(make("span", "product-vendor-category", product.company.category));
    vendorText.append(make("span", "product-vendor-name", product.company.display_name));
    vendor.append(vendorText);
    head.append(vendor);
    head.append(make("span", "product-status product-status-" + product.availability, statusLabels[product.availability] || product.availability));
    card.append(head);

    card.append(make("h3", "product-card-title", product.name));
    const metadata = [product.architecture, product.generation, product.process_node, product.form_factor].filter(Boolean);
    card.append(make("p", "product-card-meta", metadata.join(" · ") || "Architecture details not yet reviewed"));
    if (product.market_segment) card.append(make("p", "product-card-segment", product.market_segment));

    const tags = make("div", "product-tags");
    tags.append(make("span", "product-tag", product.product_type.toUpperCase()));
    if (product.family) tags.append(make("span", "product-tag", product.family));
    card.append(tags);

    const specs = make("div", "product-key-specs");
    const highlights = keyClaims(product);
    if (highlights.length) {
      highlights.forEach(claim => {
        const item = make("div", "product-key-spec");
        item.append(make("span", "product-key-label", topicLabels[claim.topic] || claim.topic));
        item.append(make("strong", "product-key-value", formatValue(claim)));
        const context = contextLabel(claim);
        if (context) item.append(make("small", "product-key-context", context));
        specs.append(item);
      });
    } else {
      specs.append(make("p", "product-no-specs", "No reviewed technical claims yet."));
    }
    card.append(specs);

    const actions = make("div", "product-card-actions");
    const compareButton = make("button", "button button-secondary product-compare-toggle",
      selected.has(product.id) ? "Added to comparison" : "Add to comparison");
    compareButton.type = "button";
    compareButton.dataset.compareProduct = product.id;
    compareButton.setAttribute("aria-pressed", selected.has(product.id) ? "true" : "false");
    compareButton.disabled = !selected.has(product.id) && selected.size >= 4;
    actions.append(compareButton);

    const details = make("details", "product-details");
    const summary = make("summary", "", "Specifications & sources (" + product.claims.length + " claims)");
    details.append(summary);
    const list = make("ul", "product-claim-list");
    product.claims.forEach(claim => {
      const item = make("li", "product-claim-item");
      const title = make("strong", "product-claim-value", formatValue(claim));
      item.append(title);
      item.append(make("span", "product-claim-topic", (topicLabels[claim.topic] || claim.topic) + (contextLabel(claim) ? " · " + contextLabel(claim) : "")));
      item.append(make("p", "product-claim-statement", claim.statement));
      if (claim.scope) item.append(make("p", "product-claim-scope", "Scope: " + claim.scope));
      const evidence = claim.evidence_ids.map(id => product.evidence.find(item => item.id === id)).filter(Boolean);
      if (evidence.length) {
        const links = make("div", "product-evidence-links");
        evidence.forEach(item => addLink(links, item.url, item.publisher + ": " + item.title, ""));
        item.append(links);
      }
      list.append(item);
    });
    details.append(list);
    actions.append(details);
    card.append(actions);
    return card;
  };

  const filteredProducts = () => {
    const query = search.value.trim().toLowerCase();
    return products.filter(product => {
      if (companyFilter.value && product.company.id !== companyFilter.value) return false;
      if (typeFilter.value && product.product_type !== typeFilter.value) return false;
      if (availabilityFilter.value && product.availability !== availabilityFilter.value) return false;
      if (precisionFilter.value && !product.claims.some(claim => claim.metric_context?.precision === precisionFilter.value)) return false;
      if (query) {
        const haystack = [
          product.name, product.company.display_name,
          product.architecture, product.generation, product.family, product.market_segment,
          ...product.claims.map(claim => claim.statement)
        ].filter(Boolean).join(" ").toLowerCase();
        if (!haystack.includes(query)) return false;
      }
      return true;
    });
  };

  const renderResults = () => {
    const matches = filteredProducts();
    results.replaceChildren();
    matches.forEach(product => results.append(buildCard(product)));
    count.textContent = matches.length + " of " + products.length + " products";
    empty.hidden = matches.length !== 0;
  };

  const comparisonKey = (claim) => {
    const context = claim.metric_context || {};
    return [
      claim.topic, claim.unit || "", context.metric_type || "unspecified",
      context.precision || "unspecified", context.sparsity || "unspecified",
      context.measurement_scope || "unspecified", context.operation || "unspecified"
    ].join("|");
  };

  const comparisonLabel = (claim) => {
    const context = claim.metric_context || {};
    const details = [
      context.precision,
      context.sparsity && context.sparsity !== "not_applicable" ? context.sparsity.replaceAll("_", " ") : "",
      context.measurement_scope,
      context.metric_type
    ].filter(Boolean);
    return {
      topic: topicLabels[claim.topic] || claim.topic,
      context: details.join(" · ") || claim.scope || "Scope not specified",
      unit: claim.unit || ""
    };
  };

  const renderCompareCell = (product, claim) => {
    const cell = make("td", "product-compare-cell");
    if (!claim) {
      cell.append(make("span", "product-compare-missing", "—"));
      return cell;
    }
    cell.append(make("strong", "product-compare-value", formatValue(claim)));
    const status = make("small", "product-compare-status", claim.claim_status.replaceAll("_", " "));
    cell.append(status);
    const evidence = claim.evidence_ids.map(id => product.evidence.find(item => item.id === id)).filter(Boolean);
    if (evidence.length) {
      const links = make("div", "product-compare-sources");
      evidence.forEach(item => addLink(links, item.url, item.publisher, ""));
      cell.append(links);
    }
    return cell;
  };

  const renderCompare = () => {
    const chosen = products.filter(product => selected.has(product.id));
    compareCount.textContent = chosen.length + " / 4 selected";
    compareEmpty.hidden = chosen.length > 0;
    compareTable.hidden = chosen.length === 0;
    compareTable.replaceChildren();

    if (!chosen.length) {
      compareNote.textContent = "Select two to four products from the catalogue. Metrics are aligned only when their topic, precision, sparsity, scope, measurement type and unit match; unmatched values remain separate.";
      return;
    }

    const rows = new Map();
    chosen.forEach(product => product.claims.forEach(claim => {
      const key = comparisonKey(claim);
      if (!rows.has(key)) rows.set(key, { label: comparisonLabel(claim), cells: new Map() });
      rows.get(key).cells.set(product.id, claim);
    }));
    const rowValues = [...rows.values()].sort((a, b) =>
      (topicLabels[a.label.topic] || a.label.topic).localeCompare(topicLabels[b.label.topic] || b.label.topic) ||
      a.label.context.localeCompare(b.label.context)
    );
    const sharedRows = rowValues.filter(row => chosen.every(product => row.cells.has(product.id))).length;
    compareNote.textContent = chosen.length + " products selected · " + sharedRows +
      " metric rows have identical precision, sparsity, scope, measurement type and unit across all selected products. Other values remain separate; no ranking is generated.";

    const table = make("table", "product-compare-table");
    const thead = make("thead");
    const header = make("tr");
    header.append(make("th", "", "Metric / context"));
    chosen.forEach(product => header.append(make("th", "", product.name)));
    thead.append(header);
    table.append(thead);

    const tbody = make("tbody");
    rowValues.forEach(row => {
      const tr = make("tr");
      const label = make("th", "product-compare-metric");
      label.scope = "row";
      label.append(make("strong", "", row.label.topic));
      label.append(make("small", "", row.label.context + (row.label.unit ? " · " + row.label.unit : "")));
      tr.append(label);
      chosen.forEach(product => tr.append(renderCompareCell(product, row.cells.get(product.id))));
      tbody.append(tr);
    });
    table.append(tbody);
    compareTable.append(table);
  };

  const render = () => {
    renderResults();
    renderCompare();
  };

  const load = async () => {
    try {
      const response = await fetch(source, { cache: "no-cache" });
      if (!response.ok) throw new Error("HTTP " + response.status);
      database = await response.json();
      const companies = Array.isArray(database.companies) ? database.companies : [];
      products = companies.flatMap(company => (company.products || []).map(product => {
        const claims = (company.claims || []).filter(claim =>
          product.claim_ids.includes(claim.id) &&
          claim.subject_type === "product" &&
          claim.subject_id === product.id
        );
        return { ...product, company, claims, evidence: company.evidence || [] };
      }));

      version.textContent = database.database_version || database.schema_version || "—";
      reviewed.textContent = database.registry_reviewed_at || "—";
      root.querySelector('[data-product-stat="companies"]').textContent = companies.length;
      root.querySelector('[data-product-stat="products"]').textContent = products.length;
      root.querySelector('[data-product-stat="claims"]').textContent =
        companies.reduce((sum, company) => sum + (company.claims?.length || 0), 0);
      root.querySelector('[data-product-stat="evidence"]').textContent =
        companies.reduce((sum, company) => sum + (company.evidence?.length || 0), 0);

      populate(companyFilter, companies
        .filter(company => products.some(product => product.company.id === company.id))
        .sort((a, b) => a.display_name.localeCompare(b.display_name))
        .map(company => ({ value: company.id, label: company.display_name })));
      populate(typeFilter, [...new Set(products.map(product => product.product_type))].sort()
        .map(value => ({ value, label: value.toUpperCase() })));
      populate(availabilityFilter, [...new Set(products.map(product => product.availability))].sort()
        .map(value => ({ value, label: statusLabels[value] || value })));
      populate(precisionFilter, [...new Set(products.flatMap(product =>
        product.claims.map(claim => claim.metric_context?.precision).filter(value => value && !["unspecified", "not_applicable"].includes(value))
      ))].sort().map(value => ({ value, label: value })));

      root.dataset.loaded = "true";
      render();
    } catch (error) {
      root.dataset.loaded = "false";
      count.textContent = "Product registry unavailable: " + error.message;
      empty.hidden = false;
      empty.querySelector("strong").textContent = "Unable to load product records";
      empty.querySelector("p").textContent = "Check the raw registry or try again later.";
    }
  };

  [search, companyFilter, typeFilter, availabilityFilter, precisionFilter].forEach(control => {
    control.addEventListener(control.tagName === "INPUT" ? "input" : "change", render);
  });
  resetButton.addEventListener("click", () => {
    search.value = "";
    companyFilter.value = "";
    typeFilter.value = "";
    availabilityFilter.value = "";
    precisionFilter.value = "";
    render();
  });
  compareClear.addEventListener("click", () => {
    selected.clear();
    render();
  });
  root.addEventListener("click", event => {
    const button = event.target.closest("[data-compare-product]");
    if (!button) return;
    const id = button.dataset.compareProduct;
    if (selected.has(id)) selected.delete(id);
    else if (selected.size < 4) selected.add(id);
    else {
      compareNote.textContent = "You can compare up to four products at a time. Remove one product before adding another.";
      return;
    }
    render();
  });

  load();
})();
