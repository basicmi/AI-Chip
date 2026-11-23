(() => {
  "use strict";
  const root=document.querySelector("[data-quality-dashboard]");
  if(!root)return;
  const $=selector=>root.querySelector(selector);
  const input=$("[data-eq-files]"),status=$("[data-eq-status]");
  const table=$("[data-eq-history]"),select=$("[data-eq-select]");
  const history=$("[data-eq-history-panel]"),detail=$("[data-eq-detail-panel]");
  const MAX_RUNS=52,MAX_BYTES=2*1024*1024;
  let runs=[];
  const integer=x=>Number.isSafeInteger(x)&&x>=0;
  const pair=(row,name)=>{
    if(!row||!integer(row.passed)||!integer(row.total)||row.passed>row.total)
      throw Error("Invalid "+name+" counts.");
    const expected=row.total?Math.round(row.passed/row.total*10000)/10000:null;
    if(row.rate!==expected)throw Error("Inconsistent "+name+" rate.");
  };
  const validate=data=>{
    if(!data||data.schema_version!=="1.0"||data.read_only!==true||
       data.factual_verification_performed!==false||!data.metrics||
       !data.availability||data.availability.independent_verification!=="not_measured")
      throw Error("Expected read-only evidence-quality snapshot v1.0.");
    if(!/^(\d{4}-\d\d-\d\dT)/.test(data.generated_at||"")||
       !/(Z|[+-]\d\d:\d\d)$/.test(data.generated_at)||
       !Number.isFinite(Date.parse(data.generated_at)))
      throw Error("Timestamp must be timezone-aware.");
    const m=data.metrics;
    for(const key of ["current_claims","source_metadata_mismatches","distinct_source_documents",
      "distinct_publishers","review_backlog","unresolved_claims","pending_claims",
      "needs_more_evidence","accepted_for_evidence_attachment","rejected_claims",
      "multi_document_exact_duplicate_clusters","lineage_clusters_queued","semantic_claims_queued"])
      if(!integer(m[key]))throw Error("Invalid metric: "+key);
    for(const key of ["quote_traceability","provenance_completeness","payload_coverage"])pair(m[key],key);
    if(m.quote_traceability.total!==m.current_claims||
       m.provenance_completeness.total!==m.current_claims||
       m.payload_coverage.total!==m.review_backlog||
       m.unresolved_claims!==m.pending_claims+m.needs_more_evidence||
       m.review_backlog!==m.unresolved_claims+m.accepted_for_evidence_attachment+m.rejected_claims||
       m.source_metadata_mismatches>m.current_claims||
       m.lineage_clusters_queued>m.multi_document_exact_duplicate_clusters)
      throw Error("Dashboard cross-metric counts are inconsistent.");
    for(const field of ["semantic_double_review_rate","semantic_reviewer_agreement",
      "lineage_human_review_coverage","independently_verified_claims"])
      if(m[field]!==null)throw Error("Human validation status cannot be inferred from unlabelled templates: "+field);
    if(data.availability.semantic_evaluation!=="not_provided"||
       data.availability.lineage_evaluation!=="not_provided")
      throw Error("Human evaluation availability must remain unknown.");
    return data;
  };
  const fmt=x=>new Intl.NumberFormat().format(x);
  const percent=x=>x.rate===null?"N/A":(100*x.rate).toFixed(1)+"%";
  const cell=x=>{const td=document.createElement("td");td.textContent=String(x);return td;};
  const stat=(key,value)=>{$("[data-eq-stat='"+key+"']").textContent=String(value);};
  const reset=()=>{
    runs=[];input.value="";table.replaceChildren();select.replaceChildren();
    history.hidden=true;detail.hidden=true;
    ["quotes","provenance","unresolved","runs"].forEach(k=>stat(k,"—"));
    status.textContent="No snapshots loaded.";status.classList.remove("is-error");
  };
  const inspect=()=>{
    const run=runs.find(x=>x.generated_at===select.value);
    if(!run)return;
    const m=run.metrics;
    $("[data-eq-details]").textContent=
      "Claim candidates: "+fmt(m.current_claims)+
      " · source documents: "+fmt(m.distinct_source_documents)+
      " · publishers: "+fmt(m.distinct_publishers)+
      " · lineage worksheets queued: "+fmt(m.lineage_clusters_queued)+
      " · semantic Claims queued: "+fmt(m.semantic_claims_queued)+
      " · human double-review agreement: N/A (not supplied)"+
      " · independently verified Claims: N/A (not measured).";
  };
  const render=()=>{
    const latest=runs[runs.length-1],m=latest.metrics;
    stat("quotes",percent(m.quote_traceability));stat("provenance",percent(m.provenance_completeness));
    stat("unresolved",fmt(m.unresolved_claims));stat("runs",runs.length);
    table.replaceChildren();select.replaceChildren();
    for(const run of runs){
      const m=run.metrics,tr=document.createElement("tr");
      for(const val of [run.generated_at,fmt(m.current_claims),percent(m.quote_traceability),
          percent(m.provenance_completeness),fmt(m.source_metadata_mismatches),
          fmt(m.distinct_source_documents),fmt(m.review_backlog),fmt(m.unresolved_claims),
          percent(m.payload_coverage),fmt(m.lineage_clusters_queued),
          fmt(m.semantic_claims_queued),"N/A"])tr.append(cell(val));
      table.append(tr);
      const option=document.createElement("option");
      option.value=run.generated_at;option.textContent=run.generated_at;
      select.append(option);
    }
    select.value=latest.generated_at;history.hidden=false;detail.hidden=false;inspect();
    status.classList.remove("is-error");
    status.textContent="Loaded "+runs.length+" completed local evidence-quality snapshot(s). No files uploaded.";
  };
  input.addEventListener("change",async()=>{
    try{
      const files=[...input.files];
      if(!files.length){reset();return;}
      if(files.length>MAX_RUNS)throw Error("Choose at most "+MAX_RUNS+" runs.");
      const values=[];
      for(const file of files){
        if(!file.size||file.size>MAX_BYTES)throw Error("Each JSON file must be between 1 byte and 2 MiB.");
        values.push(validate(JSON.parse(await file.text())));
      }
      if(new Set(values.map(x=>x.generated_at)).size!==values.length)
        throw Error("Duplicate run timestamps.");
      runs=values.sort((a,b)=>Date.parse(a.generated_at)-Date.parse(b.generated_at));
      render();
    }catch(error){
      reset();status.classList.add("is-error");
      status.textContent="Cannot load evidence-quality snapshots: "+error.message;
    }
  });
  select.addEventListener("change",inspect);
  $("[data-eq-clear]").addEventListener("click",reset);
  reset();
})();
