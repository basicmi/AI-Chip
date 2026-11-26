(() => {
  "use strict";
  const root=document.querySelector("[data-performance-evidence]");
  if(!root)return;
  const $=s=>root.querySelector(s);
  const files={record:$("[data-pe-record]"),plan:$("[data-pe-plan]"),submission:$("[data-pe-submission]"),review:$("[data-pe-review]"),ledger:$("[data-pe-ledger]")};
  const state={record:null,plan:null,submission:null,review:null,ledger:null,experiment:null};
  const status=$("[data-pe-status]");
  const el=(tag,cls,text)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=String(text);return n;};
  const safeUrl=value=>{try{const u=new URL(value);return u.protocol==="https:"?u.href:null;}catch(_){return null;}};
  const link=(label,url)=>{const href=safeUrl(url);if(!href)return el("span","",label);const a=el("a","",label);a.href=href;a.target="_blank";a.rel="noopener noreferrer";return a;};
  const cell=(row,value)=>row.append(el("td","",value??"—"));
  const show=(selector,value)=>{const n=$(selector);if(n)n.textContent=value===null||value===undefined?"—":String(value);};
  const reset=()=>{Object.keys(state).forEach(k=>state[k]=null);state.experiment=null;["records","experiments","runs","decisions","blockers"].forEach(k=>show("[data-pe-stat='"+k+"']","—"));["[data-pe-summary]","[data-pe-experiment-detail]","[data-pe-run-table] tbody","[data-pe-decision-list]"].forEach(s=>$(s)?.replaceChildren());$("[data-pe-content]").hidden=true;};
  const validate=()=>{
    const {record:r,plan:p,submission:s,review:v,ledger:l}=state;
    if(!r||!p||!s||!v)return false;
    if(!r.id||p.schema_version!=="1.0"||s.schema_version!=="1.0"||v.schema_version!=="1.0"||v.report_type!=="performance_evidence_review")throw Error("Input schema or record identity is unsupported.");
    if(p.record_context?.record_id!==r.id||s.plan_id!==p.plan_id||v.record_id!==r.id||v.plan_id!==p.plan_id||v.experiment_id!==s.experiment_id)throw Error("Record, plan, submission and review do not refer to the same evidence chain.");
    if(!Array.isArray(p.experiments)||!p.experiments.some(x=>x.experiment_id===s.experiment_id))throw Error("Experiment ID is not present in the selected plan.");
    if(v.record_sha256!==s.record_sha256||v.plan_sha256!==s.plan_sha256||v.submission_sha256!==s.submission_sha256)throw Error("Review and submission digest references do not match.");
    if(!/^[a-f0-9]{64}$/.test(v.record_sha256||"")||!/^[a-f0-9]{64}$/.test(v.plan_sha256||"")||!/^[a-f0-9]{64}$/.test(v.submission_sha256||""))throw Error("Evidence digest references are malformed.");
    if(!Array.isArray(v.runs)||!Array.isArray(v.review_blockers)||!v.statistics||!["blocked","needs_review"].includes(v.review_status)||v.hypothesis_verdict!=="undetermined")throw Error("Review report has unsupported status or structure.");
    if(l){if(l.schema_version!=="1.0"||!Array.isArray(l.entries))throw Error("Decision ledger schema is invalid.");let previous=null;const ids=new Set();for(const entry of l.entries){if(!entry||!entry.decision||!/^[a-f0-9]{64}$/.test(entry.entry_sha256||"")||entry.previous_entry_sha256!==previous||!entry.evidence_identity||!entry.decision.decision_id||ids.has(entry.decision.decision_id))throw Error("Decision ledger structure or hash-chain links are invalid.");ids.add(entry.decision.decision_id);previous=entry.entry_sha256;}}
    return true;
  };
  const render=()=>{
    try{
      if(!validate())return;
      const {record:r,plan:p,submission:s,review:v,ledger:l}=state;
      const exp=p.experiments.find(x=>x.experiment_id===s.experiment_id);
      $("[data-pe-content]").hidden=false;
      show("[data-pe-stat='records']",1);show("[data-pe-stat='experiments']",p.experiment_count);show("[data-pe-stat='runs']",v.runs.length);show("[data-pe-stat='blockers']",v.review_blockers.length);
      const summary=$("[data-pe-summary]");summary.replaceChildren();
      summary.append(el("h3","",r.model_display_name||r.model||r.id),el("p","", "Record "+r.id+" · Plan "+p.plan_id+" · Experiment "+s.experiment_id));
      const pills=el("div","pe-pills");pills.append(el("span","pe-pill", "Review: "+v.review_status),el("span","pe-pill", "Hypothesis: "+v.hypothesis_verdict),el("span","pe-pill","Execution: not performed"));summary.append(pills);
      const detail=$("[data-pe-experiment-detail]");detail.replaceChildren(el("h3","",exp.title||exp.mechanism),el("p","",exp.hypothesis||"No hypothesis text supplied."),el("p","", "Observed signal: "+(exp.observed_signal||"Not supplied")),el("p","", "Intervention: "+(s.protocol?.parameter||"—")+" · baseline "+String(s.protocol?.baseline_value??"—")+" → treatment "+String(s.protocol?.treatment_value??"—")),el("p","", "Primary metric: "+(s.protocol?.primary_metric?.key||"—")+" ("+(s.protocol?.primary_metric?.unit||"—")+")"));
      const blockers=$("[data-pe-blockers]");blockers.replaceChildren();if(v.review_blockers.length){v.review_blockers.forEach(x=>blockers.append(el("li","",x)));}else blockers.append(el("li","","No automated structural blockers reported; human review is still required."));
      const stats=$("[data-pe-metric-stats]");stats.replaceChildren();for(const condition of ["baseline","treatment"]){const x=v.statistics[condition]||{};const card=el("div","pe-stat-card");card.append(el("span","",condition),el("strong","",x.median??"—"),el("small","", "n="+(x.valid_runs??0)+" · range "+(x.min??"—")+" – "+(x.max??"—")));stats.append(card);}
      show("[data-pe-improvement]",v.relative_improvement_percent===null?"Unavailable":Number(v.relative_improvement_percent).toFixed(2)+"%");show("[data-pe-threshold]",v.effect_threshold_met===null?"Not assessable":v.effect_threshold_met?"Reported threshold met":"Reported threshold not met");
      const tbody=$("[data-pe-run-table] tbody");tbody.replaceChildren();v.runs.forEach(run=>{const tr=el("tr");cell(tr,run.run_id);cell(tr,run.condition);cell(tr,run.status);cell(tr,run.value===undefined?"—":run.value+" "+(run.unit||""));const td=el("td");td.append(link("source ↗",run.source_url));tr.append(td);cell(tr,run.reason);tbody.append(tr);});
      const decisions=$("[data-pe-decision-list]");decisions.replaceChildren();const matching=(l?.entries||[]).filter(x=>{const id=x.evidence_identity||{};return id.record_id===v.record_id&&id.plan_id===v.plan_id&&id.experiment_id===v.experiment_id&&id.submission_sha256===v.submission_sha256;});if(!matching.length)decisions.append(el("p","pe-muted","No decision entries for this exact evidence version. Load the current ledger to inspect prior decisions."));matching.forEach(entry=>{const card=el("article","pe-decision");card.append(el("strong","",entry.decision.verdict),el("p","",entry.decision.rationale),el("small","",entry.decision.reviewer+" · "+entry.decision.reviewed_at),el("p","pe-muted","Applicability: "+entry.decision.applicability),el("p","pe-muted","Limitations: "+entry.decision.limitations),el("small","", "Entry SHA-256: "+entry.entry_sha256));decisions.append(card);});
      show("[data-pe-ledger-count]",l?l.entries.length:"Not loaded");
      show("[data-pe-hash-note]","Digest references are compared across files and formatted; cryptographic recomputation and full ledger verification remain in the Python CLI.");
      status.textContent="Loaded and structurally matched. This workbench does not verify external source truth or issue decisions.";
      status.classList.remove("is-error");
    }catch(error){status.textContent=error.message;status.classList.add("is-error");$("[data-pe-content]").hidden=true;}
  };
  Object.entries(files).forEach(([key,input])=>input.addEventListener("change",async()=>{
    const file=input.files?.[0];if(!file){state[key]=null;render();return;}
    if(file.size>8*1024*1024){status.textContent="File exceeds 8 MB limit.";status.classList.add("is-error");input.value="";return;}
    try{state[key]=JSON.parse(await file.text());render();}catch(error){state[key]=null;status.textContent="Cannot load "+key+": "+error.message;status.classList.add("is-error");}
  }));
  $("[data-pe-reset]").addEventListener("click",()=>{Object.values(files).forEach(x=>x.value="");reset();status.textContent="Choose the five evidence files to begin.";status.classList.remove("is-error");});
  reset();
})();
