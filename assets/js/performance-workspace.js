(() => {
  const root=document.querySelector("[data-performance-workspace]");
  if(!root)return;
  const $=s=>root.querySelector(s);
  const metricDefs={
    output_throughput_per_gpu:{label:"Output throughput / GPU",unit:"tok/s/GPU",family:"throughput",direction:"higher"},
    median_interactivity:{label:"Median interactivity",unit:"tok/s/user",family:"interactivity",direction:"higher"},
    median_ttft:{label:"Median TTFT",unit:"s",family:"latency",direction:"lower"},
    p99_ttft:{label:"P99 TTFT",unit:"s",family:"latency",direction:"lower"},
    median_tpot:{label:"Median TPOT",unit:"s",family:"latency",direction:"lower"},
    p99_tpot:{label:"P99 TPOT",unit:"s",family:"latency",direction:"lower"},
    p99_itl:{label:"P99 ITL",unit:"s",family:"latency",direction:"lower"}
  };
  const valid=v=>v!==null&&v!==undefined&&!(typeof v==="string"&&["","unknown","not reported","n/a","none"].includes(v.trim().toLowerCase()));
  const unique=values=>[...new Set(values.filter(valid).map(v=>String(v)))].sort((a,b)=>a.localeCompare(b,undefined,{numeric:true}));
  const text=(node,value)=>{if(node)node.textContent=value;};
  const make=(tag,cls,value)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(value!==undefined)n.textContent=String(value);return n;};
  const metricValue=(r,key)=>{const m=r.normalized_metrics?.[key],d=metricDefs[key];if(!m||!d||typeof m.value!=="number"||!Number.isFinite(m.value)||m.value<0||m.unit!==d.unit||m.family!==d.family||m.direction!==d.direction)return null;return m.value;};
  const fields={
    model:r=>r.model_display_name||r.model,
    hardware:r=>r.system?.hardware,
    framework:r=>r.software?.framework,
    benchmark_type:r=>r.workload?.benchmark_type,
    precision:r=>r.workload?.precision||r.weight_data_types,
    serving:r=>typeof r.workload?.disaggregated==="boolean"?(r.workload.disaggregated?"Disaggregated":"Aggregated"):null
  };
  let all=[],filtered=[],metricKey="output_throughput_per_gpu";
  const getFilters=()=>Object.fromEntries(Object.keys(fields).map(k=>[k,$("[data-pw-filter='"+k+"']").value]));
  const applyFilters=()=>{
    const selected=getFilters();
    filtered=all.filter(r=>Object.entries(selected).every(([k,v])=>!v||String(fields[k](r)??"")===v));
    render();
  };
  const setStat=(key,value)=>text($("[data-pw-stat='"+key+"']"),new Intl.NumberFormat("en-US").format(value));
  const addSelectOptions=(select,values)=>{const current=select.value;while(select.options.length>1)select.remove(1);values.forEach(v=>{const o=document.createElement("option");o.value=v;o.textContent=v;select.append(o);});if(values.includes(current))select.value=current;};
  const renderEvidence=()=>{
    const host=$("[data-pw-evidence]");host.replaceChildren();
    const counts=[
      ["Records in selection",filtered.length],
      ["With hardware identity",filtered.filter(r=>valid(r.system?.hardware)).length],
      ["With recipe fingerprint",filtered.filter(r=>valid(r.software?.recipe_fingerprint)).length],
      ["With stable configuration",filtered.filter(r=>r.configuration&&Object.keys(r.configuration).length>0).length],
      ["With workload dimensions",filtered.filter(r=>valid(r.workload?.isl)&&valid(r.workload?.osl)&&valid(r.workload?.concurrency)).length],
      ["With source-linked evidence",filtered.filter(r=>valid(r.detail_url||r.source_url)).length]
    ];
    counts.forEach(([label,count])=>{const card=make("div","pw-evidence-card");card.append(make("span","",label),make("strong","",count+" / "+filtered.length));const pct=filtered.length?count/filtered.length*100:0;const track=make("div","pw-evidence-track");const fill=make("span","");fill.style.width=pct+"%";track.append(fill);card.append(track);host.append(card);});
  };
  const renderObservations=()=>{
    const key=metricKey,def=metricDefs[key],items=filtered.map(r=>({r,value:metricValue(r,key)})).filter(x=>x.value!==null);
    const body=$("[data-pw-observations]");body.replaceChildren();
    items.slice(0,100).forEach(({r,value})=>{
      const tr=document.createElement("tr");
      const id=make("td","",r.id||"—"),model=make("td","",r.model_display_name||r.model||"—"),hardware=make("td","",r.system?.hardware||"—");
      const workload=make("td","",[
        r.workload?.benchmark_type,
        valid(r.workload?.isl)?"ISL "+r.workload.isl:null,
        valid(r.workload?.osl)?"OSL "+r.workload.osl:null,
        valid(r.workload?.concurrency)?"C="+r.workload.concurrency:null
      ].filter(Boolean).join(" · ")||"—");
      const valueCell=make("td","pw-number",value+" "+def.unit);
      const source=make("td","");const url=r.detail_url||r.source_url;
      if(valid(url)){try{const u=new URL(url);if(["http:","https:"].includes(u.protocol)){const a=make("a","","Open ↗");a.href=u.href;a.target="_blank";a.rel="noopener noreferrer";source.append(a);}}catch(_){}}
      tr.append(id,model,hardware,workload,valueCell,source);body.append(tr);
    });
    text($("[data-pw-metric-summary]"),items.length+" valid observations · "+def.label+" · "+def.unit+" · "+(def.direction==="higher"?"higher is better":"lower is better")+(items.length>100?" · first 100 shown":""));
    $("[data-pw-empty]").hidden=items.length!==0;
  };
  const render=()=>{
    text($("[data-pw-filter-status]"),"Showing "+filtered.length+" of "+all.length+" published InferenceX records. Filtered records are not automatically a strict comparison cohort.");
    renderEvidence();renderObservations();
  };
  const load=async()=>{
    const response=await fetch(root.dataset.source,{cache:"no-cache"});if(!response.ok)throw new Error("Registry request failed: HTTP "+response.status);
    const bytes=await response.arrayBuffer(),gz=bytes.length>1&&new Uint8Array(bytes)[0]===31&&new Uint8Array(bytes)[1]===139;
    if(gz){if(typeof DecompressionStream!=="function")throw new Error("This browser cannot decompress the benchmark registry.");return new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream("gzip"))).json();}
    return JSON.parse(new TextDecoder().decode(bytes));
  };
  Object.keys(fields).forEach(k=>$("[data-pw-filter='"+k+"']").addEventListener("change",applyFilters));
  $("[data-pw-metric]").addEventListener("change",e=>{metricKey=e.target.value;renderObservations();});
  $("[data-pw-reset]").addEventListener("click",()=>{Object.keys(fields).forEach(k=>$("[data-pw-filter='"+k+"']").value="");applyFilters();});
  const metricSelect=$("[data-pw-metric]");
  Object.entries(metricDefs).forEach(([key,def])=>{const o=document.createElement("option");o.value=key;o.textContent=def.label;metricSelect.append(o);});
  load().then(data=>{
    if(!Array.isArray(data.records))throw new Error("Registry has no records array.");
    all=data.records.filter(r=>r.source_id==="inferencex");
    if(!all.length)throw new Error("No InferenceX records were found in the registry.");
    Object.entries(fields).forEach(([k,get])=>addSelectOptions($("[data-pw-filter='"+k+"']"),unique(all.map(get))));
    const models=new Set(all.map(fields.model).filter(valid)),hardware=new Set(all.map(fields.hardware).filter(valid));
    setStat("records",all.length);setStat("models",models.size);setStat("hardware",hardware.size);
    setStat("metrics",all.filter(r=>Object.keys(metricDefs).some(k=>metricValue(r,k)!==null)).length);
    document.querySelector("[data-pw-version]").textContent=data.database_version||"—";
    document.querySelector("[data-pw-imported]").textContent=data.last_imported||data.last_updated||"—";
    $("[data-pw-load]").hidden=true;applyFilters();
  }).catch(error=>{$("[data-pw-load]").hidden=true;const box=$("[data-pw-error]");box.hidden=false;box.textContent=error.stack||error.message;});
})();
