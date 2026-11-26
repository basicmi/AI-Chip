(() => {
  const root=document.querySelector("[data-diagnosis-workbench]");if(!root)return;
  const $=s=>root.querySelector(s);
  const valid=v=>v!==null&&v!==undefined&&!(typeof v==="string"&&["","unknown","not reported","n/a","none"].includes(v.trim().toLowerCase()));
  const make=(tag,cls,value)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(value!==undefined)n.textContent=String(value);return n;};
  const fmt=v=>typeof v==="number"?new Intl.NumberFormat("en-US",{maximumFractionDigits:4}).format(v):String(v??"Not reported");
  const safeLink=(parent,url,label)=>{try{const u=new URL(url);if(!["https:","http:"].includes(u.protocol))return;const a=make("a","",label);a.href=u.href;a.target="_blank";a.rel="noopener noreferrer";parent.append(a);}catch(_){}};
  const metricDefs=[
    ["median_ttft","Median TTFT"],["p99_ttft","P99 TTFT"],["median_tpot","Median TPOT"],["p99_tpot","P99 TPOT"],["p99_itl","P99 ITL"],["output_throughput_per_gpu","Output throughput/GPU"],["median_interactivity","Median interactivity"],["mean_gpu_utilization","Mean GPU utilization"],["mean_gpu_memory_used","Mean GPU memory used"]
  ];
  const groups=[
    {id:"compute",title:"Compute / Roofline",need:["compute_flop_count","theoretical_peak_flops","sm_active_pct","tensor_active_pct"],optional:["dram_read_bytes","dram_write_bytes","dram_peak_bandwidth_bytes_per_s"],explain:"A measured arithmetic-intensity/roofline position needs interval FLOPs, DRAM read+write totals, a matching precision/sparsity peak, DRAM peak bandwidth and a valid sampling window. Activity percentages alone do not establish a compute bottleneck.",next:"Capture interval FLOP counts and SM/Tensor activity; pair with precision-matched peak FLOP/s and DRAM byte counters over the same sampling interval."},
    {id:"memory",title:"Memory bandwidth",need:["dram_read_bytes","dram_write_bytes","dram_peak_bandwidth_bytes_per_s"],optional:["dram_bandwidth_bytes_per_s","dram_bandwidth_utilization_pct","hbm_used_bytes","hbm_capacity_bytes"],explain:"DRAM byte totals and a same-boundary peak can support achieved bandwidth and a ceiling comparison. A counter value alone does not establish saturation or critical-path impact.",next:"Collect DRAM read/write byte totals or achieved bytes/s and a same-device peak bandwidth measurement; align scope and time window."},
    {id:"communication",title:"Interconnect / communication",need:["link_bandwidth_bytes_per_s","link_peak_bandwidth_bytes_per_s"],optional:["link_utilization_pct","nvlink_tx_bytes","nvlink_rx_bytes","pcie_tx_bytes","pcie_rx_bytes","network_tx_bytes","network_rx_bytes"],explain:"Per-link directional traffic and matching directional capacity are needed to estimate utilization. Even high utilization does not prove the link is on the critical path.",next:"Collect per-link TX/RX counters, directionality-matched capacity, topology and request-correlated communication intervals."},
    {id:"kv",title:"KV cache capacity pressure",need:["kv_cache_used_bytes","kv_cache_capacity_bytes"],optional:["kv_cache_tokens","kv_cache_token_capacity","kv_cache_hit_rate_pct"],explain:"Used/capacity pairs must share scope and entity. Occupancy alone does not prove allocator pressure, eviction, preemption or decode stalls.",next:"Capture KV-cache used bytes/tokens, capacity, allocator events, eviction/preemption counters and request-level stalls at a matching boundary."},
    {id:"thermal",title:"Thermal / power throttling",need:["throttle_active_pct"],optional:["temperature_c","gpu_power_w","gpu_clock_hz","memory_clock_hz"],explain:"A non-zero throttle-active counter is direct evidence of throttle activity during the sampled window. Temperature, power or clock values alone do not prove throttling.",next:"Capture throttle reason counters with synchronized clocks, GPU clocks, power and temperature across the workload interval."},
    {id:"runtime",title:"Runtime scheduling / queueing",need:[],optional:[],trace:["queue_wait","batch_wait","cpu_scheduling","host_runtime","kernel","communication_wait","prefill","decode"],explain:"TTFT/TPOT and throughput do not isolate queue wait, batch formation, CPU dispatch, kernel gaps or synchronization. Request-correlated traces are required.",next:"Capture request arrival, queue-wait, batch formation, dispatch, CPU scheduling and kernel intervals with correlation IDs and a common clock."}
  ];
  let records=[],filtered=[];
  const hardwareMetrics=r=>Array.isArray(r.hardware_evidence?.metrics)?r.hardware_evidence.metrics:[];
  const selectRecord=id=>records.find(r=>r.id===id);
  const evidenceHas=(metrics,id)=>metrics.some(m=>m.metric_id===id);
  const showRecord=r=>{
    const summary=$("[data-dw-record-summary]");summary.replaceChildren();
    const title=make("h3","",r.model_display_name||r.model||"Model not reported");
    const details=make("dl","dw-meta");
    [["Record",r.id],["Benchmark",r.benchmark_suite],["Version",r.benchmark_version],["Scenario",r.scenario],["Division",r.division],["Hardware",r.system?.hardware||r.system?.accelerator_model||r.product_id],["Framework",r.software?.framework],["Precision",r.workload?.precision||r.weight_data_types],["Evidence class",r.evidence_level||r.source_class]].forEach(([k,v])=>{details.append(make("dt","",k),make("dd","",valid(v)?v:"Not reported"));});
    const links=make("div","dw-links");safeLink(links,r.detail_url||r.source_url,"Open publisher record ↗");safeLink(links,r.dataset_url,"Open dataset ↗");
    summary.append(title,details,links);
    const runtime=$("[data-dw-runtime]");runtime.replaceChildren();
    const table=make("div","dw-table-wrap"),tbl=make("table","dw-table"),thead=make("thead",""),tr=make("tr","");["Metric","Observed value","Unit","Source metric"].forEach(x=>tr.append(make("th","",x)));thead.append(tr);tbl.append(thead);
    const body=make("tbody","");let count=0;
    metricDefs.forEach(([key,label])=>{const m=r.normalized_metrics?.[key];if(!m||typeof m.value!=="number"||!Number.isFinite(m.value))return;const row=make("tr","");[label,fmt(m.value),m.unit||"—",m.source_metric||"Not reported"].forEach(v=>row.append(make("td","",v)));body.append(row);count++;});
    tbl.append(body);table.append(tbl);
    if(!count)runtime.append(make("p","dw-empty","No recognized normalized serving metrics are attached to this record. Missing metrics are unknown, not zero."));
    else runtime.append(table,make("p","dw-note",count+" recognized normalized metrics shown. These are observations, not causal diagnosis."));
    const ev=r.hardware_evidence,metrics=hardwareMetrics(r),trace=r.runtime_trace;
    const host=$("[data-dw-evidence]");host.replaceChildren();
    const ids=[...new Set(metrics.map(m=>m.metric_id))];
    const card=(label,value,sub)=>{const n=make("div","dw-evidence-card");n.append(make("span","",label),make("strong","",value),make("small","",sub));host.append(n);};
    card("Profiler metrics",metrics.length,ev?"Attached hardware_evidence bundle":"No hardware_evidence bundle attached");
    card("Distinct metric IDs",ids.length,ids.length?ids.join(", "):"No hardware counters or telemetry reported");
    card("Runtime trace events",Array.isArray(trace?.events)?trace.events.length:0,trace?"Runtime trace attached":"No runtime_trace bundle attached");
    card("Trace clock",trace?.clock_domain||"Unknown",trace?.collector?.name||"No trace collector metadata");
    const prov=$("[data-dw-provenance]");prov.replaceChildren();
    if(ev){const e=ev.provenance||{},s=ev.sampling||{},scope=ev.system_scope||{};prov.append(make("p","", "Profiler provenance: "+(e.source_type||"unknown")+" · collector "+(ev.collector?.name||"unknown")+" · scope "+(scope.scope_type||"unknown")+" · devices "+(scope.device_count??"unknown")+" · sample "+(s.started_at||"unknown")+" → "+(s.ended_at||"unknown")));safeLink(prov,e.source_url,"Open profiler evidence ↗");}
    if(trace){const e=trace.provenance||{};prov.append(make("p","","Runtime trace provenance: "+(e.source_type||"unknown")+" · collector "+(trace.collector?.name||"unknown")+" · clock "+(trace.clock_domain||"unknown")+" · events "+(trace.events?.length||0)));safeLink(prov,e.source_url,"Open runtime trace ↗");if(trace.clock_domain==="monotonic_ns")prov.append(make("p","dw-note","Monotonic clock mapping present: "+(trace.clock_mapping?"yes":"no")+"; cross-clock alignment must be validated."));}
    if(!ev&&!trace)prov.append(make("p","dw-note","No profiler or runtime trace provenance is attached. Public benchmark serving metrics remain available independently."));
    const mechanisms=$("[data-dw-mechanisms]");mechanisms.replaceChildren();
    groups.forEach(g=>{
      const found=g.need.filter(id=>evidenceHas(metrics,id)),missing=g.need.filter(id=>!evidenceHas(metrics,id)),optional=g.optional.filter(id=>evidenceHas(metrics,id));
      const traceEvents=Array.isArray(trace?.events)?trace.events:[];
      const foundTrace=g.trace?g.trace.filter(cat=>traceEvents.some(e=>e.category===cat)):[],missingTrace=g.trace?g.trace.filter(cat=>!traceEvents.some(e=>e.category===cat)):[];
      const box=make("article","dw-mechanism");box.append(make("h3","",g.title));
      const state= g.id==="runtime"?(foundTrace.length?"Trace categories observed":"No trace categories observed"):(found.length?"Some required metric IDs observed":"No required metric IDs observed");
      box.append(make("span","dw-state",state));
      const coverage=make("p","dw-coverage",g.id==="runtime"?"Trace categories: "+(foundTrace.join(", ")||"none")+". Missing: "+(missingTrace.join(", ")||"none"):"Required observed: "+(found.join(", ")||"none")+". Missing: "+(missing.join(", ")||"none")+". Optional observed: "+(optional.join(", ")||"none"));
      box.append(coverage,make("p","dw-explain",g.explain),make("p","dw-next","Next measurement: "+g.next));
      mechanisms.append(box);
    });
    mechanisms.append(make("p","dw-note","No bottleneck verdict is generated in this browser view. For validated scope/entity matching, precision checks, roofline calculations, communication analysis and evidence validation, use the repository diagnosis engine against the record and its attached evidence bundle."));
  };
  const renderOptions=()=>{
    const q=$("[data-dw-search]").value.trim().toLowerCase();
    filtered=records.filter(r=>[r.id,r.model_display_name,r.model,r.system?.hardware,r.system?.accelerator_model,r.product_id,r.software?.framework].join(" ").toLowerCase().includes(q));
    const select=$("[data-dw-record]"),prior=select.value;select.replaceChildren();const first=document.createElement("option");first.value="";first.textContent="Select a record…";select.append(first);
    filtered.slice(0,1000).forEach(r=>{const o=document.createElement("option");o.value=r.id;o.textContent=[r.id,r.model_display_name||r.model,r.system?.hardware||r.system?.accelerator_model||r.product_id].filter(valid).join(" · ");select.append(o);});
    if(filtered.some(r=>r.id===prior))select.value=prior;else if(filtered.length){select.value=filtered[0].id;showRecord(filtered[0]);}
    else{$("[data-dw-record-summary]").replaceChildren(make("p","dw-empty","No records match this search."));}
    $("[data-dw-status]").textContent="Showing "+Math.min(filtered.length,1000)+" of "+filtered.length+" matching records. Selection is limited to the first 1,000 options.";
  };
  const load=async()=>{
    const res=await fetch(root.dataset.source,{cache:"no-cache"});if(!res.ok)throw new Error("Registry request failed: HTTP "+res.status);
    const buf=await res.arrayBuffer(),bytes=new Uint8Array(buf);
    if(bytes[0]===31&&bytes[1]===139){if(typeof DecompressionStream!=="function")throw new Error("This browser cannot decompress the benchmark registry.");return new Response(new Blob([buf]).stream().pipeThrough(new DecompressionStream("gzip"))).json();}
    return JSON.parse(new TextDecoder().decode(buf));
  };
  $("[data-dw-search]").addEventListener("input",renderOptions);
  $("[data-dw-record]").addEventListener("change",e=>{const r=selectRecord(e.target.value);if(r)showRecord(r);});
  load().then(data=>{
    if(!Array.isArray(data.records))throw new Error("Registry records array missing");
    records=data.records.filter(r=>r&&r.availability==="published");
    const count=(predicate)=>records.filter(predicate).length;
    [["records",records.length],["hardware",count(r=>!!r.hardware_evidence)],["traces",count(r=>!!r.runtime_trace)],["serving",count(r=>metricDefs.some(([k])=>typeof r.normalized_metrics?.[k]?.value==="number"))]].forEach(([key,value])=>{$("[data-dw-stat='"+key+"']").textContent=new Intl.NumberFormat("en-US").format(value);});
    $("[data-dw-load]").hidden=true;renderOptions();
  }).catch(error=>{$("[data-dw-load]").hidden=true;const box=$("[data-dw-error]");box.hidden=false;box.textContent=error.stack||error.message;});
})();
