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
    inferred: $("[data-results-inferred]"),
    division: $("[data-results-division]"),
    system: $("[data-results-system]"),
    framework: $("[data-results-framework]"),
    precision: $("[data-results-precision]"),
    benchmarkType: $("[data-results-benchmark-type]"),
    isl: $("[data-results-isl]"),
    osl: $("[data-results-osl]"),
    concurrency: $("[data-results-concurrency]"),
    servingMode: $("[data-results-serving-mode]"),
    topology: $("[data-results-topology]"),
    metric: $("[data-results-metric]")
  };
  const rowsNode = $("[data-results-rows]");
  const sortSelect = $("[data-results-sort]");
  const load = $("[data-results-load]");
  const cohortPanel = $("[data-results-cohort]");
  const cohortSummary = $("[data-results-cohort-summary]");
  const cohortClear = $("[data-results-cohort-clear]");
  const pageSize = 50;
  let database = null;
  let currentPage = 1;
  let filteredRecords = [];
  let metricCatalog = new Map();
  let activeCohort = null;

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
    const normalized = record.normalized_metrics || {};
    const preferredNormalized = [
      "output_throughput_per_gpu", "median_interactivity", "p99_ttft", "p99_tpot", "p99_itl"
    ];
    const normalizedItems = preferredNormalized
      .filter(key => normalized[key] && typeof normalized[key].value === "number")
      .slice(0, 3)
      .map(key => {
        const metric = normalized[key];
        return metric.label + ": " + numberText(metric.value) + " " + metric.unit;
      });
    if (normalizedItems.length) return normalizedItems.join(" · ");

    // Backward-compatible display for older snapshots without normalized_metrics.
    const metrics = record.metrics || {};
    const fallback = [
      ["output_tput_per_gpu", "Output throughput (tok/s/GPU)"],
      ["median_intvty", "Median interactivity (tok/s/user)"],
      ["p99_ttft", "P99 TTFT (s)"],
      ["p99_tpot", "P99 TPOT (s)"],
      ["p99_itl", "P99 inter-token latency (s)"]
    ];
    const items = fallback
      .filter(([key]) => typeof metrics[key] === "number")
      .slice(0, 3)
      .map(([key, label]) => label + ": " + numberText(metrics[key]));
    return items.length ? items.join(" · ") : Object.keys(metrics).length + " scalar metrics";
  };

  const resultText = (record, selectedMetricKey = "") => {
    if (selectedMetricKey) {
      const metric = record.normalized_metrics?.[selectedMetricKey];
      if (metric && typeof metric.value === "number") {
        return numberText(metric.value) + (metric.unit ? " " + metric.unit : "");
      }
    }
    if (typeof record.result_value === "number") {
      return numberText(record.result_value) + (record.result_unit ? " " + record.result_unit : "");
    }
    if ((record.metrics && Object.keys(record.metrics).length) ||
        (record.normalized_metrics && Object.keys(record.normalized_metrics).length)) return metricSummary(record);
    return "Metric not provided";
  };

  const addDetailLine = (parent, label, value) => {
    if (value === null || value === undefined || value === "") return;
    const line = make("p", "benchmark-detail-line");
    line.append(make("strong", "", label + ": "));
    line.append(document.createTextNode(String(value)));
    parent.append(line);
  };


  const missingCohortValue = value =>
    value === null || value === undefined ||
    (typeof value === "string" && (!value.trim() || value.trim().toLowerCase() === "unknown"));

  const buildCohortDescriptor = (record) => {
    if (record.source_id === "inferencex") {
      const metricKey = filters.metric.value;
      if (!metricKey) return { error: "Select a normalized metric in Advanced workload filters before creating a strict cohort." };
      const metric = record.normalized_metrics?.[metricKey];
      if (!metric || typeof metric.value !== "number" || !Number.isFinite(metric.value)) {
        return { error: "This record does not report the selected normalized metric." };
      }
      if (missingCohortValue(metric.unit)) {
        return { error: "The selected metric has no unit; a unit-safe cohort cannot be formed." };
      }

      const workload = record.workload || {};
      const source = sourceMap().get(record.source_id);
      const version = record.benchmark_version || source?.version;
      const model = record.model_display_name || record.model;
      const precision = workload.precision || record.weight_data_types;
      const workloadType = workload.benchmark_type || record.scenario;
      const required = [
        ["source version", version], ["model checkpoint", model],
        ["workload type", workloadType], ["scenario", record.scenario],
        ["input length (ISL)", workload.isl], ["output length (OSL)", workload.osl],
        ["concurrency", workload.concurrency], ["precision", precision],
        ["speculative decoding mode", workload.speculative_method],
        ["serving mode", typeof workload.disaggregated === "boolean" ? workload.disaggregated : null],
        ["division", record.division], ["system type", record.system_type]
      ];
      const missing = required.filter(([, value]) => missingCohortValue(value)).map(([name]) => name);
      if (missing.length) return { error: "Strict cohort unavailable: missing " + missing.join(", ") + "." };

      const speculativeMethod = workload.speculative_method;
      const values = [
        record.source_id, record.benchmark_suite, version, model, record.model,
        workloadType, record.scenario, record.division, record.availability, record.system_type,
        workload.isl, workload.osl, workload.concurrency, precision, speculativeMethod,
        workload.disaggregated, metricKey, metric.unit, metric.direction || "context", metric.family || "unknown"
      ];
      return {
        key: JSON.stringify(values),
        metricKey,
        title: "InferenceX · " + model,
        summary: [
          "Model " + model, "workload " + workloadType, "ISL " + workload.isl,
          "OSL " + workload.osl, "concurrency " + workload.concurrency,
          "precision " + precision, "speculative mode " + speculativeMethod,
          workload.disaggregated ? "disaggregated" : "aggregated",
          metric.label + " (" + metric.unit + ")"
        ].join(" · "),
        explanation: "Same InferenceX source/version, model, workload shape, precision, speculative mode, serving mode and metric/unit. Hardware, GPU count, software stack and parallelism remain variables; inspect each run's configuration before drawing conclusions."
      };
    }

    if (record.source_id === "mlperf-inference-v6.1") {
      if (typeof record.result_value !== "number" || !Number.isFinite(record.result_value)) {
        return { error: "This MLPerf record has no numeric published result." };
      }
      const required = [
        ["suite version", record.benchmark_version], ["model", record.model],
        ["scenario", record.scenario], ["division", record.division],
        ["availability status", record.availability], ["system type", record.system_type],
        ["accuracy target", record.accuracy_text], ["precision", record.weight_data_types],
        ["result unit", record.result_unit]
      ];
      const missing = required.filter(([, value]) => missingCohortValue(value)).map(([name]) => name);
      if (missing.length) return { error: "Strict cohort unavailable: missing " + missing.join(", ") + "." };
      const values = [
        record.source_id, record.benchmark_suite, record.benchmark_version, record.model,
        record.scenario, record.division, record.availability, record.system_type,
        record.accuracy_text, record.weight_data_types, record.inferred, record.result_unit
      ];
      return {
        key: JSON.stringify(values),
        metricKey: "result_value",
        title: "MLPerf Inference " + record.benchmark_version + " · " + record.model,
        summary: [
          "Model " + record.model, record.scenario, record.division, record.system_type,
          "accuracy " + record.accuracy_text, "precision " + record.weight_data_types,
          record.inferred ? "inferred submission" : "non-inferred submission",
          "metric " + record.result_unit
        ].join(" · "),
        explanation: "Same MLPerf suite/version, model, scenario, division, availability, system type, accuracy target, precision, inferred status and result unit. Hardware and system scale remain variables; inspect the full system boundary in each record."
      };
    }
    return { error: "Strict cohort matching is currently supported for MLPerf Inference v6.1 and SemiAnalysis InferenceX." };
  };

  const renderCohortPanel = () => {
    if (!cohortPanel || !cohortSummary) return;
    if (!activeCohort || !database) {
      cohortPanel.hidden = true;
      return;
    }
    const cohortSize = database.records.reduce((count, record) => {
      const descriptor = buildCohortDescriptor(record);
      return count + (descriptor && !descriptor.error && descriptor.key === activeCohort.key ? 1 : 0);
    }, 0);
    cohortSummary.textContent = activeCohort.title + " · " + cohortSize +
      " records share this strict workload/metric definition. " + activeCohort.summary +
      ". " + activeCohort.explanation;
    cohortPanel.hidden = false;
  };

  const buildCohortAction = (record) => {
    const descriptor = buildCohortDescriptor(record);
    const wrapper = make("div", "benchmark-cohort-actions");
    const button = make("button", "benchmark-cohort-action",
      descriptor.error ? "Strict cohort unavailable" : "Show strict cohort");
    button.type = "button";
    button.disabled = Boolean(descriptor.error);
    if (descriptor.error) {
      button.title = descriptor.error;
      wrapper.append(button, make("small", "benchmark-cohort-note", descriptor.error));
    } else {
      button.addEventListener("click", () => {
        activeCohort = descriptor;
        renderCohortPanel();
        applyFilters();
      });
      wrapper.append(button);
    }
    return wrapper;
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
    addDetailLine(body, "Model display name", record.model_display_name);
    addDetailLine(body, "Raw model key", record.model_display_name ? record.model : "");
    addDetailLine(body, "Division / availability", record.division + " / " + record.availability);
    addDetailLine(body, "System", record.system_name);
    addDetailLine(body, "Accelerator", system.accelerator_model || system.hardware || "Not separately specified");
    addDetailLine(body, "Accelerator count", system.total_accelerators || "");
    if (system.physical_prefill_gpus !== null && system.physical_prefill_gpus !== undefined ||
        system.physical_decode_gpus !== null && system.physical_decode_gpus !== undefined) {
      addDetailLine(body, "Physical prefill / decode GPUs", [
        system.physical_prefill_gpus, system.physical_decode_gpus
      ].map(value => value === null || value === undefined ? "—" : value).join(" / "));
    }
    addDetailLine(body, "Deployment topology", system.is_multinode === true ? "Multi-node" : system.is_multinode === false ? "Single-node" : "");
    const workerPools = Array.isArray(system.workers) ? system.workers : [];
    if (workerPools.length) addDetailLine(body, "Worker pools", workerPools.map(worker =>
      [
        worker.role,
        worker.worker_idx !== undefined ? "worker " + worker.worker_idx : "",
        worker.num_gpus !== undefined ? worker.num_gpus + " GPUs" : "",
        Array.isArray(worker.hosts) ? worker.hosts.join(", ") : (worker.hosts || "")
      ].filter(Boolean).join(" · ")
    ).join(" | "));
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
      workload.precision ? "Precision " + workload.precision : "",
      workload.disaggregated === true ? "Disaggregated" : workload.disaggregated === false ? "Aggregated" : "Serving mode not reported",
      workload.speculative_method ? "Speculative decoding " + workload.speculative_method : ""
    ].filter(Boolean).join(" · "));
    addDetailLine(body, "Parallelism", Object.entries(configuration)
      .filter(([key]) => [
        "prefill_tp", "prefill_ep", "prefill_dp_attention", "prefill_num_workers",
        "decode_tp", "decode_ep", "decode_dp_attention", "decode_num_workers", "offload_mode"
      ].includes(key))
      .map(([key, value]) => key + "=" + value).join(" · "));
    addDetailLine(body, "Workflow run ID", configuration.workflow_run_id);
    addDetailLine(body, "Run started at", configuration.run_started_at);
    if (record.normalized_metrics && Object.keys(record.normalized_metrics).length) {
      const metrics = Object.values(record.normalized_metrics)
        .map(metric => {
          const direction = metric.direction === "higher" ? "higher is better"
            : metric.direction === "lower" ? "lower is better" : "context only";
          return metric.label + ": " + numberText(metric.value) + " " + metric.unit + " (" + direction + ")";
        })
        .join(" · ");
      addDetailLine(body, "Normalized metrics", metrics);
    }
    if (record.metrics && Object.keys(record.metrics).length) {
      const metrics = Object.entries(record.metrics)
        .map(([key, value]) => key + ": " + numberText(value))
        .join(" · ");
      addDetailLine(body, "Raw publisher metrics", metrics);
    }
    addDetailLine(body, "Notes", record.notes);
    addDetailLine(body, "Source record key", record.source_record_key);
    if (record.inferred) body.append(make("p", "benchmark-result-warning", "This submission is marked as inferred by the source."));
    if (record.source_id === "inferencex") {
      const gpuPowerStatus = {
        valid: "Valid · schema v2",
        failed: "Failed validation",
        schema_incomplete: "Schema v2 not confirmed",
        unreported: "No validation verdict reported",
        invalid_verdict: "Invalid source verdict"
      }[record.power_measurement_status] || "Unknown";
      const cpuPowerStatus = {
        valid: "Valid · independent CPU-side leg",
        failed: "Failed validation",
        not_present: "No CPU-side measurement leg",
        invalid_verdict: "Invalid source verdict"
      }[record.cpu_power_measurement_status] || "Unknown";
      addDetailLine(body, "GPU power validation", gpuPowerStatus);
      addDetailLine(body, "CPU / module power validation", cpuPowerStatus);
      if (record.power_metrics_available === true) {
        body.append(make("p", "benchmark-result-power", "At least one GPU or CPU/module power/energy metric passed its source-specific validation. Compare component boundaries separately."));
      } else if (record.power_measurement_valid === true || record.cpu_power_measurement_valid === true) {
        body.append(make("p", "benchmark-result-warning", "A power measurement leg is valid, but this row exposes no measured power/energy value for that leg."));
      } else {
        body.append(make("p", "benchmark-result-warning", "No validated measured power/energy metric is available in this record. Design power, if present, is not measured power."));
      }
    } else if (record.power_metrics_available === true) {
      body.append(make("p", "benchmark-result-power", "The source marks this record as containing measured power metrics; compare only within its stated measurement boundary."));
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
    body.append(buildCohortAction(record));
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
    workload.append(make("strong", "benchmark-model", record.model_display_name || record.model));
    workload.append(make("small", "benchmark-scenario", record.scenario));
    row.append(workload);

    const result = document.createElement("td");
    result.append(make("strong", "benchmark-result-value", resultText(record, filters.metric.value)));
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
    // The source-status section intentionally sits outside the filter/table root.
    const container = document.querySelector("[data-results-source-cards]");
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
        const message = source.import_status === "api_adapter_ready_not_yet_imported"
          ? "No rows are cached in this snapshot. The repository importer supports this public API; the empty cache is not a zero-performance result."
          : source.import_status === "methodology_only_no_result_snapshot"
            ? "The methodology is catalogued separately. No machine-readable result snapshot is imported here."
            : "No result rows are imported in this snapshot.";
        card.append(make("p", "benchmark-result-warning", message));
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
      if (filters.model.value && (record.model_display_name || record.model) !== filters.model.value) return false;
      if (filters.scenario.value && record.scenario !== filters.scenario.value) return false;
      if (filters.availability.value && record.availability !== filters.availability.value) return false;
      if (filters.inferred.value === "true" && !record.inferred) return false;
      if (filters.inferred.value === "false" && record.inferred) return false;
      if (filters.division.value && record.division !== filters.division.value) return false;
      if (filters.system.value && record.system_type !== filters.system.value) return false;
      if (filters.framework.value && (record.software?.framework || "") !== filters.framework.value) return false;
      if (filters.precision.value && (record.workload?.precision || record.weight_data_types || "") !== filters.precision.value) return false;
      if (filters.benchmarkType.value && (record.workload?.benchmark_type || "") !== filters.benchmarkType.value) return false;
      if (filters.isl.value && String(record.workload?.isl ?? "") !== filters.isl.value) return false;
      if (filters.osl.value && String(record.workload?.osl ?? "") !== filters.osl.value) return false;
      if (filters.concurrency.value && String(record.workload?.concurrency ?? "") !== filters.concurrency.value) return false;
      if (filters.servingMode.value && (record.workload?.disaggregated === true ? "disaggregated" : record.workload?.disaggregated === false ? "aggregated" : "") !== filters.servingMode.value) return false;
      if (filters.topology.value && (record.system?.is_multinode === true ? "multi-node" : record.system?.is_multinode === false ? "single-node" : "") !== filters.topology.value) return false;
      if (filters.metric.value && typeof record.normalized_metrics?.[filters.metric.value]?.value !== "number") return false;
      if (activeCohort) {
        const descriptor = buildCohortDescriptor(record);
        if (!descriptor || descriptor.error || descriptor.key !== activeCohort.key) return false;
      }
      const searchable = [
        record.submitter, record.accelerator_vendor, record.system_name,
        record.system?.accelerator_model, record.system?.hardware,
        record.model_display_name, record.model, record.scenario, record.division, record.availability,
        record.software?.framework, record.software?.operating_system,
        record.workload?.precision, record.workload?.benchmark_type,
        ...Object.entries(record.normalized_metrics || {}).flatMap(([key, metric]) =>
          [key, metric.label, metric.unit, metric.value]),
        record.notes, record.accuracy_text, record.benchmark_suite
      ].join(" ").toLowerCase();
      return !query || searchable.includes(query);
    });
    const sortField = sortSelect.value;
    if (sortField === "metric-best" || sortField === "metric-worst") {
      const definition = metricCatalog.get(filters.metric.value);
      if (definition && definition.direction !== "context") {
        const bestAscending = definition.direction === "lower";
        const ascending = sortField === "metric-best" ? bestAscending : !bestAscending;
        filteredRecords.sort((a, b) => {
          const av = a.normalized_metrics?.[filters.metric.value]?.value;
          const bv = b.normalized_metrics?.[filters.metric.value]?.value;
          if (typeof av !== "number") return typeof bv === "number" ? 1 : String(a.id).localeCompare(String(b.id));
          if (typeof bv !== "number") return -1;
          return (ascending ? av - bv : bv - av) || String(a.id).localeCompare(String(b.id));
        });
      }
    } else if (sortField) {
      const fieldValue = (record) => {
        if (sortField === "vendor") return record.accelerator_vendor || "Not specified";
        if (sortField === "model") return record.model_display_name || record.model || "";
        if (sortField === "submitter") return record.submitter || "";
        if (sortField === "system") return record.system_name || "";
        return "";
      };
      filteredRecords.sort((a, b) =>
        String(fieldValue(a)).localeCompare(String(fieldValue(b)), undefined, {
          numeric: true,
          sensitivity: "base"
        }) || String(a.id).localeCompare(String(b.id))
      );
    }
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
        " of " + filteredRecords.length + " filtered records" +
        (activeCohort ? " · strict workload cohort" : " · no cross-suite ranking")
      : "No records match the current filters.";
    $("[data-results-empty]").hidden = filteredRecords.length > 0;
    $("[data-results-page]").textContent = "Page " + currentPage + " of " + totalPages;
    $("[data-results-prev]").disabled = currentPage <= 1;
    $("[data-results-next]").disabled = currentPage >= totalPages;
  };

  const reset = () => {
    search.value = "";
    Object.values(filters).forEach(select => { select.value = ""; });
    sortSelect.value = "";
    activeCohort = null;
    renderCohortPanel();
    applyFilters();
  };

  Object.entries(filters).forEach(([key, select]) => select.addEventListener("change", () => {
    if (key === "metric" && activeCohort) {
      activeCohort = null;
      renderCohortPanel();
    }
    applyFilters();
  }));
  if (cohortClear) cohortClear.addEventListener("click", () => {
    activeCohort = null;
    renderCohortPanel();
    applyFilters();
  });
  sortSelect.addEventListener("change", applyFilters);
  search.addEventListener("input", applyFilters);
  $("[data-results-reset]").addEventListener("click", reset);
  $("[data-results-prev]").addEventListener("click", () => {
    if (currentPage > 1) { currentPage -= 1; renderRows(); }
  });
  $("[data-results-next]").addEventListener("click", () => {
    if (currentPage * pageSize < filteredRecords.length) { currentPage += 1; renderRows(); }
  });

  const fetchRegistry = async () => {
    const response = await fetch(root.dataset.source, { cache: "no-cache" });
    if (!response.ok) throw new Error("Benchmark results request failed: HTTP " + response.status);
    const bytes = await response.arrayBuffer();
    const isGzip = bytes.byteLength >= 2 && new Uint8Array(bytes, 0, 2)[0] === 0x1f &&
      new Uint8Array(bytes, 0, 2)[1] === 0x8b;
    if (!isGzip) return JSON.parse(new TextDecoder().decode(bytes));
    if (typeof DecompressionStream !== "function") {
      throw new Error("This browser cannot decompress the benchmark data. Open the raw JSON results instead.");
    }
    const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream("gzip"));
    return new Response(stream).json();
  };

  fetchRegistry()
    .then(data => {
      if (!Array.isArray(data.records) || !Array.isArray(data.sources) || !data.summary) {
        throw new Error("Benchmark results registry has an invalid structure.");
      }
      database = data;
      const sources = sourceMap();
      populate(filters.source, data.sources.map(source => source.id),
        id => (sources.get(id)?.name || id));
      populate(filters.vendor, data.records.map(record => record.accelerator_vendor || "Not specified"));
      populate(filters.model, data.records.map(record => record.model_display_name || record.model));
      populate(filters.scenario, data.records.map(record => record.scenario));
      populate(filters.availability, data.records.map(record => record.availability));
      populate(filters.inferred, ["false", "true"], value => value === "true" ? "Inferred submissions" : "Non-inferred submissions");
      populate(filters.division, data.records.map(record => record.division));
      populate(filters.system, data.records.map(record => record.system_type));
      populate(filters.framework, data.records.map(record => record.software?.framework));
      populate(filters.precision, data.records.map(record => record.workload?.precision || record.weight_data_types));
      populate(filters.benchmarkType, data.records.map(record => record.workload?.benchmark_type));
      populate(filters.isl, data.records.map(record => record.workload?.isl));
      populate(filters.osl, data.records.map(record => record.workload?.osl));
      populate(filters.concurrency, data.records.map(record => record.workload?.concurrency));
      populate(filters.servingMode, data.records.map(record =>
        typeof record.workload?.disaggregated === "boolean" ? (record.workload.disaggregated ? "disaggregated" : "aggregated") : null
      ));
      populate(filters.topology, data.records.map(record =>
        typeof record.system?.is_multinode === "boolean" ? (record.system.is_multinode ? "multi-node" : "single-node") : null
      ));
      metricCatalog = new Map();
      const metricConflicts = new Set();
      data.records.forEach(record => {
        Object.entries(record.normalized_metrics || {}).forEach(([key, metric]) => {
          if (typeof metric.value !== "number" || metricConflicts.has(key)) return;
          const definition = { label: metric.label || key, unit: metric.unit || "", direction: metric.direction || "context" };
          const existing = metricCatalog.get(key);
          if (!existing) metricCatalog.set(key, definition);
          else if (existing.unit !== definition.unit || existing.direction !== definition.direction) {
            metricCatalog.delete(key);
            metricConflicts.add(key);
          }
        });
      });
      populate(filters.metric, [...metricCatalog.keys()], key => {
        const metric = metricCatalog.get(key);
        return metric.label + (metric.unit ? " (" + metric.unit + ")" : "");
      });
      const bestSort = sortSelect.querySelector('option[value="metric-best"]');
      const worstSort = sortSelect.querySelector('option[value="metric-worst"]');
      if (bestSort) bestSort.disabled = true;
      if (worstSort) worstSort.disabled = true;
      filters.metric.addEventListener("change", () => {
        const selected = metricCatalog.get(filters.metric.value);
        const canSort = Boolean(selected && selected.direction !== "context");
        if (bestSort) bestSort.disabled = !canSort;
        if (worstSort) worstSort.disabled = !canSort;
        if (!canSort && ["metric-best", "metric-worst"].includes(sortSelect.value)) sortSelect.value = "";
      });

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
