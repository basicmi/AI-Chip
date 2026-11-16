(() => {
  "use strict";
  const root=document.querySelector("[data-ops-dashboard]");
  if(!root) return;
  const $=selector=>root.querySelector(selector);
  const input=$("[data-ops-files]"),status=$("[data-ops-status]");
  const historyPanel=$("[data-ops-history-panel]"),sourcesPanel=$("[data-ops-sources-panel]");
  const historyBody=$("[data-ops-history]"),sourcesBody=$("[data-ops-sources]");
  const selection=$("[data-ops-select]");
  let runs=[];
  const MAX_FILE_BYTES=2*1024*1024,MAX_RUNS=52;
  const cell=(text,tag="td")=>{const item=document.createElement(tag);item.textContent=String(text);return item;};
  const stat=(id,value)=>{$("[data-ops-stat='"+id+"']").textContent=String(value);};
  const number=value=>new Intl.NumberFormat().format(value);
  const bytes=value=>number(value)+" B";
  const reset=()=>{
    runs=[];input.value="";historyBody.replaceChildren();sourcesBody.replaceChildren();
    selection.replaceChildren();historyPanel.hidden=true;sourcesPanel.hidden=true;
    ["availability","leads","backlog","runs"].forEach(id=>stat(id,"—"));
    status.textContent="No snapshots loaded.";
    status.classList.remove("is-error");
  };
  const integer=value=>Number.isSafeInteger(value)&&value>=0;
  const validateRequestMetrics=(metrics)=>{
    if(metrics===null)return null;
    if(!metrics||typeof metrics!=="object"||
       !integer(metrics.request_count)||!integer(metrics.failed_request_count)||
       !integer(metrics.response_bytes)||metrics.failed_request_count>metrics.request_count){
      throw Error("Invalid per-source request counters.");
    }
    for(const key of ["total_elapsed_ms","max_request_ms"]){
      if(typeof metrics[key]!=="number"||!Number.isFinite(metrics[key])||metrics[key]<0)
        throw Error("Invalid request timing: "+key);
    }
    if(metrics.request_count===0){
      if(metrics.average_request_ms!==null||metrics.failed_request_count!==0||
         metrics.response_bytes!==0||metrics.total_elapsed_ms!==0||metrics.max_request_ms!==0||
         metrics.last_http_error_status!==null||metrics.last_request_failure_category!==null)
        throw Error("Inconsistent zero-request diagnostics.");
    }else{
      if(typeof metrics.average_request_ms!=="number"||
         !Number.isFinite(metrics.average_request_ms)||metrics.average_request_ms<0||
         Math.abs(metrics.average_request_ms-metrics.total_elapsed_ms/metrics.request_count)>0.002||
         metrics.max_request_ms>metrics.total_elapsed_ms+0.002)
        throw Error("Inconsistent request latency diagnostics.");
    }
    if(metrics.last_http_error_status!==null&&
       (!Number.isSafeInteger(metrics.last_http_error_status)||
        metrics.last_http_error_status<100||metrics.last_http_error_status>599))
      throw Error("Invalid last HTTP status.");
    const categories=["http_rate_limit","http_server_error","http_client_error",
      "timeout","network","parse_error","invalid_payload","source_error"];
    if(metrics.last_request_failure_category!==null&&
       !categories.includes(metrics.last_request_failure_category))
      throw Error("Unknown request failure category.");
    if(metrics.failed_request_count===0&&
       (metrics.last_http_error_status!==null||metrics.last_request_failure_category!==null))
      throw Error("Failure metadata without failed requests.");
    return metrics;
  };
  const valid=(data)=>{
    if(!data||!["1.0","1.1"].includes(data.schema_version)||
       data.operational_only!==true||!["healthy","degraded"].includes(data.health)||
       !data.cache||data.cache.checkpoint_audit_passed!==true||
       !data.summary||!Array.isArray(data.sources)||!Array.isArray(data.warnings)){
      throw Error("Expected a successful read-only operational snapshot v1.0 or v1.1.");
    }
    const stamp=Date.parse(data.generated_at);
    if(!Number.isFinite(stamp)||!/[zZ]|[+-]\d\d:\d\d$/.test(data.generated_at)){
      throw Error("Snapshot timestamp must be timezone-aware.");
    }
    const s=data.summary;
    for(const key of ["sources_total","sources_observed","sources_unavailable",
      "review_leads","extracted_claims","persistent_backlog","unresolved_backlog",
      "oldest_unresolved_days"]){
      if(!integer(s[key])) throw Error("Missing or invalid operational metric: "+key);
    }
    if(s.sources_total!==data.sources.length||s.sources_observed+s.sources_unavailable!==s.sources_total||
       s.unresolved_backlog>s.persistent_backlog) throw Error("Operational summary counts do not match.");
    const seen=new Set();
    let observed=0,telemetrySources=0,totalRequests=0,failedRequests=0,responseBytes=0,slowSources=0;
    for(const source of data.sources){
      if(!source||typeof source.source_id!=="string"||!source.source_id||
         seen.has(source.source_id)||!["observed","unavailable"].includes(source.status)||
         !integer(source.recent_item_count)){
        throw Error("Invalid/duplicate per-source operational data.");
      }
      seen.add(source.source_id);
      if(source.status==="observed")observed++;
      if(data.schema_version==="1.1"){
        const metrics=validateRequestMetrics(source.request_diagnostics);
        if(metrics){
          telemetrySources++;
          totalRequests+=metrics.request_count;
          failedRequests+=metrics.failed_request_count;
          responseBytes+=metrics.response_bytes;
          if(metrics.max_request_ms>=5000)slowSources++;
        }
      }
    }
    if(observed!==s.sources_observed) throw Error("Source availability count mismatch.");
    const expected=s.sources_total?Math.round(1000*observed/s.sources_total)/10:null;
    if(s.availability_percent!==expected)throw Error("Availability percentage mismatch.");
    if(data.schema_version==="1.1"){
      for(const key of ["request_telemetry_sources","total_requests","failed_requests",
        "response_bytes","sources_with_slow_request_over_5s"]){
        if(!integer(s[key]))throw Error("Missing or invalid request metric: "+key);
      }
      if(s.request_telemetry_sources!==telemetrySources||s.total_requests!==totalRequests||
         s.failed_requests!==failedRequests||s.response_bytes!==responseBytes||
         s.sources_with_slow_request_over_5s!==slowSources)
        throw Error("Request telemetry summary does not match per-source diagnostics.");
    }
    for(const key of ["discovery_restored_file_present","review_restored_file_present"]){
      if(data.cache[key]!==null&&typeof data.cache[key]!=="boolean")
        throw Error("Cache presence must be true, false or unknown.");
    }
    if(data.warnings.some(w=>typeof w!=="string"))throw Error("Invalid warning messages.");
    return data;
  };
  const fmtCache=value=>value===true?"file found":value===false?"no restored file":"unknown";
  const renderSources=()=>{
    const data=runs.find(row=>row.generated_at===selection.value);
    if(!data)return;
    sourcesBody.replaceChildren();
    for(const source of data.sources){
      const tr=document.createElement("tr");
      const diagnostics=source.status==="unavailable"
        ?"unavailable · "+(source.failure_category||"unclassified")+
          (source.failure_tier?" · "+source.failure_tier:"")+
          (Number.isSafeInteger(source.consecutive_failures)?" · streak "+source.consecutive_failures:"")
        :source.health_transition==="recovered"?"observed · recovered":"observed";
      const metrics=source.request_diagnostics;
      tr.append(cell(source.name||source.source_id),cell(source.kind||"unknown"),
        cell(diagnostics),cell(source.recent_item_count),
        cell(metrics?number(metrics.request_count):"—"),
        cell(metrics?number(metrics.failed_request_count):"—"),
        cell(metrics?(metrics.average_request_ms===null?"—":number(Math.round(metrics.average_request_ms))):"—"),
        cell(metrics?number(Math.round(metrics.max_request_ms)):"—"),
        cell(metrics?bytes(metrics.response_bytes):"—"));
      sourcesBody.append(tr);
    }
    const telemetry=data.schema_version==="1.1"&&data.summary.request_telemetry_sources>0
      ?data.summary.request_telemetry_sources+"/"+data.summary.sources_total+" sources have request telemetry."
      :"Request telemetry unavailable in this snapshot.";
    $("[data-ops-cache]").textContent=
      "Cache at run start — Discovery: "+fmtCache(data.cache.discovery_restored_file_present)+
      " · Review backlog: "+fmtCache(data.cache.review_restored_file_present)+
      ". "+telemetry+" File presence does not establish continuity.";
    $("[data-ops-warnings]").textContent=data.warnings.length?
      "Warnings: "+data.warnings.join(" · "):"No audit warnings in this snapshot.";
  };
  const render=()=>{
    const latest=runs[runs.length-1];
    stat("runs",runs.length);
    stat("availability",latest.summary.availability_percent===null?"N/A":latest.summary.availability_percent+"%");
    stat("leads",latest.summary.review_leads);
    stat("backlog",latest.summary.unresolved_backlog);
    historyPanel.hidden=false;sourcesPanel.hidden=false;
    historyBody.replaceChildren();
    selection.replaceChildren();
    for(const run of runs){
      const tr=document.createElement("tr");
      const s=run.summary;
      const hasTelemetry=run.schema_version==="1.1"&&s.request_telemetry_sources>0;
      tr.append(cell(run.generated_at),cell(run.health),
        cell(s.sources_observed+"/"+s.sources_total),cell(s.review_leads),
        cell(s.extracted_claims),cell(s.unresolved_backlog),
        cell(s.oldest_unresolved_days+" days"),
        cell(hasTelemetry?number(s.total_requests):"—"),
        cell(hasTelemetry?number(s.failed_requests):"—"),
        cell(hasTelemetry?number(s.sources_with_slow_request_over_5s):"—"));
      historyBody.append(tr);
      const option=document.createElement("option");
      option.value=run.generated_at;option.textContent=run.generated_at+" · "+run.health;
      selection.append(option);
    }
    selection.value=latest.generated_at;
    renderSources();
    status.textContent="Loaded "+runs.length+" completed operational snapshot(s) locally. No data uploaded.";
    status.classList.remove("is-error");
  };
  input.addEventListener("change",async()=>{
    runs=[];historyPanel.hidden=true;sourcesPanel.hidden=true;
    try{
      const files=[...input.files];
      if(!files.length){reset();return;}
      if(files.length>MAX_RUNS)throw Error("Choose at most "+MAX_RUNS+" snapshots.");
      const collected=[];
      for(const file of files){
        if(!file.size||file.size>MAX_FILE_BYTES)throw Error("Each snapshot must be JSON ≤2 MiB.");
        collected.push(valid(JSON.parse(await file.text())));
      }
      const stamps=new Set(collected.map(row=>row.generated_at));
      if(stamps.size!==collected.length)throw Error("Duplicate run timestamps: choose one snapshot per run.");
      runs=collected.sort((a,b)=>Date.parse(a.generated_at)-Date.parse(b.generated_at));
      render();
    }catch(error){
      runs=[];historyBody.replaceChildren();sourcesBody.replaceChildren();
      historyPanel.hidden=true;sourcesPanel.hidden=true;
      ["availability","leads","backlog","runs"].forEach(id=>stat(id,"—"));
      status.textContent="Cannot load snapshots: "+error.message;
      status.classList.add("is-error");
    }
  });
  selection.addEventListener("change",renderSources);
  $("[data-ops-clear]").addEventListener("click",reset);
  reset();
})();
