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
  const reset=()=>{
    runs=[];input.value="";historyBody.replaceChildren();sourcesBody.replaceChildren();
    selection.replaceChildren();historyPanel.hidden=true;sourcesPanel.hidden=true;
    ["availability","leads","backlog","runs"].forEach(id=>stat(id,"—"));
    status.textContent="No snapshots loaded.";
    status.classList.remove("is-error");
  };
  const integer=value=>Number.isSafeInteger(value)&&value>=0;
  const valid=(data)=>{
    if(!data||data.schema_version!=="1.0"||data.operational_only!==true||
       !["healthy","degraded"].includes(data.health)||!data.cache||
       data.cache.checkpoint_audit_passed!==true||!data.summary||
       !Array.isArray(data.sources)||!Array.isArray(data.warnings)){
      throw Error("Expected a successful read-only operational snapshot v1.0.");
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
    let observed=0;
    for(const source of data.sources){
      if(!source||typeof source.source_id!=="string"||!source.source_id||
         seen.has(source.source_id)||!["observed","unavailable"].includes(source.status)||
         !integer(source.recent_item_count)){
        throw Error("Invalid/duplicate per-source operational data.");
      }
      seen.add(source.source_id);
      if(source.status==="observed")observed++;
    }
    if(observed!==s.sources_observed) throw Error("Source availability count mismatch.");
    const expected=s.sources_total?Math.round(1000*observed/s.sources_total)/10:null;
    if(s.availability_percent!==expected)throw Error("Availability percentage mismatch.");
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
      tr.append(cell(source.name||source.source_id),cell(source.kind||"unknown"),
        cell(source.status),cell(source.recent_item_count));
      sourcesBody.append(tr);
    }
    $("[data-ops-cache]").textContent=
      "Cache at run start — Discovery: "+fmtCache(data.cache.discovery_restored_file_present)+
      " · Review backlog: "+fmtCache(data.cache.review_restored_file_present)+
      ". File presence does not establish continuity.";
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
      tr.append(cell(run.generated_at),cell(run.health),
        cell(s.sources_observed+"/"+s.sources_total),cell(s.review_leads),
        cell(s.extracted_claims),cell(s.unresolved_backlog),
        cell(s.oldest_unresolved_days+" days"));
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