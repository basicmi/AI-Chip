(() => {
  "use strict";
  const root = document.querySelector("[data-benchmark-integration]");
  if (!root) return;
  const $ = selector => root.querySelector(selector);
  const inputs = {
    package: $("[data-bi-package]"),
    approval: $("[data-bi-approval]"),
    registry: $("[data-bi-registry]")
  };
  const status = $("[data-bi-status]");
  const panels = [...root.querySelectorAll("[data-bi-results]")];
  const MAX_BYTES = 32 * 1024 * 1024;
  const REQUIRED_RECORD = [
    "id","source_id","source_class","evidence_level","benchmark_suite","benchmark_version",
    "publication_date","submitter","accelerator_vendor","platform_id","product_id","system_type",
    "system_name","division","availability","model","scenario","result_value","result_unit",
    "accuracy_text","inferred","power_metrics_available","design_power_watts","system","software",
    "notes","compliance","errors","weight_data_types","source_record_key","source_location",
    "source_url","dataset_url","release_url"
  ];
  const OPTIONAL_RECORD = [
    "detail_url","model_display_name","workload","configuration","metrics",
    "power_measurement_valid","normalized_metrics","cpu_power_measurement_valid",
    "gpu_power_metrics_available","cpu_power_metrics_available","power_measurement_status",
    "cpu_power_measurement_status","hardware_evidence","runtime_trace"
  ];
  const APPROVAL_FIELDS = ["schema_version","approval_id","reviewer","reviewed_at","decision",
    "source_id","record","review_notes"];
  let verified = null;

  const canonical = value => {
    if (Array.isArray(value)) return "[" + value.map(canonical).join(",") + "]";
    if (value && typeof value === "object") return "{" + Object.keys(value).sort()
      .map(key => JSON.stringify(key) + ":" + canonical(value[key])).join(",") + "}";
    if (typeof value === "number" && Object.is(value, -0)) return "0";
    return JSON.stringify(value);
  };
  const digest = async bytes => {
    if (!globalThis.crypto?.subtle) throw Error("Secure browser context is required for SHA256.");
    const hash = await crypto.subtle.digest("SHA-256", bytes);
    return [...new Uint8Array(hash)].map(x => x.toString(16).padStart(2, "0")).join("");
  };
  const hashJson = value => digest(new TextEncoder().encode(canonical(value)));
  const read = async file => {
    if (!file || !file.size || file.size > MAX_BYTES) throw Error("Each input must be between 1 byte and 32 MiB.");
    const bytes = await file.arrayBuffer();
    return {data: JSON.parse(new TextDecoder().decode(bytes)), bytes};
  };
  const equal = (a,b) => canonical(a) === canonical(b);
  const slug = value => typeof value === "string" && /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(value);
  const text = value => typeof value === "string" && value.trim().length > 0;
  const date = value => typeof value === "string" && /^\d{4}-\d{2}-\d{2}$/.test(value) &&
    Number.isFinite(Date.parse(value + "T00:00:00Z")) &&
    new Date(value + "T00:00:00Z").toISOString().slice(0,10) === value;
  const exactKeys = (value, fields, label) => {
    if (!value || typeof value !== "object" || Array.isArray(value) ||
        !equal(Object.keys(value).sort(), fields.slice().sort())) {
      throw Error(label + " fields do not match the supported schema.");
    }
  };
  const safeUrl = value => {
    try { const u = new URL(value); return u.protocol === "https:" && !u.username && !u.password ? u.href : ""; }
    catch (_) { return ""; }
  };
  const makeCell = value => {
    const td = document.createElement("td");
    td.textContent = value === null || value === undefined || value === "" ? "Not reported" :
      typeof value === "object" ? JSON.stringify(value) : String(value);
    return td;
  };
  const row = (parent, a, b, c) => {
    const tr = document.createElement("tr");
    tr.append(makeCell(a), makeCell(b));
    if (c !== undefined) tr.append(makeCell(c));
    parent.append(tr);
  };
  const check = (label, detail) => {
    const item = document.createElement("div"); item.className = "di-check";
    const mark = document.createElement("span"); mark.className = "di-check-mark"; mark.textContent = "✓";
    const body = document.createElement("div"), strong = document.createElement("strong"), p = document.createElement("p");
    strong.textContent = label; p.textContent = detail; body.append(strong,p); item.append(mark,body);
    return item;
  };
  const summarize = records => {
    const count = field => {
      const values = new Map();
      records.forEach(item => {
        const key = String(item[field] || "unknown");
        values.set(key, (values.get(key) || 0) + 1);
      });
      return Object.fromEntries([...values.entries()].sort((a,b) => a[0].localeCompare(b[0])));
    };
    return {
      total_records: records.length,
      by_source: count("source_id"),
      by_availability: count("availability"),
      by_division: count("division"),
      by_system_type: count("system_type"),
      inferred_records: records.filter(x => x.inferred === true).length,
      power_records: records.filter(x => x.power_metrics_available === true).length,
      submitters: new Set(records.map(x => x.submitter)).size,
      models: new Set(records.map(x => x.model)).size
    };
  };
  const clearResults = () => {
    verified = null; panels.forEach(panel => panel.hidden = true);
    ["[data-bi-context]","[data-bi-diff]","[data-bi-checks]"].forEach(selector => $(selector).replaceChildren());
    $("[data-bi-operations]").textContent = "";
  };
  const clear = () => {
    clearResults(); Object.values(inputs).forEach(input => input.value = "");
    status.classList.remove("is-error");
    status.textContent = "Choose all three files to verify the benchmark result provenance chain.";
  };
  const validateApproval = approval => {
    exactKeys(approval, APPROVAL_FIELDS, "Approval Manifest");
    if (approval.schema_version !== "1.0" || approval.decision !== "approved_new_benchmark_result" ||
        !slug(approval.approval_id) || !slug(approval.source_id) ||
        !text(approval.reviewer) || !date(approval.reviewed_at) ||
        approval.reviewed_at > new Date().toISOString().slice(0,10) ||
        !text(approval.review_notes) || approval.review_notes.trim().length < 30) {
      throw Error("Approval Manifest or explicit human-review decision is invalid.");
    }
    const record = approval.record;
    if (!record || typeof record !== "object" || Array.isArray(record)) throw Error("Approval record must be an object.");
    const allowed = [...REQUIRED_RECORD, ...OPTIONAL_RECORD];
    if (REQUIRED_RECORD.some(key => !(key in record)) || Object.keys(record).some(key => !allowed.includes(key))) {
      throw Error("Approval record fields do not match the supported benchmark-result record schema.");
    }
    if (!slug(record.id) || record.source_id !== approval.source_id ||
        !["standardized_public_submission","third_party_public_benchmark","vendor_reported","independent_measurement","research_evaluation"].includes(record.source_class) ||
        record.evidence_level !== record.source_class) {
      throw Error("Result ID, source ID or evidence classification is invalid; evidence promotion is prohibited.");
    }
    for (const key of ["benchmark_suite","submitter","system_type","system_name","division","availability","model","scenario","source_record_key"]) {
      if (!text(record[key])) throw Error("record." + key + " must be explicit and non-empty.");
    }
    if (record.publication_date !== null && !date(record.publication_date)) throw Error("publication_date must be an ISO date or null.");
    if (record.publication_date && record.publication_date > approval.reviewed_at) throw Error("Publication date cannot follow human review.");
    if (record.result_value !== null && (typeof record.result_value !== "number" || !Number.isFinite(record.result_value))) {
      throw Error("result_value must be a finite number or null.");
    }
    if (typeof record.inferred !== "boolean" || record.power_metrics_available !== false ||
        record.design_power_watts !== null || !record.system || typeof record.system !== "object" ||
        Array.isArray(record.system) || !record.software || typeof record.software !== "object" ||
        Array.isArray(record.software)) throw Error("Result flags, power boundary, system or software object is invalid.");
    for (const key of ["source_url","dataset_url","release_url"]) {
      if (record[key] !== null && !safeUrl(record[key])) throw Error("record." + key + " must be an HTTPS URL or null.");
    }
    if (!safeUrl(record.source_url)) throw Error("A reviewed result must include a valid HTTPS source_url.");
    for (const key of ["metrics","configuration","workload"]) {
      if (key in record && (!record[key] || typeof record[key] !== "object" || Array.isArray(record[key]))) {
        throw Error("record." + key + " must be an object.");
      }
    }
    if (record.metrics && Object.entries(record.metrics).some(([,v]) => typeof v !== "number" || !Number.isFinite(v))) {
      throw Error("Raw metrics must contain finite numeric values only.");
    }
    for (const key of ["hardware_evidence","runtime_trace","normalized_metrics","power_measurement_valid",
      "cpu_power_measurement_valid","gpu_power_metrics_available","cpu_power_metrics_available",
      "power_measurement_status","cpu_power_measurement_status"]) {
      if (key in record && record[key] !== null && record[key] !== false &&
          !(typeof record[key] === "object" && !Array.isArray(record[key]) && Object.keys(record[key]).length === 0) &&
          !(Array.isArray(record[key]) && record[key].length === 0)) {
        throw Error("v1 adapter does not accept " + key + ".");
      }
    }
  };
  const verify = async () => {
    const files = Object.fromEntries(Object.entries(inputs).map(([key,input]) => [key,input.files[0]]));
    if (Object.values(files).some(file => !file)) {
      clearResults(); status.classList.remove("is-error");
      status.textContent = "Choose all three files to verify the benchmark result provenance chain."; return;
    }
    clearResults(); status.classList.remove("is-error");
    try {
      const [packageFile,approvalFile,registryFile] = await Promise.all([
        read(files.package),read(files.approval),read(files.registry)
      ]);
      const pkg=packageFile.data,approval=approvalFile.data,db=registryFile.data;
      const packageFields=["schema_version","proposal_id","proposal_type","created_at","target_registry",
        "source_snapshot","approval","target","operations","audit","proposed_registry_sha256","policy","package_sha256"];
      exactKeys(pkg,packageFields,"Proposal package");
      if (pkg.schema_version !== "1.0" || pkg.proposal_type !== "benchmark_result_creation" ||
          !slug(pkg.proposal_id) || pkg.proposal_id !== approval.approval_id) throw Error("Unsupported proposal type or ID.");
      if (typeof pkg.created_at !== "string" || !/(Z|[+-]\d{2}:\d{2})$/.test(pkg.created_at) ||
          !Number.isFinite(Date.parse(pkg.created_at)) || Date.parse(pkg.created_at)>Date.now()) {
        throw Error("Proposal timestamp must be valid, timezone-aware and not in the future.");
      }
      validateApproval(approval);
      if (!equal(pkg.approval,approval)) throw Error("Separate Approval Manifest does not exactly match the proposal.");
      if (Date.parse(pkg.created_at) < Date.parse(approval.reviewed_at+"T00:00:00Z")) {
        throw Error("Proposal cannot predate its human review.");
      }
      const packageBody={...pkg}; delete packageBody.package_sha256;
      const packageHash=await hashJson(packageBody);
      if (packageHash!==pkg.package_sha256) throw Error("Proposal package SHA256 mismatch.");
      if (!db || db.schema_version!=="1.0" ||
          !equal(Object.keys(db).sort(),["schema_version","database_version","last_imported_at","scope","sources","summary","records"].sort()) ||
          !Array.isArray(db.sources) || !Array.isArray(db.records) || typeof db.database_version!=="string") {
        throw Error("Expected the exact benchmark-results registry schema 1.0.");
      }
      const baseHash=await digest(registryFile.bytes);
      if (!pkg.target_registry || pkg.target_registry.path!=="data/benchmark-results.json" ||
          pkg.target_registry.schema_version!=="1.0" || pkg.target_registry.base_sha256!==baseHash) {
        throw Error("Base registry SHA256 or target registry binding mismatch.");
      }
      const matches=db.sources.map((source,index)=>({source,index})).filter(x=>x.source?.id===approval.source_id);
      if (matches.length!==1) throw Error("Source ID must resolve exactly once in the existing registry.");
      const {source, index:sourceIndex}=matches[0],record=approval.record;
      if (!equal(source,pkg.source_snapshot)) throw Error("Source snapshot differs from the exact base registry.");
      if (source.source_class!==record.source_class) throw Error("Result source_class must match the registered source.");
      const sourceUrls=["results_url","release_url","dataset_url","repository_url","api_url"]
        .map(key=>source[key]).filter(Boolean);
      if (!sourceUrls.includes(record.source_url)) throw Error("Result source_url is not registered for this source.");
      if (db.records.some(x=>x.id===record.id)) throw Error("Benchmark result ID already exists.");
      if (db.records.some(x=>x.source_id===record.source_id && x.source_record_key===record.source_record_key)) {
        throw Error("Source record key already exists for this source.");
      }
      if (!Number.isSafeInteger(source.record_count) || source.record_count<0) throw Error("Registered source record_count is invalid.");
      const target={source_id:source.id,record_id:record.id,source_record_key:record.source_record_key};
      if (!equal(pkg.target,target)) throw Error("Proposal target does not match the approved result.");
      const updated=JSON.parse(JSON.stringify(db));
      updated.records.push(record);
      updated.sources[sourceIndex].record_count+=1;
      updated.last_imported_at=approval.reviewed_at;
      updated.database_version=String(db.database_version)+"+reviewed-"+approval.approval_id;
      updated.summary=summarize(updated.records);
      const operations=[
        {op:"add",path:"/records/-",value:record},
        {op:"replace",path:"/sources/"+sourceIndex+"/record_count",value:updated.sources[sourceIndex].record_count},
        {op:"replace",path:"/last_imported_at",value:updated.last_imported_at},
        {op:"replace",path:"/database_version",value:updated.database_version},
        {op:"replace",path:"/summary",value:updated.summary}
      ];
      if (!equal(pkg.operations,operations)) throw Error("Proposal does not contain the exact five permitted operations.");
      const proposedHash=await hashJson(updated);
      if (proposedHash!==pkg.proposed_registry_sha256 ||
          pkg.audit?.verification_status!=="exact_one_result_append" || pkg.audit?.unapproved_changes!==0 ||
          pkg.audit?.source_truth_verified!==false || pkg.audit?.evidence_level_promoted!==false ||
          pkg.audit?.source_id!==source.id || pkg.audit?.source_class!==source.source_class ||
          pkg.audit?.reviewer!==approval.reviewer || pkg.audit?.reviewed_at!==approval.reviewed_at ||
          pkg.audit?.base_registry_sha256!==baseHash || pkg.audit?.proposed_registry_sha256!==proposedHash) {
        throw Error("Audit metadata or proposed registry SHA256 is inconsistent.");
      }
      if (pkg.policy?.human_approval_required!==true || pkg.policy?.source_truth_verified!==false ||
          pkg.policy?.evidence_level_promoted!==false || pkg.policy?.automatic_merge!==false ||
          pkg.policy?.power_claims_supported!==false) throw Error("Proposal policy guardrails are missing or inconsistent.");
      const patch={schema:"https://json.schemastore.org/json-patch.json",base_registry_sha256:baseHash,operations};
      verified={pkg,updated,patch,audit:pkg.audit};
      const sourceLink=$("[data-bi-source-link]");
      const sourceUrl=record.source_url;
      sourceLink.href=sourceUrl; sourceLink.textContent="Open registered source ↗";
      $("[data-bi-source-name]").textContent=source.name;
      $("[data-bi-source-publisher]").textContent=source.publisher;
      $("[data-bi-source-meta]").textContent=source.source_class+" · "+source.record_count+" existing records";
      $("[data-bi-record-name]").textContent=record.system_name+" · "+record.model;
      $("[data-bi-record-summary]").textContent=(record.result_value===null?"Result not provided":record.result_value+" "+(record.result_unit||""))+" · "+record.benchmark_suite+" · "+record.scenario;
      $("[data-bi-evidence-level]").textContent=record.evidence_level;
      $("[data-bi-record-meta]").textContent=record.submitter+" · "+record.availability+" · "+record.division;
      $("[data-bi-base-hash]").textContent=baseHash;
      $("[data-bi-package-hash]").textContent=packageHash;
      $("[data-bi-proposed-hash]").textContent=proposedHash;
      $("[data-bi-suite]").textContent=record.benchmark_suite+" · "+(record.benchmark_version||"version not reported");
      $("[data-bi-model]").textContent=record.model+" · "+record.scenario;
      $("[data-bi-system]").textContent=record.system_type+" · "+record.system_name;
      $("[data-bi-value]").textContent=record.result_value===null?"Not reported":record.result_value+" "+(record.result_unit||"");
      const context=$("[data-bi-context]"); context.replaceChildren();
      [
        ["Accelerator vendor",record.accelerator_vendor],["System",record.system],
        ["Software stack",record.software],["Precision / weight data types",record.weight_data_types],
        ["Accuracy target",record.accuracy_text],["Division / availability",record.division+" / "+record.availability],
        ["Workload",record.workload],["Configuration",record.configuration],
        ["Source record key",record.source_record_key],["Source location",record.source_location],
        ["Publication date",record.publication_date],["Inferred",record.inferred]
      ].forEach(([key,value])=>row(context,key, value===null?"Not reported":value));
      const diff=$("[data-bi-diff]"); diff.replaceChildren();
      operations.forEach(op=>row(diff,op.path,op.op,op.path==="/records/-"?record.id:op.value));
      $("[data-bi-operations]").textContent=JSON.stringify(operations,null,2);
      $("[data-bi-checks]").replaceChildren(
        check("Package integrity","Canonical package SHA256 matches."),
        check("Separate human approval","Approval Manifest matches the embedded approval exactly."),
        check("Registered source identity","Source ID, source class and registered source URL match the base registry."),
        check("Base registry identity","Raw benchmark-results.json SHA256 matches the package."),
        check("Append-only write set","Exactly one result append plus four deterministic registry reconciliations."),
        check("Duplicate protection","Result ID and source-scoped source_record_key are unique."),
        check("Evidence boundary","Source class is preserved; no evidence promotion or source-truth claim."),
        check("Proposed registry hash","Reconstructed result registry matches the proposed SHA256.")
      );
      panels.forEach(panel=>panel.hidden=false);
      status.textContent="Verified locally: source, approval, base registry, five operations and proposed hash are consistent. This is not source-truth verification or GitHub submission.";
    } catch(error) {
      clearResults(); status.classList.add("is-error");
      status.textContent="Benchmark proposal validation failed: "+error.message;
    }
  };
  const download=(name,value)=>{
    const blob=new Blob([JSON.stringify(value,null,2)+"\n"],{type:"application/json"});
    const url=URL.createObjectURL(blob),a=document.createElement("a");
    a.href=url;a.download=name;document.body.append(a);a.click();a.remove();
    setTimeout(()=>URL.revokeObjectURL(url),3000);
  };
  Object.values(inputs).forEach(input=>input.addEventListener("change",verify));
  $("[data-bi-clear]").addEventListener("click",clear);
  root.querySelectorAll("[data-bi-download]").forEach(button=>button.addEventListener("click",()=>{
    if(!verified)return;
    const kind=button.dataset.biDownload;
    if(kind==="patch")download(verified.pkg.proposal_id+"-patch.json",verified.patch);
    if(kind==="audit")download(verified.pkg.proposal_id+"-audit.json",verified.audit);
    if(kind==="database")download("benchmark-results-proposed.json",verified.updated);
  }));
})();