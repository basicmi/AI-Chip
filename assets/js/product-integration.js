(() => {
  "use strict";
  const root=document.querySelector("[data-product-integration]");
  if(!root)return;
  const $=selector=>root.querySelector(selector);
  const inputs={
    package:$("[data-pi-package]"),claims:$("[data-pi-claims]"),
    approval:$("[data-pi-approval]"),registry:$("[data-pi-registry]")
  };
  const status=$("[data-pi-status]"),panels=[...root.querySelectorAll("[data-pi-results]")];
  const MAX_BYTES=16*1024*1024;
  let verified=null;
  const canonical=value=>{
    if(Array.isArray(value))return "["+value.map(canonical).join(",")+"]";
    if(value&&typeof value==="object")return "{"+Object.keys(value).sort().map(k=>JSON.stringify(k)+":"+canonical(value[k])).join(",")+"}";
    if(typeof value==="number"&&Object.is(value,-0))return "0";
    return JSON.stringify(value);
  };
  const digest=async bytes=>{
    if(!globalThis.crypto?.subtle)throw Error("Secure browser context is required for SHA256.");
    const hash=await crypto.subtle.digest("SHA-256",bytes);
    return [...new Uint8Array(hash)].map(x=>x.toString(16).padStart(2,"0")).join("");
  };
  const hashJson=value=>digest(new TextEncoder().encode(canonical(value)));
  const read=async file=>{
    if(!file||!file.size||file.size>MAX_BYTES)throw Error("Each input must be between 1 byte and 16 MiB.");
    const bytes=await file.arrayBuffer();
    return {data:JSON.parse(new TextDecoder().decode(bytes)),bytes};
  };
  const equal=(a,b)=>canonical(a)===canonical(b);
  const check=(label,detail)=>{
    const row=document.createElement("div");row.className="di-check";
    const mark=document.createElement("span");mark.className="di-check-mark";mark.textContent="✓";
    const body=document.createElement("div"),strong=document.createElement("strong"),p=document.createElement("p");
    strong.textContent=label;p.textContent=detail;body.append(strong,p);row.append(mark,body);return row;
  };
  const cell=value=>{const td=document.createElement("td");td.textContent=value;return td;};
  const clearResults=()=>{
    verified=null;panels.forEach(x=>x.hidden=true);
    $("[data-pi-diff]").replaceChildren();$("[data-pi-checks]").replaceChildren();
    $("[data-pi-operations]").textContent="";
  };
  const clear=()=>{
    clearResults();Object.values(inputs).forEach(x=>x.value="");
    status.classList.remove("is-error");
    status.textContent="Choose all four files to verify a complete product provenance chain.";
  };
  const verify=async()=>{
    const files=Object.fromEntries(Object.entries(inputs).map(([key,input])=>[key,input.files[0]]));
    if(Object.values(files).some(x=>!x)){
      clearResults();status.classList.remove("is-error");
      status.textContent="Choose all four files to verify a complete product provenance chain.";return;
    }
    clearResults();status.classList.remove("is-error");
    try{
      const [packageFile,claimFile,approvalFile,registryFile]=await Promise.all([
        read(files.package),read(files.claims),read(files.approval),read(files.registry)
      ]);
      const pkg=packageFile.data,report=claimFile.data,approval=approvalFile.data,db=registryFile.data;
      if(!pkg||pkg.schema_version!=="1.0"||pkg.proposal_type!=="company_profile_product_creation"||
         !pkg.target_registry||pkg.target_registry.path!=="data/company-profiles.json"||
         pkg.target_registry.schema_version!=="1.3")throw Error("Unsupported product proposal or registry schema.");
      const body={...pkg};delete body.package_sha256;
      const packageHash=await hashJson(body);
      if(packageHash!==pkg.package_sha256)throw Error("Proposal package SHA256 mismatch.");
      const baseHash=await digest(registryFile.bytes);
      if(baseHash!==pkg.target_registry.base_sha256)throw Error("Base registry SHA256 mismatch.");
      if(!equal(pkg.approval,approval)||pkg.proposal_id!==approval.approval_id||
         approval.decision!=="approved_new_product_with_identity_claim")
        throw Error("Separate Approval Manifest or explicit product-creation decision does not exactly match proposal.");
      if(report.schema_version!=="1.0"||!Array.isArray(report.claims)||report.claim_count!==report.claims.length)
        throw Error("Original Claim report schema or count is invalid.");
      const source=pkg.source_claim;
      const sourceRows=report.claims.filter(x=>x&&x.claim_id===source?.claim_id);
      if(sourceRows.length!==1||!equal(sourceRows[0],source)||source.review_status!=="unverified_candidate")
        throw Error("Original Claim report does not exactly match the proposal source Claim.");
      const target=pkg.target,product=approval.product,claim=approval.claim,evidence=approval.evidence;
      if(!target||!Number.isSafeInteger(target.company_index))throw Error("Invalid target company index.");
      const company=db.companies?.[target.company_index];
      if(db.schema_version!=="1.3"||!company||company.id!==approval.company_id||
         company.id!==target.company_id||target.product_id!==product.id||
         target.claim_id!==claim.id||target.source_claim_id!==source.claim_id)
        throw Error("Target company or product/Claim identity does not match the exact base registry.");
      if(!Array.isArray(company.products)||!Array.isArray(company.claims)||!Array.isArray(company.evidence))
        throw Error("Target company product, Claim and Evidence collections must be arrays.");
      if(company.products.some(x=>x.id===product.id)||company.claims.some(x=>x.id===claim.id)||
         company.evidence.some(x=>x.id===evidence.id||x.url===evidence.url))
        throw Error("Product, Claim or Evidence ID/URL already exists.");
      if(!Array.isArray(product.claim_ids)||!equal(product.claim_ids,[claim.id])||
         claim.subject_type!=="product"||claim.subject_id!==product.id||
         claim.topic!=="product_identity"||claim.claim_status!=="vendor_reported"||
         !equal(claim.evidence_ids,[evidence.id])||claim.statement!==source.statement||
         source.source?.url!==evidence.url||!Array.isArray(product.availability_history)||
         product.availability_history.length!==1||
         product.availability_history[0].status!==product.availability||
         product.availability_history[0].evidence_id!==evidence.id)
        throw Error("Product, initial Claim and source Evidence relationships violate the typed adapter policy.");
      if(approval.decision!=="approved_new_product_with_identity_claim"||
         approval.extracted_claim_id!==source.claim_id||claim.last_reviewed!==approval.reviewed_at||
         evidence.review_status!=="reviewed"||!/^https:\/\//.test(evidence.url))
        throw Error("Approval decision, review status or provenance fields are invalid.");
      const updated=JSON.parse(JSON.stringify(db)),next=updated.companies[target.company_index];
      next.evidence.push(evidence);next.products.push(product);next.claims.push(claim);
      const operations=[
        {op:"add",path:"/companies/"+target.company_index+"/evidence/-",value:evidence},
        {op:"add",path:"/companies/"+target.company_index+"/products/-",value:product},
        {op:"add",path:"/companies/"+target.company_index+"/claims/-",value:claim}
      ];
      if(!equal(pkg.operations,operations))throw Error("Proposal does not contain the exact three permitted append operations.");
      const proposedHash=await hashJson(updated);
      if(proposedHash!==pkg.proposed_registry_sha256||pkg.audit?.proposed_registry_sha256!==proposedHash||
         pkg.audit?.base_registry_sha256!==baseHash||pkg.audit?.verification_status!=="exact_three_record_append"||
         pkg.audit?.unapproved_changes!==0||pkg.audit?.source_truth_verified!==false||
         pkg.audit?.claim_status_changed!==false||pkg.audit?.new_claim_status!=="vendor_reported"||
         pkg.audit?.approval_id!==approval.approval_id||pkg.audit?.source_claim_id!==source.claim_id||
         pkg.audit?.source_url!==evidence.url||
         pkg.audit?.evidence_quote_sha256!==await digest(new TextEncoder().encode(source.evidence_quote)))
        throw Error("Audit metadata or proposed registry SHA256 is inconsistent.");
      if(pkg.policy?.human_approval_required!==true||pkg.policy?.automatic_merge!==false||
         pkg.policy?.source_truth_verified!==false||pkg.policy?.claim_status_changed!==false||
         pkg.policy?.new_claim_status!=="vendor_reported")
        throw Error("Proposal policy guardrails are missing or inconsistent.");
      const patch={schema:"https://json.schemastore.org/json-patch.json",base_registry_sha256:baseHash,operations};
      verified={pkg,updated,patch,audit:pkg.audit};
      $("[data-pi-source-title]").textContent=evidence.title;
      $("[data-pi-source-quote]").textContent="“"+source.evidence_quote+"”";
      const sourceLink=$("[data-pi-source-link]");sourceLink.href=evidence.url;sourceLink.textContent="Open source ↗";
      $("[data-pi-source-meta]").textContent=evidence.publisher+" · "+evidence.source_type+" · checked "+evidence.checked_at;
      $("[data-pi-product-name]").textContent=product.name;
      $("[data-pi-product-meta]").textContent=product.product_type+" · "+product.availability+" · "+(product.architecture||"Architecture not specified");
      $("[data-pi-company]").textContent=company.display_name||company.id;
      $("[data-pi-claim-id]").textContent=claim.id;
      $("[data-pi-claim-statement]").textContent=claim.statement;
      $("[data-pi-base-hash]").textContent=baseHash;
      $("[data-pi-package-hash]").textContent=packageHash;
      $("[data-pi-proposed-hash]").textContent=proposedHash;
      const diff=$("[data-pi-diff]");diff.replaceChildren();
      [
        ["/companies/"+target.company_index+"/evidence/-","Append Evidence",evidence.id],
        ["/companies/"+target.company_index+"/products/-","Append Product",product.id+" · "+product.name],
        ["/companies/"+target.company_index+"/claims/-","Append Claim",claim.id+" · vendor_reported"]
      ].forEach(row=>{const tr=document.createElement("tr");row.forEach(value=>tr.append(cell(value)));diff.append(tr);});
      $("[data-pi-operations]").textContent=JSON.stringify(operations,null,2);
      $("[data-pi-checks]").replaceChildren(
        check("Package integrity","Canonical proposal SHA256 matches."),
        check("Original source Claim","The source Claim exactly matches the separate extraction report."),
        check("Human approval","The separate Approval Manifest exactly matches the proposal."),
        check("Base registry","Raw company-profiles.json SHA256 matches the package."),
        check("Typed relationships","Product → Claim → Evidence links are internally consistent."),
        check("Write-set isolation","Exactly three append-only operations; no existing record is modified."),
        check("Claim status boundary","Initial product identity Claim remains vendor_reported; source truth is not inferred.")
      );
      panels.forEach(x=>x.hidden=false);
      status.textContent="Verified locally: source, approval, base registry and three-record append are consistent. This is not a source-truth verification or GitHub submission.";
    }catch(error){
      clearResults();status.classList.add("is-error");
      status.textContent="Product proposal validation failed: "+error.message;
    }
  };
  const download=(name,value)=>{
    const blob=new Blob([JSON.stringify(value,null,2)+"\n"],{type:"application/json"});
    const url=URL.createObjectURL(blob),a=document.createElement("a");
    a.href=url;a.download=name;document.body.append(a);a.click();a.remove();
    setTimeout(()=>URL.revokeObjectURL(url),3000);
  };
  Object.values(inputs).forEach(input=>input.addEventListener("change",verify));
  root.querySelector("[data-pi-clear]").addEventListener("click",clear);
  root.querySelectorAll("[data-pi-download]").forEach(button=>button.addEventListener("click",()=>{
    if(!verified)return;
    const kind=button.dataset.piDownload;
    if(kind==="patch")download(verified.pkg.proposal_id+"-patch.json",verified.patch);
    if(kind==="audit")download(verified.pkg.proposal_id+"-audit.json",verified.audit);
    if(kind==="database")download("company-profiles-proposed.json",verified.updated);
  }));
})();