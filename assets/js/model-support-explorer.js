(() => {
  const root = document.querySelector("[data-model-support-explorer]");
  if (!root) return;
  const $ = selector => root.querySelector(selector);
  const search = $("[data-model-search]");
  const platformFilter = $("[data-model-platform]");
  const levelFilter = $("[data-model-level]");
  const publisherFilter = $("[data-model-publisher]");
  const cards = $("[data-model-cards]");
  const load = $("[data-model-load]");
  const labels = {
    documented_recipe: "Documented recipe",
    upstream_verified: "Upstream verified",
    vendor_reported: "Vendor reported",
    independently_tested: "Independently tested",
    integration_only: "Integration only"
  };
  let database, products = new Map(), platforms = new Map(), integrations = new Map();
  const el = (tag, cls, value) => {
    const node = document.createElement(tag);
    if (cls) node.className = cls;
    if (value !== undefined) node.textContent = value;
    return node;
  };
  const safeUrl = value => {
    try {
      const url = new URL(value);
      return ["https:", "http:"].includes(url.protocol) ? url.href : null;
    } catch (_) { return null; }
  };
  const link = (url, label) => {
    const node = el("a", "", label);
    const href = safeUrl(url);
    if (href) {
      node.href = href;
      node.target = "_blank";
      node.rel = "noopener noreferrer";
    }
    return node;
  };
  const tag = (parent, value) => parent.append(el("span", "compat-tag", value));
  const renderCard = path => {
    const model = database.models.find(item => item.id === path.model_id);
    const platform = platforms.get(path.platform_id);
    const card = el("article", "model-support-card");
    const head = el("div", "model-support-card-head");
    const copy = el("div", "");
    copy.append(el("p", "compat-vendor", model.publisher + " · " + model.family));
    copy.append(el("h3", "", model.display_name));
    copy.append(el("p", "model-support-id", model.model_id));
    head.append(copy);
    head.append(el("span", "status-pill status-" + path.support_level, labels[path.support_level] || path.support_level));
    card.append(head);

    const productNames = path.product_ids.map(id => {
      const item = products.get(id);
      return item ? item.name : id;
    });
    card.append(el("p", "model-support-hardware", (platform?.vendor || platform?.name || path.platform_id) +
      " · " + productNames.join(" / ")));
    card.append(el("p", "model-support-stack", path.software_stack));

    const tags = el("div", "compat-tags");
    path.precision_modes.forEach(value => tag(tags, value));
    path.execution_modes.forEach(value => tag(tags, value));
    card.append(tags);

    const details = el("details", "compat-details");
    details.append(el("summary", "", "Configuration, limitations & evidence"));
    details.append(el("p", "model-support-scope", path.hardware_scope));
    details.append(el("p", "model-support-quantization", "Quantization: " + path.quantization));
    details.append(el("p", "compat-limitations", path.limitations));
    if (path.integration_ids.length) {
      const stackList = el("ul", "compat-evidence-list");
      path.integration_ids.forEach(id => {
        const integration = integrations.get(id);
        if (!integration) return;
        const item = el("li", "");
        item.append(link(integration.project_url, integration.project + " · " + (integration.status || "")));
        item.append(el("span", "compat-evidence-meta", integration.hardware_scope));
        stackList.append(item);
      });
      details.append(stackList);
    }
    const evidenceList = el("ul", "compat-evidence-list");
    path.evidence.forEach(source => {
      const item = el("li", "");
      item.append(link(source.url, source.publisher + " — " + source.claim));
      item.append(el("span", "compat-evidence-meta", "Checked " + source.checked_at + " · " + source.type));
      evidenceList.append(item);
    });
    details.append(evidenceList);
    card.append(details);
    return card;
  };
  const render = () => {
    const query = search.value.trim().toLowerCase();
    const selectedPlatform = platformFilter.value;
    const selectedLevel = levelFilter.value;
    const selectedPublisher = publisherFilter.value;
    const matches = database.support_paths.filter(path => {
      if (selectedPlatform && path.platform_id !== selectedPlatform) return false;
      if (selectedLevel && path.support_level !== selectedLevel) return false;
      const model = database.models.find(item => item.id === path.model_id);
      if (selectedPublisher && model.publisher !== selectedPublisher) return false;
      const platform = platforms.get(path.platform_id);
      const hardware = path.product_ids.map(id => products.get(id)?.name || id);
      const sourceText = path.evidence.map(item => item.publisher + " " + item.claim).join(" ");
      const haystack = [model.display_name, model.model_id, model.publisher, platform?.vendor, platform?.name,
        ...hardware, path.software_stack, path.precision_modes.join(" "), path.execution_modes.join(" "),
        path.hardware_scope, sourceText].join(" ").toLowerCase();
      return !query || haystack.includes(query);
    });
    cards.replaceChildren(...matches.map(renderCard));
    $("[data-model-result-count]").textContent = String(matches.length);
    $("[data-model-result-summary]").textContent = matches.length + " of " +
      database.support_paths.length + " documented paths · no performance ranking implied";
    $("[data-model-empty]").hidden = matches.length > 0;
  };
  const initialize = ([models, profileDb, compatibility]) => {
    database = models;
    profileDb.companies.forEach(company => company.products.forEach(product => {
      products.set(product.id, { ...product, company: company.display_name });
    }));
    compatibility.platforms.forEach(platform => platforms.set(platform.id, platform));
    compatibility.integrations.forEach(integration => integrations.set(integration.id, integration));
    const levels = Object.keys(database.support_levels);
    [...new Set(database.models.map(model => model.publisher))].sort().forEach(publisher => {
      const option = el("option", "", publisher);
      option.value = publisher;
      publisherFilter.append(option);
    });
    levels.forEach(level => {
      const option = el("option", "", labels[level] || level);
      option.value = level;
      levelFilter.append(option);
    });
    [...new Set(database.support_paths.map(path => path.platform_id))].forEach(id => {
      const platform = platforms.get(id);
      const option = el("option", "", platform ? platform.vendor + " · " + platform.name : id);
      option.value = id;
      platformFilter.append(option);
    });
    // Registry metadata lives in the page heading, outside the explorer root.
    const versionNode = document.querySelector("[data-model-support-version]");
    const reviewedNode = document.querySelector("[data-model-support-reviewed]");
    if (!versionNode || !reviewedNode) {
      throw new Error("Model support page metadata elements are missing from the document");
    }
    versionNode.textContent = database.database_version;
    reviewedNode.textContent = database.last_reviewed;
    $("[data-model-stat=\"models\"]").textContent = String(database.models.length);
    $("[data-model-stat=\"paths\"]").textContent = String(database.support_paths.length);
    $("[data-model-stat=\"recipes\"]").textContent = String(database.support_paths.filter(path => path.support_level === "documented_recipe").length);
    $("[data-model-stat=\"upstream\"]").textContent = String(database.support_paths.filter(path => path.support_level === "upstream_verified").length);
    search.addEventListener("input", render);
    platformFilter.addEventListener("change", render);
    levelFilter.addEventListener("change", render);
    publisherFilter.addEventListener("change", render);
    $("[data-model-reset]").addEventListener("click", () => {
      search.value = "";
      platformFilter.value = "";
      levelFilter.value = "";
      publisherFilter.value = "";
      render();
    });
    render();
    load.hidden = true;
  };
  Promise.all([root.dataset.source, root.dataset.productSource, root.dataset.compatSource].map(url =>
    fetch(url).then(response => {
      if (!response.ok) throw new Error("Request failed: " + response.status);
      return response.json();
    })
  )).then(initialize).catch(error => {
    load.classList.add("is-error");
    load.textContent = "Model support explorer initialization failed: " + error.message;
    root.dataset.loadError = "true";
  });
})();
