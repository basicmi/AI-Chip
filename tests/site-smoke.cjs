const { chromium } = require("playwright");

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1365, height: 900 } });
  const base = "http://127.0.0.1:4173/AI-Chip";
  const errors = [];
  const homeDataRequests = [];

  page.on("request", request => {
    if (request.url().includes("/AI-Chip/data/")) homeDataRequests.push(request.url());
  });
  page.on("pageerror", error => errors.push("Page error: " + error.message));
  page.on("response", response => {
    if (response.url().startsWith(base + "/") && response.status() >= 400) {
      errors.push("HTTP " + response.status() + " " + response.url());
    }
  });

  const waitForDataset = async ({ name, loadSelector, statSelector, countSelector }) => {
    await page.waitForFunction((selector) => {
      const state = document.querySelector(selector);
      return state && (state.hidden || state.classList.contains("is-error"));
    }, loadSelector, { timeout: 15000 });

    const state = await page.locator(loadSelector).evaluate(node => ({
      hidden: node.hidden,
      message: node.textContent.trim()
    }));
    if (!state.hidden) {
      throw new Error(name + " dataset failed to load: " + state.message);
    }

    const total = (await page.locator(statSelector).textContent()).trim();
    const visible = (await page.locator(countSelector).textContent()).trim();
    if (!/^\d+$/.test(total) || visible !== total) {
      throw new Error(name + " count mismatch: visible=" + visible + ", dataset total=" + total);
    }
  };

  const routes = ["/", "/directory/", "/products/", "/software-ecosystem/", "/compatibility/", "/workloads/", "/model-support/", "/evidence-review/", "/database-integration/", "/product-integration/", "/benchmark-integration/", "/intelligence-operations/", "/benchmarks/", "/results/", "/concurrency/", "/coverage/", "/performance/", "/recipe-review/", "/cross-benchmark/", "/diagnosis/", "/performance-evidence/"];
  for (const route of routes) {
    const response = await page.goto(base + route, { waitUntil: "networkidle" });
    if (!response || !response.ok()) throw new Error("Route failed: " + route);
    await page.locator("header.site-header").waitFor();
    await page.locator("main#main-content").waitFor();
  }

  // Performance Evidence Workbench: local file loading, identity matching and decision-history rendering.
  const peRecord = {id:"pe-fixture",model:"Fixture Model"};
  const pePlan = {schema_version:"1.0",plan_id:"plan-fixture",record_context:{record_id:"pe-fixture"},experiment_count:1,experiments:[{experiment_id:"exp-fixture",title:"Decode TP experiment",mechanism:"runtime_scheduling_or_queueing",hypothesis:"Queueing contributes to the observed latency.",observed_signal:"Elevated p99 TPOT",baseline:{source_record_id:"pe-fixture"}}]};
  const peSubmission = {schema_version:"1.0",plan_id:"plan-fixture",experiment_id:"exp-fixture",protocol:{parameter:"decode_tp",baseline_value:4,treatment_value:8,primary_metric:{key:"median_tpot",unit:"s"}}};
  const hashFixture = "a".repeat(64);
  const peReview = {schema_version:"1.0",report_type:"performance_evidence_review",record_id:"pe-fixture",plan_id:"plan-fixture",experiment_id:"exp-fixture",record_sha256:hashFixture,plan_sha256:"b".repeat(64),submission_sha256:"c".repeat(64),review_status:"needs_review",hypothesis_verdict:"undetermined",review_blockers:[],runs:[{run_id:"base-1",condition:"baseline",status:"valid",value:0.12,unit:"s",source_url:"https://example.org/base"},{run_id:"treat-1",condition:"treatment",status:"valid",value:0.1,unit:"s",source_url:"https://example.org/treat"}],statistics:{baseline:{valid_runs:1,min:0.12,max:0.12,median:0.12},treatment:{valid_runs:1,min:0.1,max:0.1,median:0.1}},relative_improvement_percent:16.67,effect_threshold_met:true};
  peSubmission.record_sha256=hashFixture;
  peSubmission.plan_sha256="b".repeat(64);
  peSubmission.submission_sha256="c".repeat(64);
  const peLedger = {schema_version:"1.0",entries:[{evidence_identity:{record_id:"pe-fixture",plan_id:"plan-fixture",experiment_id:"exp-fixture",submission_sha256:"c".repeat(64)},decision:{decision_id:"decision-1",verdict:"inconclusive",reviewer:"Fixture reviewer",reviewed_at:"2026-11-26T00:00:00Z",rationale:"Synthetic review only.",applicability:"Fixture only",limitations:"Not production evidence."},previous_entry_sha256:null,entry_sha256:"d".repeat(64)}]};
  await page.goto(base+"/performance-evidence/",{waitUntil:"networkidle"});
  const uploadJson = async (selector,name,value) => page.locator(selector).setInputFiles({name,mimeType:"application/json",buffer:Buffer.from(JSON.stringify(value))});
  await uploadJson("[data-pe-record]","record.json",peRecord);
  await uploadJson("[data-pe-plan]","plan.json",pePlan);
  await uploadJson("[data-pe-submission]","submission.json",peSubmission);
  await uploadJson("[data-pe-review]","review.json",peReview);
  await uploadJson("[data-pe-ledger]","ledger.json",peLedger);
  if(await page.locator("[data-pe-content]").isHidden())throw new Error("Performance Evidence Workbench did not render a matched evidence chain");
  if((await page.locator("[data-pe-stat='runs']").textContent()).trim()!=="2")throw new Error("Performance Evidence Workbench run count mismatch");
  if(!(await page.locator("[data-pe-decision-list]").textContent()).includes("inconclusive"))throw new Error("Performance Evidence Workbench did not render human decision history");
  const badSubmission={...peSubmission,plan_id:"wrong-plan"};
  await uploadJson("[data-pe-submission]","bad-submission.json",badSubmission);
  if(!(await page.locator("[data-pe-status]").textContent()).includes("do not refer to the same evidence chain"))throw new Error("Performance Evidence Workbench accepted mismatched evidence identity");
  await page.locator("[data-pe-reset]").click();
  if(!(await page.locator("[data-pe-status]").textContent()).includes("Choose the five evidence files"))throw new Error("Performance Evidence Workbench reset failed");

  // InferenceX coverage explorer: missing metadata remains visible and source-linked.
  const coverageFixture = (id, hardware, recipe) => ({
    id, source_id:"inferencex", source_class:"third_party_public_benchmark",
    evidence_level:"publisher_published_observation", benchmark_suite:"SemiAnalysis InferenceX",
    benchmark_version:"2026.1", model:"model-a", model_display_name:"Model A",
    scenario:"single_turn",division:"third_party",availability:"published",
    weight_data_types:"FP8",inferred:false,errors:0,system_type:"datacenter",
    system:{hardware,physical_prefill_gpus:0,physical_decode_gpus:8,is_multinode:false,workers:[]},
    software:{framework:"vllm",recipe_fingerprint:recipe},
    configuration:{decode_tp:8,workflow_run_id:id},
    workload:{benchmark_type:"single_turn",isl:1024,osl:256,concurrency:32,precision:"FP8",speculative_method:"none",disaggregated:false},
    normalized_metrics:{output_throughput_per_gpu:{value:100,unit:"tok/s/GPU",family:"throughput",direction:"higher"}},
    source_url:"https://example.org/"+id
  });
  await page.route("**/data/benchmark-results.json.gz", route=>route.fulfill({
    status:200,contentType:"application/json",body:JSON.stringify({records:[
      coverageFixture("coverage-a","GPU A","recipe-a"),
      coverageFixture("coverage-b",null,null)
    ],database_version:"test-v1",last_updated:"2026-11-25"})
  }));
  await page.goto(base+"/coverage/",{waitUntil:"networkidle"});
  await page.locator("[data-coverage-load]").waitFor({state:"hidden",timeout:15000});
  const coverageTotal=(await page.locator("[data-coverage-stat='records']").textContent()).trim();
  if(coverageTotal!=="2")throw Error("Coverage explorer record count mismatch: "+coverageTotal+"; error="+await page.locator("[data-coverage-error]").textContent()+"; root="+await page.locator("[data-coverage-explorer]").count());
  await page.locator("[data-coverage-dimension]").selectOption("recipe");
  if(!(await page.locator("[data-coverage-dimension-summary]").textContent()).includes("1 / 2 records"))throw Error("Coverage dimension percentage mismatch");
  await page.locator("[data-coverage-gap-field]").selectOption("hardware");
  if(!(await page.locator("[data-coverage-gap-count]").textContent()).includes("1 records missing Hardware"))throw Error("Coverage gap filter mismatch");
  if(await page.locator("[data-coverage-gap-rows] a").count()!==1)throw Error("Coverage gap record source link missing");
  // Performance Intelligence Workspace: filter the same published registry fixture.
  await page.goto(base+"/performance/",{waitUntil:"networkidle"});
  await page.locator("[data-pw-load]").waitFor({state:"hidden",timeout:15000});
  if((await page.locator("[data-pw-stat='records']").textContent()).trim()!=="2")throw Error("Performance workspace registry count mismatch");
  await page.locator("[data-pw-filter='model']").selectOption({label:"Model A"});
  await page.locator("[data-pw-filter='hardware']").selectOption({label:"GPU A"});
  if(!(await page.locator("[data-pw-filter-status]").textContent()).includes("Showing 1 of 2"))throw Error("Performance workspace filters did not narrow the registry");
  await page.locator("[data-pw-metric]").selectOption("output_throughput_per_gpu");
  if(await page.locator("[data-pw-observations] tr").count()!==1)throw Error("Performance workspace metric observation missing");
  // Recipe evidence review: one axis changes, other stable configuration remains fixed.
  const recipeFixture = (id, degree, fingerprint) => ({
    id,source_id:"inferencex",source_class:"third_party_public_benchmark",
    evidence_level:"publisher_published_observation",benchmark_suite:"SemiAnalysis InferenceX",
    benchmark_version:"2026.1",model:"model-r",model_display_name:"Model R",
    scenario:"single_turn",division:"third_party",availability:"published",
    weight_data_types:"FP8",inferred:false,errors:0,system_type:"datacenter",
    system:{hardware:"GPU R",physical_prefill_gpus:0,physical_decode_gpus:8,is_multinode:false,workers:[]},
    software:{framework:"vllm",recipe_fingerprint:fingerprint},
    configuration:{decode_tp:degree,decode_ep:1},
    workload:{benchmark_type:"single_turn",isl:1024,osl:256,concurrency:32,precision:"FP8",speculative_method:"disabled",disaggregated:false},
    normalized_metrics:{output_throughput_per_gpu:{value:100*degree,unit:"tok/s/GPU",family:"throughput",direction:"higher"}},
    source_url:"https://example.org/"+id
  });
  await page.route("**/data/benchmark-results.json.gz", route=>route.fulfill({
    status:200,contentType:"application/json",body:JSON.stringify({records:[
      recipeFixture("recipe-a",4,"fingerprint-a"),recipeFixture("recipe-b",8,"fingerprint-b")
    ]})
  }));
  await page.goto(base+"/recipe-review/",{waitUntil:"networkidle"});
  await page.locator("[data-rr-load]").waitFor({state:"hidden",timeout:15000});
  if((await page.locator("[data-rr-stat='groups']").textContent()).trim()!=="1")throw Error("Recipe review candidate grouping mismatch: groups="+(await page.locator("[data-rr-stat='groups']").textContent())+"; status="+await page.locator("[data-rr-status]").textContent()+"; error="+await page.locator("[data-rr-error]").textContent());
  if(await page.locator("[data-rr-groups] .rr-group").count()!==1)throw Error("Recipe review candidate group missing");
  if(await page.locator("[data-rr-groups] tbody tr").count()!==2)throw Error("Recipe review observations missing");
  await page.locator("[data-rr-axis]").selectOption("decode_tp");
  if(await page.locator("[data-rr-groups] .rr-group").count()!==1)throw Error("Recipe review axis filter failed");
  // Cross-benchmark crosswalk: exact signature, same-dimensional, and unit-review links.
  const crossFixture = (id,suite,key,unit,label,sourceMetric) => ({
    id,source_id:id,source_class:"third_party_public_benchmark",evidence_level:"publisher_published_observation",
    benchmark_suite:suite,benchmark_version:"1.0",model:"Model X",scenario:"offline",division:"closed",
    availability:"published",weight_data_types:"FP8",inferred:false,errors:0,
    normalized_metrics:{[key]:{value:123,unit,family:"throughput",direction:"higher",label,source_metric:sourceMetric}},
    source_url:"https://example.org/"+id
  });
  await page.route("**/data/benchmark-results.json.gz", route=>route.fulfill({
    status:200,contentType:"application/json",body:JSON.stringify({records:[
      crossFixture("cross-a","Suite Alpha","output_throughput","token/s","Output throughput","tokens_per_second"),
      crossFixture("cross-b","Suite Beta","output_throughput","token/s","Generated tokens per second","tokens_per_second"),
      crossFixture("cross-c","Suite Gamma","throughput_rate","token/s","Token generation rate","tokens_per_second"),
      crossFixture("cross-d","Suite Delta","output_rate","k token/s","Output rate","output_rate")
    ]})
  }));
  await page.goto(base+"/cross-benchmark/",{waitUntil:"networkidle"});
  await page.locator("[data-cb-load]").waitFor({state:"hidden",timeout:15000});
  if((await page.locator("[data-cb-stat='suites']").textContent()).trim()!=="4")throw Error("Cross-benchmark suite count mismatch");
  if((await page.locator("[data-cb-stat='candidates']").textContent()).trim()!=="6")throw Error("Cross-benchmark candidate count mismatch");
  await page.locator("[data-cb-relation]").selectOption("same_signature");
  if(await page.locator("[data-cb-candidates] .cb-candidate").count()!==1)throw Error("Exact normalized metric signature mapping mismatch");
  await page.locator("[data-cb-candidates] .cb-inspect-button").first().click();
  if(!(await page.locator("[data-cb-inspector]").textContent()).includes("tokens_per_second"))throw Error("Cross-benchmark metric definition inspector omitted source metric");
  if(await page.locator("[data-cb-inspector] a").count()!==1)throw Error("Cross-benchmark inspector omitted source traceability");
  await page.locator("[data-cb-relation]").selectOption("same_dimension");
  if(await page.locator("[data-cb-candidates] .cb-candidate").count()!==2)throw Error("Same-dimension candidate classification mismatch");
  await page.locator("[data-cb-relation]").selectOption("unit_review");
  if(await page.locator("[data-cb-candidates] .cb-candidate").count()!==3)throw Error("Unit-review candidate classification mismatch");
  // Evidence-based diagnosis workbench: observed signals and missing profiler/trace inputs stay distinct.
  const diagnosisRecord = (id, withEvidence) => ({
    id,source_id:"inferencex",source_class:"third_party_public_benchmark",
    evidence_level:"publisher_published_observation",benchmark_suite:"SemiAnalysis InferenceX",
    benchmark_version:"2026.1",model:"model-d",model_display_name:"Model Diagnosis",
    scenario:"single_turn",division:"third_party",availability:"published",weight_data_types:"FP8",
    inferred:false,errors:0,system:{hardware:"GPU D",physical_decode_gpus:8},
    software:{framework:"vllm"},source_url:"https://example.org/"+id,
    normalized_metrics:{
      p99_ttft:{value:1.2,unit:"s",family:"latency",direction:"lower",source_metric:"p99_ttft"},
      p99_tpot:{value:0.12,unit:"s",family:"latency",direction:"lower",source_metric:"p99_tpot"},
      output_throughput_per_gpu:{value:120,unit:"tok/s/GPU",family:"throughput",direction:"higher",source_metric:"output_tput"}
    },
    ...(withEvidence?{
      hardware_evidence:{
        collector:{name:"fixture-profiler",type:"profiler"},
        system_scope:{scope_type:"per_gpu",device_count:1,device_model:"GPU D"},
        sampling:{started_at:"2026-11-26T00:00:00Z",ended_at:"2026-11-26T00:00:10Z",sample_interval_ms:1000,sample_count:10},
        provenance:{source_type:"profiler_export",source_url:"https://example.org/profiler.json",collected_at:"2026-11-26T00:00:11Z"},
        metrics:[
          {metric_id:"compute_flop_count",value:1000,unit:"FLOP",measurement_kind:"hardware_counter",aggregation:"sum",scope:"per_gpu",source_name:"flop"},
          {metric_id:"dram_read_bytes",value:500,unit:"byte",measurement_kind:"hardware_counter",aggregation:"sum",scope:"per_gpu",source_name:"dram_read"},
          {metric_id:"throttle_active_pct",value:0,unit:"%",measurement_kind:"telemetry",aggregation:"mean",scope:"per_gpu",source_name:"throttle"}
        ]
      },
      runtime_trace:{
        collector:{name:"fixture-trace",type:"runtime_trace"},clock_domain:"utc_wall_clock",
        sampling:{started_at:"2026-11-26T00:00:00Z",ended_at:"2026-11-26T00:00:10Z"},
        provenance:{source_type:"runtime_trace_export",source_url:"https://example.org/trace.json",collected_at:"2026-11-26T00:00:11Z"},
        events:[{event_id:"q1",name:"queue",category:"queue_wait",started_at:"2026-11-26T00:00:01Z",ended_at:"2026-11-26T00:00:02Z"}]
      }
    }:{})
  });
  await page.route("**/data/benchmark-results.json.gz", route=>route.fulfill({
    status:200,contentType:"application/json",body:JSON.stringify({records:[diagnosisRecord("diagnosis-a",true),diagnosisRecord("diagnosis-b",false)]})
  }));
  await page.goto(base+"/diagnosis/",{waitUntil:"networkidle"});
  await page.locator("[data-dw-load]").waitFor({state:"hidden",timeout:15000});
  if((await page.locator("[data-dw-stat='records']").textContent()).trim()!=="2")throw Error("Diagnosis workbench record count mismatch");
  if((await page.locator("[data-dw-stat='hardware']").textContent()).trim()!=="1")throw Error("Diagnosis profiler evidence coverage count mismatch");
  if((await page.locator("[data-dw-stat='traces']").textContent()).trim()!=="1")throw Error("Diagnosis runtime trace coverage count mismatch");
  if((await page.locator("[data-dw-stat='serving']").textContent()).trim()!=="2")throw Error("Diagnosis serving metric coverage count mismatch");
  if(await page.locator("[data-dw-runtime] tbody tr").count()!==3)throw Error("Diagnosis serving metrics were not rendered");
  if(!(await page.locator("[data-dw-evidence]").textContent()).includes("compute_flop_count"))throw Error("Diagnosis profiler metric evidence missing");
  if(!(await page.locator("[data-dw-mechanisms]").textContent()).includes("theoretical_peak_flops"))throw Error("Diagnosis missing-input checklist did not identify absent roofline inputs");
  if(!(await page.locator("[data-dw-mechanisms]").textContent()).includes("No bottleneck verdict is generated"))throw Error("Diagnosis workbench must preserve no-automatic-verdict guardrail");
  await page.locator("[data-dw-record]").selectOption("diagnosis-b");
  if(!(await page.locator("[data-dw-provenance]").textContent()).includes("No profiler or runtime trace provenance"))throw Error("Missing evidence was not represented as unknown");
  await page.unroute("**/data/benchmark-results.json.gz");


  // Concurrency explorer: deterministic fixture through the production fetch/render path.
  const sweepFixture = (id, concurrency, value, recipe="recipe-a") => ({
    id, source_id:"inferencex", source_class:"third_party_public_benchmark",
    evidence_level:"publisher_published_observation", benchmark_suite:"SemiAnalysis InferenceX",
    benchmark_version:null, model:"model-a", model_display_name:"Model A",
    scenario:"single_turn",division:"third_party",availability:"published",
    weight_data_types:"FP8",inferred:false,errors:0,system_type:"datacenter",
    system:{hardware:"GPU A",physical_prefill_gpus:0,physical_decode_gpus:8,is_multinode:false,workers:[]},
    software:{framework:"vllm",recipe_fingerprint:recipe},
    configuration:{decode_tp:8,workflow_run_id:id},
    workload:{benchmark_type:"single_turn",isl:1024,osl:256,concurrency,precision:"FP8",speculative_method:"none",disaggregated:false},
    normalized_metrics:{output_throughput_per_gpu:{value,unit:"tok/s/GPU",family:"throughput",direction:"higher"}},
    source_url:"https://example.org/"+id
  });
  await page.route("**/data/benchmark-results.json.gz", route=>route.fulfill({
    status:200,contentType:"application/json",body:JSON.stringify({records:[
      sweepFixture("a",8,80),sweepFixture("b",32,120),sweepFixture("c",32,140),sweepFixture("d",64,200,"other")
    ]})
  }));
  await page.goto(base+"/concurrency/",{waitUntil:"networkidle"});
  await page.locator("[data-sweep-load]").click();
  await page.waitForFunction(()=>document.querySelector("[data-sweep-status]").textContent.includes("Loaded 1 matching-context"));
  if(await page.locator("[data-sweep-table] tr").count()!==2)throw Error("Concurrency explorer must show exactly two observed levels");
  const sweepCells=await page.locator("[data-sweep-table] tr").nth(1).locator("td").allTextContents();
  if(sweepCells.join(",")!=="32,2,120,130,140")throw Error("Concurrency repeated observation summary mismatch");
  if(await page.locator("[data-sweep-chart] circle").count()!==3)throw Error("Concurrency plot lost source observations");
  if(await page.locator("[data-sweep-records] a").count()!==3)throw Error("Concurrency plot lost source links");
  await page.unroute("**/data/benchmark-results.json.gz");
  await page.goto(base+"/concurrency/",{waitUntil:"networkidle"});
  await page.locator("[data-sweep-load]").click();
  await page.waitForFunction(()=>/Loaded \d+ matching-context metric series/.test(document.querySelector("[data-sweep-status]").textContent),null,{timeout:30000});
  // Actual registry may validly have no qualifying sweeps.

  // PR #140: local-only typed Product Integration Workbench.
  await page.goto(base + "/product-integration/", {waitUntil:"networkidle"});
  for (const selector of ["[data-pi-package]","[data-pi-claims]","[data-pi-approval]","[data-pi-registry]","[data-pi-status]"]) {
    await page.locator(selector).waitFor();
  }
  if (!(await page.locator("[data-pi-results]").first().isHidden())) {
    throw new Error("Product Integration Workbench must hide unverified results before loading a package");
  }

  const piCrypto = require("crypto");
  const piCanonical = value => Array.isArray(value) ? "[" + value.map(piCanonical).join(",") + "]" :
    value && typeof value === "object" ? "{" + Object.keys(value).sort().map(k =>
      JSON.stringify(k) + ":" + piCanonical(value[k])).join(",") + "}" :
    typeof value === "number" && Object.is(value,-0) ? "0" : JSON.stringify(value);
  const piHash = value => piCrypto.createHash("sha256").update(value).digest("hex");
  const piArtifact = (name,data) => ({name,mimeType:"application/json",buffer:Buffer.from(JSON.stringify(data))});
  const piDb = {schema_version:"1.3",companies:[{id:"nvidia",display_name:"NVIDIA",products:[],claims:[],evidence:[]}]};
  const piSource = {claim_id:"claim-rubin",review_status:"unverified_candidate",
    statement:"NVIDIA announced the Rubin GPU architecture and product family.",
    evidence_quote:"Rubin is our next-generation GPU architecture.",
    source:{url:"https://vendor.example/rubin",publisher:"NVIDIA"}};
  const piReport = {schema_version:"1.0",claim_count:1,claims:[piSource]};
  const piEvidence = {id:"nvidia-rubin-announcement",title:"NVIDIA Rubin announcement",
    url:"https://vendor.example/rubin",publisher:"NVIDIA",source_type:"vendor_primary",
    independence:"vendor",published_at:"2026-10-28",checked_at:"2026-11-20",
    review_status:"reviewed",notes:"Original vendor announcement inspected by reviewer."};
  const piProduct = {id:"rubin",name:"Rubin",product_type:"gpu",availability:"announced",
    claim_ids:["rubin-identity"],architecture:"Rubin",announced_at:"2026-10-28",
    availability_history:[{status:"announced",effective_at:"2026-10-28",
      evidence_id:piEvidence.id,notes:"Vendor announced the product family."}]};
  const piClaim = {id:"rubin-identity",subject_type:"product",subject_id:"rubin",
    topic:"product_identity",statement:piSource.statement,
    scope:"Product identity and vendor-announced architecture only; no performance claim.",
    claim_status:"vendor_reported",evidence_ids:[piEvidence.id],last_reviewed:"2026-11-20"};
  const piApproval = {schema_version:"1.0",approval_id:"approve-rubin",
    reviewer:"maintainer@example.org",reviewed_at:"2026-11-20",
    decision:"approved_new_product_with_identity_claim",company_id:"nvidia",
    extracted_claim_id:piSource.claim_id,product:piProduct,claim:piClaim,evidence:piEvidence,
    review_notes:"Reviewer inspected the original vendor announcement and verified the product identity and source context."};
  const piUpdated=JSON.parse(JSON.stringify(piDb));
  piUpdated.companies[0].evidence.push(piEvidence);piUpdated.companies[0].products.push(piProduct);
  piUpdated.companies[0].claims.push(piClaim);
  const piRegistryText=JSON.stringify(piDb,null,2)+"\n",piBaseHash=piHash(piRegistryText);
  const piProposedHash=piHash(piCanonical(piUpdated));
  const piOperations=[
    {op:"add",path:"/companies/0/evidence/-",value:piEvidence},
    {op:"add",path:"/companies/0/products/-",value:piProduct},
    {op:"add",path:"/companies/0/claims/-",value:piClaim}
  ];
  const piBody={schema_version:"1.0",proposal_id:"approve-rubin",
    proposal_type:"company_profile_product_creation",created_at:"2026-11-23T04:00:00Z",
    target_registry:{path:"data/company-profiles.json",schema_version:"1.3",base_sha256:piBaseHash},
    source_claim:piSource,approval:piApproval,
    target:{company_id:"nvidia",company_display_name:"NVIDIA",company_index:0,
      product_id:"rubin",product_name:"Rubin",claim_id:"rubin-identity",source_claim_id:"claim-rubin"},
    operations:piOperations,
    audit:{verification_status:"exact_three_record_append",unapproved_changes:0,
      source_truth_verified:false,claim_status_changed:false,new_claim_status:"vendor_reported",
      approval_id:"approve-rubin",reviewer:"maintainer@example.org",reviewed_at:"2026-11-20",
      source_claim_id:"claim-rubin",source_url:piEvidence.url,
      evidence_quote_sha256:piHash(piSource.evidence_quote),
      base_registry_sha256:piBaseHash,proposed_registry_sha256:piProposedHash},
    proposed_registry_sha256:piProposedHash,
    policy:{human_approval_required:true,source_truth_verified:false,claim_status_changed:false,
      new_claim_status:"vendor_reported",automatic_merge:false,
      allowed_changes:["append one reviewed Evidence","append one new Product",
        "append one initial vendor_reported product_identity Claim"]}};
  const piPackage={...piBody,package_sha256:piHash(piCanonical(piBody))};
  await page.locator("[data-pi-package]").setInputFiles(piArtifact("product-proposal.json",piPackage));
  await page.locator("[data-pi-claims]").setInputFiles(piArtifact("claims.json",piReport));
  await page.locator("[data-pi-approval]").setInputFiles(piArtifact("approval.json",piApproval));
  await page.locator("[data-pi-registry]").setInputFiles({
    name:"company-profiles.json",mimeType:"application/json",buffer:Buffer.from(piRegistryText)
  });
  await page.waitForFunction(() => (document.querySelector("[data-pi-status]")?.textContent || "").includes("Verified locally"));
  if (!(await page.locator("[data-pi-results]").first().isVisible())) {
    throw new Error("Product Integration Workbench failed to verify the valid three-record append fixture");
  }
  const piTampered={...piPackage,operations:[{...piOperations[0],path:"/companies/0/summary"},...piOperations.slice(1)]};
  await page.locator("[data-pi-package]").setInputFiles(piArtifact("tampered-product-proposal.json",piTampered));
  await page.waitForFunction(() => (document.querySelector("[data-pi-status]")?.textContent || "").includes("SHA256 mismatch"));
  if (!(await page.locator("[data-pi-results]").first().isHidden())) {
    throw new Error("Product Integration Workbench exposed a tampered proposal");
  }

  // PR #142: local-only typed Benchmark Result Integration Workbench.
  await page.goto(base + "/benchmark-integration/", {waitUntil:"networkidle"});
  for (const selector of ["[data-bi-package]","[data-bi-approval]","[data-bi-registry]","[data-bi-status]"]) {
    await page.locator(selector).waitFor();
  }
  if (!(await page.locator("[data-bi-results]").first().isHidden())) {
    throw new Error("Benchmark Integration Workbench must hide unverified results before loading a package");
  }
  const biSource = {
    id:"vendor-benchmark",name:"Vendor Benchmark",publisher:"Vendor",
    source_class:"vendor_reported",results_url:"https://vendor.example/benchmark/results",
    record_count:0,notes:"Existing registered benchmark source"
  };
  const biRecord = {
    id:"vendor-model-a-001",source_id:"vendor-benchmark",source_class:"vendor_reported",
    evidence_level:"vendor_reported",benchmark_suite:"Vendor Inference Benchmark",
    benchmark_version:"2026.1",publication_date:"2026-11-18",submitter:"Vendor",
    accelerator_vendor:"Vendor",platform_id:null,product_id:null,system_type:"datacenter",
    system_name:"Eight accelerator server",division:"closed",availability:"available",
    model:"Model A",scenario:"offline",result_value:1250,result_unit:"tokens/s",
    accuracy_text:"Not reported",inferred:false,power_metrics_available:false,
    design_power_watts:null,system:{nodes:1,accelerator_model:"Vendor X",accelerators_per_node:8},
    software:{framework:"Framework X"},notes:"Reviewed vendor result.",compliance:"Not independently assessed",
    errors:0,weight_data_types:"BF16",source_record_key:"vendor-row-001",
    source_location:"results table row 1",source_url:biSource.results_url,dataset_url:null,release_url:null
  };
  const biApproval = {
    schema_version:"1.0",approval_id:"review-benchmark-001",reviewer:"reviewer@example.org",
    reviewed_at:"2026-11-20",decision:"approved_new_benchmark_result",source_id:"vendor-benchmark",
    record:biRecord,review_notes:"Inspected the original results page and confirmed workload and system context."
  };
  const biDb = {
    schema_version:"1.0",database_version:"test",last_imported_at:"2026-11-01",
    scope:"Synthetic browser test fixture",sources:[biSource],
    summary:{total_records:0,by_source:{},by_availability:{},by_division:{},by_system_type:{},
      inferred_records:0,power_records:0,submitters:0,models:0},records:[]
  };
  const biRegistryText=JSON.stringify(biDb,null,2)+"\n";
  const biBaseHash=piHash(biRegistryText);
  const biUpdated=JSON.parse(JSON.stringify(biDb));
  biUpdated.records.push(biRecord);biUpdated.sources[0].record_count=1;
  biUpdated.last_imported_at=biApproval.reviewed_at;
  biUpdated.database_version="test+reviewed-"+biApproval.approval_id;
  biUpdated.summary={
    total_records:1,by_source:{"vendor-benchmark":1},by_availability:{available:1},
    by_division:{closed:1},by_system_type:{datacenter:1},inferred_records:0,
    power_records:0,submitters:1,models:1
  };
  const biProposedHash=piHash(piCanonical(biUpdated));
  const biOperations=[
    {op:"add",path:"/records/-",value:biRecord},
    {op:"replace",path:"/sources/0/record_count",value:1},
    {op:"replace",path:"/last_imported_at",value:biApproval.reviewed_at},
    {op:"replace",path:"/database_version",value:biUpdated.database_version},
    {op:"replace",path:"/summary",value:biUpdated.summary}
  ];
  const biBody={
    schema_version:"1.0",proposal_id:biApproval.approval_id,proposal_type:"benchmark_result_creation",
    created_at:"2026-11-21T12:00:00Z",
    target_registry:{path:"data/benchmark-results.json",schema_version:"1.0",base_sha256:biBaseHash},
    source_snapshot:biSource,approval:biApproval,
    target:{source_id:biSource.id,record_id:biRecord.id,source_record_key:biRecord.source_record_key},
    operations:biOperations,
    audit:{verification_status:"exact_one_result_append",unapproved_changes:0,
      source_truth_verified:false,evidence_level_promoted:false,source_id:biSource.id,
      source_class:biSource.source_class,reviewer:biApproval.reviewer,reviewed_at:biApproval.reviewed_at,
      base_registry_sha256:biBaseHash,proposed_registry_sha256:biProposedHash},
    proposed_registry_sha256:biProposedHash,
    policy:{human_approval_required:true,source_truth_verified:false,evidence_level_promoted:false,
      automatic_merge:false,power_claims_supported:false,allowed_changes:[
        "append one result for an existing registered source",
        "reconcile source record_count, database_version, last_imported_at and summary"]}
  };
  const biPackage={...biBody,package_sha256:piHash(piCanonical(biBody))};
  await page.locator("[data-bi-package]").setInputFiles(piArtifact("benchmark-proposal.json",biPackage));
  await page.locator("[data-bi-approval]").setInputFiles(piArtifact("benchmark-approval.json",biApproval));
  await page.locator("[data-bi-registry]").setInputFiles({
    name:"benchmark-results.json",mimeType:"application/json",buffer:Buffer.from(biRegistryText)
  });
  await page.waitForFunction(() => {
    const message=document.querySelector("[data-bi-status]")?.textContent || "";
    return message.includes("Verified locally") || message.includes("validation failed");
  });
  const biStatus=(await page.locator("[data-bi-status]").textContent()).trim();
  if (!biStatus.includes("Verified locally")) throw new Error("Benchmark Integration Workbench fixture rejected: "+biStatus);
  if (!(await page.locator("[data-bi-results]").first().isVisible())) {
    throw new Error("Benchmark Integration Workbench failed to verify a valid one-result append fixture");
  }
  const biTampered={...biPackage,operations:[{...biOperations[0],path:"/records/0"},...biOperations.slice(1)]};
  await page.locator("[data-bi-package]").setInputFiles(piArtifact("tampered-benchmark-proposal.json",biTampered));
  await page.waitForFunction(() => (document.querySelector("[data-bi-status]")?.textContent || "").includes("SHA256 mismatch"));
  if (!(await page.locator("[data-bi-results]").first().isHidden())) {
    throw new Error("Benchmark Integration Workbench exposed a tampered proposal");
  }

  // PR #139: local-only provenance-bound Database Integration Workbench.
  await page.goto(base + "/database-integration/", {waitUntil:"networkidle"});
  for (const selector of ["[data-di-package]","[data-di-claims]","[data-di-registry]","[data-di-status]"]) {
    await page.locator(selector).waitFor();
  }
  if (!(await page.locator("[data-di-results]").first().isHidden())) {
    throw new Error("Database Integration Workbench must hide unverified results before loading a package");
  }

  const diArtifact = (name,data) => ({name,mimeType:"application/json",buffer:Buffer.from(JSON.stringify(data))});
  const diCrypto = require("crypto");
  const diCanonical = value => Array.isArray(value) ? "[" + value.map(diCanonical).join(",") + "]" :
    value && typeof value === "object" ? "{" + Object.keys(value).sort().map(k =>
      JSON.stringify(k) + ":" + diCanonical(value[k])).join(",") + "}" :
    typeof value === "number" && Object.is(value,-0) ? "0" : JSON.stringify(value);
  const diHash = value => diCrypto.createHash("sha256").update(value).digest("hex");
  const diDb = {schema_version:"1.3",companies:[{
    id:"nvidia",display_name:"NVIDIA",
    evidence:[],
    claims:[{id:"b200-hbm",statement:"Vendor lists 180 GB HBM.",claim_status:"vendor_reported",
      subject_type:"product",subject_id:"b200-sxm",evidence_ids:["older"]}]
  }]};
  const diSource = {claim_id:"claim-test-b200",review_status:"unverified_candidate",
    statement:"NVIDIA describes B200 HBM capacity in updated documentation.",
    evidence_quote:"The system has 180 GB HBM.",
    source:{url:"https://vendor.example/new",publisher:"Vendor"}};
  const diReport = {schema_version:"1.0",claim_count:1,claims:[diSource]};
  const diApproval = {schema_version:"1.0",approval_id:"review-b200-hbm",
    reviewer:"maintainer@example.org",reviewed_at:"2026-11-20",
    decision:"approved_evidence_attachment",company_id:"nvidia",existing_claim_id:"b200-hbm",
    expected_claim_sha256:"a".repeat(64),extracted_claim_id:"claim-test-b200",
    evidence:{id:"new-evidence",title:"Updated vendor specification",url:"https://vendor.example/new",
      publisher:"Vendor",source_type:"vendor_primary",independence:"vendor",
      published_at:"2026-11-18",checked_at:"2026-11-20",review_status:"reviewed",
      notes:"Manually inspected the original vendor specification page."},
    review_notes:"Maintainer checked the original source, exact product configuration and selected database Claim."};
  const diRegistryText=JSON.stringify(diDb);
  const diBaseHash=diHash(diRegistryText);
  const diUpdated=JSON.parse(JSON.stringify(diDb));
  diUpdated.companies[0].evidence.push(diApproval.evidence);
  diUpdated.companies[0].claims[0].evidence_ids.push("new-evidence");
  const diProposedHash=diHash(diCanonical(diUpdated));
  const diOperations=[
    {op:"add",path:"/companies/0/evidence/-",value:diApproval.evidence},
    {op:"add",path:"/companies/0/claims/0/evidence_ids/-",value:"new-evidence"}
  ];
  const diBody={schema_version:"1.0",proposal_id:"review-b200-hbm",
    proposal_type:"company_profile_evidence_attachment",created_at:"2026-11-23T04:00:00Z",
    target_registry:{path:"data/company-profiles.json",schema_version:"1.3",base_sha256:diBaseHash},
    source_claim:diSource,approval:diApproval,
    target:{company_id:"nvidia",company_display_name:"NVIDIA",company_index:0,
      claim_id:"b200-hbm",claim_statement:"Vendor lists 180 GB HBM.",claim_index:0,
      subject_type:"product",subject_id:"b200-sxm",original_claim_sha256:"a".repeat(64),
      evidence_ids_before:["older"],evidence_ids_after:["older","new-evidence"]},
    operations:diOperations,
    audit:{verification_status:"exact_append_only_change",unapproved_changes:0,
      source_truth_verified:false,claim_status_changed:false,approval_id:"review-b200-hbm",
      source_claim_id:"claim-test-b200",source_url:"https://vendor.example/new",
      evidence_quote_sha256:diHash(diSource.evidence_quote),
      original_claim_sha256:"a".repeat(64),base_registry_sha256:diBaseHash,
      proposed_registry_sha256:diProposedHash},
    proposed_registry_sha256:diProposedHash,
    policy:{human_approval_required:true,source_truth_verified:false,claim_status_changed:false,
      claim_value_or_scope_changed:false,product_identity_changed:false,automatic_merge:false,
      allowed_changes:["append one reviewed evidence object","append its ID to the existing Claim"]}};
  const diPackage={...diBody,package_sha256:diHash(diCanonical(diBody))};
  await page.locator("[data-di-package]").setInputFiles(diArtifact("proposal.json",diPackage));
  await page.locator("[data-di-claims]").setInputFiles(diArtifact("claims.json",diReport));
  await page.locator("[data-di-registry]").setInputFiles({
    name:"company-profiles.json",mimeType:"application/json",buffer:Buffer.from(diRegistryText)
  });
  await page.waitForFunction(() => (document.querySelector("[data-di-status]")?.textContent || "").includes("Verified locally"));
  if (!(await page.locator("[data-di-results]").first().isVisible()) ||
      (await page.locator("[data-di-change-count]").textContent()).trim() !== "2") {
    throw new Error("Database Integration Workbench failed to verify the append-only package fixture");
  }
  const tamperedDiPackage={...diPackage,proposal_id:"tampered"};
  await page.locator("[data-di-package]").setInputFiles(diArtifact("tampered-proposal.json",tamperedDiPackage));
  await page.waitForFunction(() => (document.querySelector("[data-di-status]")?.textContent || "").includes("SHA256 mismatch"));
  if (!(await page.locator("[data-di-results]").first().isHidden())) {
    throw new Error("Database Integration Workbench exposed a tampered proposal");
  }

  // PR #101: local-only multi-run Intelligence Operations dashboard.
  await page.goto(base + "/intelligence-operations/", {waitUntil:"networkidle"});
  const opsSource = (id,status) => ({
    source_id:id,name:id,kind:"rss_atom",status,recent_item_count:status==="observed"?3:0
  });
  const opsRun = (generated_at, unresolved, health, restored) => ({
    schema_version:"1.0",generated_at,operational_only:true,health,
    cache:{checkpoint_audit_passed:true,
      discovery_restored_file_present:restored,review_restored_file_present:restored},
    summary:{sources_total:2,sources_observed:health==="healthy"?2:1,
      sources_unavailable:health==="healthy"?0:1,
      availability_percent:health==="healthy"?100:50,
      review_leads:5,extracted_claims:3,persistent_backlog:unresolved+1,
      unresolved_backlog:unresolved,oldest_unresolved_days:21},
    sources:[opsSource("vendor-feed","observed"),
      opsSource("arxiv",health==="healthy"?"observed":"unavailable")],
    warnings:health==="degraded"?["arxiv feed unavailable"]:[]
  });
  const earlyOps=opsRun("2026-11-02T10:00:00Z",7,"degraded",false);
  const lateOps=opsRun("2026-11-09T10:00:00Z",9,"healthy",true);
  lateOps.schema_version="1.1";
  lateOps.sources[0].request_diagnostics={
    request_count:3,failed_request_count:1,response_bytes:2048,
    total_elapsed_ms:9000,average_request_ms:3000,max_request_ms:5000,
    last_http_error_status:503,last_request_failure_category:"http_server_error"
  };
  lateOps.sources[1].request_diagnostics={
    request_count:2,failed_request_count:0,response_bytes:1024,
    total_elapsed_ms:1000,average_request_ms:500,max_request_ms:600,
    last_http_error_status:null,last_request_failure_category:null
  };
  Object.assign(lateOps.summary,{
    request_telemetry_sources:2,total_requests:5,failed_requests:1,
    response_bytes:3072,sources_with_slow_request_over_5s:1
  });
  const opsFile=(name,data)=>({name,mimeType:"application/json",buffer:Buffer.from(JSON.stringify(data))});
  await page.locator("[data-ops-files]").setInputFiles([
    opsFile("late.json",lateOps),opsFile("early.json",earlyOps)
  ]);
  await page.waitForFunction(()=>document.querySelector("[data-ops-stat='runs']")?.textContent==="2");
  if(await page.locator("[data-ops-stat='backlog']").textContent()!=="9" ||
     await page.locator("[data-ops-stat='availability']").textContent()!=="100%"){
    throw Error("Intelligence Operations did not summarize latest completed run");
  }
  const latestHistoryRow=await page.locator("[data-ops-history] tr").last().textContent();
  if(!latestHistoryRow.includes("5") || !latestHistoryRow.includes("1")) {
    throw Error("Intelligence Operations did not expose request totals in run history");
  }
  const firstRow=await page.locator("[data-ops-history] tr").first().textContent();
  if(!firstRow.includes("2026-11-02") || !firstRow.includes("degraded")){
    throw Error("Intelligence Operations did not sort timestamps chronologically");
  }
  await page.locator("[data-ops-select]").selectOption("2026-11-02T10:00:00Z");
  if(!(await page.locator("[data-ops-cache]").textContent()).includes("no restored file") ||
     !(await page.locator("[data-ops-warnings]").textContent()).includes("arxiv feed unavailable")){
    throw Error("Source-level outage or cache restore diagnostics missing");
  }
  if(!(await page.locator("[data-ops-cache]").textContent()).includes("Request telemetry unavailable") ||
     await page.locator("[data-ops-sources] tr").first().locator("td").nth(4).textContent()!=="—") {
    throw Error("Legacy Operations snapshots must show missing request telemetry as unavailable");
  }
  await page.locator("[data-ops-select]").selectOption("2026-11-09T10:00:00Z");
  const vendorRequestRow=page.locator("[data-ops-sources] tr").filter({hasText:"vendor-feed"});
  const vendorRequestCells=await vendorRequestRow.locator("td").allTextContents();
  if(vendorRequestCells[4]!=="3" || vendorRequestCells[5]!=="1" ||
     vendorRequestCells[6]!=="3,000" || vendorRequestCells[7]!=="5,000" ||
     vendorRequestCells[8]!=="2,048 B") {
    throw Error("Per-source request latency and payload metrics were not rendered: "+vendorRequestCells.join("|"));
  }
  const inconsistentOps={...lateOps,summary:{...lateOps.summary,failed_requests:99}};
  await page.locator("[data-ops-files]").setInputFiles(opsFile("inconsistent-telemetry.json",inconsistentOps));
  await page.waitForFunction(()=>document.querySelector("[data-ops-status]")?.textContent?.includes("Cannot load snapshots"));
  if(!(await page.locator("[data-ops-history-panel]").isHidden())) {
    throw Error("Inconsistent request telemetry totals were accepted");
  }
  const forgedOps={...earlyOps,operational_only:false};
  await page.locator("[data-ops-files]").setInputFiles(opsFile("forged.json",forgedOps));
  await page.waitForFunction(()=>document.querySelector("[data-ops-status]")?.textContent?.includes("Cannot load snapshots"));
  if(!(await page.locator("[data-ops-history-panel]").isHidden())){
    throw Error("Forged operation status was accepted as successful telemetry");
  }
  await page.locator("[data-ops-clear]").click();
  if(await page.locator("[data-ops-stat='runs']").textContent()!=="—"){
    throw Error("Intelligence Operations reset failed");
  }

  // Evidence-quality dashboard: current-run hygiene is not human factual verification.
  await page.goto(base + "/evidence-quality/", {waitUntil:"networkidle"});
  const eqSnapshot=(stamp,claims,passed)=>({
    schema_version:"1.0",generated_at:stamp,semantic_batch_id:"claim-review-"+stamp.slice(0,10),
    lineage_generated_at:stamp,lineage_cluster_ids:["lineage-"+stamp.slice(0,10)],
    read_only:true,factual_verification_performed:false,
    metrics:{
      current_claims:claims,
      quote_traceability:{passed,total:claims,rate:Math.round(passed/claims*10000)/10000},
      provenance_completeness:{passed:claims,total:claims,rate:1},
      source_metadata_mismatches:0,
      distinct_source_documents:2,distinct_publishers:2,
      review_backlog:14,unresolved_claims:12,pending_claims:9,needs_more_evidence:3,
      accepted_for_evidence_attachment:1,rejected_claims:1,
      payload_coverage:{passed:12,total:14,rate:Math.round(12/14*10000)/10000},
      multi_document_exact_duplicate_clusters:2,lineage_clusters_queued:1,
      semantic_claims_queued:2,
      semantic_double_review_rate:null,semantic_reviewer_agreement:null,
      lineage_human_review_coverage:null,independently_verified_claims:null
    },
    availability:{semantic_evaluation:"not_provided",lineage_evaluation:"not_provided",
      independent_verification:"not_measured"}
  });
  const eqOld=eqSnapshot("2026-11-02T00:00:00Z",4,2);
  const eqNew=eqSnapshot("2026-11-09T00:00:00Z",4,3);
  const eqFile=(name,data)=>({name,mimeType:"application/json",buffer:Buffer.from(JSON.stringify(data))});
  await page.locator("[data-eq-files]").setInputFiles([eqFile("eq-new.json",eqNew),eqFile("eq-old.json",eqOld)]);
  await page.waitForFunction(()=>document.querySelector("[data-eq-stat='runs']")?.textContent==="2");
  if(await page.locator("[data-eq-stat='quotes']").textContent()!=="75.0%" ||
     await page.locator("[data-eq-stat='unresolved']").textContent()!=="12"){
    throw Error("Evidence Quality Dashboard did not render latest run metrics");
  }
  if(await page.locator("[data-eq-history] tr").count()!==2 ||
     !(await page.locator("[data-eq-history] tr").first().textContent()).includes("2026-11-02") ||
     !(await page.locator("[data-eq-history] tr").last().textContent()).includes("N/A")){
    throw Error("Evidence Quality Dashboard trend ordering or unavailable review status invalid");
  }
  // Load a *reviewer-reported*, batch-matched evaluation. Never present it
  // as independently authenticated or as factual accuracy.
  const eqEvaluation={
    schema_version:"1.0",batch_id:eqNew.semantic_batch_id,status:"pending",
    total_claims:2,double_reviewed_claims:1,
    pending_claim_ids:["claim-b"],agreements:[{claim_id:"claim-a",label:"supported_by_source"}],
    disagreements:[],raw_agreement:1,reviewer_label_counts:{supported_by_source:2},
    human_adjudication_needed:0,automatically_verified_claims:0
  };
  await page.locator("[data-eq-semantic-eval]").setInputFiles(eqFile("semantic-evaluation.json",eqEvaluation));
  await page.waitForFunction(()=>document.querySelector("[data-eq-eval-status]")?.textContent?.includes("Reviewer-reported evaluation loaded"));
  if(!(await page.locator("[data-eq-history] tr").last().textContent()).includes("100.0% (n=1, reviewer-reported)") ||
     !(await page.locator("[data-eq-details]").textContent()).includes("double-reviewed Claims: 1/2") ||
     !(await page.locator("[data-eq-eval-status]").textContent()).includes("Not authenticated")){
    throw Error("Human semantic review overlay must show paired coverage and its provenance warning");
  }
  const eqBadEvaluation={...eqEvaluation,raw_agreement:0};
  await page.locator("[data-eq-semantic-eval]").setInputFiles(eqFile("invalid-agreement.json",eqBadEvaluation));
  await page.waitForFunction(()=>document.querySelector("[data-eq-eval-status]")?.textContent?.includes("Cannot load semantic evaluation"));
  if(!(await page.locator("[data-eq-history] tr").last().textContent()).includes("N/A")){
    throw Error("Invalid semantic evaluation should clear reviewer-reported statistics");
  }
  const eqWrongBatch={...eqEvaluation,batch_id:"claim-review-other"};
  await page.locator("[data-eq-semantic-eval]").setInputFiles(eqFile("wrong-batch.json",eqWrongBatch));
  await page.waitForFunction(()=>document.querySelector("[data-eq-eval-status]")?.textContent?.includes("Cannot load semantic evaluation"));
  if(!(await page.locator("[data-eq-eval-status]").textContent()).includes("does not match")){
    throw Error("Semantic evaluation from another batch must be refused");
  }
  const lineageReport={
    schema_version:"1.0",review_type:"source_lineage",
    generated_at:eqNew.lineage_generated_at,status:"complete",
    cluster_count:1,fully_reviewed_clusters:1,pending_cluster_ids:[],
    same_reviewer_assigned_origin_clusters:1,
    different_reviewer_assigned_origin_clusters:0,
    relationship_label_counts:{original_material:1,syndicated_reprint:1},
    completed_clusters:[{cluster_id:eqNew.lineage_cluster_ids[0],
      distinct_reviewer_assigned_origin_keys:1}],
    automatically_verified_independent_evidence:0
  };
  await page.locator("[data-eq-lineage-eval]").setInputFiles(eqFile("lineage-report.json",lineageReport));
  await page.waitForFunction(()=>document.querySelector("[data-eq-lineage-status]")?.textContent?.includes("source-lineage review loaded"));
  if(!(await page.locator("[data-eq-history] tr").last().textContent()).includes("1/1 (reviewer-reported)") ||
     !(await page.locator("[data-eq-details]").textContent()).includes("same reviewer-assigned origin: 1")){
    throw Error("Valid reviewer-reported source lineage must display on its matching run");
  }
  const incorrectLineage={...lineageReport,
    same_reviewer_assigned_origin_clusters:0,
    different_reviewer_assigned_origin_clusters:1};
  await page.locator("[data-eq-lineage-eval]").setInputFiles(eqFile("lineage-invalid.json",incorrectLineage));
  await page.waitForFunction(()=>document.querySelector("[data-eq-lineage-status]")?.textContent?.includes("Cannot load lineage evaluation"));
  if(!(await page.locator("[data-eq-history] tr").last().textContent()).includes("N/A")){
    throw Error("Invalid source-lineage review must remove reviewer-reported overlay");
  }
  const wrongLineage={...lineageReport,generated_at:"2026-10-01T00:00:00Z"};
  await page.locator("[data-eq-lineage-eval]").setInputFiles(eqFile("lineage-wrong-run.json",wrongLineage));
  await page.waitForFunction(()=>document.querySelector("[data-eq-lineage-status]")?.textContent?.includes("Cannot load lineage evaluation"));
  if(!(await page.locator("[data-eq-lineage-status]").textContent()).includes("does not match")){
    throw Error("Lineage evaluation from a different run must be rejected");
  }
  const eqForged=eqSnapshot("2026-11-10T00:00:00Z",4,4);
  eqForged.metrics.semantic_reviewer_agreement=1;
  await page.locator("[data-eq-files]").setInputFiles(eqFile("eq-forged.json",eqForged));
  await page.waitForFunction(()=>document.querySelector("[data-eq-status]")?.textContent?.includes("Cannot load"));
  if(!(await page.locator("[data-eq-status]").textContent()).includes("Human validation status cannot be inferred") ||
     !(await page.locator("[data-eq-history-panel]").isHidden()) ||
     !(await page.locator("[data-eq-detail-panel]").isHidden()) ||
     await page.locator("[data-eq-history] tr").count()!==0 ||
     await page.locator("[data-eq-stat='runs']").textContent()!=="—"){
    throw Error("Evidence Quality Dashboard failed to reject and clear fabricated human agreement");
  }
  await page.locator("[data-eq-clear]").click();
  if(await page.locator("[data-eq-stat='runs']").textContent()!=="—"){
    throw Error("Evidence Quality Dashboard clear did not reset state");
  }

  // Evidence-to-database conversion funnel: local snapshots, explicit denominators.
  await page.goto(base + "/intelligence-funnel/", {waitUntil:"networkidle"});
  const cfSnapshot=(stamp,overrides={})=>{
    const m={
      discovery_candidates:5,candidates_with_claims:3,claims_extracted:4,
      triage_groups:3,duplicate_claims_collapsed:1,persistent_review_backlog:5,
      human_decisions_recorded:3,
      review_states:{pending:2,needs_more_evidence:1,rejected:1,accepted_for_evidence_attachment:1},
      decision_coverage:{numerator:3,denominator:5,rate:0.6},
      accepted_for_evidence_attachment:1,
      acceptance_rate_among_decisions:{numerator:1,denominator:3,rate:0.3333},
      eligible_claims_not_integrated:1,integrated_claims:0,integration_receipts:0,
      integration_coverage:{numerator:0,denominator:1,rate:0}
    };
    return {
      schema_version:"1.0",generated_at:stamp,
      source_timestamps:{discovery:stamp,claims:stamp,triage:stamp,review_state:stamp},
      metrics:{...m,...overrides},
      stages:[],integration_receipts:[],
      policy:{read_only:true,formal_factual_verification_performed:false,
        automatic_registry_writes:false,accepted_for_evidence_attachment_is_final_approval:false,
        interpretation:"Stage counts have explicitly named denominators."}
    };
  };
  const cfOld=cfSnapshot("2026-11-17T00:00:00Z");
  const cfNew=cfSnapshot("2026-11-24T00:00:00Z",{discovery_candidates:8,claims_extracted:6});
  await page.locator("[data-cf-files]").setInputFiles([
    eqFile("funnel-new.json",cfNew),eqFile("funnel-old.json",cfOld)
  ]);
  await page.waitForFunction(()=>document.querySelector("[data-cf-stat='claims']")?.textContent==="6");
  if(await page.locator("[data-cf-stat='candidates']").textContent()!=="8" ||
     await page.locator("[data-cf-stat='decisions']").textContent()!=="3" ||
     await page.locator("[data-cf-stat='integrated']").textContent()!=="0" ||
     await page.locator("[data-cf-history] tr").count()!==2 ||
     !(await page.locator("[data-cf-history] tr").last().textContent()).includes("0.0%")){
    throw Error("Conversion Funnel dashboard failed to render ordered snapshots and explicit integration coverage");
  }
  const cfForged=cfSnapshot("2026-11-25T00:00:00Z",{
    integration_coverage:{numerator:1,denominator:1,rate:1}
  });
  await page.locator("[data-cf-files]").setInputFiles(eqFile("funnel-forged.json",cfForged));
  await page.waitForFunction(()=>document.querySelector("[data-cf-status]")?.textContent?.includes("Cannot load"));
  if(!(await page.locator("[data-cf-history-panel]").isHidden()) ||
     await page.locator("[data-cf-stat='claims']").textContent()!=="—"){
    throw Error("Conversion Funnel accepted inconsistent integration metrics or retained stale data");
  }
  await page.locator("[data-cf-clear]").click();
  if(await page.locator("[data-cf-stat='candidates']").textContent()!=="—"){
    throw Error("Conversion Funnel clear did not reset metrics");
  }

  homeDataRequests.length = 0;
  await page.goto(base + "/", { waitUntil: "networkidle" });
  const landscape = page.locator(".hero-visual-frame img");
  await landscape.waitFor();
  await page.waitForFunction(() => {
    const image = document.querySelector(".hero-visual-frame img");
    return image && image.complete && image.naturalWidth > 0 && image.naturalHeight > 0;
  }, { timeout: 10000 });
  const landscapeInfo = await landscape.evaluate(image => ({
    src: image.currentSrc,
    width: image.naturalWidth,
    height: image.naturalHeight
  }));
  if (!landscapeInfo.src.includes("AI_Chip_Landscape_v0p9p1.svg") ||
      landscapeInfo.width < 1800 || landscapeInfo.height < 1200) {
    throw new Error("Landscape image did not load the expected high-resolution v0.9.1 asset: " +
      JSON.stringify(landscapeInfo));
  }

  await page.waitForFunction(() => {
    const stats = document.querySelector("[data-home-stats]");
    return stats && stats.dataset.statsLoaded === "true";
  }, null, { timeout: 15000 });
  const initialHomeDataRequests = homeDataRequests.length;
  const homeStatValues = await page.locator("[data-home-stat]").evaluateAll(nodes =>
    nodes.map(node => node.textContent.trim())
  );
  if (initialHomeDataRequests !== 3 || homeStatValues.length !== 4 ||
      !homeStatValues.every(value => /^\d+$/.test(value))) {
    throw new Error("Homepage coverage metrics did not load all four datasets: " +
      JSON.stringify({ initialHomeDataRequests, homeStatValues }));
  }
  await page.locator("[data-theme-toggle]").click();
  await page.locator("[data-theme-toggle]").click();
  await page.waitForLoadState("networkidle");
  if (homeDataRequests.length !== initialHomeDataRequests) {
    throw new Error("Theme changes unexpectedly reloaded homepage coverage datasets");
  }

  await page.goto(base + "/directory/", { waitUntil: "networkidle" });
  await page.waitForFunction(() => {
    const count = document.querySelector("[data-directory-count]");
    const root = document.querySelector("[data-directory-explorer]");
    return count && count.dataset.ready === "true" &&
      root && root.dataset.profileRegistryLoaded === "true" &&
      root.dataset.profileMatchedCount === "53";
  }, null, { timeout: 10000 });
  const companyCount = Number(await page.locator("[data-directory-count]").getAttribute("data-count"));
  if (companyCount !== 53) throw new Error("Directory company index count changed unexpectedly: " + companyCount);
  const registrySummary = (await page.locator("[data-directory-review-summary]").textContent()).trim();
  if (!registrySummary.includes("53 profiles") ||
      !registrySummary.includes("159 source links") ||
      !registrySummary.includes("58 audited evidence records") ||
      !registrySummary.includes("165 structured claims") ||
      !registrySummary.includes("30 profiles not yet reviewed")) {
    throw new Error("Company profile registry summary is inconsistent: " + registrySummary);
  }
  const profileRegistry = await page.evaluate(async () => {
    const root = document.querySelector("[data-directory-explorer]");
    const response = await fetch(root.dataset.profileSource);
    if (!response.ok) throw new Error("Company profile registry request failed");
    return response.json();
  });
  const productCount = profileRegistry.companies.reduce((sum, company) => sum + company.products.length, 0);
  const claimCount = profileRegistry.companies.reduce((sum, company) => sum + company.claims.length, 0);
  const evidenceCount = profileRegistry.companies.reduce((sum, company) => sum + company.evidence.length, 0);
  const metricContextCount = profileRegistry.companies.reduce((sum, company) =>
    sum + company.claims.filter(claim => claim.metric_context).length, 0);
  const lifecycleProducts = profileRegistry.companies.flatMap(company =>
    company.products.map(product => ({ company, product }))).filter(item =>
      Array.isArray(item.product.availability_history) && item.product.availability_history.length);
  const invalidLifecycleEvents = lifecycleProducts.flatMap(({ company, product }) =>
    product.availability_history.filter((event, index, events) =>
      !company.evidence.some(record => record.id === event.evidence_id) ||
      (index === events.length - 1 && event.status !== product.availability)));
  const tenstorrentProfile = profileRegistry.companies.find(company => company.id === "tenstorrent");
  const corporateProfiles = Object.fromEntries(profileRegistry.companies.filter(company => company.corporate_status).map(company => [company.id, company.corporate_status]));
  const rebellionsProfile = profileRegistry.companies.find(company => company.id === "rebellions");
  const nvidiaProfile = profileRegistry.companies.find(company => company.id === "nvidia");
  const gb200 = nvidiaProfile.products.find(product => product.id === "gb200-nvl72");
  const gb200Bandwidth = nvidiaProfile.claims.find(claim => claim.id === "gb200-hbm-bandwidth");
  const awsProfile = profileRegistry.companies.find(company => company.id === "amazon-aws");
  const trainium2Dense = awsProfile.claims.find(claim => claim.id === "trainium2-fp8-dense");
  const trainium2Sparse = awsProfile.claims.find(claim => claim.id === "trainium2-fp8-sparse");
  if (profileRegistry.schema_version !== "1.3" || profileRegistry.companies.length !== 53 || productCount !== 40 ||
      claimCount !== 165 || evidenceCount !== 58 || metricContextCount < 40 ||
      !profileRegistry.comparison_policy.precision_must_match ||
      !profileRegistry.comparison_policy.sparsity_must_match ||
      !profileRegistry.comparison_policy.measurement_scope_must_match ||
      lifecycleProducts.length < 10 || invalidLifecycleEvents.length ||
      !tenstorrentProfile.products.some(product => product.id === "tenstorrent-blackhole-p150b") ||
      !rebellionsProfile.products.some(product => product.id === "rebellions-rebel-quad") ||
      !profileRegistry.companies.find(company => company.id === "cambricon").products.some(product => product.id === "mlu370-s4-s8") ||
      corporateProfiles.graphcore?.ownership_status !== "wholly_owned_subsidiary" ||
      corporateProfiles.kinara?.parent_company !== "NXP Semiconductors" ||
      corporateProfiles.ampere?.parent_company !== "SoftBank Group" ||
      corporateProfiles["untether-ai"]?.operating_status !== "ceased" ||
      corporateProfiles.groq?.ownership_status !== "independent" ||
      gb200.product_type !== "system" ||
      gb200Bandwidth.metric_context.measurement_scope !== "rack" ||
      trainium2Dense.metric_context.sparsity !== "dense" ||
      trainium2Sparse.metric_context.sparsity !== "structured_sparse") {
    throw new Error("Product registry v1.1 comparison metadata is inconsistent");
  }
  await page.locator("[data-directory-search]").fill("MI355X");
  const mi355Matches = await page.locator(".directory-result-title").allTextContents();
  if (mi355Matches.length !== 1 || !mi355Matches[0].includes("AMD")) {
    throw new Error("Structured company search did not locate AMD MI355X");
  }
  const mi355Product = (await page.locator(".directory-result-products").first().textContent()).trim();
  if (!mi355Product.includes("AMD Instinct MI355X")) {
    throw new Error("Directory result did not display the structured MI355X product: " + mi355Product);
  }
  const mi355Evidence = (await page.locator(".directory-result-evidence").first().textContent()).trim();
  if (!mi355Evidence.includes("Fresh evidence") ||
      !mi355Evidence.includes("4 evidence records") ||
      !mi355Evidence.includes("17 reviewed claims")) {
    throw new Error("AMD MI355X evidence card is inconsistent: " + mi355Evidence);
  }
  await page.locator("[data-directory-search]").fill("Graphcore");
  const graphcoreCard = page.locator(".directory-result-card").first();
  if (!(await graphcoreCard.textContent()).includes("Wholly owned subsidiary") ||
      !(await graphcoreCard.textContent()).includes("SoftBank Group")) {
    throw new Error("Graphcore ownership status missing from directory search");
  }
  await page.locator("[data-directory-search]").fill("Groq");
  const groqCard = page.locator(".directory-result-card").filter({ hasText: "Groq — LPU" });
  if (await groqCard.count() !== 1 || !(await groqCard.textContent()).includes("Independent")) {
    throw new Error("Groq must remain classified as independent after its NVIDIA licensing agreement");
  }
  await page.locator("[data-directory-search]").fill("");
  await page.locator("[data-directory-evidence-filter]").selectOption("fresh");
  if (await page.locator(".directory-result-title").count() !== 23) {
    throw new Error("Freshness filter should return all 23 recently reviewed company profiles");
  }
  await page.locator("[data-directory-search]").fill("Qualcomm");
  await page.locator("[data-directory-evidence-filter]").selectOption("not_reviewed");
  await page.locator("[data-directory-search]").fill("Qualcomm");
  const companyMatches = await page.locator(".directory-result-title").allTextContents();
  if (!companyMatches.some(name => name.includes("Qualcomm"))) {
    throw new Error("Directory search did not find Qualcomm");
  }
  const profileEvidence = (await page.locator(".directory-result-evidence").first().textContent()).trim();
  if (!profileEvidence.includes("Not reviewed") ||
      !profileEvidence.includes("2 source links") ||
      !profileEvidence.includes("0 evidence records") ||
      !profileEvidence.includes("0 reviewed claims")) {
    throw new Error("Company card did not show profile evidence state: " + profileEvidence);
  }
  await page.locator("[data-directory-evidence-filter]").selectOption("not_reviewed");
  if (await page.locator(".directory-result-title").count() !== 1) {
    throw new Error("Not-reviewed evidence filter did not retain the FuriosaAI profile");
  }
  await page.locator("[data-directory-evidence-filter]").selectOption("stale");
  if (!(await page.locator("[data-directory-empty]").isVisible())) {
    throw new Error("Stale evidence filter should not match unreviewed profiles");
  }
  await page.locator("[data-directory-reset]").click();
  await page.locator("[data-directory-group]").selectOption({ label: "China AI Accelerator Vendors" });
  const chinaMatches = await page.locator(".directory-result-title").allTextContents();
  if (!chinaMatches.some(name => name.includes("Huawei Ascend"))) {
    throw new Error("Directory group filter did not include Huawei Ascend");
  }
  await page.locator("[data-directory-reset]").click();

  await page.goto(base + "/products/", { waitUntil: "networkidle" });
  await page.waitForFunction(() => {
    const root = document.querySelector("[data-product-explorer]");
    const products = document.querySelector('[data-product-stat="products"]');
    return root && root.dataset.loaded === "true" && products && products.textContent.trim() === "40";
  }, null, { timeout: 15000 });
  const productStats = await page.locator(".product-stat strong").allTextContents();
  if (productStats.join(",") !== "53,40,165,58,29,28") {
    throw new Error("Product Explorer coverage stats are inconsistent: " + productStats.join(","));
  }
  await page.locator("[data-product-search]").fill("RNGD");
  const rngdCard = page.locator(".product-card").filter({ hasText: "FuriosaAI RNGD Tensor Contraction Processor" }).first();
  if (!(await rngdCard.locator(".product-lifecycle-note").textContent()).includes("2026-01")) {
    throw new Error("Product Explorer did not show source-precision lifecycle status on the RNGD card");
  }
  await rngdCard.locator("details.product-details summary").click();
  const rngdLifecycle = rngdCard.locator(".product-lifecycle-item");
  if (await rngdLifecycle.count() !== 1 ||
      !(await rngdLifecycle.first().textContent()).includes("production") ||
      !(await rngdLifecycle.first().locator("a").getAttribute("href")).includes("furiosa.ai")) {
    throw new Error("Product Explorer did not render the dated, source-linked RNGD lifecycle history");
  }
  await page.locator("[data-product-search]").fill("");
  await page.locator("[data-product-search]").fill("MI355X");
  const mi355Card = page.locator(".product-card").filter({ hasText: "AMD Instinct MI355X" }).first();
  await mi355Card.locator("details.product-details summary").click();
  if (!(await mi355Card.locator(".product-system-details").filter({ hasText: "Product-specific software integrations" }).textContent()).includes("SGLang")) {
    throw new Error("Product Explorer did not link SGLang's exact MI355X support to the product record");
  }
  if ((await mi355Card.locator(".product-system-details").filter({ hasText: "Platform-level software integrations" }).textContent()).includes("SGLang")) {
    throw new Error("Product Explorer incorrectly duplicated an exact product integration as platform-level support");
  }
  await page.locator("[data-product-search]").fill("");
  await page.locator("[data-product-search]").fill("Trainium2");
  if (await page.locator(".product-card-title").count() !== 1 ||
      !(await page.locator(".product-card-title").first().textContent()).includes("Trainium2")) {
    throw new Error("Product Explorer search did not isolate Trainium2");
  }
  const trainiumCardText = (await page.locator(".product-card").first().textContent()).toLowerCase();
  if (!trainiumCardText.includes("torchneuron") ||
      !trainiumCardText.includes("vllm neuron") ||
      !trainiumCardText.includes("llm serving") ||
      !trainiumCardText.includes("llm pretraining") ||
      !trainiumCardText.includes("integration only") ||
      !trainiumCardText.includes("no product-specific benchmark result")) {
    throw new Error("Product Explorer did not show platform software, workload and benchmark evidence boundaries");
  }
  await page.locator('[data-compare-product="trainium2"]').click();
  await page.locator("[data-product-search]").fill("Trainium3");
  if (await page.locator(".product-card-title").count() !== 1) {
    throw new Error("Product Explorer search did not isolate Trainium3");
  }
  await page.locator('[data-compare-product="trainium3"]').click();
  const compareTable = page.locator("[data-product-compare-table]");
  await compareTable.waitFor({ state: "visible" });
  if (await compareTable.locator("thead th").count() !== 3) {
    throw new Error("Product comparison should show a metric column and two selected products");
  }
  const comparisonText = (await compareTable.textContent()).toLowerCase();
  if (!comparisonText.includes("fp8") || !comparisonText.includes("dense") ||
      !comparisonText.includes("structured sparse") ||
      !comparisonText.includes("96 gib hbm") || !comparisonText.includes("144 gib hbm3e")) {
    throw new Error("Product comparison did not preserve dense/sparse precision and memory context");
  }

  await page.locator("[data-product-compare-clear]").click();
  if (await page.locator("[data-product-compare-table]").isVisible()) {
    throw new Error("Product comparison did not clear selected products");
  }
  await page.locator("[data-product-search]").fill("");
  const sixProductIds = ["rubin-gpu", "mi455x", "tpu7x-ironwood", "trainium3", "maia300", "mtia300"];
  for (const id of sixProductIds) {
    await page.locator('[data-compare-product="' + id + '"]').click();
  }
  if ((await page.locator("[data-product-compare-count]").textContent()).trim() !== "6 / 6 selected" ||
      await page.locator("[data-product-compare-table] thead th").count() !== 7) {
    throw new Error("Product comparison should support six products plus the metric column");
  }
  const seventhCompareButton = page.locator('[data-compare-product="intel-gpu-d270"]');
  if (!(await seventhCompareButton.isDisabled())) {
    throw new Error("Product comparison should disable unselected products after six selections");
  }
  if ((await page.locator("[data-product-compare-count]").textContent()).trim() !== "6 / 6 selected") {
    throw new Error("Product comparison should enforce a maximum of six selected products");
  }
  await page.locator("[data-product-compare-clear]").click();

  await page.goto(base + "/compatibility/", { waitUntil: "networkidle" });
  await waitForDataset({
    name: "Compatibility",
    loadSelector: "[data-load-state]",
    statSelector: '[data-stat="integrations"]',
    countSelector: "[data-result-count]"
  });
  const databaseVersion = (await page.locator("[data-database-version]").textContent()).trim();
  const lastReviewed = (await page.locator("[data-last-reviewed]").textContent()).trim();
  if (!databaseVersion || databaseVersion === "Loading…" || !lastReviewed || lastReviewed === "—") {
    throw new Error("Compatibility page metadata did not render");
  }
  await page.locator("[data-filter-search]").fill("vLLM");
  if (Number(await page.locator("[data-result-count]").textContent()) < 1) {
    throw new Error("Compatibility search did not return vLLM records");
  }
  await page.locator("[data-filter-reset]").click();
  await page.locator("[data-filter-search]").fill("SGLang AWS Trainium");
  if (Number(await page.locator("[data-result-count]").textContent()) !== 1 ||
      !(await page.locator("[data-result-cards]").textContent()).toLowerCase().includes("in progress")) {
    throw new Error("Compatibility Explorer did not distinguish SGLang Trainium as an in-progress integration");
  }
  await page.locator("[data-filter-reset]").click();

  await page.locator("[data-theme-toggle]").click();
  if (await page.locator("html").getAttribute("data-theme") !== "dark") {
    throw new Error("Dark theme toggle failed");
  }
  await page.locator("[data-theme-toggle]").click();

  await page.goto(base + "/benchmarks/", { waitUntil: "networkidle" });
  await waitForDataset({
    name: "Benchmark",
    loadSelector: "[data-benchmark-load]",
    statSelector: '[data-benchmark-stat="projects"]',
    countSelector: "[data-benchmark-count]"
  });
  const benchmarkVersion = (await page.locator("[data-benchmark-version]").textContent()).trim();
  const benchmarkReviewed = (await page.locator("[data-benchmark-reviewed]").textContent()).trim();
  if (!benchmarkVersion || benchmarkVersion === "Loading…" ||
      !benchmarkReviewed || benchmarkReviewed === "—") {
    throw new Error("Benchmark page metadata did not render");
  }
  await page.locator("[data-benchmark-search]").fill("InferenceX");
  if (Number(await page.locator("[data-benchmark-count]").textContent()) < 1) {
    throw new Error("Benchmark search did not return InferenceX");
  }
  await page.locator("[data-benchmark-reset]").click();

  await page.goto(base + "/results/", { waitUntil: "networkidle" });
  await page.waitForFunction(() => {
    const root = document.querySelector("[data-benchmark-results]");
    const load = document.querySelector("[data-results-load]");
    return (root && root.dataset.loaded === "true") || (load && load.classList.contains("is-error"));
  }, null, { timeout: 15000 });
  const resultsLoadError = await page.locator("[data-results-load]").textContent();
  if (await page.locator("[data-results-load]").isVisible()) {
    throw new Error("Benchmark Results Explorer failed to initialize: " + resultsLoadError);
  }
  const qualityPanel = page.locator("[data-results-quality]");
  const qualityText = await qualityPanel.locator("[data-results-quality-content]").textContent();
  if (!qualityText.includes("Source attribution") || !qualityText.includes("Hardware identity") ||
      !qualityText.includes("Software stack") || !qualityText.includes("Measurement validation")) {
    throw new Error("Benchmark quality dashboard is missing evidence coverage dimensions or measurement validation");
  }
  if (!(/^\d+%/.test((await qualityPanel.locator(".benchmark-quality-score strong").textContent()).trim()))) {
    throw new Error("Benchmark quality dashboard did not calculate a core provenance coverage percentage");
  }
  const resultTotal = (await page.locator('[data-results-stat="total"]').textContent()).trim();
  const registryTotal = await page.evaluate(async () => {
    const root = document.querySelector("[data-benchmark-results]");
    const response = await fetch(root.dataset.source);
    if (!response.ok) throw new Error("Benchmark registry request failed");
    const bytes = await response.arrayBuffer();
    const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream("gzip"));
    const data = await new Response(stream).json();
    return data.records.length;
  });
  if (resultTotal !== String(registryTotal)) {
    throw new Error("Benchmark Results Explorer summary does not match registry length");
  }
  if (Number(await page.locator("[data-results-count]").textContent()) !== registryTotal) {
    throw new Error("Benchmark Results Explorer should initially show all registry rows");
  }
  await page.locator("[data-results-sort]").selectOption("model");
  const sortedModels = await page.locator("[data-results-rows] .benchmark-model").allTextContents();
  const expectedModels = [...sortedModels].sort((a, b) =>
    a.localeCompare(b, undefined, { numeric: true, sensitivity: "base" })
  );
  if (JSON.stringify(sortedModels) !== JSON.stringify(expectedModels)) {
    throw new Error("Benchmark Results Explorer model sorting is not alphabetical");
  }
  await page.locator("[data-results-sort]").selectOption("vendor");
  const sortedVendors = await page.locator("[data-results-rows] .benchmark-vendor-tag").allTextContents();
  const expectedVendors = [...sortedVendors].sort((a, b) =>
    a.localeCompare(b, undefined, { numeric: true, sensitivity: "base" })
  );
  if (JSON.stringify(sortedVendors) !== JSON.stringify(expectedVendors)) {
    throw new Error("Benchmark Results Explorer vendor sorting is not alphabetical");
  }
  await page.locator("[data-results-reset]").click();
  if (await page.locator("[data-results-sort]").inputValue() !== "") {
    throw new Error("Benchmark Results Explorer reset did not restore source order");
  }
  if ((await page.locator("[data-results-source-cards]").textContent()).indexOf("InferenceX") < 0) {
    throw new Error("Benchmark Results Explorer did not show the InferenceX source status");
  }
  await page.locator("[data-results-search]").fill("MI355X");
  if (Number(await page.locator("[data-results-count]").textContent()) < 1) {
    throw new Error("Benchmark result search did not locate MI355X submissions");
  }
  await page.locator("[data-results-reset]").click();
  await page.locator("[data-results-vendor]").selectOption("AMD");
  await page.locator("[data-results-model]").selectOption("deepseek-r1");
  await page.locator("[data-results-scenario]").selectOption("Server");
  await page.locator("[data-results-availability]").selectOption("available");
  await page.locator("[data-results-division]").selectOption("closed");
  await page.locator("[data-results-system]").selectOption("datacenter");
  if (Number(await page.locator("[data-results-count]").textContent()) < 1) {
    throw new Error("Like-for-like MLPerf filters did not return AMD DeepSeek R1 Server results");
  }
  await page.locator("[data-results-reset]").click();
  await page.locator("[data-results-inferred]").selectOption("true");
  if (Number(await page.locator("[data-results-count]").textContent()) !== 125) {
    throw new Error("Inferred-submission filter should isolate the 125 source-marked inferred rows");
  }
  await page.locator("[data-results-reset]").click();
  const resultDetails = page.locator("[data-results-rows] .benchmark-result-details").first();
  await resultDetails.locator("summary").click();
  if (!(await resultDetails.locator(".benchmark-result-detail-links a").count())) {
    throw new Error("Benchmark result details did not retain the publisher source link");
  }

  const metricFixture = {
    database_version: "fixture",
    last_imported_at: "2026-11-10",
    summary: { total_records: 4, by_availability: { published: 4 }, inferred_records: 0, power_records: 3, submitters: 1 },
    sources: [{ id: "inferencex", name: "SemiAnalysis InferenceX", version: "Public API v1", publisher: "SemiAnalysis", source_class: "third_party_public_benchmark", record_count: 4, results_url: "https://inferencex.semianalysis.com/" }],
    records: [100, 250, 150, 400].map((value, index) => ({
      id: "fixture-" + index, source_id: "inferencex", source_class: "third_party_public_benchmark",
      submitter: "SemiAnalysis", accelerator_vendor: index === 1 ? "AMD" : "NVIDIA", system_name: index === 1 ? "MI300X" : "H200 SXM",
      system: {
        hardware: index === 1 ? "MI300X" : "H200 SXM",
        is_multinode: false,
        physical_prefill_gpus: index === 2 ? null : 0,
        physical_decode_gpus: index === 2 ? null : (index === 0 ? 8 : index === 1 ? 8 : 16),
        workers: [{ role: "decode", worker_idx: 0, num_gpus: index === 0 ? 8 : index === 1 ? 8 : index === 2 ? 4 : 16 }]
      }, model: "dsr1",
      model_display_name: "DeepSeek-R1-0528", scenario: "single_turn", availability: "published",
      division: "third_party", system_type: "datacenter", benchmark_suite: "SemiAnalysis InferenceX",
      benchmark_version: null, publication_date: "2026-11-10", inferred: false, errors: 0,
      result_value: null, result_unit: "", accuracy_text: "", source_url: "https://inferencex.semianalysis.com/",
      normalized_metrics: {
        output_throughput_per_gpu: { value, unit: "tok/s/GPU", label: "Output throughput", direction: "higher", family: "throughput" },
        median_ttft: { value: 0.8 + index * 0.1, unit: "s", label: "Median TTFT", direction: "lower", family: "latency" },
        ...(index === 1 ? {} : {
          median_tpot: { value: 0.08 + index * 0.01, unit: "s", label: "Median TPOT", direction: "lower", family: "latency" }
        }),
        mean_gpu_utilization: { value: [76, 65, 80, 91][index], unit: "%", label: "Mean GPU utilization", direction: "context", family: "telemetry" },
        ...(index === 2 ? {} : {
          mean_gpu_memory_used: { value: 19000 + index * 3000, unit: "MB", label: "Mean GPU memory used", direction: "context", family: "telemetry" }
        }),
        p99_ttft: { value: [1.2, 0.8, 1.0, 1.5][index], unit: "s", label: "P99 TTFT", direction: "lower", family: "latency" },
        p99_tpot: { value: [0.15, 0.16, 0.12, 0.2][index], unit: "s", label: "P99 TPOT", direction: "lower", family: "latency" },
        ...(index === 2 ? {} : {
          p99_itl: { value: 0.18 + index * 0.01, unit: "s", label: "P99 inter-token latency", direction: "lower", family: "latency" }
        }),
        energy_per_output_token: { value: [0.30, 0.45, 0.18, 0.22][index], unit: "J/output token", label: "Energy per output token", direction: "lower", family: "energy" },
        ...(index === 1 ? {} : {
          energy_per_total_token: { value: [0.12, 0, 0.08, 0.09][index], unit: "J/total token", label: "Energy per total token", direction: "lower", family: "energy" }
        }),
        ...(index === 0 ? {
          energy_per_successful_query: { value: 8.4, unit: "J/query", label: "Energy per successful query", direction: "lower", family: "energy" },
          prefill_energy_per_input_token: { value: 0.04, unit: "J/input token", label: "Prefill energy per input token", direction: "lower", family: "energy" },
          decode_energy_per_output_token: { value: 0.28, unit: "J/output token", label: "Decode energy per output token", direction: "lower", family: "energy" },
          prefill_gpu_power_per_gpu: { value: 280, unit: "W/GPU", label: "Prefill GPU power", direction: "context", family: "power" },
          decode_gpu_power_per_gpu: { value: 245, unit: "W/GPU", label: "Decode GPU power", direction: "context", family: "power" },
          mean_total_cpu_power: { value: 75, unit: "W", label: "Mean total CPU power", direction: "context", family: "cpu_power" }
        } : {}),
        mean_gpu_power_per_gpu: { value: [260, 280, 180, 240][index], unit: "W/GPU", label: "Mean GPU power", direction: "context", family: "power" },
        mean_total_gpu_power: { value: [2080, 2240, 720, 3840][index], unit: "W", label: "Mean total GPU power", direction: "context", family: "power" },
        ...(index === 2 ? {
          prefill_gpu_power_per_gpu: { value: 999, unit: "W/GPU", label: "Prefill GPU power", direction: "context", family: "power" },
          decode_gpu_power_per_gpu: { value: 999, unit: "W/GPU", label: "Decode GPU power", direction: "context", family: "power" }
        } : {})
      },
      power_measurement_valid: index !== 2,
      power_measurement_status: index === 2 ? "failed" : "valid",
      gpu_power_metrics_available: index !== 2,
      cpu_power_measurement_valid: index === 0,
      cpu_power_measurement_status: index === 0 ? "valid" : "not_present",
      cpu_power_metrics_available: index === 0,
      metrics: { output_tput_per_gpu: value },
      workload: { precision: "FP8", benchmark_type: "single_turn", isl: index === 3 ? 2048 : 1024, osl: 1024, concurrency: 32, speculative_method: "none", disaggregated: false },
      software: {
        framework: "vLLM 0.11",
        image: "ghcr.io/vllm-project/vllm-openai:v0.11.0",
        recipe_fingerprint: "vllm-0.11-fp8"
      }, configuration: {},
      ...(index === 0 ? {
        hardware_evidence: {
          schema_version: "1.0",
          collector: { name: "Nsight Compute", version: "2026.3", type: "profiler" },
          system_scope: { scope_type: "per_gpu", device_count: 8, device_model: "H200 SXM", topology: "8-GPU NVLink node" },
          sampling: { started_at: "2026-11-12T10:00:00Z", ended_at: "2026-11-12T10:01:00Z", sample_interval_ms: 1000, sample_count: 60 },
          provenance: { source_type: "profiler_export", source_url: "https://example.com/hardware-evidence/fixture-0", collected_at: "2026-11-12T10:02:00Z" },
          metrics: [
            { metric_id: "sm_throughput_pct", value: 72, unit: "%", measurement_kind: "telemetry", aggregation: "mean", scope: "per_kernel", source_name: "sm__throughput.avg.pct_of_peak_sustained_elapsed", mapping_quality: "direct", mapping_note: "Profiler throughput relative to peak sustained rate over elapsed cycles.", entity_id: "gpu0", sampling_window: { started_at: "2026-11-12T10:00:02Z", ended_at: "2026-11-12T10:00:02.500Z" } },
            { metric_id: "sm_active_pct", value: 72, unit: "%", measurement_kind: "telemetry", aggregation: "mean", scope: "per_gpu", source_name: "DCGM_FI_PROF_SM_UTIL_RATIO", mapping_quality: "direct", mapping_note: "Ratio of cycles with at least one warp assigned to an SM." },
            { metric_id: "theoretical_peak_flops", value: 1.9e15, unit: "FLOP/s", measurement_kind: "telemetry", aggregation: "max", scope: "per_gpu", source_name: "device_fp8_peak_flops", precision: "FP8", sparsity: "dense" },
            { metric_id: "compute_flop_count", value: 7.2e16, unit: "FLOP", measurement_kind: "hardware_counter", aggregation: "sum", scope: "per_gpu", source_name: "flop_count_sp", precision: "FP8", sparsity: "dense" },
            { metric_id: "achieved_flops", value: 1.2e15, unit: "FLOP/s", measurement_kind: "derived", aggregation: "mean", scope: "per_gpu", source_name: "derived_achieved_flops", formula: "compute_flop_count / measured_window_seconds", input_metric_ids: ["compute_flop_count"], precision: "FP8", sparsity: "dense" },
            { metric_id: "dram_read_bytes", value: 2e12, unit: "byte", measurement_kind: "hardware_counter", aggregation: "sum", scope: "per_gpu", source_name: "dram__bytes_read.sum" },
            { metric_id: "nvlink_tx_bytes", value: 8e12, unit: "byte", measurement_kind: "hardware_counter", aggregation: "sum", scope: "per_link", source_name: "nvlink_tx_bytes", link_type: "nvlink" },
            { metric_id: "gpu_power_w", value: 650, unit: "W", measurement_kind: "telemetry", aggregation: "mean", scope: "per_gpu", source_name: "gpu_power_w" }
          ]
        }
      } : {}),
      ...(index === 0 ? {
        runtime_trace: {
          schema_version: "1.0",
          collector: { name: "Serving Runtime Trace", version: "1.0", type: "runtime_trace" },
          clock_domain: "utc_wall_clock",
          sampling: { started_at: "2026-11-12T10:00:00Z", ended_at: "2026-11-12T10:01:00Z" },
          provenance: { source_type: "runtime_trace_export", source_url: "https://example.com/runtime-trace/fixture-0", collected_at: "2026-11-12T10:02:01Z" },
          events: [
            { event_id: "request-root-17", name: "request 17", category: "request", started_at: "2026-11-12T10:00:00Z", ended_at: "2026-11-12T10:00:20Z", correlation_id: "request-17", dependency_graph_complete: true },
            { event_id: "queue-17", name: "queue wait", category: "queue_wait", started_at: "2026-11-12T10:00:00Z", ended_at: "2026-11-12T10:00:01Z", parent_event_id: "request-root-17", depends_on_event_ids: ["request-root-17"] },
            { event_id: "prefill-1", name: "prefill batch 1", category: "prefill", started_at: "2026-11-12T10:00:01Z", ended_at: "2026-11-12T10:00:08Z", entity_id: "gpu0", parent_event_id: "request-root-17", depends_on_event_ids: ["queue-17"] },
            { event_id: "kernel-1", name: "attention kernel", category: "kernel", started_at: "2026-11-12T10:00:02Z", ended_at: "2026-11-12T10:00:04Z", entity_id: "gpu0", parent_event_id: "prefill-1", stream_id: "stream-0" },
            { event_id: "communication-17", name: "collective communication", category: "communication", started_at: "2026-11-12T10:00:03Z", ended_at: "2026-11-12T10:00:05Z", entity_id: "gpu0", parent_event_id: "request-root-17" },
            { event_id: "decode-17", name: "decode phase", category: "decode", started_at: "2026-11-12T10:00:08Z", ended_at: "2026-11-12T10:00:12Z", parent_event_id: "request-root-17" },
            { event_id: "communication-wait-17", name: "communication wait", category: "communication_wait", started_at: "2026-11-12T10:00:10Z", ended_at: "2026-11-12T10:00:11Z", parent_event_id: "decode-17" },
            { event_id: "token-17-1", name: "first token", category: "token_emit", started_at: "2026-11-12T10:00:08Z", ended_at: "2026-11-12T10:00:08Z", token_index: 1, parent_event_id: "request-root-17", depends_on_event_ids: ["prefill-1"] },
            { event_id: "token-17-2", name: "second token", category: "token_emit", started_at: "2026-11-12T10:00:12Z", ended_at: "2026-11-12T10:00:12Z", token_index: 2, parent_event_id: "request-root-17" }
          ]
        }
      } : {}),
      weight_data_types: "FP8"
    }))
  };
  await page.route("**/data/benchmark-results.json.gz", route => route.fulfill({
    status: 200, contentType: "application/json", body: JSON.stringify(metricFixture)
  }));
  await page.goto(base + "/results/", { waitUntil: "networkidle" });
  await page.waitForFunction(() => document.querySelector("[data-benchmark-results]")?.dataset.loaded === "true");
  await page.locator(".benchmark-results-advanced summary").click();
  const metricSelect = page.locator("[data-results-metric]");
  if (await metricSelect.locator("option").count() < 3) {
    throw new Error("Metric selector did not load normalized metric definitions");
  }
  const unselectedCohortAction = page.locator('[data-results-rows] tr[data-result-id="fixture-0"] .benchmark-result-details summary');
  await unselectedCohortAction.click();
  if (!(await page.locator('[data-results-rows] tr[data-result-id="fixture-0"] .benchmark-cohort-action').isDisabled())) {
    throw new Error("InferenceX strict cohort action must require an explicit normalized metric");
  }
  await metricSelect.selectOption("output_throughput_per_gpu");
  if (Number(await page.locator("[data-results-count]").textContent()) !== 4) {
    throw new Error("Metric filter should retain all four rows reporting the selected metric");
  }
  await page.locator("[data-results-sort]").selectOption("metric-best");
  const bestFirst = await page.locator("[data-results-rows] .benchmark-result-value").allTextContents();
  if (!bestFirst[0].includes("400") || !bestFirst[1].includes("250") ||
      !bestFirst[2].includes("150") || !bestFirst[3].includes("100")) {
    throw new Error("Higher-is-better metric sorting did not rank the largest throughput first: " + bestFirst.join(", "));
  }
  await page.locator("[data-results-sort]").selectOption("metric-worst");
  const worstFirst = await page.locator("[data-results-rows] .benchmark-result-value").allTextContents();
  if (!worstFirst[0].includes("100") || !worstFirst[3].includes("400")) {
    throw new Error("Metric worst-first sorting did not reverse the throughput order");
  }
  await metricSelect.selectOption("median_ttft");
  await page.locator("[data-results-sort]").selectOption("metric-best");
  const latencyBest = await page.locator("[data-results-rows] .benchmark-result-value").allTextContents();
  if (!latencyBest[0].includes("0.8")) {
    throw new Error("Lower-is-better latency sorting did not put the smallest TTFT first");
  }
  const cohortRow = page.locator('[data-results-rows] tr[data-result-id="fixture-0"]');
  await cohortRow.locator(".benchmark-result-details summary").click();
  await cohortRow.locator(".benchmark-cohort-action").click();
  if (Number(await page.locator("[data-results-count]").textContent()) !== 3) {
    throw new Error("Strict InferenceX cohort should exclude the row with a different ISL");
  }
  const cohortIds = await page.locator("[data-results-rows] tr").evaluateAll(rows => rows.map(row => row.dataset.resultId));
  if (!cohortIds.includes("fixture-1") || !cohortIds.includes("fixture-2") || cohortIds.includes("fixture-3")) {
    throw new Error("Strict InferenceX cohort should retain hardware/software variants but exclude workload mismatches: " + cohortIds.join(", "));
  }
  const cohortText = await page.locator("[data-results-cohort-summary]").textContent();
  if (!cohortText.includes("3 records") || !cohortText.includes("software stack")) {
    throw new Error("Strict InferenceX cohort explanation did not render its count and variable dimensions");
  }
  await page.locator("[data-results-cohort-clear]").click();
  if (Number(await page.locator("[data-results-count]").textContent()) !== 4) {
    throw new Error("Clearing the strict cohort did not restore all four InferenceX records");
  }

  // Build the cohort from a metric published by only two records. The frontier
  // must still consider fixture-2 because it reports the three frontier metrics.
  await metricSelect.selectOption("p99_itl");
  const partialMetricRow = page.locator('[data-results-rows] tr[data-result-id="fixture-0"]');
  await partialMetricRow.locator(".benchmark-result-details summary").click();
  await partialMetricRow.locator(".benchmark-cohort-action").click();
  const partialMetricFrontierIds = await page.locator("[data-results-frontier-content] tbody tr")
    .evaluateAll(rows => rows.map(row => row.dataset.recordId));
  if (!partialMetricFrontierIds.includes("fixture-2")) {
    throw new Error("Pareto frontier incorrectly required the selected display metric on every cohort record");
  }
  await page.locator("[data-results-cohort-clear]").click();

  await metricSelect.selectOption("output_throughput_per_gpu");
  if (!(await page.locator("[data-results-scaling]").isHidden())) {
    throw new Error("Scaling analysis must remain hidden until a strict workload cohort is selected");
  }
  if (!(await page.locator("[data-results-energy]").isHidden())) {
    throw new Error("Energy analysis must remain hidden until a strict workload cohort is selected");
  }
  if (!(await page.locator("[data-results-decomposition]").isHidden())) {
    throw new Error("Performance decomposition must remain hidden before a strict workload cohort");
  }
  if (!(await page.locator("[data-results-hardware-evidence]").isHidden())) {
    throw new Error("Hardware evidence coverage must remain hidden before a strict workload cohort");
  }
  const scalingRow = page.locator('[data-results-rows] tr[data-result-id="fixture-0"]');
  await scalingRow.locator(".benchmark-result-details summary").click();
  await scalingRow.locator(".benchmark-cohort-action").click();
  if (await page.locator("[data-results-scaling]").isHidden()) {
    throw new Error("Selecting an InferenceX output-throughput cohort did not reveal scaling analysis");
  }
  const scalingText = await page.locator("[data-results-scaling-content]").textContent();
  if (!scalingText.includes("H200 SXM") || !scalingText.includes("66.7%") ||
      !scalingText.includes("4 GPUs") || !scalingText.includes("8 GPUs") ||
      !scalingText.includes("worker-pool counts") || !scalingText.includes("derived estimates")) {
    throw new Error("Scaling analysis did not derive a provenance-aware 4-to-8 GPU efficiency curve: " + scalingText);
  }
  if (await page.locator("[data-results-frontier]").isHidden()) {
    throw new Error("Selecting a strict InferenceX cohort did not reveal the latency-throughput frontier");
  }
  if (await page.locator("[data-results-energy]").isHidden()) {
    throw new Error("Selecting a strict InferenceX cohort did not reveal GPU energy analysis");
  }
  if (await page.locator("[data-results-decomposition]").isHidden()) {
    throw new Error("Selecting a strict InferenceX cohort did not reveal performance decomposition");
  }
  if (await page.locator("[data-results-hardware-evidence]").isHidden()) {
    throw new Error("Selecting a strict InferenceX cohort did not reveal hardware evidence coverage");
  }
  const hardwareEvidenceText = await page.locator("[data-results-hardware-evidence-content]").textContent();
  if (!hardwareEvidenceText.includes("1/3 records include a provenance-backed hardware evidence bundle") ||
      !hardwareEvidenceText.includes("Compute") || !hardwareEvidenceText.includes("HBM bandwidth") ||
      !hardwareEvidenceText.includes("KV cache") || !hardwareEvidenceText.includes("Communication") ||
      !hardwareEvidenceText.includes("Power / thermal") || !hardwareEvidenceText.includes("not a bottleneck verdict")) {
    throw new Error("Hardware evidence coverage did not report the five evidence domains and limitations: " + hardwareEvidenceText);
  }
  const evidenceDomains = page.locator("[data-hardware-evidence-domain]");
  if (await evidenceDomains.count() !== 5) {
    throw new Error("Hardware evidence coverage should expose exactly five domains");
  }
  const computeEvidence = await page.locator('[data-hardware-evidence-domain="compute"]').textContent();
  const hbmEvidence = await page.locator('[data-hardware-evidence-domain="hbm"]').textContent();
  const communicationEvidence = await page.locator('[data-hardware-evidence-domain="communication"]').textContent();
  if (!computeEvidence.includes("1 core · 0 partial · 2 missing") ||
      !hbmEvidence.includes("0 core · 1 partial · 2 missing") ||
      !communicationEvidence.includes("0 core · 1 partial · 2 missing")) {
    throw new Error("Hardware evidence readiness incorrectly classified complete/partial/missing signals: " +
      JSON.stringify({computeEvidence, hbmEvidence, communicationEvidence}));
  }
  const evidenceRows = page.locator("[data-hardware-evidence-record-id]");
  if (await evidenceRows.count() !== 3) {
    throw new Error("Hardware evidence table did not retain the selected strict cohort");
  }
  if (await page.locator("[data-results-gpu-execution]").isHidden()) {
    throw new Error("Selecting a strict workload cohort did not reveal GPU execution efficiency analysis");
  }
  const gpuExecutionText = await page.locator("[data-results-gpu-execution-content]").textContent();
  if (!gpuExecutionText.includes("scope/entity/window-matched hardware activity groups") ||
      !gpuExecutionText.includes("SM inactive-cycle complement") ||
      !gpuExecutionText.includes("SM throughput") ||
      !gpuExecutionText.includes("50% (n=1)") ||
      !gpuExecutionText.includes("25% (n=1)")) {
    throw new Error("GPU execution analysis did not preserve counter semantics and request-level compute/communication overlap: " + gpuExecutionText);
  }
  if (await page.locator("[data-gpu-execution-activity] tbody tr").count() !== 2 ||
      await page.locator("[data-gpu-execution-overlap] tbody tr").count() !== 1) {
    throw new Error("GPU activity and request-overlap tables did not render the expected fixture rows");
  }
  const crossLayerText = await page.locator("[data-results-cross-layer-content]").textContent();
  if (!crossLayerText.includes("3 strict-cohort records") ||
      !crossLayerText.includes("3 execution identities") ||
      !crossLayerText.includes("3 descriptive contrasts") ||
      !crossLayerText.includes("P99 TTFT") ||
      !crossLayerText.includes("Not established")) {
    throw new Error("Cross-layer matrix did not compare the strict cohort with runtime and evidence limits: " + crossLayerText);
  }
  if (await page.locator("[data-cross-layer-comparison]").count() !== 3) {
    throw new Error("Cross-layer matrix should render the three unique execution contrasts");
  }
  const runtimeAlignmentText = await page.locator("[data-results-runtime-alignment-content]").textContent();
  if (!runtimeAlignmentText.includes("3 strict-cohort records") ||
      !runtimeAlignmentText.includes("1 runtime traces") ||
      !runtimeAlignmentText.includes("1 hardware/trace pairs") ||
      !runtimeAlignmentText.includes("1 metric-specific windows") ||
      !runtimeAlignmentText.includes("1 eligible phase joins")) {
    throw new Error("Runtime trace alignment panel did not report exact evidence coverage: " + runtimeAlignmentText);
  }
  if (await page.locator("[data-runtime-trace-record-id]").count() !== 1 ||
      await page.locator("[data-runtime-phase-join]").count() !== 1 ||
      !(await page.locator("[data-runtime-phase-join]").textContent()).includes("kernel")) {
    throw new Error("Runtime phase alignment did not join the metric window to the exact nested kernel event");
  }
  const phaseDecompositionText = await page.locator("[data-results-phase-decomposition-content]").textContent();
  if (!phaseDecompositionText.includes("1 request roots") ||
      !phaseDecompositionText.includes("1 trace-derived TTFT samples") ||
      !phaseDecompositionText.includes("1 trace-derived TPOT samples")) {
    throw new Error("Request-level TTFT/TPOT decomposition did not report the explicit token-marker sample");
  }
  const phaseRow = page.locator("[data-runtime-phase-decomposition] tbody tr");
  if (await phaseRow.count() !== 1 ||
      !(await phaseRow.textContent()).includes("8,000 / 8,000 ms") ||
      !(await phaseRow.textContent()).includes("4,000 / 4,000 ms")) {
    throw new Error("Trace-derived TTFT/TPOT values do not match the request and token marker timestamps: " + await phaseRow.textContent());
  }
  const criticalPathRow = page.locator("[data-runtime-critical-path] tbody tr").first();
  if (await page.locator("[data-runtime-critical-path] tbody tr").count() !== 1 ||
      !(await criticalPathRow.textContent()).includes("queue wait") ||
      !(await criticalPathRow.textContent()).includes("prefill batch 1") ||
      !(await criticalPathRow.textContent()).includes("8,000 ms") ||
      !(await criticalPathRow.textContent()).includes("0 ms") ||
      !(await criticalPathRow.textContent()).includes("Available")) {
    throw new Error("Explicit TTFT dependency path did not reconcile event time and unclassified gaps: " +
      await criticalPathRow.textContent());
  }
  const evidenceRecord = page.locator('[data-hardware-evidence-record-id="fixture-0"]');
  await page.locator(".benchmark-hardware-evidence-details summary").click();
  const evidenceDetails = await page.locator(".benchmark-hardware-evidence-details").textContent();
  if (!evidenceDetails.includes("sm_throughput_pct") ||
      !evidenceDetails.includes("dram_read_bytes") ||
      !evidenceDetails.includes("sm__throughput.avg.pct_of_peak_sustained_elapsed") ||
      !evidenceDetails.includes("mapping: direct")) {
    throw new Error("Hardware evidence details did not preserve canonical and raw counter names: " + evidenceDetails);
  }
  if (!evidenceDetails.includes("Roofline: insufficient evidence") ||
      !evidenceDetails.includes("Communication: no comparable per-link utilization") ||
      !evidenceDetails.includes("P99 TTFT") ||
      !evidenceDetails.includes("no automatic bottleneck verdict") ||
      !evidenceDetails.includes("kernel-gap traces")) {
    throw new Error("Hardware diagnostics inferred a bottleneck or omitted runtime/evidence limitations: " + evidenceDetails);
  }
  const noEvidenceRecord = await page.locator('[data-hardware-evidence-record-id="fixture-1"]').textContent();
  if (!noEvidenceRecord.includes("Not reported")) {
    throw new Error("Aggregate GPU metrics were incorrectly promoted to low-level hardware evidence");
  }
  const frontierText = await page.locator("[data-results-frontier-content]").textContent();
  if (!frontierText.includes("3 report all three required metrics") ||
      !frontierText.includes("2 Pareto-optimal configurations") ||
      !frontierText.includes("P99 TTFT") || !frontierText.includes("P99 TPOT")) {
    throw new Error("Pareto frontier did not summarize the three-metric cohort correctly: " + frontierText);
  }
  const frontierIds = await page.locator("[data-results-frontier-content] tbody tr")
    .evaluateAll(rows => rows.map(row => row.dataset.recordId));
  if (frontierIds.length !== 2 || !frontierIds.includes("fixture-1") ||
      !frontierIds.includes("fixture-2") || frontierIds.includes("fixture-0")) {
    throw new Error("Pareto frontier should retain the two non-dominated configurations and exclude fixture-0: " + frontierIds.join(", "));
  }
  const dominanceAudit = page.locator("[data-pareto-dominance-audit]");
  const dominatedObservation = dominanceAudit.locator("[data-dominated-record='fixture-0']");
  if(await dominatedObservation.count()!==1)throw Error("Missing dominance witness for fixture-0");
  if(await dominatedObservation.getAttribute("data-dominating-record")!=="fixture-2")throw Error("Unexpected non-dominated witness");
  if(await dominatedObservation.locator("li").count()!==3)throw Error("Dominance explanation must cover all three metrics");
  if(await dominanceAudit.locator("[data-dominated-record='fixture-1'], [data-dominated-record='fixture-2']").count())throw Error("Non-dominated records incorrectly marked dominated");
  const paretoPlot = page.locator("[data-pareto-plot]");
  if (await paretoPlot.locator(".benchmark-frontier-point").count() !== 3 ||
      await paretoPlot.locator(".benchmark-frontier-point.is-pareto").count() !== 2) {
    throw new Error("Pareto scatter plot did not distinguish all candidates from non-dominated points");
  }
  const energyText = await page.locator("[data-results-energy-content]").textContent();
  if (!energyText.includes("3 records in the selected strict workload cohort") ||
      !energyText.includes("2 have validated GPU energy per output token") ||
      !energyText.includes("2 Pareto-optimal energy/throughput configurations") ||
      !energyText.includes("75 W") || !energyText.includes("0.04 J/input token") ||
      !energyText.includes("0.28 J/output token") || !energyText.includes("CPU/socket/module telemetry")) {
    throw new Error("Energy analysis did not summarize validated GPU energy and separate CPU telemetry: " + energyText);
  }
  const energyIds = await page.locator("[data-results-energy-content] tbody tr")
    .evaluateAll(rows => rows.map(row => row.dataset.recordId));
  if (energyIds.length !== 2 || !energyIds.includes("fixture-0") ||
      !energyIds.includes("fixture-1") || energyIds.includes("fixture-2")) {
    throw new Error("Energy analysis included an unvalidated power record or omitted a valid record: " + energyIds.join(", "));
  }
  const energyPlot = page.locator("[data-energy-plot]");
  if (await energyPlot.locator(".benchmark-energy-point").count() !== 2 ||
      await energyPlot.locator(".benchmark-energy-point.is-pareto").count() !== 2) {
    throw new Error("Energy Pareto plot did not distinguish the two non-dominated energy/throughput configurations");
  }
  const decompositionText = await page.locator("[data-results-decomposition-content]").textContent();
  if (!decompositionText.includes("3 records in selected strict workload cohort") ||
      !decompositionText.includes("Median TTFT") ||
      !decompositionText.includes("Median TPOT") ||
      !decompositionText.includes("P99 ITL") ||
      !decompositionText.includes("Prefill GPU energy") ||
      !decompositionText.includes("not a measured decode-kernel breakdown") ||
      !decompositionText.includes("classifications remain undetermined")) {
    throw new Error("Performance decomposition did not explain phase signals and diagnostic boundaries: " + decompositionText);
  }
  const decompositionRows = page.locator("[data-results-decomposition-content] [data-decomposition-record-id]");
  if (await decompositionRows.count() !== 3) {
    throw new Error("Performance decomposition did not respect the strict workload cohort");
  }
  const validPhase = await page.locator('[data-decomposition-record-id="fixture-0"]').textContent();
  const invalidPhase = await page.locator('[data-decomposition-record-id="fixture-2"]').textContent();
  if (!validPhase.includes("280 W/GPU") || !validPhase.includes("245 W/GPU") ||
      !validPhase.includes("0.04 J/input token") || !validPhase.includes("19,000 MB") ||
      !invalidPhase.includes("Validated phase-energy telemetry unavailable") ||
      invalidPhase.includes("999 W/GPU")) {
    throw new Error("Performance decomposition failed to gate phase power and preserve publisher telemetry: " +
      JSON.stringify({validPhase, invalidPhase}));
  }
  const decompositionCoverage = await page.locator("[data-decomposition-signal]").count();
  if (decompositionCoverage !== 12) {
    throw new Error("Performance decomposition must report all twelve signal coverage dimensions");
  }
  await page.locator("[data-results-cohort-clear]").click();
  if (!(await page.locator("[data-results-scaling]").isHidden())) {
    throw new Error("Clearing the strict cohort did not hide scaling analysis");
  }
  if (!(await page.locator("[data-results-frontier]").isHidden())) {
    throw new Error("Clearing the strict cohort did not hide the Pareto frontier");
  }
  if (!(await page.locator("[data-results-energy]").isHidden())) {
    throw new Error("Clearing the strict cohort did not hide energy analysis");
  }
  if (!(await page.locator("[data-results-decomposition]").isHidden())) {
    throw new Error("Clearing the strict cohort did not hide performance decomposition");
  }
  if (!(await page.locator("[data-results-hardware-evidence]").isHidden())) {
    throw new Error("Clearing the strict cohort did not hide hardware evidence coverage");
  }

  const compareRow = id => page.locator('[data-results-rows] tr[data-result-id="' + id + '"]');
  await metricSelect.selectOption("output_throughput_per_gpu");
  await compareRow("fixture-0").locator(".benchmark-result-details summary").click();
  await compareRow("fixture-0").locator(".benchmark-compare-action").click();
  if (!(await page.locator("[data-comparison-count]").textContent()).includes("1 / 4") ||
      !(await page.locator("[data-comparison-content]").textContent()).includes("Add one more record")) {
    throw new Error("Comparison workspace did not retain the first selected InferenceX record");
  }
  await compareRow("fixture-1").locator(".benchmark-result-details summary").click();
  await compareRow("fixture-1").locator(".benchmark-compare-action").click();
  let comparisonWorkspaceText = await page.locator("[data-comparison-content]").textContent();
  if (!comparisonWorkspaceText.includes("Like-for-like cohort") || !comparisonWorkspaceText.includes("+150.0%") ||
      !comparisonWorkspaceText.includes("better (higher is better)")) {
    throw new Error("Higher-is-better InferenceX comparison did not calculate the source-directed delta: " + comparisonWorkspaceText);
  }
  await compareRow("fixture-3").locator(".benchmark-result-details summary").click();
  await compareRow("fixture-3").locator(".benchmark-compare-action").click();
  comparisonWorkspaceText = await page.locator("[data-comparison-content]").textContent();
  if (!comparisonWorkspaceText.includes("Not directly comparable") ||
      await page.locator(".benchmark-comparison-table").count() !== 0) {
    throw new Error("Comparison workspace must block metric comparison across different workload shapes");
  }
  await page.locator('.benchmark-comparison-remove[data-record-id="fixture-3"]').click();
  if (!(await page.locator("[data-comparison-content]").textContent()).includes("Like-for-like cohort")) {
    throw new Error("Removing a mismatched workload did not restore the valid comparison");
  }
  await page.locator("[data-comparison-clear]").click();
  if (!(await page.locator("[data-comparison-count]").textContent()).includes("0 / 4") ||
      await page.locator(".benchmark-comparison-table").count() !== 0) {
    throw new Error("Clear comparison did not reset the workspace");
  }

  await metricSelect.selectOption("median_ttft");
  await compareRow("fixture-0").locator(".benchmark-result-details summary").click();
  await compareRow("fixture-0").locator(".benchmark-compare-action").click();
  await compareRow("fixture-1").locator(".benchmark-result-details summary").click();
  await compareRow("fixture-1").locator(".benchmark-compare-action").click();
  const latencyComparisonText = await page.locator("[data-comparison-content]").textContent();
  if (!latencyComparisonText.includes("+12.5%") ||
      !latencyComparisonText.includes("worse (lower is better)")) {
    throw new Error("Lower-is-better latency comparison incorrectly interpreted a positive delta: " + latencyComparisonText);
  }
  await page.locator("[data-comparison-clear]").click();
  await page.unroute("**/data/benchmark-results.json.gz");

  const attributionRows = [
    { id: "attr-base-a", hardware: "H200 SXM", gpuCount: 8, framework: "vLLM 0.11", image: "ghcr.io/vllm-project/vllm-openai:v0.11.0", recipe: "vllm-0.11-fp8", prefillTp: 1, value: 100 },
    { id: "attr-base-b", hardware: "H200 SXM", gpuCount: 8, framework: "vLLM 0.11", image: "ghcr.io/vllm-project/vllm-openai:v0.11.0", recipe: "vllm-0.11-fp8", prefillTp: 1, value: 102 },
    { id: "attr-software", hardware: "H200 SXM", gpuCount: 8, framework: "SGLang 0.5", image: "lmsysorg/sglang:v0.5.0", recipe: "sglang-0.5-fp8", prefillTp: 1, value: 120 },
    { id: "attr-parallelism", hardware: "H200 SXM", gpuCount: 8, framework: "vLLM 0.11", image: "ghcr.io/vllm-project/vllm-openai:v0.11.0", recipe: "vllm-0.11-fp8", prefillTp: 2, value: 90 },
    { id: "attr-gpu-count", hardware: "H200 SXM", gpuCount: 4, framework: "vLLM 0.11", image: "ghcr.io/vllm-project/vllm-openai:v0.11.0", recipe: "vllm-0.11-fp8", prefillTp: 1, value: 130 },
    { id: "attr-hardware", hardware: "MI300X", gpuCount: 8, framework: "vLLM 0.11", image: "ghcr.io/vllm-project/vllm-openai:v0.11.0", recipe: "vllm-0.11-fp8", prefillTp: 1, value: 110 }
  ];
  const attributionFixture = {
    database_version: "attribution-fixture",
    last_imported_at: "2026-11-12",
    summary: { total_records: attributionRows.length, by_availability: { published: attributionRows.length }, inferred_records: 0, power_records: 0, submitters: 1 },
    sources: [{ id: "inferencex", name: "SemiAnalysis InferenceX", version: "Public API v1", publisher: "SemiAnalysis", source_class: "third_party_public_benchmark", record_count: attributionRows.length, results_url: "https://inferencex.semianalysis.com/" }],
    records: attributionRows.map(row => ({
      id: row.id, source_id: "inferencex", source_class: "third_party_public_benchmark",
      submitter: "SemiAnalysis", accelerator_vendor: row.hardware === "MI300X" ? "AMD" : "NVIDIA",
      system_name: row.gpuCount + "x" + row.hardware,
      system: {
        hardware: row.hardware, accelerator_model: row.hardware,
        total_accelerators: row.gpuCount, physical_prefill_gpus: 0,
        physical_decode_gpus: row.gpuCount, is_multinode: false,
        workers: [{ role: "decode", worker_idx: 0, num_gpus: row.gpuCount }]
      },
      model: "dsr1", model_display_name: "DeepSeek-R1-0528",
      scenario: "single_turn", availability: "published", division: "third_party",
      system_type: "datacenter", benchmark_suite: "SemiAnalysis InferenceX",
      benchmark_version: null, publication_date: "2026-11-12", inferred: false,
      result_value: null, result_unit: "", accuracy_text: "",
      source_url: "https://inferencex.semianalysis.com/",
      detail_url: "https://inferencex.semianalysis.com/",
      normalized_metrics: {
        output_throughput_per_gpu: {
          value: row.value, unit: "tok/s/GPU", label: "Output throughput",
          direction: "higher", family: "throughput"
        }
      },
      workload: {
        precision: "FP8", benchmark_type: "single_turn", isl: 1024, osl: 1024,
        concurrency: 32, speculative_method: "none", disaggregated: false
      },
      software: { framework: row.framework, image: row.image, recipe_fingerprint: row.recipe },
      configuration: {
        prefill_tp: row.prefillTp, prefill_ep: 1, prefill_dp_attention: 1,
        prefill_num_workers: 1, decode_tp: 1, decode_ep: 1,
        decode_dp_attention: 1, decode_num_workers: 1, offload_mode: "none"
      },
      weight_data_types: "FP8"
    }))
  };
  await page.route("**/data/benchmark-results.json.gz", route => route.fulfill({
    status: 200, contentType: "application/json", body: JSON.stringify(attributionFixture)
  }));
  await page.goto(base + "/results/", { waitUntil: "networkidle" });
  await page.waitForFunction(() => document.querySelector("[data-benchmark-results]")?.dataset.loaded === "true");
  if (!(await page.locator("[data-results-attribution]").isHidden())) {
    throw new Error("Configuration attribution must remain hidden until a strict InferenceX cohort is selected");
  }
  await page.locator(".benchmark-results-advanced summary").click();
  await page.locator("[data-results-metric]").selectOption("output_throughput_per_gpu");
  const attributionBaseRow = page.locator('[data-results-rows] tr[data-result-id="attr-base-a"]');
  await attributionBaseRow.locator(".benchmark-result-details summary").click();
  await attributionBaseRow.locator(".benchmark-cohort-action").click();
  if (await page.locator("[data-results-attribution]").isHidden()) {
    throw new Error("Selecting a strict InferenceX cohort did not reveal configuration attribution");
  }
  const attributionSummary = await page.locator("[data-results-attribution-content]").textContent();
  if (!attributionSummary.includes("6 records in the selected strict workload cohort") ||
      !attributionSummary.includes("6 report the selected metric") ||
      !attributionSummary.includes("5 distinct reported configuration signatures") ||
      !attributionSummary.includes("4 matched one-dimension contrast groups")) {
    throw new Error("Configuration attribution did not summarize the strict cohort and matched contrasts: " + attributionSummary);
  }
  const attributionContrasts = page.locator("[data-results-attribution-content] [data-attribution-contrast]");
  if (await attributionContrasts.count() !== 4) {
    throw new Error("Configuration attribution should produce exactly four isolated hardware/software/parallelism/GPU-count contrasts");
  }
  const contrastDimensions = await attributionContrasts.evaluateAll(rows => rows.map(row => row.dataset.attributionContrast).sort());
  if (JSON.stringify(contrastDimensions) !== JSON.stringify(["gpuCount", "hardware", "parallelism", "software"])) {
    throw new Error("Configuration attribution did not isolate the four expected dimensions: " + contrastDimensions.join(", "));
  }
  const contrastRows = await attributionContrasts.evaluateAll(rows =>
    rows.map(row => ({ dimension: row.dataset.attributionContrast, text: row.textContent, ids: row.dataset.attributionRecords }))
  );
  const hardwareContrast = contrastRows.find(row => row.dimension === "hardware");
  const gpuContrast = contrastRows.find(row => row.dimension === "gpuCount");
  const softwareContrast = contrastRows.find(row => row.dimension === "software");
  const parallelismContrast = contrastRows.find(row => row.dimension === "parallelism");
  if (!hardwareContrast.text.includes("H200 SXM → MI300X") ||
      !hardwareContrast.ids.includes("attr-hardware") ||
      !hardwareContrast.text.includes("+9 tok/s/GPU")) {
    throw new Error("Hardware contrast failed to aggregate duplicate baseline runs or calculate the median delta: " + JSON.stringify(hardwareContrast));
  }
  if (!gpuContrast.text.includes("4 GPUs → 8 GPUs") ||
      !gpuContrast.ids.includes("attr-gpu-count") ||
      !gpuContrast.text.includes("-29 tok/s/GPU")) {
    throw new Error("GPU-count contrast did not hold hardware/software/parallelism constant: " + JSON.stringify(gpuContrast));
  }
  if (!softwareContrast.text.includes("SGLang 0.5") ||
      !softwareContrast.text.includes("vLLM 0.11") ||
      !softwareContrast.ids.includes("attr-software")) {
    throw new Error("Software-stack contrast did not isolate the framework/image/recipe change: " + JSON.stringify(softwareContrast));
  }
  if (!parallelismContrast.text.includes("prefill_tp=1") ||
      !parallelismContrast.text.includes("prefill_tp=2") ||
      !parallelismContrast.ids.includes("attr-parallelism")) {
    throw new Error("Parallelism contrast did not isolate the prefill TP change: " + JSON.stringify(parallelismContrast));
  }
  const attributionCoverage = await page.locator("[data-attribution-coverage-dimension]")
    .evaluateAll(rows => rows.map(row => row.dataset.attributionCoverageDimension));
  if (attributionCoverage.length !== 5) {
    throw new Error("Configuration attribution coverage table is missing one or more dimensions");
  }
  await page.locator("[data-results-cohort-clear]").click();
  if (!(await page.locator("[data-results-attribution]").isHidden())) {
    throw new Error("Clearing the strict cohort did not hide configuration attribution");
  }
  await page.unroute("**/data/benchmark-results.json.gz");

  const mlperfFixture = {
    database_version: "fixture",
    last_imported_at: "2026-11-10",
    summary: { total_records: 3, by_availability: { available: 3 }, inferred_records: 0, power_records: 0, submitters: 3 },
    sources: [{ id: "mlperf-inference-v6.1", name: "MLPerf Inference v6.1", version: "v6.1", publisher: "MLCommons", source_class: "standardized_public_submission", record_count: 3, results_url: "https://mlcommons.org/benchmarks/inference-datacenter/" }],
    records: [
      { id: "mlperf-0", source_id: "mlperf-inference-v6.1", source_class: "standardized_public_submission", submitter: "Vendor A", accelerator_vendor: "NVIDIA", system_name: "8xH100", system: { accelerator_model: "H100", total_accelerators: 8 }, software: { framework: "TensorRT" }, model: "deepseek-r1", scenario: "Server", availability: "available", division: "closed", system_type: "datacenter", benchmark_suite: "MLPerf Inference", benchmark_version: "v6.1", accuracy_text: "99% of reference", weight_data_types: "FP8", inferred: false, result_value: 1000, result_unit: "tokens/s", power_metrics_available: false },
      { id: "mlperf-1", source_id: "mlperf-inference-v6.1", source_class: "standardized_public_submission", submitter: "Vendor B", accelerator_vendor: "AMD", system_name: "8xMI355X", system: { accelerator_model: "MI355X", total_accelerators: 8 }, software: { framework: "ROCm" }, model: "deepseek-r1", scenario: "Server", availability: "available", division: "closed", system_type: "datacenter", benchmark_suite: "MLPerf Inference", benchmark_version: "v6.1", accuracy_text: "99% of reference", weight_data_types: "FP8", inferred: false, result_value: 1500, result_unit: "tokens/s", power_metrics_available: false },
      { id: "mlperf-2", source_id: "mlperf-inference-v6.1", source_class: "standardized_public_submission", submitter: "Vendor C", accelerator_vendor: "NVIDIA", system_name: "8xB200", system: { accelerator_model: "B200", total_accelerators: 8 }, software: { framework: "TensorRT" }, model: "deepseek-r1", scenario: "Server", availability: "available", division: "closed", system_type: "datacenter", benchmark_suite: "MLPerf Inference", benchmark_version: "v6.1", accuracy_text: "99.9% of reference", weight_data_types: "FP8", inferred: false, result_value: 1700, result_unit: "tokens/s", power_metrics_available: false }
    ]
  };
  await page.route("**/data/benchmark-results.json.gz", route => route.fulfill({
    status: 200, contentType: "application/json", body: JSON.stringify(mlperfFixture)
  }));
  await page.goto(base + "/results/", { waitUntil: "networkidle" });
  await page.waitForFunction(() => document.querySelector("[data-benchmark-results]")?.dataset.loaded === "true");
  const mlperfRow = page.locator('[data-results-rows] tr[data-result-id="mlperf-0"]');
  await mlperfRow.locator(".benchmark-result-details summary").click();
  await mlperfRow.locator(".benchmark-cohort-action").click();
  if (Number(await page.locator("[data-results-count]").textContent()) !== 2) {
    throw new Error("Strict MLPerf cohort should match accuracy target and exclude a different accuracy row");
  }
  const mlperfCohortIds = await page.locator("[data-results-rows] tr").evaluateAll(rows => rows.map(row => row.dataset.resultId));
  if (!mlperfCohortIds.includes("mlperf-1") || mlperfCohortIds.includes("mlperf-2")) {
    throw new Error("Strict MLPerf cohort should retain other systems with the same benchmark conditions");
  }
  await page.locator("[data-results-cohort-clear]").click();
  if (Number(await page.locator("[data-results-count]").textContent()) !== 3) {
    throw new Error("Clearing the strict MLPerf cohort did not restore all fixture rows");
  }
  await page.locator('[data-results-rows] tr[data-result-id="mlperf-0"] .benchmark-result-details summary').click();
  await page.locator('[data-results-rows] tr[data-result-id="mlperf-0"] .benchmark-compare-action').click();
  await page.locator('[data-results-rows] tr[data-result-id="mlperf-1"] .benchmark-result-details summary').click();
  await page.locator('[data-results-rows] tr[data-result-id="mlperf-1"] .benchmark-compare-action').click();
  const mlperfComparison = await page.locator("[data-comparison-content]").textContent();
  if (!mlperfComparison.includes("Like-for-like cohort") ||
      !mlperfComparison.includes("direction not ranked") ||
      !mlperfComparison.includes("no winner is declared")) {
    throw new Error("MLPerf comparison must show deltas without inventing an optimization direction");
  }
  await page.locator("[data-comparison-clear]").click();
  await page.unroute("**/data/benchmark-results.json.gz");

  await page.goto(base + "/workloads/", { waitUntil: "networkidle" });
  await waitForDataset({
    name: "Workload",
    loadSelector: "[data-workload-load]",
    statSelector: '[data-workload-stat="paths"]',
    countSelector: "[data-workload-result-count]"
  });
  await page.locator("[data-workload-search]").fill("Biren");
  if (Number(await page.locator("[data-workload-result-count]").textContent()) !== 1) {
    throw new Error("Workload search did not isolate the Biren path");
  }

  await page.goto(base + "/model-support/", { waitUntil: "networkidle" });
  await waitForDataset({
    name: "Model support",
    loadSelector: "[data-model-load]",
    statSelector: '[data-model-stat="paths"]',
    countSelector: "[data-model-result-count]"
  });
  if (await page.locator("[data-model-support-version]").textContent() === "Loading…" ||
      !(await page.locator("[data-model-support-reviewed]").textContent()).trim()) {
    throw new Error("Model Support page-level registry metadata did not initialize");
  }
  const catalogCount = Number(await page.locator('[data-model-stat="models"]').textContent());
  if (catalogCount < 13 || Number(await page.locator("[data-catalog-result-count]").textContent()) !== catalogCount) {
    throw new Error("Model catalog did not render all independently curated checkpoints");
  }
  await page.locator("[data-catalog-search]").fill("Kimi K2 Thinking");
  if (Number(await page.locator("[data-catalog-result-count]").textContent()) !== 1) {
    throw new Error("Catalog search failed for an independently curated checkpoint");
  }
  const catalogOnly = await page.locator("[data-catalog-cards] .model-support-card").first().textContent();
  if (!catalogOnly.includes("No verified hardware path") || !catalogOnly.includes("official model card")) {
    throw new Error("Catalog-only model did not distinguish metadata from accelerator support");
  }
  await page.locator("[data-catalog-reset]").click();
  await page.locator("[data-catalog-coverage]").selectOption("catalog_only");
  if (Number(await page.locator("[data-catalog-result-count]").textContent()) < 6) {
    throw new Error("Catalog-only coverage filtering failed");
  }
  await page.locator("[data-catalog-reset]").click();
  await page.locator("[data-model-search]").fill("Llama 3.3 70B");
  if (Number(await page.locator("[data-model-result-count]").textContent()) !== 1) {
    throw new Error("Model support search did not isolate Llama 3.3 70B");
  }
  const llamaPath = await page.locator("[data-model-cards] .model-support-card").first().textContent();
  if (!llamaPath.includes("Trainium2") || !llamaPath.includes("Trainium3") ||
      !llamaPath.includes("BF16") || !llamaPath.includes("FP8 static")) {
    throw new Error("Llama 3.3 70B model support path is missing hardware or precision details");
  }
  await page.locator("[data-model-reset]").click();
  await page.locator("[data-model-platform]").selectOption("aws-trainium");
  if (Number(await page.locator("[data-model-result-count]").textContent()) !== 2) {
    throw new Error("Model support platform filter did not return both AWS Trainium paths");
  }

  // Local-only Evidence Review Workbench: no network-provided claim snapshot.
  await page.goto(base + "/evidence-review/", { waitUntil: "networkidle" });
  if (!(await page.locator("[data-ew-search]").isDisabled())) {
    throw new Error("Evidence Workbench unexpectedly allowed browsing before local upload");
  }
  const reviewClaims = [
    {claim_id:"claim-test-a",statement:"Example accelerator provides 180 GB HBM per GPU.",
     topic:"memory_capacity",claim_type:"quantitative_specification",assertion_class:"technical_specification_candidate",relevance:{class:"direct_ai_compute",matched_signals:["hbm"]},evidence_class:"vendor_primary_statement",value:180,unit:"GB",
     scope:{status:"explicit_per_unit",text:"per GPU"},qualifiers:[],review_status:"unverified_candidate",
     evidence_quote:"Example accelerator provides 180 GB HBM per GPU.",
     extraction:{method:"deterministic_rules_v4",confidence:"low"},
     source:{url:"https://example.org/vendor-release",publisher:"Example Vendor",published_at:"2026-11-12",
       evidence_scope:"official_vendor_feed_metadata_and_excerpt"},
     review_gates:["Read the original primary source."]},
    {claim_id:"claim-test-b",statement:"Example accelerator provides 180 GB HBM per GPU.",
     topic:"memory_capacity",claim_type:"quantitative_specification",assertion_class:"technical_specification_candidate",relevance:{class:"direct_ai_compute",matched_signals:["hbm"]},evidence_class:"vendor_primary_statement",value:180,unit:"GB",
     scope:{status:"explicit_per_unit",text:"per GPU"},qualifiers:[],review_status:"unverified_candidate",
     evidence_quote:"Example accelerator provides 180 GB HBM per GPU.",
     extraction:{method:"deterministic_rules_v4",confidence:"low"},
     evidence_class:"independent_reporting",source:{url:"https://example.org/reprint",publisher:"Example Reporter",published_at:"2026-11-13",
       evidence_scope:"independent_media_metadata"},
     review_gates:["Check reprint and dependency on original source."]},
    {claim_id:"claim-test-c",statement:"Example accelerator provides 192 GB HBM per GPU.",
     topic:"memory_capacity",claim_type:"quantitative_specification",assertion_class:"technical_specification_candidate",relevance:{class:"direct_ai_compute",matched_signals:["hbm"]},evidence_class:"research_preprint",value:192,unit:"GB",
     scope:{status:"explicit_per_unit",text:"per GPU"},qualifiers:[],review_status:"unverified_candidate",
     evidence_quote:"Example accelerator provides 192 GB HBM per GPU.",
     extraction:{method:"deterministic_rules_v4",confidence:"low"},
     source:{url:"https://example.org/other-report",publisher:"Example Third Party",published_at:"2026-11-14",
       evidence_scope:"research_preprint_metadata"},
     review_gates:["Confirm hardware SKU, version and scope."]}
  ];
  const reviewClaimJson = {schema_version:"1.0",claim_count:3,generated_at:"2026-11-14T00:00:00Z",claims:reviewClaims};
  const reviewGraphJson = {
    schema_version:"1.0",input_claim_count:3,generated_at:"2026-11-14T01:00:00Z",
    summary:{independently_verified_claims:0},
    nodes:reviewClaims.map(item=>({type:"claim_candidate",claim_id:item.claim_id,review_status:"unverified_candidate"})),
    edges:[],
    duplicate_clusters:[{claim_ids:["claim-test-a","claim-test-b"],independent_corroboration:false}],
    scoped_comparisons:[{claim_ids:["claim-test-a","claim-test-c"],
      subject_key:"example:gpu",metric_key:"hbm-capacity",
      context_key:"per-gpu:capacity",status:"possible_specification_conflict",independently_verified:false}]
  };
  const artifact = (name, data) => ({
    name, mimeType:"application/json", buffer:Buffer.from(JSON.stringify(data))
  });
  await page.locator("[data-ew-claims]").setInputFiles(artifact("ai-chip-intelligence-claims.json", reviewClaimJson));
  await page.locator("[data-ew-graph]").setInputFiles(artifact("ai-chip-intelligence-evidence-graph.json", reviewGraphJson));
  await page.waitForFunction(() => document.querySelector("[data-ew-stat='claims']").textContent === "3" &&
    document.querySelector("[data-ew-stat='duplicates']").textContent === "1" &&
    document.querySelector("[data-ew-stat='conflicts']").textContent === "1");
  if (Number(await page.locator("[data-ew-result-count]").textContent()) !== 3 ||
      !(await page.locator("[data-ew-status]").textContent()).includes("Nothing was uploaded or approved")) {
    throw new Error("Evidence workbench did not load local unverified review artifacts");
  }
  const triageFixture = {
    schema_version:"1.0", ranking_method:"transparent_rule_based_v1",
    score_is_truth_confidence:false,
    summary:{input_claims:3,automatically_verified:0},
    queue:[
      {claim_id:"claim-test-c",score:99,review_status:"unverified_candidate",related_claim_ids:["claim-test-c"]},
      {claim_id:"claim-test-a",score:75,review_status:"unverified_candidate",related_claim_ids:["claim-test-a","claim-test-b"]}
    ]
  };
  await page.locator("[data-ew-triage]").setInputFiles(artifact("ai-chip-intelligence-triage.json",triageFixture));
  await page.waitForFunction(() => document.querySelector("[data-ew-provenance]").textContent.includes("Sorted by review urgency"));
  if (!(await page.locator("[data-ew-results] .model-support-card").first().textContent()).includes("192 GB")) {
    throw new Error("Evidence Workbench did not sort by triage review priority");
  }
  // PR #99 persistent review state snapshot (all data synthetic and read-only).
  const historyFixture = [
    {claim_id:"claim-test-a",observed_this_run:true,days_since_first_seen:16,
     first_seen_at:"2026-10-29T00:00:00Z",last_seen_at:"2026-11-14T00:00:00Z",
     review_state:"pending",alert_level:"overdue_14d",review_is_factual_verification:false,
     source_url:"https://example.org/vendor-release"},
    {claim_id:"claim-test-b",observed_this_run:true,days_since_first_seen:35,
     first_seen_at:"2026-10-10T00:00:00Z",last_seen_at:"2026-11-14T00:00:00Z",
     review_state:"needs_more_evidence",alert_level:"follow_up_needed",review_is_factual_verification:false,
     source_url:"https://example.org/reprint"},
    {claim_id:"claim-test-c",observed_this_run:true,days_since_first_seen:40,
     first_seen_at:"2026-10-05T00:00:00Z",last_seen_at:"2026-11-14T00:00:00Z",
     review_state:"rejected",alert_level:"handled",review_is_factual_verification:false,
     source_url:"https://example.org/other-report"},
    {claim_id:"claim-test-old",observed_this_run:false,days_since_first_seen:52,
     first_seen_at:"2026-09-23T00:00:00Z",last_seen_at:"2026-11-07T00:00:00Z",
     review_state:"pending",alert_level:"overdue_30d",review_is_factual_verification:false,
     source_url:"https://example.org/old-claim"}
  ];
  const historicalBatchClaim = {
    ...reviewClaims[0],
    claim_id:"claim-test-old",candidate_id:"candidate-test-old",
    statement:"Historical restored Claim: Example accelerator reaches 160 GB HBM per GPU.",
    evidence_quote:"The archived source lists 160 GB HBM per accelerator.",
    source:{url:"https://example.org/historical-source",publisher:"Historical Vendor",
      published_at:"2026-10-01",evidence_scope:"official_vendor_feed_metadata_and_excerpt"}
  };
  const historicalBacklogRow = {
    ...historyFixture[3],claim_snapshot:historicalBatchClaim,
    priority:{score:65,score_factors:{high_impact_topic:18},risk_flags:["vendor_primary_not_independent_corroboration"]}
  };
  const historyJson = {
    schema_version:"1.0",generated_at:"2026-11-14T00:00:00Z",
    observation_state:"cache_persisted",state_is_approval:false,
    summary:{tracked_current_claims:3,tracked_backlog_claims:4,backlog_not_observed_this_run:1,
      unknown_first_seen_if_cache_reset:true,
      review_states:{pending:2,needs_more_evidence:1,rejected:1,accepted_for_evidence_attachment:0}},
    claim_aging:historyFixture,
    aging_backlog:[historyFixture[0],historyFixture[1],historicalBacklogRow],
    queue:[]
  };
  await page.locator("[data-ew-aging]").setInputFiles(artifact("ai-chip-intelligence-review-state.json",historyJson));
  await page.waitForFunction(() => document.querySelector("[data-ew-aging-count='tracked']")?.textContent === "4");
  const reviewBatchFixture = {
    schema_version:"1.0",generated_at:historyJson.generated_at,status:"ready",
    batch_id:"claim-review-smoke",batch_size_limit:25,
    summary:{pending_claims:2,selected_for_this_batch:1},
    policy:{decisions_written:false,factual_verification_performed:false,priority_is_truth_confidence:false},
    items:[{claim_id:"claim-test-old",review_state:"pending",first_seen_at:"2026-09-23T00:00:00Z",
      days_since_first_seen:52,priority_score:65,priority_score_is_truth_confidence:false,
      priority_score_factors:{high_impact_topic:18},risk_flags:["vendor_primary_not_independent_corroboration"],
      claim:historicalBatchClaim}],
    decision_template:{schema_version:"1.0",decisions:[{
      claim_id:"claim-test-old",decision:"",reviewer:"",decided_at:"",notes:""
    }]}
  };
  await page.locator("[data-ew-batch]").setInputFiles(artifact("ai-chip-intelligence-claim-review-batch.json",reviewBatchFixture));
  await page.waitForFunction(() => document.querySelector("[data-ew-stat='claims']")?.textContent === "4");
  if (!(await page.locator("[data-ew-results]").textContent()).includes("Historical restored Claim") ||
      !(await page.locator("[data-ew-historical-list]").textContent()).includes("Historical restored Claim")) {
    throw new Error("Evidence Workbench did not load restored historical Claim details from the bounded batch");
  }
  if (await page.locator("[data-ew-aging-count='fourteen']").textContent() !== "3" ||
      await page.locator("[data-ew-aging-count='thirty']").textContent() !== "2" ||
      !(await page.locator("[data-ew-historical-list]").textContent()).includes("claim-test-old")) {
    throw new Error("Persistent review state dashboard did not show accurate historical backlog");
  }
  await page.locator("[data-ew-age-filter]").selectOption("overdue_30d");
  if (Number(await page.locator("[data-ew-result-count]").textContent()) !== 3) {
    throw new Error("Evidence Review Workbench 30+ day review age filter failed after adding the restored batch Claim");
  }
  await page.locator("[data-ew-age-filter]").selectOption("");
  await page.locator("[data-ew-state-filter]").selectOption("needs_more_evidence");
  if (Number(await page.locator("[data-ew-result-count]").textContent()) !== 1 ||
      !(await page.locator("[data-ew-results]").textContent()).includes("claim-test-b")) {
    throw new Error("Evidence Review Workbench workflow review-state filter failed");
  }
  await page.locator("[data-ew-clear-filters]").click();
  await page.locator("[data-ew-relationship]").selectOption("conflicts");
  if (Number(await page.locator("[data-ew-result-count]").textContent()) !== 2) {
    throw new Error("Evidence Workbench failed reviewer-scoped conflict filter");
  }
  await page.locator("[data-ew-relationship]").selectOption("duplicates");
  if (Number(await page.locator("[data-ew-result-count]").textContent()) !== 2) {
    throw new Error("Evidence Workbench failed exact-text duplicate filter");
  }
  await page.locator("[data-ew-clear-filters]").click();
  await page.locator("[data-ew-search]").fill("192 GB");
  if (Number(await page.locator("[data-ew-result-count]").textContent()) !== 1) {
    throw new Error("Evidence Workbench claim search failed");
  }
  // PR #96 review-decision and Approval Manifest Builder exercise.
  await page.locator("[data-ew-clear-filters]").click();
  await page.locator("[data-ew-ledger]").setInputFiles(artifact("intelligence-review-decisions.json",{
    schema_version:"1.0",decisions:[]
  }));
  await page.locator("[data-ew-review-claim='claim-test-a']").click();
  await page.locator("[data-ew-decision]").selectOption("accepted_for_evidence_attachment");
  await page.locator("[data-ew-reviewer]").fill("ci-synthetic-fixture-not-a-real-reviewer");
  await page.locator("[data-ew-reviewed]").fill("2026-11-14");
  await page.locator("[data-ew-decision-note]").fill("CI synthetic fixture: manual review would be required for a real Claim and exact source.");
  await page.locator("[data-ew-record-decision]").click();
  if (!(await page.locator("[data-ew-decision-status]").textContent()).includes("Decision recorded locally")) {
    throw new Error("Workbench did not record an explicit local review decision");
  }
  const [ledgerDownload] = await Promise.all([
    page.waitForEvent("download"),
    page.locator("[data-ew-export-decisions]").click()
  ]);
  if (ledgerDownload.suggestedFilename() !== "intelligence-review-decisions.json") {
    throw new Error("Workbench downloaded an unexpected decision ledger name");
  }
  const ledgerPath = require("path").join(require("os").tmpdir(), "ai-chip-review-ledger-smoke.json");
  await ledgerDownload.saveAs(ledgerPath);
  const exportedLedger = JSON.parse(require("fs").readFileSync(ledgerPath, "utf8"));
  const ledgerDecision = exportedLedger.decisions.find(item => item.claim_id === "claim-test-a");
  if (Object.keys(exportedLedger).sort().join(",") !== "decisions,schema_version" ||
      Object.keys(ledgerDecision || {}).sort().join(",") !== "claim_id,decided_at,decision,notes,reviewer" ||
      ledgerDecision.decision !== "accepted_for_evidence_attachment" ||
      ledgerDecision.reviewer !== "ci-synthetic-fixture-not-a-real-reviewer" ||
      ledgerDecision.notes.length < 30 || !Number.isFinite(Date.parse(ledgerDecision.decided_at))) {
    throw new Error("Workbench did not export a tracker-compatible human decision ledger");
  }
  require("fs").unlinkSync(ledgerPath);
  const profileFixture = {
    schema_version:"1.0",
    companies:[{id:"test-company",name:"Test Company",evidence:[],claims:[{
      id:"existing-hbm-claim",subject_type:"product",subject_id:"test-gpu",topic:"memory_capacity",
      statement:"Example test card has a synthetic capacity claim.",scope:"Per GPU",
      claim_status:"vendor_reported",value:180,unit:"GB",evidence_ids:[],last_reviewed:"2026-11-14"
    }]}]
  };
  await page.locator("[data-ew-profiles]").setInputFiles(artifact("company-profiles.json", profileFixture));
  await page.locator("[data-ew-company]").selectOption("test-company");
  await page.locator("[data-ew-existing]").selectOption("existing-hbm-claim");
  await page.locator("[data-ew-approval-id]").fill("test-only-approval-2026");
  await page.locator("[data-ew-evidence-id]").fill("test-only-evidence");
  await page.locator("[data-ew-reviewer]").fill("ci-synthetic-fixture-not-a-real-reviewer");
  await page.locator("[data-ew-reviewed]").fill("2026-11-14");
  await page.locator("[data-ew-title]").fill("CI Test source (not a factual datasheet)");
  await page.locator("[data-ew-publisher-input]").fill("Synthetic Test Publisher");
  await page.locator("[data-ew-published]").fill("2026-11-12");
  await page.locator("[data-ew-checked]").fill("2026-11-14");
  await page.locator("[data-ew-evidence-notes]").fill("Synthetic fixture only; this must never enter the production registry.");
  await page.locator("[data-ew-review-notes]").fill("This automated browser fixture tests manifest serialization; it does not represent genuine human review.");
  if (!(await page.locator("[data-ew-export-manifest]").isDisabled())) {
    throw new Error("Workbench enabled approval export without explicit human consent");
  }
  await page.locator("[data-ew-confirm]").check();
  const [approvalDownload] = await Promise.all([
    page.waitForEvent("download"),
    page.locator("[data-ew-export-manifest]").click()
  ]);
  if (approvalDownload.suggestedFilename() !== "test-only-approval-2026.json") {
    throw new Error("Workbench downloaded an unexpected approval file name");
  }
  const approvalPath = require("path").join(require("os").tmpdir(), "ai-chip-manifest-smoke.json");
  await approvalDownload.saveAs(approvalPath);
  const exportedApproval = JSON.parse(require("fs").readFileSync(approvalPath, "utf8"));
  const canonical = object => Array.isArray(object) ? "[" + object.map(canonical).join(",") + "]" :
    object && typeof object === "object" ? "{" + Object.keys(object).sort().map(
      key => JSON.stringify(key) + ":" + canonical(object[key])).join(",") + "}" : JSON.stringify(object);
  const expectedHash = require("crypto").createHash("sha256").update(
    canonical(profileFixture.companies[0].claims[0])).digest("hex");
  if (exportedApproval.expected_claim_sha256 !== expectedHash ||
      exportedApproval.extracted_claim_id !== "claim-test-a" ||
      exportedApproval.evidence.url !== "https://example.org/vendor-release" ||
      exportedApproval.decision !== "approved_evidence_attachment") {
    throw new Error("Approval export mismatched existing Claim SHA256, selected source or approval format");
  }
  if (!(await page.locator("[data-ew-export-manifest]").isDisabled())) {
    throw new Error("Approval confirmation was not cleared after export");
  }
  require("fs").unlinkSync(approvalPath);
  await page.locator("[data-ew-aging]").setInputFiles(artifact("invalid-review-state.json", {
    ...historyJson,
    state_is_approval:true
  }));
  await page.waitForFunction(() => document.querySelector("[data-ew-status]")?.textContent?.includes("Cannot load review artifact"));
  if (!(await page.locator("[data-ew-age-filter]").isDisabled())) {
    throw new Error("Evidence Workbench accepted a forged approval-state snapshot");
  }
  await page.locator("[data-ew-aging]").setInputFiles(artifact("ai-chip-intelligence-review-state.json",historyJson));
  await page.waitForFunction(() => document.querySelector("[data-ew-aging-count='tracked']")?.textContent === "4");
  await page.locator("[data-ew-claims]").setInputFiles(artifact("invalid-claims.json", {
    ...reviewClaimJson, claims:[{...reviewClaims[0], review_status:"verified"}], claim_count:1
  }));
  await page.waitForFunction(() => {
    const status = document.querySelector("[data-ew-status]")?.textContent || "";
    const count = document.querySelector("[data-ew-result-count]")?.textContent || "";
    return status.includes("Cannot load review artifact") && count === "0";
  });
  if (!(await page.locator("[data-ew-status]").textContent()).includes("Cannot load review artifact") ||
      Number(await page.locator("[data-ew-result-count]").textContent()) !== 0) {
    throw new Error("Evidence Workbench did not reject an unsafe verified-status file");
  }
  await page.locator("[data-ew-reset]").click();
  if (!(await page.locator("[data-ew-search]").isDisabled())) {
    throw new Error("Evidence Workbench reset did not clear controls");
  }

  await page.setViewportSize({ width: 390, height: 844 });
  await page.locator("[data-nav-toggle]").click();
  if (await page.locator("[data-nav-toggle]").getAttribute("aria-expanded") !== "true") {
    throw new Error("Mobile nav did not open");
  }
  await page.locator("[data-site-nav] a[href*='workloads']").click();
  if (await page.locator("[data-nav-toggle]").getAttribute("aria-expanded") !== "false") {
    throw new Error("Mobile nav did not close after navigation");
  }

  if (errors.length) throw new Error("Browser errors:\n" + errors.join("\n"));
  console.log("PASS: thirteen routes including Database Integration Workbench, Product Integration Workbench, Intelligence Operations, Evidence Review Workbench, Model Support Explorer, Benchmark Results Explorer, Product Explorer, landscape asset, homepage coverage stats, directory search/group/evidence filters, company profile registry, compatibility/workload/benchmark search, theme toggle and mobile navigation.");
  await browser.close();
})().catch(error => {
  console.error(error);
  process.exit(1);
});
