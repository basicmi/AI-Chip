(() => {
  const root=document.querySelector("[data-recipe-review]");if(!root)return;
  const $=s=>root.querySelector(s);
  const stableKeys=["prefill_tp","prefill_ep","prefill_dp_attention","prefill_num_workers","decode_tp","decode_ep","decode_dp_attention","decode_num_workers","offload_mode"];
  const axes=["prefill_tp","prefill_ep","decode_tp","decode_ep"];
  const metrics={
    median_ttft:{unit:"s",family:"latency",direction:"lower",phase:"prefill"},
    p99_ttft:{unit:"s",family:"latency",direction:"lower",phase:"prefill"},
    median_tpot:{unit:"s",family:"latency",direction:"lower",phase:"decode"},
    p99_tpot:{unit:"s",family:"latency",direction:"lower",phase:"decode"},
    p99_itl:{unit:"s",family:"latency",direction:"lower",phase:"decode"},
    output_throughput_per_gpu:{unit:"tok/s/GPU",family:"throughput",direction:"higher",phase:"decode"}
  };
  const present=v=>v!==null&&v!==undefined&&!(typeof v==="string"&&["","unknown","not reported","n/a","none"].includes(v.trim().toLowerCase()));
  const positive=v=>typeof v==="number"&&Number.isFinite(v)&&v>0&&Number.isInteger(v);
  const canonical=v=>JSON.stringify(v,Object.keys(v||{}).sort());
  const stableString=v=>{if(Array.isArray(v))return "["+v.map(stableString).join(",")+"]";if(v&&typeof v==="object")return "{"+Object.keys(v).sort().map(k=>JSON.stringify(k)+":"+stableString(v[k])).join(",")+"}";return JSON.stringify(v);};
  const make=(tag,cls,value)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(value!==undefined)n.textContent=String(value);return n;};
  const fmt=v=>new Intl.NumberFormat("en-US",{maximumFractionDigits:4}).format(v);
  let groups=[];
  const metricValue=(r,key)=>{const m=r.normalized_metrics?.[key],d=metrics[key];return m&&typeof m.value==="number"&&Number.isFinite(m.value)&&m.value>=0&&m.unit===d.unit&&m.family===d.family&&m.direction===d.direction?m.value:null;};
  const recordContext=(r,axis)=>{
    const w=r.workload||{},s=r.system||{},sw=r.software||{},config=r.configuration||{};
    const phase=axis.split("_")[0],rest={};
    stableKeys.filter(k=>k!==axis).forEach(k=>{if(Object.prototype.hasOwnProperty.call(config,k))rest[k]=config[k];});
    if(!Object.keys(rest).length||Object.values(rest).some(v=>v===null||v===undefined))return null;
    if(r.inferred!==false||r.errors!==0||!present(r.id)||!present(r.model)||!present(r.benchmark_suite)||!present(r.scenario)||!present(r.division)||!present(r.availability)||!present(r.weight_data_types))return null;
    if(!present(s.hardware)||!present(sw.framework)||!positive(s["physical_"+phase+"_gpus"]))return null;
    if(!["benchmark_type","isl","osl","concurrency","precision","speculative_method"].every(k=>present(w[k]))||typeof w.disaggregated!=="boolean")return null;
    if(typeof s.is_multinode!=="boolean"||!present(r.system_type)||!present(r.source_class)||!present(r.evidence_level))return null;
    const swRest={};Object.keys(sw).filter(k=>k!=="recipe_fingerprint").sort().forEach(k=>swRest[k]=sw[k]);
    return {protocol:{benchmark_suite:r.benchmark_suite,benchmark_version:r.benchmark_version??null,model:r.model,scenario:r.scenario,division:r.division,availability:r.availability,weight_data_types:r.weight_data_types,workload:w},hardware:s.hardware,system_type:r.system_type,is_multinode:s.is_multinode,workers:(s.workers||[]).map(x=>x.role).filter(Boolean).sort(),software:swRest,other_configuration:rest,source_class:r.source_class,evidence_level:r.evidence_level};
  };
  const build=records=>{
    const buckets=new Map();
    records.filter(r=>r.source_id==="inferencex").forEach(r=>{
      axes.forEach(axis=>{
        const phase=axis.split("_")[0],cfg=r.configuration||{},degree=cfg[axis];
        if(!positive(degree))return;
        const context=recordContext(r,axis);if(!context)return;
        Object.entries(metrics).filter(([,d])=>d.phase===phase).forEach(([metric,def])=>{
          const value=metricValue(r,metric);if(value===null)return;
          const key=axis+"|"+metric+"|"+stableString(context);
          if(!buckets.has(key))buckets.set(key,{axis,metric,context,levels:new Map()});
          const group=buckets.get(key);if(!group.levels.has(degree))group.levels.set(degree,[]);
          group.levels.get(degree).push({id:r.id,degree,fingerprint:present(r.software?.recipe_fingerprint)?String(r.software.recipe_fingerprint):null,value,unit:def.unit,source:r.detail_url||r.source_url||null,date:r.publication_date||null,model:r.model_display_name||r.model,hardware:r.system?.hardware,configuration:cfg});
        });
      });
    });
    return [...buckets.values()].filter(g=>{
      if(g.levels.size<2)return false;
      const obs=[...g.levels.values()].flat(),fps=new Set(obs.map(x=>x.fingerprint));
      return fps.size>1||fps.has(null);
    }).map(g=>{
      const observations=[...g.levels.entries()].sort((a,b)=>a[0]-b[0]).flatMap(([,rows])=>rows.sort((a,b)=>a.id.localeCompare(b.id)));
      const fingerprints=new Set(observations.map(x=>x.fingerprint));
      return {...g,observations,reasons:[...(fingerprints.has(null)?["Missing fingerprint"]:[]),...(fingerprints.size-(fingerprints.has(null)?1:0)>1?["Different fingerprints"]:[])]};
    }).sort((a,b)=>a.axis.localeCompare(b.axis)||a.metric.localeCompare(b.metric)||a.observations[0].model.localeCompare(b.observations[0].model));
  };
  const render=()=>{
    const axis=$("[data-rr-axis]").value,metric=$("[data-rr-metric]").value,q=$("[data-rr-search]").value.trim().toLowerCase();
    const visible=groups.filter(g=>(!axis||g.axis===axis)&&(!metric||g.metric===metric)&&(!q||[g.observations[0].model,g.observations[0].hardware,g.axis,g.metric,...g.observations.flatMap(x=>[x.id,x.fingerprint||"missing"])].join(" ").toLowerCase().includes(q)));
    const host=$("[data-rr-groups]");host.replaceChildren();
    visible.slice(0,100).forEach(g=>{
      const card=make("article","rr-group");
      const head=make("div","rr-group-head");const title=make("div","");
      title.append(make("p","rr-kicker",g.axis.replace("_"," ").toUpperCase()+" · "+g.metric.replaceAll("_"," ")),make("h3","",g.observations[0].model),make("p","rr-context",g.observations[0].hardware+" · "+g.observations.length+" observations · "+g.levels.size+" degrees"));
      const flags=make("div","rr-flags");g.reasons.forEach(reason=>flags.append(make("span","rr-flag",reason)));
      head.append(title,flags);card.append(head);
      const table=make("div","rr-table-wrap"),t=document.createElement("table");t.className="rr-table";
      const thead=document.createElement("thead"),hr=document.createElement("tr");["Degree","Record","Recipe fingerprint","Observed value","Other configuration","Source"].forEach(label=>hr.append(make("th","",label)));thead.append(hr);t.append(thead);
      const tbody=document.createElement("tbody");
      g.observations.forEach(o=>{
        const tr=document.createElement("tr");tr.append(make("td","",o.degree),make("td","",o.id),make("td","rr-fingerprint",o.fingerprint||"Not reported"),make("td","",fmt(o.value)+" "+o.unit));
        const other=Object.fromEntries(Object.entries(o.configuration||{}).filter(([k])=>!["workflow_run_id","run_id","job_id"].includes(k)));
        tr.append(make("td","rr-config",stableString(other)));
        const source=make("td","");if(o.source){try{const u=new URL(o.source);if(["https:","http:"].includes(u.protocol)){const a=make("a","","Open ↗");a.href=u.href;a.target="_blank";a.rel="noopener noreferrer";source.append(a);}}catch(_){}}
        tr.append(source);tbody.append(tr);
      });t.append(tbody);table.append(t);card.append(table);
      card.append(make("p","rr-note","Review each source and full execution recipe. No equivalence is approved or inferred by this page."));
      host.append(card);
    });
    $("[data-rr-empty]").hidden=visible.length!==0;
    $("[data-rr-status]").textContent="Showing "+Math.min(visible.length,100)+" of "+visible.length+" candidate groups. Candidate groups are metric-level and may overlap.";
  };
  const load=async()=>{
    const response=await fetch(root.dataset.source,{cache:"no-cache"});if(!response.ok)throw new Error("Registry request failed: HTTP "+response.status);
    const bytes=await response.arrayBuffer(),gz=bytes.length>1&&new Uint8Array(bytes)[0]===31&&new Uint8Array(bytes)[1]===139;
    if(gz){if(typeof DecompressionStream!=="function")throw new Error("This browser cannot decompress the benchmark registry.");return new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream("gzip"))).json();}
    return JSON.parse(new TextDecoder().decode(bytes));
  };
  Object.entries(metrics).forEach(([key,d])=>{const o=document.createElement("option");o.value=key;o.textContent=key.replaceAll("_"," ")+" ("+d.unit+")";$("[data-rr-metric]").append(o);});
  ["change"].forEach(event=>{$("[data-rr-axis]").addEventListener(event,render);$("[data-rr-metric]").addEventListener(event,render);});
  $("[data-rr-search]").addEventListener("input",render);
  load().then(data=>{
    if(!Array.isArray(data.records))throw new Error("Registry has no records array.");
    groups=build(data.records);
    const observations=groups.reduce((n,g)=>n+g.observations.length,0);
    const missing=groups.filter(g=>g.reasons.includes("Missing fingerprint")).length,different=groups.filter(g=>g.reasons.includes("Different fingerprints")).length;
    $("[data-rr-stat='groups']").textContent=fmt(groups.length);$("[data-rr-stat='observations']").textContent=fmt(observations);$("[data-rr-stat='missing']").textContent=fmt(missing);$("[data-rr-stat='different']").textContent=fmt(different);
    $("[data-rr-load]").hidden=true;render();
  }).catch(error=>{$("[data-rr-load]").hidden=true;const box=$("[data-rr-error]");box.hidden=false;box.textContent=error.stack||error.message;});
})();
