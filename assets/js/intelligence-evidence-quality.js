(() => {
  "use strict";
  const root=document.querySelector("[data-quality-dashboard]");
  if(!root)return;
  const $=selector=>root.querySelector(selector);
  const input=$("[data-eq-files]"),status=$("[data-eq-status]");
  const evaluationInput=$("[data-eq-semantic-eval]"),evaluationStatus=$("[data-eq-eval-status]");
  const table=$("[data-eq-history]"),select=$("[data-eq-select]");
  const history=$("[data-eq-history-panel]"),detail=$("[data-eq-detail-panel]");
  const MAX_RUNS=52,MAX_BYTES=2*1024*1024;
  let runs=[],semanticEvaluation=null;
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
  // An evaluation is supplied by the local reviewer; this validates internal
  // arithmetic and batch identity, not reviewer identity or technical truth.
  const semanticLabels=new Set(["supported_by_source","contradicted_by_source",
    "insufficient_context","source_unavailable"]);
  const validateEvaluation=data=>{
    if(!data||data.schema_version!=="1.0"||typeof data.batch_id!=="string"||
       !runs.some(r=>r.semantic_batch_id===data.batch_id)||
       data.automatically_verified_claims!==0||
       !["pending","complete"].includes(data.status))
      throw Error("Semantic evaluation does not match an imported Claim review batch.");
    const run=runs.find(r=>r.semantic_batch_id===data.batch_id);
    if(!integer(data.total_claims)||data.total_claims!==run.metrics.semantic_claims_queued||
       !integer(data.double_reviewed_claims)||data.double_reviewed_claims>data.total_claims||
       !Array.isArray(data.pending_claim_ids)||!Array.isArray(data.agreements)||
       !Array.isArray(data.disagreements)||!integer(data.human_adjudication_needed)||
       !data.reviewer_label_counts||typeof data.reviewer_label_counts!=="object"||
       Array.isArray(data.reviewer_label_counts))
      throw Error("Malformed semantic evaluation counts.");
    if(data.double_reviewed_claims!==data.agreements.length+data.disagreements.length||
       data.total_claims!==data.double_reviewed_claims+data.pending_claim_ids.length||
       data.human_adjudication_needed!==data.disagreements.length)
      throw Error("Semantic evaluation coverage does not reconcile.");
    const claimIds=new Set();
    for(const cid of data.pending_claim_ids){
      if(typeof cid!=="string"||!cid||claimIds.has(cid))throw Error("Duplicate evaluation Claim ID.");
      claimIds.add(cid);
    }
    for(const item of data.agreements){
      if(!item||typeof item.claim_id!=="string"||!item.claim_id||
         !semanticLabels.has(item.label)||claimIds.has(item.claim_id))
        throw Error("Invalid semantic agreement row.");
      claimIds.add(item.claim_id);
    }
    for(const item of data.disagreements){
      if(!item||typeof item.claim_id!=="string"||!item.claim_id||
         claimIds.has(item.claim_id)||!Array.isArray(item.labels)||
         item.labels.length!==2||!item.labels.every(x=>semanticLabels.has(x))||
         item.labels[0]===item.labels[1]||item.requires_human_adjudication!==true)
        throw Error("Invalid semantic disagreement row.");
      claimIds.add(item.claim_id);
    }
    let labelsCount=0;
    for(const [key,value] of Object.entries(data.reviewer_label_counts)){
      if(!semanticLabels.has(key)||!integer(value))throw Error("Invalid reviewer label count.");
      labelsCount+=value;
    }
    if(labelsCount!==2*data.double_reviewed_claims)
      throw Error("Semantic reviewer labels do not reconcile.");
    const expected=data.double_reviewed_claims?
      Math.round(data.agreements.length/data.double_reviewed_claims*10000)/10000:null;
    if(data.raw_agreement!==expected||
       data.status!==(data.pending_claim_ids.length||data.disagreements.length?"pending":"complete"))
      throw Error("Semantic agreement or status is inconsistent.");
    return data;
  };
  const humanAgreement=run=>semanticEvaluation &&
    run.semantic_batch_id===semanticEvaluation.batch_id?
    (semanticEvaluation.raw_agreement===null?"N/A":
      (100*semanticEvaluation.raw_agreement).toFixed(1)+"%"+
      " (n="+semanticEvaluation.double_reviewed_claims+", reviewer-reported)"):"N/A";
  const fmt=x=>new Intl.NumberFormat().format(x);
  const percent=x=>x.rate===null?"N/A":(100*x.rate).toFixed(1)+"%";
  const cell=x=>{const td=document.createElement("td");td.textContent=String(x);return td;};
  const stat=(key,value)=>{$("[data-eq-stat='"+key+"']").textContent=String(value);};
  const reset=()=>{
    runs=[];semanticEvaluation=null;input.value="";evaluationInput.value="";
    evaluationStatus.textContent="No human evaluation loaded. Reviewer reports are not independently authenticated.";
    evaluationStatus.classList.remove("is-error");
    table.replaceChildren();select.replaceChildren();
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
      " · human double-review agreement: "+humanAgreement(run)+
      (semanticEvaluation && semanticEvaluation.batch_id===run.semantic_batch_id?
        " · double-reviewed Claims: "+semanticEvaluation.double_reviewed_claims+"/"+semanticEvaluation.total_claims+
        " · disagreements needing adjudication: "+semanticEvaluation.human_adjudication_needed:" · no matched human evaluation supplied") +
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
          fmt(m.semantic_claims_queued),humanAgreement(run)])tr.append(cell(val));
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
      semanticEvaluation=null;
      evaluationInput.value="";
      evaluationStatus.classList.remove("is-error");
      evaluationStatus.textContent="No human evaluation loaded. Reviewer reports are not independently authenticated.";
      render();
    }catch(error){
      reset();status.classList.add("is-error");
      status.textContent="Cannot load evidence-quality snapshots: "+error.message;
    }
  });
  evaluationInput.addEventListener("change",async()=>{
    try{
      if(!runs.length)throw Error("Load a matching Evidence Quality snapshot first.");
      const file=evaluationInput.files[0];
      if(!file||!file.size||file.size>MAX_BYTES)throw Error("Choose one nonempty semantic evaluation JSON under 2 MiB.");
      const report=validateEvaluation(JSON.parse(await file.text()));
      semanticEvaluation=report;
      evaluationStatus.classList.remove("is-error");
      evaluationStatus.textContent="Reviewer-reported evaluation loaded for "+report.batch_id+
        " ("+report.double_reviewed_claims+"/"+report.total_claims+
        " double-reviewed). Not authenticated and not factual verification.";
      render();
    }catch(error){
      semanticEvaluation=null;
      evaluationInput.value="";
      evaluationStatus.classList.add("is-error");
      evaluationStatus.textContent="Cannot load semantic evaluation: "+error.message;
      if(runs.length)render();
    }
  });
  select.addEventListener("change",inspect);
  $("[data-eq-clear]").addEventListener("click",reset);
  reset();
})();
