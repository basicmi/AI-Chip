(() => {
  const root = document.querySelector("[data-coverage-explorer]");
  if (!root) return;
  const $ = selector => root.querySelector(selector);
  const dimensions = {
    model: {label:"Model", get:r=>r.model_display_name},
    hardware: {label:"Hardware", get:r=>r.system?.hardware},
    framework: {label:"Framework", get:r=>r.software?.framework},
    recipe: {label:"Recipe fingerprint", get:r=>r.software?.recipe_fingerprint},
    "benchmark-version": {label:"Benchmark version", get:r=>r.benchmark_version},
    isl: {label:"ISL", get:r=>r.workload?.isl},
    osl: {label:"OSL", get:r=>r.workload?.osl},
    concurrency: {label:"Concurrency", get:r=>r.workload?.concurrency},
    precision: {label:"Precision", get:r=>r.workload?.precision || r.weight_data_types},
    "serving-mode": {label:"Serving mode", get:r=>typeof r.workload?.disaggregated==="boolean" ? (r.workload.disaggregated?"Disaggregated":"Aggregated") : null},
    "prefill-gpus": {label:"Prefill GPUs", get:r=>r.system?.physical_prefill_gpus},
    "decode-gpus": {label:"Decode GPUs", get:r=>r.system?.physical_decode_gpus},
    topology: {label:"Topology", get:r=>typeof r.system?.is_multinode==="boolean" ? (r.system.is_multinode?"Multi-node":"Single-node") : null},
    configuration: {label:"Stable configuration", get:r=>stableConfig(r)}
  };
  const stableKeys=["prefill_tp","prefill_ep","prefill_dp_attention","prefill_num_workers","decode_tp","decode_ep","decode_dp_attention","decode_num_workers","offload_mode"];
  const metrics = {
    output_throughput_per_gpu:["tok/s/GPU","throughput","higher"],
    median_interactivity:["tok/s/user","interactivity","higher"],
    median_ttft:["s","latency","lower"],
    p99_ttft:["s","latency","lower"],
    median_tpot:["s","latency","lower"],
    p99_tpot:["s","latency","lower"],
    p99_itl:["s","latency","lower"]
  };
  const valid = value => value!==null && value!==undefined &&
    !(typeof value==="string" && ["","unknown","not reported","n/a","none"].includes(value.trim().toLowerCase())) &&
    !(typeof value==="number" && !Number.isFinite(value));
  const stableConfig = r => {
    const c=r.configuration;
    if (!c || typeof c!=="object") return null;
    const result={};
    stableKeys.forEach(k=>{if (Object.prototype.hasOwnProperty.call(c,k)) result[k]=c[k];});
    return Object.keys(result).length ? result : null;
  };
  const fmt = n => new Intl.NumberFormat("en-US",{maximumFractionDigits:2}).format(n);
  const el=(tag,cls,txt)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(txt!==undefined)n.textContent=String(txt);return n;};
  const setStat=(key,value)=>{const n=$("[data-coverage-stat='"+key+"']");if(n)n.textContent=fmt(value);};
  let records=[], gaps=[], page=1, pageSize=15;

  const metricValid=(r,key,definition)=>{
    const m=r.normalized_metrics?.[key];
    return !!m && typeof m.value==="number" && Number.isFinite(m.value) && m.value>=0 &&
      m.unit===definition[0] && m.family===definition[1] && m.direction===definition[2];
  };
  const blockers=r=>{
    const b=[];
    const nonempty=v=>valid(v);
    ["id","benchmark_suite","model","scenario","division","availability","weight_data_types"].forEach(k=>{if(!nonempty(r[k]))b.push("missing_"+k);});
    if(r.inferred!==false)b.push("inferred_or_unknown");
    if(r.errors!==0)b.push("errors_unknown_or_nonzero");
    const s=r.system||{}, sw=r.software||{}, w=r.workload||{};
    if(!r.system || typeof r.system!=="object")b.push("missing_system");
    if(!nonempty(sw.framework))b.push("missing_framework");
    if(!nonempty(s.hardware)||["unknown","not reported"].includes(String(s.hardware).trim().toLowerCase()))b.push("missing_hardware");
    if(!w || typeof w!=="object")b.push("missing_workload");
    ["benchmark_type","isl","osl","concurrency","precision"].forEach(k=>{if(w[k]===null||w[k]===undefined||w[k]===""||w[k]==="unknown")b.push("missing_"+k);});
    if(typeof w.disaggregated!=="boolean")b.push("missing_serving_mode");
    if(!nonempty(w.speculative_method))b.push("missing_speculative_method");
    if(!r.configuration||typeof r.configuration!=="object")b.push("missing_configuration");
    ["physical_prefill_gpus","physical_decode_gpus"].forEach(k=>{const v=s[k];if(typeof v!=="number"||!Number.isFinite(v)||v<0)b.push("missing_"+k);});
    if(typeof s.is_multinode!=="boolean")b.push("missing_topology");
    if(!nonempty(r.model_display_name))b.push("missing_model_display_name");
    if(!Object.entries(r.normalized_metrics||{}).some(([k,m])=>m&&typeof m.value==="number"&&Number.isFinite(m.value)))b.push("missing_numeric_metric");
    return b;
  };
  const drawBars=()=>{
    const key=$("[data-coverage-dimension]").value, def=dimensions[key];
    const values=new Map();let missing=0;
    records.forEach(r=>{const v=def.get(r);if(!valid(v)){missing++;return;}const label=typeof v==="object"?JSON.stringify(v):String(v);values.set(label,(values.get(label)||0)+1);});
    const presentCount=records.length-missing, pct=records.length?presentCount/records.length*100:0;
    $("[data-coverage-dimension-summary]").textContent=def.label+": "+fmt(presentCount)+" / "+fmt(records.length)+" records ("+fmt(pct)+"% coverage); "+fmt(values.size)+" distinct reported values.";
    const host=$("[data-coverage-bars]");host.replaceChildren();
    const bar=el("div","coverage-bar-row");bar.append(el("span","coverage-bar-label","Reported"));const track=el("div","coverage-bar-track");const fill=el("span","coverage-bar-fill");fill.style.width=pct+"%";track.append(fill);bar.append(track,el("strong","coverage-bar-value",fmt(pct)+"%"));host.append(bar);
    const miss=el("div","coverage-bar-row");miss.append(el("span","coverage-bar-label","Missing"));const mt=el("div","coverage-bar-track");const mf=el("span","coverage-bar-missing");mf.style.width=(100-pct)+"%";mt.append(mf);miss.append(mt,el("strong","coverage-bar-value",fmt(missing)));host.append(miss);
    const list=$("[data-coverage-values]");list.replaceChildren();
    [...values.entries()].sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0])).slice(0,12).forEach(([label,count])=>{
      const item=el("div","coverage-value-item");item.append(el("span","",label),el("strong","",fmt(count)+" · "+fmt(count/records.length*100)+"%"));list.append(item);
    });
    if(values.size>12)list.append(el("p","coverage-note",(values.size-12)+" additional distinct values not shown."));
  };
  const drawMetrics=()=>{
    const host=$("[data-coverage-metrics]");host.replaceChildren();
    Object.entries(metrics).forEach(([key,def])=>{
      const count=records.filter(r=>metricValid(r,key,def)).length,pct=records.length?count/records.length*100:0;
      const row=el("div","coverage-metric-row");const top=el("div","coverage-metric-top");
      top.append(el("strong","",key.replaceAll("_"," ")),el("span","",fmt(count)+" / "+fmt(records.length)+" · "+fmt(pct)+"%"));
      const track=el("div","coverage-bar-track");const fill=el("span","coverage-bar-fill");fill.style.width=pct+"%";track.append(fill);
      row.append(top,track,el("small","coverage-note",def[0]+" · "+def[1]+" · "+def[2]+" is better"));host.append(row);
    });
  };
  const fieldValue=(r,key)=>dimensions[key]?.get(r);
  const drawGaps=()=>{
    const key=$("[data-coverage-gap-field]").value, query=$("[data-coverage-search]").value.trim().toLowerCase();
    gaps=records.filter(r=>!valid(fieldValue(r,key))).filter(r=>!query||[r.id,r.model_display_name,r.model,r.system?.hardware,r.submitter].join(" ").toLowerCase().includes(query));
    const pages=Math.max(1,Math.ceil(gaps.length/pageSize));page=Math.min(page,pages);
    const start=(page-1)*pageSize,shown=gaps.slice(start,start+pageSize),body=$("[data-coverage-gap-rows]");body.replaceChildren();
    shown.forEach(r=>{
      const tr=document.createElement("tr");const id=el("td","",r.id||"—");const model=el("td","",r.model_display_name||r.model||"—");const hw=el("td","",r.system?.hardware||"—");const missing=el("td","",dimensions[key].label);
      const src=el("td","");const url=r.detail_url||r.source_url;if(url){try{const u=new URL(url);if(["http:","https:"].includes(u.protocol)){const a=el("a","","Open source ↗");a.href=u.href;a.target="_blank";a.rel="noopener noreferrer";src.append(a);}}catch(_){}}
      tr.append(id,model,hw,missing,src);body.append(tr);
    });
    $("[data-coverage-gap-count]").textContent=fmt(gaps.length)+" records missing "+dimensions[key].label+" · showing "+(gaps.length?start+1:0)+"–"+(start+shown.length);
    $("[data-coverage-page]").textContent="Page "+page+" of "+pages;
    $("[data-coverage-prev]").disabled=page<=1;$("[data-coverage-next]").disabled=page>=pages;
  };
  const render=()=>{
    drawBars();drawMetrics();drawGaps();
    const complete=records.filter(r=>blockers(r).length===0).length;
    const hardwareRecipe=records.filter(r=>valid(r.system?.hardware)&&valid(r.software?.recipe_fingerprint)).length;
    const metricRows=records.filter(r=>Object.entries(metrics).some(([k,d])=>metricValid(r,k,d))).length;
    setStat("records",records.length);setStat("comparable",complete);setStat("hardware-recipe",hardwareRecipe);setStat("metrics",metricRows);
  };
  const loadRegistry=async()=>{
    const response=await fetch(root.dataset.source,{cache:"no-cache"});if(!response.ok)throw new Error("Registry request failed: HTTP "+response.status);
    const bytes=await response.arrayBuffer();const zipped=bytes.byteLength>=2&&new Uint8Array(bytes)[0]===31&&new Uint8Array(bytes)[1]===139;
    if(zipped){if(typeof DecompressionStream!=="function")throw new Error("This browser cannot decompress the registry. Open the raw JSON registry instead.");return new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream("gzip"))).json();}
    return JSON.parse(new TextDecoder().decode(bytes));
  };
  $("[data-coverage-dimension]").addEventListener("change",drawBars);
  $("[data-coverage-gap-field]").addEventListener("change",()=>{page=1;drawGaps();});
  $("[data-coverage-search]").addEventListener("input",()=>{page=1;drawGaps();});
  $("[data-coverage-prev]").addEventListener("click",()=>{page--;drawGaps();});
  $("[data-coverage-next]").addEventListener("click",()=>{page++;drawGaps();});
  loadRegistry().then(data=>{
    if(!Array.isArray(data.records))throw new Error("Registry has no records array.");
    records=data.records.filter(r=>r.source_id==="inferencex");
    document.querySelector("[data-coverage-version]").textContent=data.database_version||"—";
    document.querySelector("[data-coverage-imported]").textContent=data.last_imported||data.last_updated||"—";
    $("[data-coverage-load]").hidden=true;
    if(!records.length)throw new Error("No InferenceX records were found in the registry.");
    render();
  }).catch(error=>{
    $("[data-coverage-load]").hidden=true;
    const box=$("[data-coverage-error]");box.hidden=false;box.textContent=error.stack||error.message;
  });
})();
