(() => {
  "use strict";
  const root=document.querySelector("[data-decision-analytics]");
  if(!root)return;
  const $=selector=>root.querySelector(selector);
  const input=$("[data-da-files]"),status=$("[data-da-status]");
  const panels=[...root.querySelectorAll("[data-da-results]")];
  const history=$("[data-da-history]"),outcomes=$("[data-da-outcomes]"),reasons=$("[data-da-reasons]");
  const MAX_RUNS=52,MAX_BYTES=2*1024*1024;
  const OUTCOMES=["needs_more_evidence","rejected","accepted_for_evidence_attachment"];
  const integer=x=>Number.isSafeInteger(x)&&x>=0;
  const ratio=(value,numerator,denominator,label)=>{
    const expected=denominator?Math.round(numerator/denominator*10000)/10000:null;
    if(value!==expected)throw Error("Inconsistent "+label+".");
  };
  const validate=data=>{
    if(!data||data.schema_version!=="1.0"||data.read_only!==true||
       data.factual_verification_performed!==false||!data.metrics||
       !data.taxonomy||data.taxonomy.reason_codes_are_explicit_human_labels!==true||
       data.taxonomy.free_text_notes_auto_classified!==false||
       !data.policy||data.policy.decision_is_factual_verification!==false)
      throw Error("Expected read-only decision analytics snapshot v1.0.");
    if(!/(Z|[+-][0-9]{2}:[0-9]{2})$/.test(data.generated_at||"")||
       !Number.isFinite(Date.parse(data.generated_at)))
      throw Error("Snapshot timestamp must be timezone-aware.");
    const m=data.metrics;
    for(const key of ["current_claims","persistent_backlog","decisions_recorded",
      "reason_coded_decisions","unresolved_claims","overdue_14d_or_more"])
      if(!integer(m[key]))throw Error("Invalid metric: "+key);
    if(m.current_claims>m.persistent_backlog||m.decisions_recorded>m.persistent_backlog||
       m.reason_coded_decisions>m.decisions_recorded)
      throw Error("Decision analytics counts exceed their denominators.");
    ratio(m.decision_coverage,m.decisions_recorded,m.persistent_backlog,"decision coverage");
    ratio(m.reason_code_coverage,m.reason_coded_decisions,m.decisions_recorded,"reason-code coverage");
    if(!m.outcome_counts||OUTCOMES.reduce((n,k)=>n+(integer(m.outcome_counts[k])?m.outcome_counts[k]:-100000),0)!==m.decisions_recorded)
      throw Error("Decision outcome counts do not reconcile.");
    if(!Array.isArray(m.uncoded_decision_claim_ids)||
       m.uncoded_decision_claim_ids.length!==m.decisions_recorded-m.reason_coded_decisions)
      throw Error("Uncoded decision list does not reconcile.");
    const allowed=data.taxonomy.allowed_reason_codes;
    if(!Array.isArray(allowed)||new Set(allowed).size!==allowed.length)
      throw Error("Invalid reason-code taxonomy.");
    const reasonCounts=m.primary_reason_counts;
    if(!reasonCounts||typeof reasonCounts!=="object"||Array.isArray(reasonCounts))
      throw Error("Missing primary reason counts.");
    let reasonTotal=0;
    for(const [key,value] of Object.entries(reasonCounts)){
      if(!allowed.includes(key)||!integer(value))throw Error("Invalid primary reason count.");
      reasonTotal+=value;
    }
    if(reasonTotal!==m.reason_coded_decisions)throw Error("Reason counts do not reconcile.");
    const buckets=m.unresolved_age_buckets;
    if(!buckets||!["within_7d","7_to_13d","14_to_29d","30d_plus"].every(k=>integer(buckets[k]))||
       Object.values(buckets).reduce((a,b)=>a+b,0)!==m.unresolved_claims||
       m.overdue_14d_or_more!==buckets["14_to_29d"]+buckets["30d_plus"])
      throw Error("Unresolved age buckets do not reconcile.");
    const latency=m.review_latency_days;
    if(!latency||!latency.overall||!latency.by_outcome||
       !OUTCOMES.every(k=>latency.by_outcome[k]&&integer(latency.by_outcome[k].samples))||
       !integer(latency.overall.samples)||latency.overall.samples>m.decisions_recorded||
       !integer(latency.unavailable_due_to_cache_reset_or_clock_order)||
       latency.overall.samples+latency.unavailable_due_to_cache_reset_or_clock_order!==m.decisions_recorded||
       OUTCOMES.reduce((n,k)=>n+latency.by_outcome[k].samples,0)!==latency.overall.samples)
      throw Error("Review-latency samples do not reconcile.");
    for(const row of [latency.overall,...OUTCOMES.map(k=>latency.by_outcome[k])]){
      if(!integer(row.samples)||!(row.median_days===null||Number.isFinite(row.median_days)&&row.median_days>=0)||
         !(row.p90_days===null||Number.isFinite(row.p90_days)&&row.p90_days>=0)||
         !(row.max_days===null||Number.isFinite(row.max_days)&&row.max_days>=0)||
         (row.samples===0&&(row.median_days!==null||row.p90_days!==null||row.max_days!==null))||
         (row.samples>0&&(row.median_days===null||row.p90_days===null||row.max_days===null)))
        throw Error("Invalid review-latency statistics.");
    }
    return data;
  };
  const fmt=x=>new Intl.NumberFormat().format(x);
  const pct=x=>x===null?"N/A":(100*x).toFixed(1)+"%";
  const human=x=>String(x).replaceAll("_"," ");
  const td=value=>{const el=document.createElement("td");el.textContent=String(value);return el;};
  const tr=values=>{const row=document.createElement("tr");values.forEach(v=>row.append(td(v)));return row;};
  const clear=()=>{
    input.value="";history.replaceChildren();outcomes.replaceChildren();reasons.replaceChildren();
    panels.forEach(el=>el.hidden=true);
    status.classList.remove("is-error");status.textContent="No decision analytics loaded.";
    ["decision-coverage","reason-coverage","median-latency","overdue"].forEach(k=>{
      const el=$("[data-da-stat='"+k+"']");if(el)el.textContent="—";
    });
  };
  const render=runs=>{
    const latest=runs[runs.length-1],m=latest.metrics,lat=m.review_latency_days.overall;
    $("[data-da-stat='decision-coverage']").textContent=pct(m.decision_coverage);
    $("[data-da-stat='reason-coverage']").textContent=pct(m.reason_code_coverage);
    $("[data-da-stat='median-latency']").textContent=lat.median_days===null?"N/A":lat.median_days+" days";
    $("[data-da-stat='overdue']").textContent=fmt(m.overdue_14d_or_more);
    history.replaceChildren();
    for(const run of runs){
      const x=run.metrics,l=x.review_latency_days.overall;
      history.append(tr([run.generated_at,x.decisions_recorded,pct(x.decision_coverage),
        x.reason_coded_decisions,pct(x.reason_code_coverage),
        l.median_days===null?"N/A":l.median_days+" d",x.overdue_14d_or_more]));
    }
    outcomes.replaceChildren();
    for(const key of OUTCOMES)outcomes.append(tr([human(key),fmt(m.outcome_counts[key])]));
    reasons.replaceChildren();
    const entries=Object.entries(m.primary_reason_counts).sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0]));
    if(!entries.length)reasons.append(tr(["No explicit human reason codes yet",0]));
    else for(const [key,value] of entries)reasons.append(tr([human(key),fmt(value)]));
    panels.forEach(el=>el.hidden=false);
    status.classList.remove("is-error");
    status.textContent="Loaded "+runs.length+" local decision-analytics snapshot(s). Free-text notes were not classified.";
  };
  input.addEventListener("change",async()=>{
    try{
      const files=[...input.files];
      if(!files.length){clear();return;}
      if(files.length>MAX_RUNS)throw Error("Choose at most "+MAX_RUNS+" snapshots.");
      const values=[];
      for(const file of files){
        if(!file.size||file.size>MAX_BYTES)throw Error("Each JSON file must be between 1 byte and 2 MiB.");
        values.push(validate(JSON.parse(await file.text())));
      }
      if(new Set(values.map(x=>x.generated_at)).size!==values.length)
        throw Error("Duplicate decision-analytics timestamps.");
      values.sort((a,b)=>Date.parse(a.generated_at)-Date.parse(b.generated_at));
      render(values);
    }catch(error){
      clear();status.classList.add("is-error");status.textContent="Cannot load decision analytics: "+error.message;
    }
  });
  root.querySelector("[data-da-clear]").addEventListener("click",clear);
})();