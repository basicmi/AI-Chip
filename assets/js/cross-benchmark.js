(() => {
  const root=document.querySelector("[data-cross-benchmark]");if(!root)return;
  const $=s=>root.querySelector(s);
  const valid=v=>v!==null&&v!==undefined&&!(typeof v==="string"&&["","unknown","not reported","n/a","none"].includes(v.trim().toLowerCase()));
  const stable=v=>{if(Array.isArray(v))return "["+v.map(stable).join(",")+"]";if(v&&typeof v==="object")return "{"+Object.keys(v).sort().map(k=>JSON.stringify(k)+":"+stable(v[k])).join(",")+"}";return JSON.stringify(v);};
  const make=(tag,cls,value)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(value!==undefined)n.textContent=String(value);return n;};
  const fmt=n=>new Intl.NumberFormat("en-US").format(n);
  let definitions=[],candidates=[],selected=null;
  const definitionKey=d=>stable({suite:d.suite,version:d.version,key:d.key,unit:d.unit,family:d.family,direction:d.direction});
  const metricDefinitions=records=>{
    const map=new Map();
    records.forEach(r=>{
      const suite=r.benchmark_suite;if(!valid(suite))return;
      const metrics=r.normalized_metrics&&typeof r.normalized_metrics==="object"?r.normalized_metrics:{};
      Object.entries(metrics).forEach(([key,m])=>{
        if(!m||typeof m!=="object"||typeof m.value!=="number"||!Number.isFinite(m.value))return;
        if(!valid(m.unit)||!valid(m.family)||!["higher","lower","context","unspecified"].includes(m.direction))return;
        if(m.family==="suite_scalar"||m.direction==="unspecified")return;
        const d={suite,version:valid(r.benchmark_version)?String(r.benchmark_version):"Not reported",key,unit:m.unit,family:m.family,direction:m.direction,label:valid(m.label)?m.label:key,sourceMetric:valid(m.source_metric)?m.source_metric:"Not reported",sourceId:r.source_id||"unknown",sourceClass:r.source_class||"unknown",evidenceLevel:r.evidence_level||"unknown",count:0,records:[]};
        const id=definitionKey(d);if(!map.has(id))map.set(id,d);
        const target=map.get(id);target.count++;
        if(target.records.length<5)target.records.push({id:r.id,url:r.detail_url||r.source_url||null,model:r.model_display_name||r.model||"Not reported",hardware:r.system?.hardware||r.system?.accelerator_model||r.product_id||"Not reported",sourceId:r.source_id||"unknown",sourceClass:r.source_class||"unknown",evidenceLevel:r.evidence_level||"unknown",sourceMetric:valid(m.source_metric)?m.source_metric:"Not reported",label:valid(m.label)?m.label:key});
      });
    });
    return [...map.values()].sort((a,b)=>a.family.localeCompare(b.family)||a.key.localeCompare(b.key)||a.suite.localeCompare(b.suite));
  };
  const classify=(a,b)=>{
    if(a.key===b.key&&a.unit===b.unit&&a.family===b.family&&a.direction===b.direction)return "same_signature";
    if(a.unit===b.unit)return "same_dimension";
    return "unit_review";
  };
  const buildCandidates=defs=>{
    const result=[];
    for(let i=0;i<defs.length;i++)for(let j=i+1;j<defs.length;j++){
      const a=defs[i],b=defs[j];if(a.suite===b.suite)continue;
      if(a.family!==b.family||a.direction!==b.direction)continue;
      result.push({id:definitionKey(a)+"||"+definitionKey(b),a,b,relation:classify(a,b),suites:[a.suite,b.suite]});
    }
    const rank={same_signature:0,same_dimension:1,unit_review:2};
    return result.sort((x,y)=>rank[x.relation]-rank[y.relation]||x.a.family.localeCompare(y.a.family)||x.a.key.localeCompare(y.a.key)||x.a.suite.localeCompare(y.a.suite));
  };
  const relationLabel=r=>({same_signature:"Same normalized signature",same_dimension:"Same family, unit and direction",unit_review:"Same family and direction; unit differs"})[r];
  const inspect=d=>{
    selected=d;const host=$("[data-cb-inspector]");host.replaceChildren();
    const head=make("div","cb-inspector-head");head.append(make("p","cb-kicker",d.suite+" · "+d.version),make("h3","",d.label),make("p","cb-context",d.key+" · "+d.family+" · "+d.unit+" · "+d.direction+" is better"));
    const meta=make("dl","cb-definition-meta");
    [["Benchmark suite",d.suite],["Version",d.version],["Normalized key",d.key],["Source metric",d.sourceMetric],["Unit",d.unit],["Family",d.family],["Optimization direction",d.direction],["Source ID",d.sourceId],["Source class",d.sourceClass],["Evidence level",d.evidenceLevel],["Registry observations",d.count]].forEach(([k,v])=>{meta.append(make("dt","",k),make("dd","",v));});
    const records=make("div","cb-source-list");records.append(make("h4","","Representative source-linked observations"));
    d.records.forEach(r=>{const row=make("div","cb-source-row");const info=make("div","");info.append(make("strong","",r.id||"Unknown record"),make("span","",r.model+" · "+r.hardware+" · "+r.sourceId+" · "+r.sourceClass));row.append(info);if(r.url){try{const u=new URL(r.url);if(["https:","http:"].includes(u.protocol)){const a=make("a","","Open source ↗");a.href=u.href;a.target="_blank";a.rel="noopener noreferrer";row.append(a);}}catch(_){}}records.append(row);});
    host.append(head,meta,records);
  };
  const render=()=>{
    const relation=$("[data-cb-relation]").value,family=$("[data-cb-family]").value,q=$("[data-cb-search]").value.trim().toLowerCase();
    const shown=candidates.filter(c=>(!relation||c.relation===relation)&&(!family||c.a.family===family)&&(!q||[c.a.suite,c.b.suite,c.a.key,c.b.key,c.a.label,c.b.label,c.a.sourceMetric,c.b.sourceMetric,c.a.sourceId,c.b.sourceId].join(" ").toLowerCase().includes(q)));
    const host=$("[data-cb-candidates]");host.replaceChildren();
    shown.slice(0,150).forEach(c=>{
      const card=make("article","cb-candidate");
      const top=make("div","cb-candidate-top");top.append(make("span","cb-relation",relationLabel(c.relation)),make("span","cb-family",c.a.family));
      const sides=make("div","cb-pair");
      [c.a,c.b].forEach(d=>{const side=make("div","cb-side");side.append(make("strong","",d.suite),make("span","",d.label+" · "+d.key),make("small","",d.unit+" · "+d.direction),make("small","",d.count+" registry observations"));const button=make("button","cb-inspect-button","Inspect definition ↗");button.type="button";button.addEventListener("click",()=>inspect(d));side.append(button);sides.append(side);});
      const footer=make("p","cb-warning",c.relation==="unit_review"?"Unit conversion has not been applied. Review the metric definition before considering any conversion.":"Metadata alignment is only a candidate mapping; workload and measurement semantics still require source review.");
      card.append(top,sides,footer);host.append(card);
    });
    $("[data-cb-empty]").hidden=shown.length!==0;
    textStatus("Showing "+Math.min(shown.length,150)+" of "+shown.length+" cross-suite candidates. "+definitions.length+" distinct suite/metric definitions were discovered.");
  };
  const textStatus=value=>{const node=$("[data-cb-status]");if(node)node.textContent=value;};
  const load=async()=>{
    const response=await fetch(root.dataset.source,{cache:"no-cache"});if(!response.ok)throw new Error("Registry request failed: HTTP "+response.status);
    const bytes=await response.arrayBuffer(),gz=bytes.length>1&&new Uint8Array(bytes)[0]===31&&new Uint8Array(bytes)[1]===139;
    if(gz){if(typeof DecompressionStream!=="function")throw new Error("This browser cannot decompress the benchmark registry.");return new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream("gzip"))).json();}
    return JSON.parse(new TextDecoder().decode(bytes));
  };
  ["change"].forEach(e=>{$("[data-cb-relation]").addEventListener(e,render);$("[data-cb-family]").addEventListener(e,render);});
  $("[data-cb-search]").addEventListener("input",render);
  load().then(data=>{
    if(!Array.isArray(data.records))throw new Error("Registry has no records array.");
    definitions=metricDefinitions(data.records);candidates=buildCandidates(definitions);
    const suites=new Set(definitions.map(d=>d.suite));
    const observations=definitions.reduce((n,d)=>n+d.count,0);
    [["suites",suites.size],["definitions",definitions.length],["candidates",candidates.length],["observations",observations]].forEach(([k,v])=>{$("[data-cb-stat='"+k+"']").textContent=fmt(v);});
    const familySelect=$("[data-cb-family]");[...new Set(definitions.map(d=>d.family))].sort().forEach(v=>{const o=document.createElement("option");o.value=v;o.textContent=v;familySelect.append(o);});
    $("[data-cb-load]").hidden=true;render();
  }).catch(error=>{$("[data-cb-load]").hidden=true;const box=$("[data-cb-error]");box.hidden=false;box.textContent=error.stack||error.message;});
})();
