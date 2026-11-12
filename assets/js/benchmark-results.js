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
  const comparisonCount = $("[data-comparison-count]");
  const comparisonContent = $("[data-comparison-content]");
  const comparisonClear = $("[data-comparison-clear]");
  const scalingPanel = $("[data-results-scaling]");
  const scalingContent = $("[data-results-scaling-content]");
  const frontierPanel = $("[data-results-frontier]");
  const frontierContent = $("[data-results-frontier-content]");
  const energyPanel = $("[data-results-energy]");
  const energyContent = $("[data-results-energy-content]");
  const attributionPanel = $("[data-results-attribution]");
  const attributionContent = $("[data-results-attribution-content]");
  const decompositionPanel = $("[data-results-decomposition]");
  const decompositionContent = $("[data-results-decomposition-content]");
  const maxComparisonRecords = 4;
  const pageSize = 50;
  let database = null;
  let currentPage = 1;
  let filteredRecords = [];
  let metricCatalog = new Map();
  let activeCohort = null;
  const comparisonSelection = new Map();

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
      const performanceValues = values.slice(0, 16);
      return {
        key: JSON.stringify(values),
        performanceKey: JSON.stringify(performanceValues),
        sourceId: record.source_id,
        metricKey,
        metricUnit: metric.unit,
        metricDirection: metric.direction || "context",
        metricLabel: metric.label || metricKey,
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



  const reportedAcceleratorCount = (record) => {
    const system = record.system || {};
    const total = Number(system.total_accelerators);
    if (Number.isInteger(total) && total > 0) {
      return { count: total, source: "reported total accelerator count" };
    }
    const prefill = system.physical_prefill_gpus;
    const decode = system.physical_decode_gpus;
    if (Number.isInteger(prefill) && prefill >= 0 &&
        Number.isInteger(decode) && decode >= 0 && prefill + decode > 0) {
      return { count: prefill + decode, source: "reported prefill / decode GPU counts" };
    }
    const workers = Array.isArray(system.workers) ? system.workers : [];
    const workerCounts = workers.map(worker => Number(worker?.num_gpus));
    if (workers.length && workerCounts.every(value => Number.isInteger(value) && value >= 0)) {
      const count = workerCounts.reduce((sum, value) => sum + value, 0);
      if (count > 0) return { count, source: "sum of reported worker-pool counts" };
    }
    return null;
  };

  const medianValue = values => {
    const sorted = [...values].filter(Number.isFinite).sort((a, b) => a - b);
    if (!sorted.length) return null;
    const middle = Math.floor(sorted.length / 2);
    return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
  };

  const scalingSoftwareIdentity = record => {
    const software = record.software || {};
    const framework = String(software.framework || "").trim();
    const image = String(software.image || "").trim();
    const recipe = String(software.recipe_fingerprint || "").trim();
    if (!framework || (!image && !recipe)) return null;
    return {
      framework,
      image,
      recipe,
      key: JSON.stringify([framework.toLowerCase(), image.toLowerCase(), recipe.toLowerCase()]),
      label: framework + " · " + (recipe ? "recipe " + recipe : "image " + image)
    };
  };

  const renderScalingAnalysis = records => {
    if (!scalingPanel || !scalingContent) return;
    const supported = activeCohort && activeCohort.sourceId === "inferencex" &&
      activeCohort.metricKey === "output_throughput_per_gpu";
    if (!supported) {
      scalingPanel.hidden = true;
      return;
    }
    scalingPanel.hidden = false;
    scalingContent.replaceChildren();

    const groups = new Map();
    const excluded = { servingMode: 0, hardware: 0, software: 0, gpuCount: 0, metric: 0 };
    records.forEach(record => {
      if (record.workload?.disaggregated !== false) {
        excluded.servingMode += 1;
        return;
      }
      const hardware = String(record.system?.hardware || record.system?.accelerator_model || "").trim();
      if (!hardware) {
        excluded.hardware += 1;
        return;
      }
      const software = scalingSoftwareIdentity(record);
      if (!software) {
        excluded.software += 1;
        return;
      }
      const gpuCount = reportedAcceleratorCount(record);
      if (!gpuCount) {
        excluded.gpuCount += 1;
        return;
      }
      const metric = record.normalized_metrics?.output_throughput_per_gpu;
      if (!metric || typeof metric.value !== "number" || !Number.isFinite(metric.value) ||
          metric.value <= 0 || metric.unit !== "tok/s/GPU") {
        excluded.metric += 1;
        return;
      }
      const key = JSON.stringify([hardware.toLowerCase(), software.key]);
      if (!groups.has(key)) groups.set(key, { hardware, software, counts: new Map() });
      const group = groups.get(key);
      if (!group.counts.has(gpuCount.count)) {
        group.counts.set(gpuCount.count, { values: [], countSources: new Set() });
      }
      const bucket = group.counts.get(gpuCount.count);
      bucket.values.push(metric.value);
      bucket.countSources.add(gpuCount.source);
    });

    const series = [...groups.values()].map(group => ({
      ...group,
      points: [...group.counts.entries()].map(([count, bucket]) => ({
        count,
        samples: bucket.values.length,
        medianPerGpu: medianValue(bucket.values),
        countSources: [...bucket.countSources]
      })).sort((a, b) => a.count - b.count)
    })).filter(group => group.points.length >= 2)
      .sort((a, b) => a.hardware.localeCompare(b.hardware) ||
        a.software.framework.localeCompare(b.software.framework));

    const eligibleCount = [...groups.values()].reduce((sum, group) =>
      sum + [...group.counts.values()].reduce((count, bucket) => count + bucket.values.length, 0), 0);
    scalingContent.append(make("p", "benchmark-scaling-summary",
      records.length + " records in the active strict cohort · " + eligibleCount +
      " records have a known GPU count and matching hardware/software identity · " +
      series.length + " scaling series with multiple GPU counts."));

    if (!series.length) {
      scalingContent.append(make("p", "benchmark-scaling-empty",
        "No defensible scaling curve is available in this filtered cohort. A curve requires at least two GPU counts for the same accelerator, framework and image/recipe, with aggregated serving and a reported GPU count."));
    } else {
      series.forEach(group => {
        const card = make("article", "benchmark-scaling-card");
        const heading = make("div", "benchmark-scaling-card-heading");
        heading.append(make("strong", "", group.hardware));
        heading.append(make("span", "", group.software.label));
        card.append(heading);
        const baseline = group.points[0];
        const baselinePerGpu = baseline.medianPerGpu;
        const baselineCount = baseline.count;
        const tableWrap = make("div", "benchmark-scaling-table-wrap");
        const table = make("table", "benchmark-scaling-table");
        const thead = document.createElement("thead");
        const header = document.createElement("tr");
        ["GPU count", "Samples", "Median output throughput / GPU", "Estimated aggregate output throughput", "Linear reference", "Scaling efficiency"].forEach(label =>
          header.append(make("th", "", label)));
        thead.append(header);
        table.append(thead);
        const tbody = document.createElement("tbody");
        group.points.forEach(point => {
          const estimatedTotal = point.medianPerGpu * point.count;
          const linearReference = baselinePerGpu * point.count;
          const efficiency = baselinePerGpu > 0 ? point.medianPerGpu / baselinePerGpu * 100 : null;
          const row = document.createElement("tr");
          const countCell = document.createElement("td");
          countCell.append(make("strong", "", point.count + " GPUs"));
          countCell.append(make("small", "", point.countSources.join(" · ")));
          row.append(countCell);
          row.append(make("td", "", point.samples));
          row.append(make("td", "", numberText(point.medianPerGpu) + " tok/s/GPU"));
          row.append(make("td", "", numberText(estimatedTotal) + " tok/s"));
          row.append(make("td", "", numberText(linearReference) + " tok/s"));
          const efficiencyCell = make("td", "benchmark-scaling-efficiency");
          efficiencyCell.append(make("strong", "", efficiency === null ? "—" : efficiency.toFixed(1) + "%"));
          efficiencyCell.append(make("small", "", point.count === baselineCount
            ? "Baseline · " + baselineCount + " GPUs"
            : (point.count / baselineCount).toFixed(2).replace(/\.00$/, "") + "× GPU scale vs baseline"));
          row.append(efficiencyCell);
          tbody.append(row);
        });
        table.append(tbody);
        tableWrap.append(table);
        card.append(tableWrap);
        scalingContent.append(card);
      });
    }

    const exclusions = [
      ["non-aggregated or unknown serving mode", excluded.servingMode],
      ["missing accelerator identity", excluded.hardware],
      ["missing framework and image/recipe fingerprint", excluded.software],
      ["missing reliable GPU count", excluded.gpuCount],
      ["missing or invalid output-throughput metric", excluded.metric]
    ].filter(([, count]) => count > 0);
    if (exclusions.length) {
      scalingContent.append(make("p", "benchmark-scaling-exclusions",
        "Excluded from scaling analysis: " + exclusions.map(([label, count]) => label + " (" + count + ")").join(" · ") + "."));
    }
    scalingContent.append(make("p", "benchmark-scaling-note",
      "Interpretation: the smallest GPU-count point is the baseline within each identical hardware/software group. Scaling efficiency = median output throughput per GPU at N GPUs ÷ baseline median output throughput per GPU × 100%. Aggregate throughput and linear references are derived estimates, not publisher-reported totals. Parallelism and run configuration remain potential confounders; this is observed system-level scaling, not a causal hardware-only measurement."));
  };


  // Shared by latency and energy analyses. The selected display metric is
  // intentionally excluded; only the strict workload identity is compared.
  const performanceKeyFor = record => {
    if (record.source_id !== "inferencex") return null;
    const workload = record.workload || {};
    const source = sourceMap().get(record.source_id);
    const version = record.benchmark_version || source?.version;
    const model = record.model_display_name || record.model;
    const precision = workload.precision || record.weight_data_types;
    const workloadType = workload.benchmark_type || record.scenario;
    const speculativeMethod = workload.speculative_method;
    const servingMode = typeof workload.disaggregated === "boolean" ? workload.disaggregated : null;
    const required = [
      version, model, workloadType, record.scenario, record.division, record.availability,
      record.system_type, workload.isl, workload.osl, workload.concurrency, precision,
      speculativeMethod, servingMode
    ];
    if (required.some(missingCohortValue)) return null;
    return JSON.stringify([
      record.source_id, record.benchmark_suite, version, model, record.model,
      workloadType, record.scenario, record.division, record.availability, record.system_type,
      workload.isl, workload.osl, workload.concurrency, precision, speculativeMethod, servingMode
    ]);
  };

  const renderParetoFrontier = () => {
    if (!frontierPanel || !frontierContent) return;
    const supported = activeCohort && activeCohort.sourceId === "inferencex" &&
      activeCohort.performanceKey && database;
    if (!supported) {
      frontierPanel.hidden = true;
      return;
    }

    frontierPanel.hidden = false;
    frontierContent.replaceChildren();
    const cohortRecords = database.records.filter(record =>
      performanceKeyFor(record) === activeCohort.performanceKey
    );

    const readMetric = (record, key, unit, direction) => {
      const metric = record.normalized_metrics?.[key];
      if (!metric || typeof metric.value !== "number" || !Number.isFinite(metric.value) ||
          metric.value <= 0 || metric.unit !== unit || metric.direction !== direction) return null;
      return metric.value;
    };

    const candidates = [];
    cohortRecords.forEach(record => {
      const ttft = readMetric(record, "p99_ttft", "s", "lower");
      const tpot = readMetric(record, "p99_tpot", "s", "lower");
      const throughput = readMetric(record, "output_throughput_per_gpu", "tok/s/GPU", "higher");
      if (ttft === null || tpot === null || throughput === null) return;
      candidates.push({ record, ttft, tpot, throughput, isPareto: false });
    });

    const dominates = (left, right) =>
      left.ttft <= right.ttft && left.tpot <= right.tpot &&
      left.throughput >= right.throughput &&
      (left.ttft < right.ttft || left.tpot < right.tpot || left.throughput > right.throughput);
    candidates.forEach(candidate => {
      candidate.isPareto = !candidates.some(other => other !== candidate && dominates(other, candidate));
    });
    const frontier = candidates.filter(candidate => candidate.isPareto)
      .sort((a, b) => a.ttft - b.ttft || a.tpot - b.tpot || b.throughput - a.throughput);

    frontierContent.append(make("p", "benchmark-frontier-summary",
      cohortRecords.length + " records in the selected strict workload cohort · " +
      candidates.length + " report all three required metrics · " +
      frontier.length + " Pareto-optimal configurations · " +
      (cohortRecords.length - candidates.length) + " excluded for incomplete or invalid metrics."));

    if (candidates.length < 2) {
      frontierContent.append(make("p", "benchmark-frontier-empty",
        "At least two records with valid P99 TTFT, P99 TPOT and output throughput per GPU are required to identify a performance trade-off. Missing metrics are not estimated."));
      return;
    }

    const svgNS = "http://www.w3.org/2000/svg";
    const svgNode = (tag, attributes, content) => {
      const node = document.createElementNS(svgNS, tag);
      Object.entries(attributes || {}).forEach(([key, value]) => node.setAttribute(key, String(value)));
      if (content !== undefined) node.textContent = String(content);
      return node;
    };
    const svg = svgNode("svg", {
      viewBox: "0 0 760 340",
      role: "img",
      "aria-label": "P99 TTFT versus P99 TPOT scatter plot; bubble size represents output throughput per GPU",
      "data-pareto-plot": ""
    });
    const plot = { left: 78, top: 24, width: 630, height: 250 };
    const xValues = candidates.map(item => item.ttft);
    const yValues = candidates.map(item => item.tpot);
    const minMax = values => {
      const min = Math.min(...values), max = Math.max(...values);
      const span = max - min || Math.max(Math.abs(min) * 0.2, 0.01);
      return { min: Math.max(0, min - span * 0.12), max: max + span * 0.12 };
    };
    const xDomain = minMax(xValues);
    const yDomain = minMax(yValues);
    const xScale = value => plot.left + (value - xDomain.min) /
      (xDomain.max - xDomain.min) * plot.width;
    const yScale = value => plot.top + plot.height - (value - yDomain.min) /
      (yDomain.max - yDomain.min) * plot.height;
    const throughputValues = candidates.map(item => item.throughput);
    const throughputMin = Math.min(...throughputValues);
    const throughputMax = Math.max(...throughputValues);

    for (let tick = 0; tick <= 4; tick += 1) {
      const x = plot.left + plot.width * tick / 4;
      const y = plot.top + plot.height * tick / 4;
      const xValue = xDomain.min + (xDomain.max - xDomain.min) * tick / 4;
      const yValue = yDomain.max - (yDomain.max - yDomain.min) * tick / 4;
      svg.append(svgNode("line", {
        x1: x, y1: plot.top, x2: x, y2: plot.top + plot.height,
        class: "benchmark-frontier-grid"
      }));
      svg.append(svgNode("line", {
        x1: plot.left, y1: y, x2: plot.left + plot.width, y2: y,
        class: "benchmark-frontier-grid"
      }));
      svg.append(svgNode("text", {
        x, y: plot.top + plot.height + 18, "text-anchor": "middle",
        class: "benchmark-frontier-tick"
      }, numberText(xValue)));
      svg.append(svgNode("text", {
        x: plot.left - 10, y: y + 3, "text-anchor": "end",
        class: "benchmark-frontier-tick"
      }, numberText(yValue)));
    }
    svg.append(svgNode("line", {
      x1: plot.left, y1: plot.top + plot.height,
      x2: plot.left + plot.width, y2: plot.top + plot.height,
      class: "benchmark-frontier-axis"
    }));
    svg.append(svgNode("line", {
      x1: plot.left, y1: plot.top, x2: plot.left, y2: plot.top + plot.height,
      class: "benchmark-frontier-axis"
    }));
    svg.append(svgNode("text", {
      x: plot.left + plot.width / 2, y: 326, "text-anchor": "middle",
      class: "benchmark-frontier-axis-label"
    }, "P99 TTFT (s) · lower is better"));
    svg.append(svgNode("text", {
      x: 17, y: plot.top + plot.height / 2,
      transform: "rotate(-90 17 " + (plot.top + plot.height / 2) + ")",
      "text-anchor": "middle", class: "benchmark-frontier-axis-label"
    }, "P99 TPOT (s) · lower is better"));

    candidates.forEach(candidate => {
      const normalizedThroughput = throughputMax === throughputMin ? 0.5 :
        (candidate.throughput - throughputMin) / (throughputMax - throughputMin);
      const radius = 5 + Math.sqrt(normalizedThroughput) * 7;
      const circle = svgNode("circle", {
        cx: xScale(candidate.ttft),
        cy: yScale(candidate.tpot),
        r: radius,
        class: "benchmark-frontier-point" + (candidate.isPareto ? " is-pareto" : ""),
        "data-record-id": candidate.record.id,
        "data-frontier": candidate.isPareto ? "true" : "false"
      });
      circle.append(svgNode("title", {}, [
        candidate.record.system_name || candidate.record.system?.hardware || "System not specified",
        "P99 TTFT " + numberText(candidate.ttft) + " s",
        "P99 TPOT " + numberText(candidate.tpot) + " s",
        "Output throughput " + numberText(candidate.throughput) + " tok/s/GPU",
        candidate.isPareto ? "Pareto optimal" : "Dominated by another configuration"
      ].join(" · ")));
      svg.append(circle);
    });
    frontierContent.append(svg);
    frontierContent.append(make("p", "benchmark-frontier-legend",
      "Each point is one published configuration. Bubble size represents output throughput per GPU; outlined points are non-dominated. Lower TTFT and TPOT are better, while higher throughput is better."));

    const tableWrap = make("div", "benchmark-frontier-table-wrap");
    const table = make("table", "benchmark-frontier-table");
    const thead = document.createElement("thead");
    const header = document.createElement("tr");
    ["Pareto configuration", "P99 TTFT", "P99 TPOT", "Output throughput / GPU", "GPU count", "Parallelism / source"].forEach(label =>
      header.append(make("th", "", label)));
    thead.append(header);
    table.append(thead);
    const tbody = document.createElement("tbody");

    frontier.forEach(candidate => {
      const record = candidate.record;
      const row = document.createElement("tr");
      row.dataset.recordId = record.id;
      const identity = document.createElement("td");
      identity.append(make("strong", "", record.system_name ||
        record.system?.hardware || record.system?.accelerator_model || "System not specified"));
      identity.append(make("small", "", (record.accelerator_vendor || "Unknown vendor") +
        " · " + (record.submitter || "Unknown submitter") +
        " · " + (record.software?.framework || "Framework not reported")));
      row.append(identity);
      row.append(make("td", "", numberText(candidate.ttft) + " s"));
      row.append(make("td", "", numberText(candidate.tpot) + " s"));
      row.append(make("td", "", numberText(candidate.throughput) + " tok/s/GPU"));

      const gpuCount = reportedAcceleratorCount(record);
      const gpuCell = make("td", "", gpuCount ? gpuCount.count + " GPUs" : "Not reported");
      if (gpuCount) gpuCell.append(make("small", "", gpuCount.source));
      row.append(gpuCell);

      const configuration = record.configuration || {};
      const parallelismKeys = [
        "prefill_tp", "prefill_ep", "prefill_dp_attention", "prefill_num_workers",
        "decode_tp", "decode_ep", "decode_dp_attention", "decode_num_workers", "offload_mode"
      ];
      const parallelism = parallelismKeys
        .filter(key => configuration[key] !== null && configuration[key] !== undefined && configuration[key] !== "")
        .map(key => key + "=" + configuration[key]).join(" · ") || "Parallelism not reported";
      const detail = make("td", "");
      detail.append(make("span", "", parallelism));
      const link = make("div", "benchmark-frontier-source");
      addLink(link, record.detail_url || record.source_url, "Source record ↗");
      if (!link.childNodes.length) link.append(make("span", "", "Source link unavailable"));
      detail.append(link);
      row.append(detail);
      tbody.append(row);
    });
    table.append(tbody);
    tableWrap.append(table);
    frontierContent.append(tableWrap);
  };


  const renderEnergyEfficiency = () => {
    if (!energyPanel || !energyContent) return;
    const supported = activeCohort && activeCohort.sourceId === "inferencex" &&
      activeCohort.performanceKey && database;
    if (!supported) {
      energyPanel.hidden = true;
      return;
    }
    energyPanel.hidden = false;
    energyContent.replaceChildren();
    const cohortRecords = database.records.filter(record =>
      performanceKeyFor(record) === activeCohort.performanceKey
    );
    const readMetric = (record, key, unit, direction) => {
      const metric = record.normalized_metrics?.[key];
      if (!metric || typeof metric.value !== "number" || !Number.isFinite(metric.value) ||
          metric.value <= 0 || metric.unit !== unit || metric.direction !== direction) return null;
      return metric;
    };
    // Keep the publisher's power_valid + schema-version evidence gate in the UI.
    const energyRecords = cohortRecords.flatMap(record => {
      if (record.power_measurement_valid !== true || record.gpu_power_metrics_available !== true) return [];
      const energy = readMetric(record, "energy_per_output_token", "J/output token", "lower");
      if (!energy) return [];
      return [{
        record, energy: energy.value,
        totalTokenEnergy: readMetric(record, "energy_per_total_token", "J/total token", "lower"),
        inputTokenEnergy: readMetric(record, "energy_per_input_token", "J/input token", "lower"),
        prefillEnergy: readMetric(record, "prefill_energy_per_input_token", "J/input token", "lower"),
        decodeEnergy: readMetric(record, "decode_energy_per_output_token", "J/output token", "lower"),
        queryEnergy: readMetric(record, "energy_per_successful_query", "J/query", "lower"),
        throughput: readMetric(record, "output_throughput_per_gpu", "tok/s/GPU", "higher"),
        gpuPower: readMetric(record, "mean_gpu_power_per_gpu", "W/GPU", "context"),
        totalGpuPower: readMetric(record, "mean_total_gpu_power", "W", "context")
      }];
    }).sort((a,b)=>a.energy-b.energy || String(a.record.id).localeCompare(String(b.record.id)));

    const excludedCount = cohortRecords.length - energyRecords.length;
    const plotCandidates = energyRecords.filter(item => item.throughput !== null);
    const dominates = (a,b) => a.energy <= b.energy && a.throughput.value >= b.throughput.value &&
      (a.energy < b.energy || a.throughput.value > b.throughput.value);
    plotCandidates.forEach(candidate => {
      candidate.isPareto = !plotCandidates.some(other => other !== candidate && dominates(other,candidate));
    });
    const frontier = plotCandidates.filter(candidate => candidate.isPareto);
    energyContent.append(make("p","benchmark-energy-summary",
      cohortRecords.length+" records in the selected strict workload cohort · "+
      energyRecords.length+" have validated GPU energy per output token · "+
      plotCandidates.length+" also report output throughput per GPU · "+
      frontier.length+" Pareto-optimal energy/throughput configurations · "+
      excludedCount+" excluded because validated GPU energy evidence is unavailable."));
    if (!energyRecords.length) {
      energyContent.append(make("p","benchmark-energy-empty",
        "No validated GPU energy-per-output-token measurements are available in this strict workload cohort. Records without publisher-validated GPU power telemetry are not ranked or estimated."));
      return;
    }

    if (plotCandidates.length) {
      const ns="http://www.w3.org/2000/svg";
      const svgNode=(tag,attrs,content)=>{
        const node=document.createElementNS(ns,tag);
        Object.entries(attrs||{}).forEach(([key,value])=>node.setAttribute(key,String(value)));
        if(content!==undefined)node.textContent=String(content);
        return node;
      };
      const svg=svgNode("svg",{
        viewBox:"0 0 760 340",role:"img",
        "aria-label":"GPU energy per output token versus output throughput per GPU; bubble size represents mean GPU power per GPU",
        "data-energy-plot":""
      });
      const plot={left:82,top:24,width:626,height:250};
      const xs=plotCandidates.map(x=>x.energy),ys=plotCandidates.map(x=>x.throughput.value);
      const domain=values=>{
        const min=Math.min(...values),max=Math.max(...values),span=max-min||Math.max(Math.abs(min)*.2,.01);
        return {min:Math.max(0,min-span*.12),max:max+span*.12};
      };
      const xd=domain(xs),yd=domain(ys);
      const sx=v=>plot.left+(v-xd.min)/(xd.max-xd.min)*plot.width;
      const sy=v=>plot.top+plot.height-(v-yd.min)/(yd.max-yd.min)*plot.height;
      const powers=plotCandidates.map(x=>x.gpuPower?.value).filter(Number.isFinite);
      const pmin=powers.length?Math.min(...powers):null,pmax=powers.length?Math.max(...powers):null;
      for(let tick=0;tick<=4;tick+=1){
        const x=plot.left+plot.width*tick/4,y=plot.top+plot.height*tick/4;
        svg.append(svgNode("line",{x1:x,y1:plot.top,x2:x,y2:plot.top+plot.height,class:"benchmark-energy-grid"}));
        svg.append(svgNode("line",{x1:plot.left,y1:y,x2:plot.left+plot.width,y2:y,class:"benchmark-energy-grid"}));
        svg.append(svgNode("text",{x,y:plot.top+plot.height+18,"text-anchor":"middle",class:"benchmark-energy-tick"},
          numberText(xd.min+(xd.max-xd.min)*tick/4)));
        svg.append(svgNode("text",{x:plot.left-10,y:y+3,"text-anchor":"end",class:"benchmark-energy-tick"},
          numberText(yd.max-(yd.max-yd.min)*tick/4)));
      }
      svg.append(svgNode("line",{x1:plot.left,y1:plot.top+plot.height,x2:plot.left+plot.width,y2:plot.top+plot.height,class:"benchmark-energy-axis"}));
      svg.append(svgNode("line",{x1:plot.left,y1:plot.top,x2:plot.left,y2:plot.top+plot.height,class:"benchmark-energy-axis"}));
      svg.append(svgNode("text",{x:plot.left+plot.width/2,y:326,"text-anchor":"middle",class:"benchmark-energy-axis-label"},
        "GPU energy per output token (J) · lower is better"));
      svg.append(svgNode("text",{x:17,y:plot.top+plot.height/2,transform:"rotate(-90 17 "+(plot.top+plot.height/2)+")",
        "text-anchor":"middle",class:"benchmark-energy-axis-label"},"Output throughput / GPU (tok/s) · higher is better"));
      plotCandidates.forEach(candidate=>{
        const power=candidate.gpuPower?.value;
        const normalized = power === undefined || power === null || pmin === pmax
          ? 0.5 : (power - pmin) / (pmax - pmin);
        const radius=power===undefined||power===null?5:5+Math.sqrt(normalized)*7;
        const circle=svgNode("circle",{
          cx:sx(candidate.energy),cy:sy(candidate.throughput.value),r:radius,
          class:"benchmark-energy-point"+(candidate.isPareto?" is-pareto":""),
          "data-record-id":candidate.record.id,"data-frontier":candidate.isPareto?"true":"false"
        });
        circle.append(svgNode("title",{},[
          candidate.record.system_name||candidate.record.system?.hardware||"System not specified",
          "GPU energy "+numberText(candidate.energy)+" J/output token",
          "Output throughput "+numberText(candidate.throughput.value)+" tok/s/GPU",
          power===undefined||power===null?"Mean GPU power not reported":"Mean GPU power "+numberText(power)+" W/GPU",
          candidate.isPareto?"Pareto optimal":"Dominated by another configuration"
        ].join(" · ")));
        svg.append(circle);
      });
      energyContent.append(svg);
      energyContent.append(make("p","benchmark-energy-legend",
        "Each point is one publisher observation. Outlined points are non-dominated on energy per output token and output throughput per GPU. Bubble size represents mean GPU power per GPU when reported; it is context, not a third optimization objective."));
    } else {
      energyContent.append(make("p","benchmark-energy-empty",
        "Validated GPU energy measurements are available, but none of these records also reports output throughput per GPU; the energy table is shown without a Pareto plot."));
    }

    const wrap=make("div","benchmark-energy-table-wrap"),table=make("table","benchmark-energy-table");
    const thead=document.createElement("thead"),header=document.createElement("tr");
    ["Configuration","GPU energy / output token","GPU energy / total token","GPU energy / input token",
     "Prefill energy / input token","Decode energy / output token","Energy / successful query",
     "Output throughput / GPU","Mean GPU power / GPU","Mean total GPU power","CPU power (separate)",
     "GPU count","Source / evidence"].forEach(label=>header.append(make("th","",label)));
    thead.append(header);table.append(thead);
    const tbody=document.createElement("tbody");
    energyRecords.forEach(item=>{
      const record=item.record,row=document.createElement("tr");
      row.dataset.recordId=record.id;
      const identity=make("td","");
      identity.append(make("strong","",record.system_name||record.system?.hardware||record.system?.accelerator_model||"System not specified"));
      identity.append(make("small","",(record.accelerator_vendor||"Unknown vendor")+" · "+
        (record.software?.framework||"Framework not reported")+" · "+(record.submitter||"Unknown submitter")));
      row.append(identity);
      row.append(make("td","",numberText(item.energy)+" J/output token"));
      row.append(make("td","",item.totalTokenEnergy?numberText(item.totalTokenEnergy.value)+" J/total token":"Not reported"));
      row.append(make("td","",item.inputTokenEnergy?numberText(item.inputTokenEnergy.value)+" J/input token":"Not reported"));
      row.append(make("td","",item.prefillEnergy?numberText(item.prefillEnergy.value)+" J/input token":"Not reported"));
      row.append(make("td","",item.decodeEnergy?numberText(item.decodeEnergy.value)+" J/output token":"Not reported"));
      row.append(make("td","",item.queryEnergy?numberText(item.queryEnergy.value)+" J/query":"Not reported"));
      row.append(make("td","",item.throughput?numberText(item.throughput.value)+" tok/s/GPU":"Not reported"));
      row.append(make("td","",item.gpuPower?numberText(item.gpuPower.value)+" W/GPU":"Not reported"));
      row.append(make("td","",item.totalGpuPower?numberText(item.totalGpuPower.value)+" W":"Not reported"));
      const cpuCell=make("td","");
      if(record.cpu_power_measurement_valid===true){
        const cpuMetric=[
          record.normalized_metrics?.mean_total_cpu_power,
          record.normalized_metrics?.mean_cpu_socket_power,
          record.normalized_metrics?.mean_total_module_power
        ].find(m=>m&&typeof m.value==="number"&&Number.isFinite(m.value)&&m.value>0&&m.direction==="context");
        cpuCell.textContent=cpuMetric?(cpuMetric.label||"CPU/module power")+": "+numberText(cpuMetric.value)+" "+cpuMetric.unit:"Validated; no CPU power value";
      }else cpuCell.textContent="Not validated / not reported";
      row.append(cpuCell);
      const count=reportedAcceleratorCount(record),gpuCell=make("td","",count?count.count+" GPUs":"Not reported");
      if(count)gpuCell.append(make("small","",count.source));
      row.append(gpuCell);
      const evidence=make("td","");
      evidence.append(make("small","","GPU power telemetry: "+(record.power_measurement_status||"status unavailable")));
      const link=make("div","benchmark-energy-source");
      addLink(link,record.detail_url||record.source_url,"Source record ↗");
      if(!link.childNodes.length)link.append(make("span","","Source link unavailable"));
      evidence.append(link);row.append(evidence);tbody.append(row);
    });
    table.append(tbody);wrap.append(table);energyContent.append(wrap);
    energyContent.append(make("p","benchmark-energy-note",
      "Measurement boundary: energy per token and GPU power are publisher-normalized GPU telemetry. CPU/socket/module telemetry is shown separately and is never added to GPU energy. No energy value is inferred from power, runtime or throughput; records without a valid GPU power verdict and schema version are excluded."));
  };



  // Publisher-reported signals only. Latency, throughput, power, and utilization
  // describe different measurement boundaries; none is a measured time breakdown.
  const renderPerformanceDecomposition = () => {
    if (!decompositionPanel || !decompositionContent) return;
    if (!activeCohort || activeCohort.sourceId !== "inferencex" ||
        !activeCohort.performanceKey || !database) {
      decompositionPanel.hidden = true;
      return;
    }
    decompositionPanel.hidden = false;
    decompositionContent.replaceChildren();
    const records = database.records.filter(record =>
      performanceKeyFor(record) === activeCohort.performanceKey
    );
    const metrics = [
      { key: "median_ttft", label: "Median TTFT", unit: "s", direction: "lower", type: "latency" },
      { key: "p99_ttft", label: "P99 TTFT", unit: "s", direction: "lower", type: "latency" },
      { key: "median_tpot", label: "Median TPOT", unit: "s", direction: "lower", type: "latency" },
      { key: "p99_tpot", label: "P99 TPOT", unit: "s", direction: "lower", type: "latency" },
      { key: "p99_itl", label: "P99 ITL", unit: "s", direction: "lower", type: "latency" },
      { key: "output_throughput_per_gpu", label: "Output throughput", unit: "tok/s/GPU", direction: "higher", type: "throughput" },
      { key: "mean_gpu_utilization", label: "Mean GPU utilization", unit: "%", direction: "context", type: "telemetry" },
      { key: "mean_gpu_memory_used", label: "Mean GPU memory used", unit: "MB", direction: "context", type: "telemetry" },
      { key: "prefill_gpu_power_per_gpu", label: "Prefill GPU power", unit: "W/GPU", direction: "context", type: "power" },
      { key: "decode_gpu_power_per_gpu", label: "Decode GPU power", unit: "W/GPU", direction: "context", type: "power" },
      { key: "prefill_energy_per_input_token", label: "Prefill GPU energy", unit: "J/input token", direction: "lower", type: "power" },
      { key: "decode_energy_per_output_token", label: "Decode GPU energy", unit: "J/output token", direction: "lower", type: "power" }
    ];
    const read = (record, spec) => {
      if (spec.type === "power" &&
          !(record.power_measurement_valid === true && record.gpu_power_metrics_available === true)) return null;
      const entry = record.normalized_metrics?.[spec.key];
      if (!entry || typeof entry.value !== "number" || !Number.isFinite(entry.value) ||
          entry.unit !== spec.unit || entry.direction !== spec.direction) return null;
      if (entry.value < 0 || (entry.value === 0 && spec.type !== "telemetry")) return null;
      return entry.value;
    };
    const sorted = [...records].sort((a, b) => String(a.id).localeCompare(String(b.id)));
    const coverage = metrics.map(spec => ({
      ...spec,
      values: sorted.map(record => read(record, spec)),
      count: sorted.filter(record => read(record, spec) !== null).length
    }));
    const coverageTotal = coverage.reduce((sum, item) => sum + item.count, 0);
    decompositionContent.append(make("p", "benchmark-decomposition-summary",
      sorted.length + " records in selected strict workload cohort · " +
      coverageTotal + " of " + (sorted.length * metrics.length) +
      " publisher-sourced signal slots populated · " +
      coverage.filter(item => item.count > 0).length + " of " + metrics.length +
      " signal types available."));

    const groupDefs = [
      { name: "Prefill / TTFT", keys: ["median_ttft", "p99_ttft"] },
      { name: "Decode / token cadence", keys: ["median_tpot", "p99_tpot", "p99_itl"] },
      { name: "Throughput", keys: ["output_throughput_per_gpu"] },
      { name: "GPU state", keys: ["mean_gpu_utilization", "mean_gpu_memory_used"] },
      { name: "GPU power / phase energy", keys: [
        "prefill_gpu_power_per_gpu", "decode_gpu_power_per_gpu",
        "prefill_energy_per_input_token", "decode_energy_per_output_token"
      ] }
    ];
    const coverageWrap = make("div", "benchmark-decomposition-coverage");
    groupDefs.forEach(group => {
      const card = make("section", "benchmark-decomposition-group");
      card.append(make("h3", "", group.name));
      group.keys.forEach(key => {
        const spec = coverage.find(item => item.key === key);
        const row = make("div", "benchmark-decomposition-coverage-row");
        row.dataset.decompositionSignal = key;
        row.append(make("span", "", spec.label));
        const meter = make("div", "benchmark-decomposition-meter");
        const fill = make("div", "benchmark-decomposition-meter-fill");
        fill.style.width = sorted.length ? (100 * spec.count / sorted.length).toFixed(1) + "%" : "0%";
        meter.append(fill);
        row.append(meter);
        row.append(make("strong", "", spec.count + "/" + sorted.length));
        card.append(row);
      });
      coverageWrap.append(card);
    });
    decompositionContent.append(coverageWrap);

    if (!sorted.length) {
      decompositionContent.append(make("p", "benchmark-decomposition-empty",
        "No records share this strict workload identity."));
      return;
    }

    const section = make("div", "benchmark-decomposition-table-wrap");
    const table = make("table", "benchmark-decomposition-table");
    const head = document.createElement("thead");
    const hr = document.createElement("tr");
    ["System / software", "Prefill signal (TTFT)", "Decode signal (TPOT / ITL)",
      "Output throughput / GPU", "GPU utilization / memory",
      "GPU phase power / energy", "GPU topology / run"].forEach(label =>
      hr.append(make("th", "", label)));
    head.append(hr);
    table.append(head);
    const body = document.createElement("tbody");
    const detail = (record, key) => {
      const spec = metrics.find(item => item.key === key);
      const value = read(record, spec);
      return value === null ? null : numberText(value) + " " + spec.unit;
    };
    const appendLines = (cell, rows, fallback) => {
      let found = 0;
      rows.forEach(([label, value]) => {
        if (value === null) return;
        cell.append(make("div", "benchmark-decomposition-reading", label + ": " + value));
        found += 1;
      });
      if (!found) cell.append(make("span", "benchmark-decomposition-missing", fallback));
    };
    sorted.forEach(record => {
      const tr = document.createElement("tr");
      tr.dataset.decompositionRecordId = record.id;
      const identity = make("td", "");
      identity.append(make("strong", "", record.system_name || record.system?.hardware || "Unspecified system"));
      identity.append(make("small", "", record.software?.framework || "Framework not reported"));
      tr.append(identity);
      const prefill = make("td", "");
      appendLines(prefill, [["Median TTFT", detail(record, "median_ttft")],
        ["P99 TTFT", detail(record, "p99_ttft")]], "TTFT not reported");
      tr.append(prefill);
      const decode = make("td", "");
      appendLines(decode, [["Median TPOT", detail(record, "median_tpot")],
        ["P99 TPOT", detail(record, "p99_tpot")],
        ["P99 ITL", detail(record, "p99_itl")]], "Decode latency not reported");
      tr.append(decode);
      tr.append(make("td", "", detail(record, "output_throughput_per_gpu") || "Not reported"));
      const state = make("td", "");
      appendLines(state, [["Mean GPU utilization", detail(record, "mean_gpu_utilization")],
        ["Mean GPU memory used", detail(record, "mean_gpu_memory_used")]],
      "GPU utilization / memory not reported");
      tr.append(state);
      const energy = make("td", "");
      appendLines(energy, [["Prefill GPU power", detail(record, "prefill_gpu_power_per_gpu")],
        ["Decode GPU power", detail(record, "decode_gpu_power_per_gpu")],
        ["Prefill energy / input token", detail(record, "prefill_energy_per_input_token")],
        ["Decode energy / output token", detail(record, "decode_energy_per_output_token")]],
        "Validated phase-energy telemetry unavailable");
      tr.append(energy);
      const topology = make("td", "");
      const count = reportedAcceleratorCount(record);
      if (count) topology.append(make("div", "", count.count + " GPUs · " + count.source));
      const serving = record.workload?.disaggregated;
      topology.append(make("div", "", serving === true ? "Disaggregated serving" :
        serving === false ? "Aggregated serving" : "Serving mode unknown"));
      const config = record.configuration || {};
      const phaseKeys = ["prefill_tp", "prefill_ep", "decode_tp", "decode_ep"];
      const reported = phaseKeys.filter(key => config[key] !== null &&
        config[key] !== undefined && config[key] !== "");
      if (reported.length) topology.append(make("small", "",
        reported.map(key => key + "=" + config[key]).join(" · ")));
      const source = make("div", "benchmark-decomposition-source");
      addLink(source, record.detail_url || record.source_url, "Source record ↗");
      topology.append(source);
      tr.append(topology);
      body.append(tr);
    });
    table.append(body);
    section.append(table);
    decompositionContent.append(section);

    const notes = make("p", "benchmark-decomposition-note",
      "Measurement semantics: TTFT is a request-level first-token latency proxy, not an isolated prefill kernel duration. TPOT and ITL are token-cadence metrics, not a measured decode-kernel breakdown. P99 figures are not added to median values. GPU utilization and memory-used are publisher telemetry, not FLOP efficiency or HBM bandwidth. Phase GPU power and token energy require validated power evidence, and their denominators differ. Absent PCIe/NVLink traffic, KV-cache occupancy, achieved FLOPs and DRAM counters, compute-, memory- and communication-bound classifications remain undetermined.");
    decompositionContent.append(notes);
  };

  const renderConfigurationAttribution = () => {
    if (!attributionPanel || !attributionContent) return;
    const supported = activeCohort && activeCohort.sourceId === "inferencex" &&
      activeCohort.performanceKey && database;
    if (!supported) {
      attributionPanel.hidden = true;
      return;
    }

    attributionPanel.hidden = false;
    attributionContent.replaceChildren();
    const cohortRecords = database.records.filter(record =>
      performanceKeyFor(record) === activeCohort.performanceKey
    );
    const dimensions = [
      { key: "hardware", label: "Accelerator" },
      { key: "gpuCount", label: "GPU count" },
      { key: "software", label: "Software stack" },
      { key: "parallelism", label: "Prefill / decode parallelism" },
      { key: "topology", label: "Node topology" }
    ];
    const parallelismKeys = [
      "prefill_tp", "prefill_ep", "prefill_dp_attention", "prefill_num_workers",
      "decode_tp", "decode_ep", "decode_dp_attention", "decode_num_workers", "offload_mode"
    ];
    const dimensionValues = record => {
      const system = record.system || {};
      const hardware = String(system.hardware || system.accelerator_model || "").trim();
      const gpuCount = reportedAcceleratorCount(record);
      const software = scalingSoftwareIdentity(record);
      const configuration = record.configuration || {};
      const parallelismEntries = parallelismKeys
        .filter(key => Object.prototype.hasOwnProperty.call(configuration, key) &&
          configuration[key] !== null && configuration[key] !== undefined && configuration[key] !== "")
        .map(key => [key, configuration[key]]);
      const topology = typeof system.is_multinode === "boolean" ? system.is_multinode : null;
      return {
        hardware: hardware ? { key: hardware.toLowerCase(), label: hardware } : null,
        gpuCount: gpuCount ? {
          key: String(gpuCount.count),
          label: gpuCount.count + " GPUs",
          evidence: gpuCount.source
        } : null,
        software: software ? { key: software.key, label: software.label } : null,
        parallelism: parallelismEntries.length ? {
          key: JSON.stringify(parallelismEntries),
          label: parallelismEntries.map(([key, value]) => key + "=" + value).join(" · ")
        } : null,
        topology: topology === null ? null : {
          key: String(topology),
          label: topology ? "Multi-node" : "Single-node"
        }
      };
    };
    const metricFor = record => {
      const metric = record.normalized_metrics?.[activeCohort.metricKey];
      if (!metric || typeof metric.value !== "number" || !Number.isFinite(metric.value) ||
          metric.unit !== activeCohort.metricUnit ||
          (metric.direction || "context") !== activeCohort.metricDirection) return null;
      return metric;
    };

    const groups = new Map();
    let metricExcluded = 0;
    cohortRecords.forEach(record => {
      const metric = metricFor(record);
      if (!metric) {
        metricExcluded += 1;
        return;
      }
      const values = dimensionValues(record);
      const signature = JSON.stringify(dimensions.map(dimension => values[dimension.key]?.key ?? null));
      if (!groups.has(signature)) {
        groups.set(signature, {
          signature,
          values,
          samples: [],
          recordIds: []
        });
      }
      const group = groups.get(signature);
      group.samples.push(metric.value);
      group.recordIds.push(record.id);
    });
    const configurations = [...groups.values()].map(group => ({
      ...group,
      median: medianValue(group.samples),
      sampleCount: group.samples.length
    }));
    const validRecordCount = configurations.reduce((sum, group) => sum + group.sampleCount, 0);

    const coverage = dimensions.map(dimension => {
      const known = cohortRecords.map(dimensionValues)
        .map(values => values[dimension.key]).filter(Boolean);
      return {
        ...dimension,
        records: known.length,
        distinct: new Set(known.map(value => value.key)).size
      };
    });

    const contrastsByDimension = new Map();
    dimensions.forEach(dimension => {
      const aggregates = new Map();
      for (let leftIndex = 0; leftIndex < configurations.length; leftIndex += 1) {
        for (let rightIndex = leftIndex + 1; rightIndex < configurations.length; rightIndex += 1) {
          const first = configurations[leftIndex];
          const second = configurations[rightIndex];
          const firstValue = first.values[dimension.key];
          const secondValue = second.values[dimension.key];
          if (!firstValue || !secondValue || firstValue.key === secondValue.key) continue;

          const controlsMatch = dimensions.every(other =>
            other.key === dimension.key ||
            (first.values[other.key]?.key ?? null) === (second.values[other.key]?.key ?? null)
          );
          if (!controlsMatch) continue;

          const firstIsA = firstValue.key.localeCompare(secondValue.key, undefined, { numeric: true }) <= 0;
          const a = firstIsA ? first : second;
          const b = firstIsA ? second : first;
          const aValue = a.values[dimension.key];
          const bValue = b.values[dimension.key];
          const pairKey = JSON.stringify([aValue.key, bValue.key]);
          if (!aggregates.has(pairKey)) {
            aggregates.set(pairKey, {
              aLabel: aValue.label,
              bLabel: bValue.label,
              aValues: [],
              bValues: [],
              deltas: [],
              percentChanges: [],
              samplesA: 0,
              samplesB: 0,
              matchedContexts: 0,
              unreportedControls: new Set(),
              recordIds: []
            });
          }
          const aggregate = aggregates.get(pairKey);
          const delta = b.median - a.median;
          aggregate.aValues.push(a.median);
          aggregate.bValues.push(b.median);
          aggregate.deltas.push(delta);
          if (a.median !== 0) aggregate.percentChanges.push(delta / Math.abs(a.median) * 100);
          aggregate.samplesA += a.sampleCount;
          aggregate.samplesB += b.sampleCount;
          aggregate.matchedContexts += 1;
          dimensions.filter(other => other.key !== dimension.key &&
            !first.values[other.key]).forEach(other => aggregate.unreportedControls.add(other.label));
          aggregate.recordIds.push(...a.recordIds, ...b.recordIds);
        }
      }
      const rows = [...aggregates.values()].map(aggregate => ({
        ...aggregate,
        medianA: medianValue(aggregate.aValues),
        medianB: medianValue(aggregate.bValues),
        medianDelta: medianValue(aggregate.deltas),
        medianPercent: medianValue(aggregate.percentChanges)
      })).sort((a, b) =>
        b.matchedContexts - a.matchedContexts ||
        Math.abs(b.medianPercent ?? b.medianDelta) - Math.abs(a.medianPercent ?? a.medianDelta) ||
        a.aLabel.localeCompare(b.aLabel)
      );
      contrastsByDimension.set(dimension.key, rows);
    });

    const totalContrasts = [...contrastsByDimension.values()]
      .reduce((sum, rows) => sum + rows.length, 0);
    const directionLabel = activeCohort.metricDirection === "higher" ? "higher is better" :
      activeCohort.metricDirection === "lower" ? "lower is better" : "context metric; no optimization direction";
    attributionContent.append(make("p", "benchmark-attribution-summary",
      cohortRecords.length + " records in the selected strict workload cohort · " +
      validRecordCount + " report the selected metric (" + activeCohort.metricLabel + ", " +
      activeCohort.metricUnit + "; " + directionLabel + ") · " + configurations.length +
      " distinct reported configuration signatures · " + totalContrasts +
      " matched one-dimension contrast groups · " + metricExcluded +
      " excluded for missing or mismatched selected-metric evidence."));

    const coverageWrap = make("div", "benchmark-attribution-coverage-wrap");
    const coverageTable = make("table", "benchmark-attribution-coverage");
    const coverageHead = document.createElement("thead");
    const coverageHeader = document.createElement("tr");
    ["Configuration dimension", "Records reporting it", "Distinct values", "Matched contrasts"].forEach(label =>
      coverageHeader.append(make("th", "", label)));
    coverageHead.append(coverageHeader);
    coverageTable.append(coverageHead);
    const coverageBody = document.createElement("tbody");
    coverage.forEach(dimension => {
      const row = document.createElement("tr");
      row.dataset.attributionCoverageDimension = dimension.key;
      row.append(make("td", "", dimension.label));
      row.append(make("td", "", dimension.records + " / " + cohortRecords.length));
      row.append(make("td", "", dimension.distinct));
      row.append(make("td", "", (contrastsByDimension.get(dimension.key) || []).length));
      coverageBody.append(row);
    });
    coverageTable.append(coverageBody);
    coverageWrap.append(coverageTable);
    attributionContent.append(coverageWrap);

    dimensions.forEach(dimension => {
      const contrasts = contrastsByDimension.get(dimension.key) || [];
      if (!contrasts.length) return;
      const card = make("section", "benchmark-attribution-dimension");
      card.dataset.attributionDimension = dimension.key;
      const heading = make("div", "benchmark-attribution-dimension-heading");
      heading.append(make("h3", "", dimension.label));
      heading.append(make("span", "", contrasts.length + " matched contrast" + (contrasts.length === 1 ? "" : "s")));
      card.append(heading);
      const tableWrap = make("div", "benchmark-attribution-table-wrap");
      const table = make("table", "benchmark-attribution-table");
      const thead = document.createElement("thead");
      const header = document.createElement("tr");
      ["Observed configuration contrast", "Median A", "Median B", "Δ B − A", "Δ %", "Matched contexts", "Samples A / B"].forEach(label =>
        header.append(make("th", "", label)));
      thead.append(header);
      table.append(thead);
      const tbody = document.createElement("tbody");
      contrasts.slice(0, 8).forEach(contrast => {
        const row = document.createElement("tr");
        row.dataset.attributionContrast = dimension.key;
        row.dataset.attributionRecords = contrast.recordIds.join(",");
        row.append(make("td", "", contrast.aLabel + " → " + contrast.bLabel));
        row.append(make("td", "", numberText(contrast.medianA) + " " + activeCohort.metricUnit));
        row.append(make("td", "", numberText(contrast.medianB) + " " + activeCohort.metricUnit));
        const delta = contrast.medianDelta;
        row.append(make("td", "", (delta > 0 ? "+" : "") + numberText(delta) + " " + activeCohort.metricUnit));
        row.append(make("td", "", contrast.medianPercent === null ? "—" :
          (contrast.medianPercent > 0 ? "+" : "") + numberText(contrast.medianPercent) + "%"));
        row.append(make("td", "", contrast.matchedContexts));
        row.append(make("td", "", contrast.samplesA + " / " + contrast.samplesB));
        tbody.append(row);
      });
      table.append(tbody);
      tableWrap.append(table);
      card.append(tableWrap);
      if (contrasts.length > 8) {
        card.append(make("p", "benchmark-attribution-note",
          "Showing 8 of " + contrasts.length + " matched contrast groups, ordered by matched-context count and observed difference."));
      }
      const unreported = [...new Set(contrasts.flatMap(contrast => [...contrast.unreportedControls]))];
      if (unreported.length) {
        card.append(make("p", "benchmark-attribution-note",
          "Some matched contrasts have unreported control dimensions: " + unreported.join(", ") +
          ". Missing fields are unknown, not defaults."));
      }
      attributionContent.append(card);
    });

    if (!totalContrasts) {
      attributionContent.append(make("p", "benchmark-attribution-empty",
        "No one-dimension contrasts can be formed from the reported configuration fields in this strict workload cohort. A contrast requires two configurations that differ in one reported dimension while all other reported dimensions match."));
    }
    attributionContent.append(make("p", "benchmark-attribution-note",
      "Interpretation: each contrast compares medians of exact configuration groups within the same strict workload cohort. A/B ordering is deterministic and Δ is B minus A; read the sign using the selected metric's optimization direction. Only the named reported dimension changes; other reported dimensions must match. Unreported fields remain unknown and may confound the result. These are observational associations, not causal estimates or a universal hardware/software ranking."));
  };

  const comparisonMetricFor = (item) => {
    const record = item.record;
    if (record.source_id === "inferencex") {
      const metric = record.normalized_metrics?.[item.descriptor.metricKey];
      if (!metric || typeof metric.value !== "number" || !Number.isFinite(metric.value)) return null;
      return { label: metric.label || item.descriptor.metricKey, value: metric.value,
        unit: metric.unit || "", direction: metric.direction || "context" };
    }
    if (typeof record.result_value !== "number" || !Number.isFinite(record.result_value)) return null;
    return { label: record.benchmark_suite + " result", value: record.result_value,
      unit: record.result_unit || "", direction: "context" };
  };

  const comparisonValue = value =>
    value === null || value === undefined || value === "" ? "Not reported" : String(value);

  const comparisonParallelism = configuration => {
    const keys = [
      "prefill_tp", "prefill_ep", "prefill_dp_attention", "prefill_num_workers",
      "decode_tp", "decode_ep", "decode_dp_attention", "decode_num_workers", "offload_mode"
    ];
    return keys.filter(key => configuration?.[key] !== null && configuration?.[key] !== undefined &&
      configuration[key] !== "").map(key => key + "=" + configuration[key]).join(" · ") || "Not reported";
  };

  const comparisonConfigurationRows = [
    ["Submitter", r => comparisonValue(r.submitter)],
    ["Accelerator", r => comparisonValue(r.system?.accelerator_model || r.system?.hardware)],
    ["Accelerator count", r => comparisonValue(r.system?.total_accelerators)],
    ["System", r => comparisonValue(r.system_name)],
    ["Nodes", r => comparisonValue(r.system?.nodes)],
    ["Framework", r => comparisonValue(r.software?.framework)],
    ["Container image", r => comparisonValue(r.software?.image)],
    ["Precision", r => comparisonValue(r.workload?.precision || r.weight_data_types)],
    ["Input / output tokens", r => {
      const isl = r.workload?.isl, osl = r.workload?.osl;
      return isl === undefined && osl === undefined ? "Not reported" :
        "ISL " + comparisonValue(isl) + " · OSL " + comparisonValue(osl);
    }],
    ["Concurrency", r => comparisonValue(r.workload?.concurrency)],
    ["Serving mode", r => typeof r.workload?.disaggregated === "boolean"
      ? (r.workload.disaggregated ? "Disaggregated" : "Aggregated") : "Not reported"],
    ["Topology", r => typeof r.system?.is_multinode === "boolean"
      ? (r.system.is_multinode ? "Multi-node" : "Single-node") : "Not reported"],
    ["Parallelism", r => comparisonParallelism(r.configuration)]
  ];

  const renderComparisonWorkspace = () => {
    if (!comparisonContent) return;
    const items = [...comparisonSelection.values()];
    if (comparisonCount) comparisonCount.textContent = items.length + " / " + maxComparisonRecords;
    if (comparisonClear) comparisonClear.disabled = items.length === 0;
    comparisonContent.replaceChildren();

    if (!items.length) {
      comparisonContent.append(make("p", "benchmark-comparison-empty",
        "Open a result’s “Configuration & source” details and choose “Add to comparison”."));
      return;
    }

    const selected = make("div", "benchmark-comparison-selected");
    items.forEach((item, index) => {
      const record = item.record;
      const chip = make("div", "benchmark-comparison-selected-item");
      const identity = make("div", "benchmark-comparison-selected-identity");
      identity.append(make("strong", "", (index + 1) + ". " +
        (record.accelerator_vendor || "Unknown vendor") + " · " +
        (record.system_name || record.system?.accelerator_model || "System not specified")));
      identity.append(make("small", "", (record.submitter || "Unknown submitter") +
        " · " + (record.model_display_name || record.model || "Model not specified")));
      chip.append(identity);
      const remove = make("button", "benchmark-comparison-remove", "Remove");
      remove.type = "button";
      remove.dataset.recordId = record.id;
      remove.addEventListener("click", () => {
        comparisonSelection.delete(record.id);
        renderRows();
      });
      chip.append(remove);
      selected.append(chip);
    });
    comparisonContent.append(selected);

    if (items.length < 2) {
      comparisonContent.append(make("p", "benchmark-comparison-note",
        "Add one more record to build a side-by-side comparison. The first selected record becomes the baseline."));
      return;
    }

    const descriptors = items.map(item => item.descriptor);
    const invalid = descriptors.find(descriptor => !descriptor || descriptor.error);
    if (invalid) {
      comparisonContent.append(make("p", "benchmark-comparison-warning",
        "Comparison unavailable: " + (invalid?.error || "one or more records lack a comparable metric definition.")));
      return;
    }
    const cohortKeys = new Set(descriptors.map(descriptor => descriptor.key));
    if (cohortKeys.size !== 1) {
      comparisonContent.append(make("p", "benchmark-comparison-warning",
        "Not directly comparable: the selected records do not share the same strict benchmark/workload definition. Remove mismatched records or select a matching cohort."));
      const definitions = make("ul", "benchmark-comparison-definitions");
      items.forEach((item, index) => {
        definitions.append(make("li", "", (index + 1) + ". " + item.descriptor.summary));
      });
      comparisonContent.append(definitions);
      return;
    }

    const metrics = items.map(comparisonMetricFor);
    if (metrics.some(metric => !metric)) {
      comparisonContent.append(make("p", "benchmark-comparison-warning",
        "Comparison unavailable: at least one selected record no longer contains the metric captured when it was added."));
      return;
    }

    const descriptor = descriptors[0];
    const direction = metrics[0].direction;
    const baseline = metrics[0];
    const banner = make("div", "benchmark-comparison-compatible");
    banner.append(make("strong", "", "Like-for-like cohort · " + descriptor.title));
    banner.append(make("p", "", descriptor.summary));
    banner.append(make("small", "", "The first selected record is the baseline. Hardware, system scale, software and parallelism remain visible variables; no composite score is calculated."));
    comparisonContent.append(banner);

    const wrap = make("div", "benchmark-comparison-table-wrap");
    const table = make("table", "benchmark-comparison-table");
    const thead = document.createElement("thead");
    const header = document.createElement("tr");
    header.append(make("th", "", "Comparison dimension"));
    items.forEach((item, index) => {
      const th = document.createElement("th");
      th.append(make("strong", "", (index === 0 ? "Baseline · " : "") +
        (item.record.accelerator_vendor || "Unknown vendor")));
      th.append(make("small", "", item.record.system_name ||
        item.record.system?.accelerator_model || "System not specified"));
      header.append(th);
    });
    thead.append(header);
    table.append(thead);

    const tbody = document.createElement("tbody");
    const metricRow = make("tr", "benchmark-comparison-metric-row");
    metricRow.append(make("th", "", metrics[0].label + (metrics[0].unit ? " · " + metrics[0].unit : "")));
    metrics.forEach((metric, index) => {
      const cell = document.createElement("td");
      cell.append(make("strong", "benchmark-comparison-value",
        numberText(metric.value) + (metric.unit ? " " + metric.unit : "")));
      if (index === 0) {
        cell.append(make("small", "benchmark-comparison-delta", "Baseline"));
      } else if (baseline.value === 0) {
        cell.append(make("small", "benchmark-comparison-delta", "Relative delta unavailable · baseline is zero"));
      } else {
        const delta = (metric.value - baseline.value) / Math.abs(baseline.value) * 100;
        const signed = (delta > 0 ? "+" : "") + delta.toFixed(1) + "%";
        let interpretation = "direction not ranked";
        if (direction === "higher") interpretation = delta > 0 ? "better (higher is better)" : delta < 0 ? "worse (higher is better)" : "equal";
        if (direction === "lower") interpretation = delta < 0 ? "better (lower is better)" : delta > 0 ? "worse (lower is better)" : "equal";
        cell.append(make("small", "benchmark-comparison-delta", "Δ " + signed + " vs baseline · " + interpretation));
      }
      metricRow.append(cell);
    });
    tbody.append(metricRow);

    comparisonConfigurationRows.forEach(([label, valueFor]) => {
      const values = items.map(item => valueFor(item.record));
      const distinct = new Set(values.map(value => value.trim().toLowerCase()));
      const row = make("tr", "benchmark-comparison-context-row" +
        (distinct.size > 1 ? " is-different" : ""));
      row.append(make("th", "", label));
      values.forEach(value => row.append(make("td", "", value)));
      tbody.append(row);
    });
    table.append(tbody);
    wrap.append(table);
    comparisonContent.append(wrap);

    const note = direction === "higher" || direction === "lower"
      ? "Relative deltas use the source-defined metric direction (“" + direction + " is better”). They are not a cross-suite score."
      : "The source does not define a higher/lower optimization direction for this result. Values and deltas are shown for context; no winner is declared.";
    comparisonContent.append(make("p", "benchmark-comparison-note", note));
  };

  const buildComparisonAction = (record) => {
    const wrapper = make("div", "benchmark-compare-actions");
    const selected = comparisonSelection.has(record.id);
    const descriptor = selected ? comparisonSelection.get(record.id).descriptor : buildCohortDescriptor(record);
    const atLimit = !selected && comparisonSelection.size >= maxComparisonRecords;
    const button = make("button", "benchmark-compare-action",
      selected ? "Remove from comparison" : atLimit ? "Comparison full" : "Add to comparison");
    button.type = "button";
    button.disabled = !selected && (atLimit || Boolean(descriptor?.error));
    if (!selected && descriptor?.error) button.title = descriptor.error;
    if (atLimit) button.title = "Remove one selected record before adding another.";
    button.addEventListener("click", () => {
      if (selected) comparisonSelection.delete(record.id);
      else comparisonSelection.set(record.id, { record, descriptor });
      renderRows();
    });
    wrapper.append(button);
    if (!selected && descriptor?.error) {
      wrapper.append(make("small", "benchmark-compare-note", descriptor.error));
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
    body.append(buildComparisonAction(record));
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


  const hasQualityValue = value => {
    if (value === null || value === undefined) return false;
    if (typeof value === "string") return value.trim() !== "" && value.trim().toLowerCase() !== "unknown";
    if (typeof value === "number") return Number.isFinite(value);
    if (typeof value === "boolean") return true;
    return false;
  };

  const renderQualityDashboard = (records) => {
    const host = $("[data-results-quality-content]");
    if (!host) return;
    host.replaceChildren();
    if (!records.length) {
      host.append(make("p", "benchmark-quality-empty", "No records are available for quality analysis."));
      return;
    }
    const dimensions = [
      { label: "Source attribution", fields: ["submitter", "source URL", "source record key"], applicable: () => true, value: r => [r.submitter, r.source_url, r.source_record_key].every(hasQualityValue) },
      { label: "Model & scenario", fields: ["model", "scenario", "version"], applicable: () => true, value: r => [r.model, r.scenario, r.benchmark_version].every(hasQualityValue) },
      { label: "Hardware identity", fields: ["accelerator model", "accelerator count"], applicable: () => true, value: r => hasQualityValue(r.system?.accelerator_model) && hasQualityValue(r.system?.total_accelerators) },
      { label: "Software stack", fields: ["framework"], applicable: () => true, value: r => hasQualityValue(r.software?.framework) },
      { label: "Workload shape", fields: ["ISL", "OSL", "concurrency", "workload type"], applicable: r => r.source_id === "inferencex", value: r => [r.workload?.isl, r.workload?.osl, r.workload?.concurrency, r.workload?.benchmark_type].every(hasQualityValue) },
      { label: "Precision & serving", fields: ["precision", "speculative mode", "serving mode"], applicable: r => r.source_id === "inferencex", value: r => [r.workload?.precision || r.weight_data_types, r.workload?.speculative_method, r.workload?.disaggregated].every(hasQualityValue) },
      { label: "Topology", fields: ["node topology"], applicable: r => r.source_id === "inferencex", value: r => hasQualityValue(r.system?.is_multinode) },
      { label: "Comparable metric", fields: ["normalized metric and unit"], applicable: r => r.source_id === "inferencex", value: r => Object.values(r.normalized_metrics || {}).some(m => typeof m?.value === "number" && hasQualityValue(m.unit)) }
    ];
    const heading = make("div", "benchmark-quality-overview");
    const complete = records.filter(r => [r.submitter, r.model, r.scenario, r.system_type, r.source_url].every(hasQualityValue)).length;
    const summary = make("div", "benchmark-quality-score");
    summary.append(make("strong", "", Math.round(100 * complete / records.length) + "%"));
    summary.append(make("span", "", " records have core provenance"));
    heading.append(summary);
    heading.append(make("p", "benchmark-quality-note", "Coverage is calculated only over applicable records. Missing metadata is not a failed measurement; InferenceX-specific fields do not penalize MLPerf."));
    host.append(heading);
    const table = make("div", "benchmark-quality-table");
    const header = make("div", "benchmark-quality-row benchmark-quality-header");
    ["Dimension", "Coverage", "Records", "Missing"].forEach(label => header.append(make("span", "", label)));
    table.append(header);
    dimensions.forEach(d => {
      const applicable = records.filter(d.applicable);
      if (!applicable.length) return;
      const covered = applicable.filter(d.value).length, missing = applicable.length - covered;
      const row = make("div", "benchmark-quality-row");
      row.append(make("strong", "", d.label));
      const meter = make("div", "benchmark-quality-meter"), track = make("span", "benchmark-quality-track");
      const fill = make("span", "benchmark-quality-fill");
      fill.style.width = Math.round(100 * covered / applicable.length) + "%";
      track.append(fill);
      meter.append(track, make("small", "", Math.round(100 * covered / applicable.length) + "%"));
      row.append(meter, make("span", "benchmark-quality-number", covered), make("span", "benchmark-quality-number", missing));
      row.title = "Required fields: " + d.fields.join(", ");
      table.append(row);
    });
    host.append(table);
    const inferencex = records.filter(r => r.source_id === "inferencex");
    if (inferencex.length) {
      const power = make("div", "benchmark-quality-power");
      power.append(make("h3", "", "Measurement validation · InferenceX"));
      [["GPU power", "power_measurement_status"], ["CPU / module power", "cpu_power_measurement_status"]].forEach(([label, key]) => {
        const counts = new Map();
        inferencex.forEach(r => { const status = r[key] || "unreported"; counts.set(status, (counts.get(status) || 0) + 1); });
        const line = make("p", "benchmark-quality-status");
        line.append(make("strong", "", label + ": "));
        line.append(document.createTextNode([...counts.entries()].sort((a,b) => a[0].localeCompare(b[0])).map(([k,v]) => k + " " + v).join(" · ")));
        power.append(line);
      });
      host.append(power);
    }
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
    renderComparisonWorkspace();
    renderScalingAnalysis(filteredRecords);
    renderParetoFrontier();
    renderEnergyEfficiency();
    renderConfigurationAttribution();
    renderPerformanceDecomposition();
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
  if (comparisonClear) comparisonClear.addEventListener("click", () => {
    comparisonSelection.clear();
    renderRows();
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
      renderQualityDashboard(data.records);
      load.hidden = true;
      root.dataset.loaded = "true";
      applyFilters();
    })
    .catch(error => {
      load.classList.add("is-error");
      load.textContent = error.message;
    });
})();
