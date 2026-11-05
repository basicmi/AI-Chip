(() => {
  const root = document.querySelector("[data-benchmark-results]");
  if (!root) return;

  const $ = (selector) => root.querySelector(selector);
  const search = $("[data-results-search]");
  const filters = {
    source: $("[data-results-source]"),
    vendor: $("[data-results-vendor]"),
    model: $("[data-results-model]"),
    scenario: $("[data-results-scenario]"),
    availability: $("[data-results-availability]"),
    division: $("[data-results-division]"),
    system: $("[data-results-system]")
  };
  const rowsNode = $("[data-results-rows]");
  const load = $("[data-results-load]");
  const pageSize = 50;
  let database = null;
  let currentPage = 1;
  let filteredRecords = [];

  const make = (tag, className, content) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (content !== undefined && content !== null) node.textContent = String(content);
    return node;
  };

  const safeUrl = (value) => {
    try {
      const url = new URL(value);
      return ["https:", "http:"].includes(url.protocol) ? url.href : "";
    } catch (_) {
      return "";
    }
  };

  const addLink = (parent, value, label) => {
    const href = safeUrl(value);
    if (!href) return;
    const link = make("a", "benchmark-result-link", label);
    link.href = href;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    parent.append(link);
  };

  const setText = (selector, value) => {
    const node = document.querySelector(selector);
    if (node) node.textContent = String(value);
  };

  const numberText = (value) => {
    if (typeof value !== "number" || !Number.isFinite(value)) return "—";
    return new Intl.NumberFormat("en-US", { maximumSignificantDigits: 5 }).format(value);
  };

  const sourceMap = () => new Map(database.sources.map(source => [source.id, source]));

  const populate = (select, values, labelFor = value => value) => {
    const first = select.options[0];
    select.replaceChildren(first);
    [...new Set(values.filter(value => value !== null && value !== undefined && String(value) !== ""))]
      .sort((a, b) => String(a).localeCompare(String(b)))
      .forEach(value => {
        const option = document.createElement("option");
        option.value = String(value);
        option.textContent = labelFor(value);
        select.append(option);
      });
  };

  const metricSummary = (record) => {
    const metrics = record.metrics || {};
    const preferred = [
      ["output_tput_per_gpu", "output tok/s/GPU"],
      ["median_intvty", "median inter-token latency (s)"],
      ["p99_ttft", "p99 TTFT (s)"],
      ["p99_tpot", "p99 TPOT (s)"],
      ["p99_itl", "p99 ITL (s)"]
    ];
    const items = preferred
      .filter(([key]) => typeof metrics[key] === "number")
      .slice(0, 3)
      .map(([key, label]) => label + ": " + numberText(metrics[key]));
    return items.length ? items.join(" · ") : Object.keys(metrics).length + " scalar metrics";
  };

  const resultText = (record) => {
    if (typeof record.result_value === "number") {
      return numberText(record.result_value) + (record.result_unit ? " " + record.result_unit : "");
    }
    if (record.metrics && Object.keys(record.metrics).length) return metricSummary(record);
    return "Metric not provided";
  };

  const addDetailLine = (parent, label, value) => {
    if (value === null || value === undefined || value === "") return;
    const line = make("p", "benchmark-detail-line");
    line.append(make("strong", "", label + ": "));
    line.append(document.createTextNode(String(value)));
    parent.append(line);
  };

  const buildDetails = (record) => {
    const details = make("details", "benchmark-result-details");
    details.append(make("summary", "", "Configuration & source"));
    const body = make("div", "benchmark-result-detail-body");
    const system = record.system || {};
    const software = record.software || {};
    const workload = record.workload || {};
    const configuration = record.configuration || {};

    addDetailLine(body, "Benchmark", record.benchmark_suite + " " + (record.benchmark_version || ""));
    addDetailLine(body, "Division / availability", record.division + " / " + record.availability);
    addDetailLine(body, "System", record.system_name);
    addDetailLine(body, "Accelerator", system.accelerator_model || system.hardware || "Not separately specified");
    addDetailLine(body, "Accelerator count", system.total_accelerators || [
      system.physical_prefill_gpus, system.physical_decode_gpus
    ].filter(value => value !== null && value !== undefined).join(" prefill / ") || "");
    addDetailLine(body, "Host CPU", system.host_processor_model);
    addDetailLine(body, "Nodes", system.nodes);
    addDetailLine(body, "Framework", software.framework);
    addDetailLine(body, "Operating system", software.operating_system);
    addDetailLine(body, "Container image", software.image);
    addDetailLine(body, "Recipe fingerprint", software.recipe_fingerprint);
    addDetailLine(body, "Accuracy / quality", record.accuracy_text);
    addDetailLine(body, "Weight data types / precision", record.weight_data_types || workload.precision);
    addDetailLine(body, "Workload configuration", [
      workload.isl !== undefined && workload.isl !== null ? "ISL " + workload.isl : "",
      workload.osl !== undefined && workload.osl !== null ? "OSL " + workload.osl : "",
      workload.concurrency !== undefined && workload.concurrency !== null ? "Concurrency " + workload.concurrency : "",
      workload.benchmark_type || "",
      workload.speculative_method ? "Speculative decoding " + workload.speculative_method : ""
    ].filter(Boolean).join(" · "));
    addDetailLine(body, "Parallelism", Object.entries(configuration)
      .filter(([key]) => ["prefill_tp", "prefill_ep", "decode_tp", "decode_ep", "offload_mode"].includes(key))
      .map(([key, value]) => key + "=" + value).join(" · "));
    if (record.metrics && Object.keys(record.metrics).length) {
      const metrics = Object.entries(record.metrics)
        .map(([key, value]) => key + ": " + numberText(value))
        .join(" · ");
      addDetailLine(body, "Metrics", metrics);
    }
    addDetailLine(body, "Notes", record.notes);
    addDetailLine(body, "Source record key", record.source_record_key);
    if (record.inferred) body.append(make("p", "benchmark-result-warning", "This submission is marked as inferred by the source."));
    if (record.power_metrics_available) {
      body.append(make("p", "benchmark-result-power", "The source marks this record as containing power metrics. Check the source-specific validation semantics before comparison."));
    } else {
      body.append(make("p", "benchmark-result-warning", "No measured power metric is available in this record. Design power, if present, is not measured power."));
    }
    const links = make("div", "benchmark-result-detail-links");
    addLink(links, record.source_url || record.dataset_url, "Publisher result / source ↗");
    if (record.detail_url && record.detail_url !== record.source_url) {
      addLink(links, record.detail_url, "Producer run ↗");
    }
    if (record.release_url) addLink(links, record.release_url, "Benchmark release ↗");
    body.append(links);
    details.append(body);
    return details;
  };

  const buildRow = (record) => {
    const row = document.createElement("tr");
    row.dataset.resultId = record.id;

    const submitter = document.createElement("td");
    submitter.append(make("strong", "benchmark-submitter", record.submitter));
    submitter.append(make("small", "benchmark-source-class", record.source_class.replaceAll("_", " ")));
    row.append(submitter);

    const accelerator = document.createElement("td");
    accelerator.append(make("strong", "benchmark-accelerator", record.system?.accelerator_model || record.system?.hardware || "Accelerator not specified"));
    accelerator.append(make("small", "benchmark-system-name", record.system_name));
    if (record.accelerator_vendor) accelerator.append(make("span", "benchmark-vendor-tag", record.accelerator_vendor));
    row.append(accelerator);

    const workload = document.createElement("td");
    workload.append(make("strong", "benchmark-model", record.model));
    workload.append(make("small", "benchmark-scenario", record.scenario));
    row.append(workload);

    const result = document.createElement("td");
    result.append(make("strong", "benchmark-result-value", resultText(record)));
    if (record.inferred) result.append(make("span", "benchmark-inferred-tag", "Inferred"));
    row.append(result);

    const evidence = document.createElement("td");
    const status = make("span", "benchmark-status benchmark-status-" + record.availability, record.availability);
    evidence.append(status);
    evidence.append(make("small", "benchmark-division", record.division + " · " + record.system_type));
    evidence.append(buildDetails(record));
    row.append(evidence);
    return row;
  };

  const renderSourceCards = () => {
    const container = $("[data-results-source-cards]");
    const map = sourceMap();
    container.replaceChildren();
    database.sources.forEach(source => {
      const card = make("article", "benchmark-source-card");
      const header = make("div", "benchmark-source-card-header");
      header.append(make("h3", "", source.name));
      header.append(make("span", "benchmark-source-count", (source.record_count || 0) + " rows"));
      card.append(header);
      card.append(make("p", "benchmark-source-publisher", source.publisher + " · " + source.source_class.replaceAll("_", " ")));
      card.append(make("p", "benchmark-source-notes", source.notes));
      const links = make("div", "benchmark-result-detail-links");
      addLink(links, source.results_url, source.record_count ? "Published results ↗" :
        (source.id === "mlperf-power" ? "Methodology ↗" : "Overview ↗"));
      if (source.dataset_url) addLink(links, source.dataset_url, "Raw data ↗");
      else if (source.api_url) addLink(links, source.api_url, "Public API ↗");
      card.append(links);
      if (!source.record_count) {
        card.append(make("p", "benchmark-result-warning", "No rows are cached in this snapshot. The repository importer supports this public source; it is not silently treated as zero performance."));
      }
      container.append(card);
    });
  };

  const applyFilters = () => {
    if (!database) return;
    const query = search.value.trim().toLowerCase();
    filteredRecords = database.records.filter(record => {
      if (filters.source.value && record.source_id !== filters.source.value) return false;
      if (filters.vendor.value && (record.accelerator_vendor || "Not specified") !== filters.vendor.value) return false;
      if (filters.model.value && record.model !== filters.model.value) return false;
      if (filters.scenario.value && record.scenario !== filters.scenario.value) return false;
      if (filters.availability.value && record.availability !== filters.availability.value) return false;
      if (filters.division.value && record.division !== filters.division.value) return false;
      if (filters.system.value && record.system_type !== filters.system.value) return false;
      const searchable = [
        record.submitter, record.accelerator_vendor, record.system_name,
        record.system?.accelerator_model, record.system?.hardware,
        record.model, record.scenario, record.division, record.availability,
        record.software?.framework, record.software?.operating_system,
        record.notes, record.accuracy_text, record.benchmark_suite
      ].join(" ").toLowerCase();
      return !query || searchable.includes(query);
    });
    currentPage = 1;
    renderRows();
  };

  const renderRows = () => {
    const totalPages = Math.max(1, Math.ceil(filteredRecords.length / pageSize));
    currentPage = Math.min(currentPage, totalPages);
    const start = (currentPage - 1) * pageSize;
    const pageRecords = filteredRecords.slice(start, start + pageSize);
    rowsNode.replaceChildren(...pageRecords.map(buildRow));
    $("[data-results-count]").textContent = String(filteredRecords.length);
    $("[data-results-summary]").textContent = filteredRecords.length
      ? "Showing " + (start + 1) + "–" + Math.min(start + pageSize, filteredRecords.length) +
        " of " + filteredRecords.length + " filtered records · no cross-suite ranking"
      : "No records match the current filters.";
    $("[data-results-empty]").hidden = filteredRecords.length > 0;
    $("[data-results-page]").textContent = "Page " + currentPage + " of " + totalPages;
    $("[data-results-prev]").disabled = currentPage <= 1;
    $("[data-results-next]").disabled = currentPage >= totalPages;
  };

  const reset = () => {
    search.value = "";
    Object.values(filters).forEach(select => { select.value = ""; });
    applyFilters();
  };

  Object.values(filters).forEach(select => select.addEventListener("change", applyFilters));
  search.addEventListener("input", applyFilters);
  $("[data-results-reset]").addEventListener("click", reset);
  $("[data-results-prev]").addEventListener("click", () => {
    if (currentPage > 1) { currentPage -= 1; renderRows(); }
  });
  $("[data-results-next]").addEventListener("click", () => {
    if (currentPage * pageSize < filteredRecords.length) { currentPage += 1; renderRows(); }
  });

  fetch(root.dataset.source, { cache: "no-cache" })
    .then(response => {
      if (!response.ok) throw new Error("Benchmark results request failed: HTTP " + response.status);
      return response.json();
    })
    .then(data => {
      if (!Array.isArray(data.records) || !Array.isArray(data.sources) || !data.summary) {
        throw new Error("Benchmark results registry has an invalid structure.");
      }
      database = data;
      const sources = sourceMap();
      populate(filters.source, data.sources.map(source => source.id),
        id => (sources.get(id)?.name || id));
      populate(filters.vendor, data.records.map(record => record.accelerator_vendor || "Not specified"));
      populate(filters.model, data.records.map(record => record.model));
      populate(filters.scenario, data.records.map(record => record.scenario));
      populate(filters.availability, data.records.map(record => record.availability));
      populate(filters.division, data.records.map(record => record.division));
      populate(filters.system, data.records.map(record => record.system_type));

      setText("[data-results-version]", data.database_version || "—");
      setText("[data-results-imported]", data.last_imported_at || "—");
      setText('[data-results-stat="total"]', data.summary.total_records);
      setText('[data-results-stat="available"]', data.summary.by_availability?.available || 0);
      setText('[data-results-stat="inferred"]', data.summary.inferred_records || 0);
      setText('[data-results-stat="power"]', data.summary.power_records || 0);
      setText('[data-results-stat="submitters"]', data.summary.submitters || 0);
      renderSourceCards();
      load.hidden = true;
      root.dataset.loaded = "true";
      applyFilters();
    })
    .catch(error => {
      load.classList.add("is-error");
      load.textContent = error.message;
    });
})();
