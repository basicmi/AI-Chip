(() => {
  "use strict";
  const root=document.querySelector("[data-database-integration]");
  if(!root)return;
  const $=selector=>root.querySelector(selector);
  const inputs={package:$("[data-di-package]"),claims:$("[data-di-claims]"),registry:$("[data-di-registry]")};
  const status=$("[data-di-status]"),panels=[...root.querySelectorAll("[data-di-results]")];
  const MAX_BYTES=16*1024*1024;
  let verified=null;
  const keys=x=>x&&typeof x==="object"&&!Array.isArray(x)?Object.keys(x).sort().join(","):"";
  const canonical=value=>{
    if(Array.isArray(value))return "["+value.map(canonical).join(",")+"]";
    if(value&&typeof value==="object")return "{"+Object.keys(value).sort().map(k=>JSON.stringify(k)+":"+canonical(value[k])).join(",")+"}";
    if(typeof value==="number"&&Object.is(value,-0))return "0";
    return JSON.stringify(value);
  };
  const digest=async bytes=>{
    if(!crypto?.subtle)throw Error("Secure browser context is required for SHA256.");
    const hash=await crypto.subtle.digest("SHA-256",bytes);
    return [...new Uint8Array(hash)].map(x=>x.toString(16).padStart(2,"0")).join("");
  };
  const hashText=value=>digest(new TextEncoder().encode(value));
  const read=async file=>{
    if(!file||!file.size||file.size>MAX_BYTES)throw Error("Each input must be between 1 byte and 16 MiB.");
    const bytes=await file.arrayBuffer();
    return {data:JSON.parse(new TextDecoder().decode(bytes)),bytes};
  };
  const slug=x=>typeof x==="string"&&/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(x);
  const date=x=>typeof x==="string"&&/^\d{4}-\d{2}-\d{2}$/.test(x)&&
    Number.isFinite(Date.parse(x+"T00:00:00Z"))&&new Date(x+"T00:00:00Z").toISOString().slice(0,10)===x;
  const nonempty=x=>typeof x==="string"&&x.trim().length>0;
  const exactKeys=(obj,list,label)=>{
    if(keys(obj)!==list.slice().sort().join(","))throw Error(label+" fields do not match the documented schema.");
  };
  const clear=()=>{
    verified=null;panels.forEach(x=>x.hidden=true);
    ["package","claims","registry"].forEach(k=>inputs[k].value="");
    status.classList.remove("is-error");status.textContent="Choose a proposal package, its original Claim report and exact base registry.";
    $("[data-di-diff]").replaceChildren();$("[data-di-checks]").replaceChildren();
    $("[data-di-operations]").textContent="";
  };
  const check=(label,detail)=>{
    const row=document.createElement("div");row.className="di-check";
    const mark=document.createElement("span");mark.className="di-check-mark";mark.textContent="✓";
    const body=document.createElement("div");const strong=document.createElement("strong");strong.textContent=label;
    const p=document.createElement("p");p.textContent=detail;body.append(strong,p);row.append(mark,body);return row;
  };
  const cell=value=>{const td=document.createElement("td");td.textContent=value;return td;};
  const addDiff=(path,before,after)=>{
    const row=document.createElement("tr");row.append(cell(path),cell(before),cell(after));$("[data-di-diff]").append(row);
  };
  const link=(node,url)=>{
    if(typeof url==="string"&&/^https:\/\//.test(url)){
      node.href=url;node.textContent=url;node.hidden=false;
    }else node.hidden=true;
  };
  const verify=async()=>{
    const [pkgFile,claimsFile,registryFile]=[inputs.package.files[0],inputs.claims.files[0],inputs.registry.files[0]];
    if(!pkgFile||!claimsFile||!registryFile){
      verified=null;panels.forEach(x=>x.hidden=true);
      status.classList.remove("is-error");
      status.textContent="Choose all three files to verify a complete provenance chain.";return;
    }
    panels.forEach(x=>x.hidden=true);verified=null;status.classList.remove("is-error");
    try{
      const [pkgRead,claimsRead,registryRead]=await Promise.all([read(pkgFile),read(claimsFile),read(registryFile)]);
      const pkg=pkgRead.data,report=claimsRead.data,db=registryRead.data;
      const packageFields=["schema_version","proposal_id","proposal_type","created_at","target_registry",
        "source_claim","approval","target","operations","audit","proposed_registry_sha256","policy","package_sha256"];
      exactKeys(pkg,packageFields,"Proposal package");
      if(pkg.schema_version!=="1.0"||pkg.proposal_type!=="company_profile_evidence_attachment"||!slug(pkg.proposal_id))
        throw Error("Unsupported proposal schema, type or ID.");
      if(!/(Z|[+-][0-9]{2}:[0-9]{2})$/.test(pkg.created_at||"")||!Number.isFinite(Date.parse(pkg.created_at))||Date.parse(pkg.created_at)>Date.now())
        throw Error("Proposal timestamp must be valid, timezone-aware and not in the future.");
      const body={...pkg};delete body.package_sha256;
      const packageHash=await hashText(canonical(body));
      if(packageHash!==pkg.package_sha256)throw Error("Proposal package SHA256 mismatch.");
      if(report.schema_version!=="1.0"||!Array.isArray(report.claims)||report.claim_count!==report.claims.length)
        throw Error("Original Claim report schema or claim_count is invalid.");
      const source=pkg.source_claim,approval=pkg.approval,target=pkg.target,reg=pkg.target_registry,audit=pkg.audit;
      if(!source||!slug(source.claim_id)||source.review_status!=="unverified_candidate"||
         !nonempty(source.statement)||!nonempty(source.evidence_quote)||!source.source)
        throw Error("Proposal must reference an unverified source-backed Claim with a non-empty quote.");
      const matches=report.claims.filter(x=>x&&x.claim_id===source.claim_id);
      if(matches.length!==1||canonical(matches[0])!==canonical(source))
        throw Error("Embedded source Claim does not exactly match the supplied original Claim report.");
      const approvalFields=["schema_version","approval_id","reviewer","reviewed_at","decision","company_id",
        "existing_claim_id","expected_claim_sha256","extracted_claim_id","evidence","review_notes"];
      exactKeys(approval,approvalFields,"Approval manifest");
      if(approval.schema_version!=="1.0"||approval.decision!=="approved_evidence_attachment"||
         !slug(approval.approval_id)||pkg.proposal_id!==approval.approval_id||
         !nonempty(approval.reviewer)||!date(approval.reviewed_at)||
         !slug(approval.company_id)||!slug(approval.existing_claim_id)||
         !/^[a-f0-9]{64}$/.test(approval.expected_claim_sha256)||
         approval.extracted_claim_id!==source.claim_id||!nonempty(approval.review_notes)||approval.review_notes.trim().length<30)
        throw Error("Approval manifest is invalid or does not match the extracted Claim.");
      const ev=approval.evidence;
      exactKeys(ev,["id","title","url","publisher","source_type","independence","published_at","checked_at","review_status","notes"],"Evidence record");
      if(!slug(ev.id)||!nonempty(ev.title)||!nonempty(ev.publisher)||!nonempty(ev.notes)||
         typeof ev.url!=="string"||ev.review_status!=="reviewed"||
         !["company_primary","vendor_primary","official_project","research_paper","independent_media","government_or_regulatory","repository","other"].includes(ev.source_type)||
         !["vendor","project","independent","official"].includes(ev.independence)||
         !date(ev.checked_at)||(ev.published_at!==null&&!date(ev.published_at))||ev.checked_at>approval.reviewed_at)
        throw Error("Reviewed Evidence record has invalid fields or dates.");
      let sourceUrl;
      try{sourceUrl=new URL(ev.url);}catch(_){throw Error("Evidence URL is invalid.");}
      if(sourceUrl.protocol!=="https:"||sourceUrl.username||sourceUrl.password)
        throw Error("Evidence URL must be HTTPS without embedded credentials.");
      if(source.source.url!==ev.url)throw Error("Approval source URL does not exactly match the extracted Claim.");
      if(!db||db.schema_version!=="1.3"||!Array.isArray(db.companies)||reg.path!=="data/company-profiles.json"||reg.schema_version!=="1.3")
        throw Error("Expected company-profiles schema 1.3 and the canonical target registry path.");
      const baseHash=await digest(registryRead.bytes);
      if(baseHash!==reg.base_sha256)throw Error("Base registry SHA256 mismatch. Use the exact company-profiles.json revision used to create the proposal.");
      if(!target||!Number.isSafeInteger(target.company_index)||!Number.isSafeInteger(target.claim_index))
        throw Error("Proposal target indices are invalid.");
      const company=db.companies[target.company_index],claim=company?.claims?.[target.claim_index];
      if(!company||company.id!==target.company_id||company.id!==approval.company_id||
         !claim||claim.id!==target.claim_id||claim.id!==approval.existing_claim_id)
        throw Error("Target company or Claim no longer matches the exact base registry.");
      if(target.company_display_name!==(company.display_name||company.id)||
         target.claim_statement!==claim.statement||target.original_claim_sha256!==approval.expected_claim_sha256)
        throw Error("Target Claim snapshot or fingerprint does not match the approval.");
      if(!Array.isArray(claim.evidence_ids)||!Array.isArray(company.evidence)||
         canonical(claim.evidence_ids)!==canonical(target.evidence_ids_before)||
         company.evidence.some(x=>x.id===ev.id||x.url===ev.url)||
         claim.evidence_ids.includes(ev.id))
        throw Error("Evidence ID, URL or target Claim references are duplicated or changed.");
      const after=[...claim.evidence_ids,ev.id];
      if(canonical(after)!==canonical(target.evidence_ids_after))throw Error("Proposed Claim evidence_ids do not represent one append.");
      if(!Array.isArray(pkg.operations)||pkg.operations.length!==2)throw Error("Only two append-only JSON Patch operations are permitted.");
      const expectedOps=[
        {op:"add",path:"/companies/"+target.company_index+"/evidence/-",value:ev},
        {op:"add",path:"/companies/"+target.company_index+"/claims/"+target.claim_index+"/evidence_ids/-",value:ev.id}
      ];
      if(canonical(pkg.operations)!==canonical(expectedOps))throw Error("Proposal operations are not the exact two permitted appends.");
      if(audit.verification_status!=="exact_append_only_change"||audit.unapproved_changes!==0||
         audit.source_truth_verified!==false||audit.claim_status_changed!==false||
         audit.approval_id!==approval.approval_id||audit.source_claim_id!==source.claim_id||
         audit.original_claim_sha256!==approval.expected_claim_sha256||audit.base_registry_sha256!==baseHash)
        throw Error("Proposal audit metadata or guardrails are inconsistent.");
      if(await hashText(source.evidence_quote)!==audit.evidence_quote_sha256)
        throw Error("Evidence quote checksum mismatch.");
      const updated=JSON.parse(JSON.stringify(db));
      updated.companies[target.company_index].evidence.push(ev);
      updated.companies[target.company_index].claims[target.claim_index].evidence_ids.push(ev.id);
      const proposedHash=await hashText(canonical(updated));
      if(proposedHash!==pkg.proposed_registry_sha256||audit.proposed_registry_sha256!==proposedHash)
        throw Error("Proposed registry SHA256 does not match the two append-only operations.");
      if(!pkg.policy||pkg.policy.source_truth_verified!==false||pkg.policy.claim_status_changed!==false||
         pkg.policy.claim_value_or_scope_changed!==false||pkg.policy.product_identity_changed!==false||
         pkg.policy.automatic_merge!==false||pkg.policy.human_approval_required!==true)
        throw Error("Proposal policy does not preserve required human-review guardrails.");
      verified={pkg,db,updated,patch:{schema:"https://json.schemastore.org/json-patch.json",base_registry_sha256:baseHash,operations:expectedOps}};
      $("[data-di-source-title]").textContent=ev.title;
      $("[data-di-source-quote]").textContent="“"+source.evidence_quote+"”";
      link($("[data-di-source-link]"),ev.url);
      $("[data-di-source-meta]").textContent=ev.publisher+" · "+ev.source_type+" · checked "+ev.checked_at;
      $("[data-di-extracted-id]").textContent=source.claim_id;
      $("[data-di-extracted-statement]").textContent=source.statement;
      $("[data-di-target-name]").textContent=company.display_name||company.id;
      $("[data-di-target-claim]").textContent=claim.statement;
      $("[data-di-target-meta]").textContent="Claim "+claim.id+" · "+(claim.claim_status||"status not supplied")+" · "+claim.subject_type+":"+claim.subject_id;
      $("[data-di-base-hash]").textContent=baseHash;
      $("[data-di-package-hash]").textContent=packageHash;
      $("[data-di-proposed-hash]").textContent=proposedHash;
      $("[data-di-change-count]").textContent="2";
      $("[data-di-diff]").replaceChildren();
      addDiff("/companies/"+target.company_index+"/evidence/-","No record","Append Evidence "+ev.id);
      addDiff("/companies/"+target.company_index+"/claims/"+target.claim_index+"/evidence_ids/-",
        JSON.stringify(claim.evidence_ids),JSON.stringify(after));
      $("[data-di-operations]").textContent=JSON.stringify(expectedOps,null,2);
      const checks=$("[data-di-checks]");checks.replaceChildren(
        check("Package integrity","Canonical package SHA256 matches."),
        check("Original source Claim","Embedded Claim exactly matches the supplied extraction report."),
        check("Base registry","Raw company-profiles.json SHA256 matches the package."),
        check("Target identity","Company, Claim index and statement match the exact base registry; the approval fingerprint is retained for independent Python revalidation."),
        check("Allowed field changes","Exactly two JSON Patch append operations; no other path is allowed."),
        check("Independent patch gate","Audit records zero unapproved changes; Claim status/value/scope remain unchanged."),
        check("Source truth boundary","No factual verification or independent corroboration is inferred.")
      );
      panels.forEach(x=>x.hidden=false);
      status.classList.remove("is-error");
      status.textContent="Verified locally: proposal package, source Claim, exact base registry and append-only patch are consistent. This is not a source-truth verification or a GitHub submission.";
    }catch(error){
      verified=null;panels.forEach(x=>x.hidden=true);
      status.classList.add("is-error");status.textContent="Proposal validation failed: "+error.message;
    }
  };
  const download=(name,value)=>{
    const blob=new Blob([JSON.stringify(value,null,2)+"\n"],{type:"application/json"});
    const url=URL.createObjectURL(blob),a=document.createElement("a");
    a.href=url;a.download=name;document.body.append(a);a.click();a.remove();
    setTimeout(()=>URL.revokeObjectURL(url),3000);
  };
  Object.values(inputs).forEach(input=>input.addEventListener("change",verify));
  root.querySelector("[data-di-clear]").addEventListener("click",clear);
  root.querySelectorAll("[data-di-download]").forEach(button=>button.addEventListener("click",()=>{
    if(!verified)return;
    const kind=button.dataset.diDownload;
    if(kind==="patch")download(verified.pkg.proposal_id+"-patch.json",verified.patch);
    if(kind==="audit")download(verified.pkg.proposal_id+"-audit.json",verified.pkg.audit);
    if(kind==="database")download("company-profiles-proposed.json",verified.updated);
  }));
})();