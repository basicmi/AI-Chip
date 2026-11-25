(() => {
  "use strict";
  const root = document.querySelector("[data-sweep-explorer]");
  if (!root) return;
  const $ = s => root.querySelector(s);
  const selects = ["metric","hardware","model","context"].map(k => $("[data-sweep-"+k+"]"));
  const status = $("[data-sweep-status]"), button = $("[data-sweep-load]");
  const metrics = {
    output_throughput_per_gpu:["tok/s/GPU","throughput","higher"],
    median_interactivity:["tok/s/user","interactivity","higher"],
    median_ttft:["s","latency","lower"],p99_ttft:["s","latency","lower"],
    median_tpot:["s","latency","lower"],p99_tpot:["s","latency","lower"],p99_itl:["s","latency","lower"]
  };
  const stableFields = ["prefill_tp","prefill_ep","prefill_dp_attention","prefill_num_workers",
    "decode_tp","decode_ep","decode_dp_attention","decode_num_workers","offload_mode"];
  const canonical = x => Array.isArray(x) ? "["+x.map(canonical).join(",")+"]" :
    x && typeof x==="object" ? "{"+Object.keys(x).sort().map(k=>JSON.stringify(k)+":"+canonical(x[k])).join(",")+"}" : JSON.stringify(x);
  const present = x => typeof x==="string" && !["","unknown","not reported","n/a","none"].includes(x.trim().toLowerCase());
  const nonempty = x => typeof x==="string" && x.trim().length>0;
  const obj = x => x && typeof x==="object" && !Array.isArray(x);
  const count = x => Number.isFinite(x) && x>=0;
  const positiveInt = x => Number.isInteger(x) && x>0;
  const pick = (x,keys) => Object.fromEntries(keys.map(k=>[k,x[k]??null]));
  let sweeps = [];
  function build(records) {
    const groups = new Map();
    for (const r of records) {
      if (!r || r.source_id!=="inferencex" || r.inferred!==false || r.errors!==0) continue;
      const w=r.workload,s=r.system,sw=r.software,c=r.configuration;
      if (![w,s,sw,c].every(obj) || !["id","benchmark_suite","model","scenario","division","availability","weight_data_types","model_display_name"].every(k=>nonempty(r[k]))) continue;
      if (!present(s.hardware)||!present(sw.recipe_fingerprint)||!nonempty(sw.framework)||
          !["isl","osl","concurrency"].every(k=>positiveInt(w[k])) ||
          !nonempty(w.speculative_method) || typeof w.disaggregated!=="boolean" ||
          !["benchmark_type","precision"].every(k=>w[k]!=null&&w[k]!==""&&w[k]!=="unknown") ||
          !count(s.physical_prefill_gpus)||!count(s.physical_decode_gpus)||typeof s.is_multinode!=="boolean") continue;
      const config=Object.fromEntries(stableFields.filter(k=>Object.hasOwn(c,k)).map(k=>[k,c[k]]));
      if (!Object.keys(config).length || Object.values(config).some(v=>v===null)) continue;
      const workers=(Array.isArray(s.workers)?s.workers:[]).filter(obj).map(x=>pick(x,["role","num_gpus"]));
      workers.sort((a,b)=>{const x=String(a.role??"None"),y=String(b.role??"None"),m=String(a.num_gpus??"None"),n=String(b.num_gpus??"None");return x<y?-1:x>y?1:m<n?-1:m>n?1:0;});
      const context={
        protocol:{profile:"inferencex",...pick(r,["source_id","benchmark_suite","benchmark_version","scenario","division","availability","weight_data_types"]),model:r.model_display_name,raw_model_key:r.model,
          workload:pick(w,["benchmark_type","isl","osl","precision","speculative_method","disaggregated"])},
        hardware:s.hardware,system_boundary:{...pick(r,["system_type"]),...pick(s,["physical_prefill_gpus","physical_decode_gpus","is_multinode"]),worker_roles:workers},
        software:sw,configuration:config,...pick(r,["source_class","evidence_level"])
      };
      for (const [metric,definition] of Object.entries(metrics)) {
        const m=r.normalized_metrics?.[metric];
        if (!obj(m)||!count(m.value)||[m.unit,m.family,m.direction].some((v,i)=>v!==definition[i])) continue;
        const key=canonical({context,metric});
        if (!groups.has(key)) groups.set(key,{context,metric,unit:definition[0],levels:new Map()});
        const levels=groups.get(key).levels;
        if (!levels.has(w.concurrency)) levels.set(w.concurrency,[]);
        levels.get(w.concurrency).push({record_id:r.id,value:m.value,source_url:r.detail_url||r.source_url,publication_date:r.publication_date});
      }
    }
    return [...groups.entries()].filter(([,g])=>g.levels.size>1).sort(([a],[b])=>a<b?-1:a>b?1:0).map(([key,g])=>({
      key,context:g.context,metric:g.metric,unit:g.unit,points:[...g.levels.entries()].sort((a,b)=>a[0]-b[0]).map(([concurrency,observations])=>{
        observations.sort((a,b)=>a.record_id.localeCompare(b.record_id));
        const v=observations.map(o=>o.value).sort((a,b)=>a-b),i=Math.floor(v.length/2);
        return {concurrency,observations,count:v.length,min:v[0],max:v.at(-1),median:v.length%2?v[i]:v[i-1]/2+v[i]/2};
      })
    }));
  }
  function fill(select,values,label) {
    const previous=select.value;
    select.replaceChildren();
    for (const value of values) {const option=document.createElement("option");option.value=value;option.textContent=label?label(value):value;select.append(option);}
    select.disabled=!values.length;
    if(values.includes(previous))select.value=previous;
  }
  const unique = a=>[...new Set(a)].sort();
  function refresh() {
    fill(selects[0],unique(sweeps.map(s=>s.metric)));
    const m=sweeps.filter(s=>s.metric===selects[0].value);
    fill(selects[1],unique(m.map(s=>s.context.hardware)));
    const h=m.filter(s=>s.context.hardware===selects[1].value);
    fill(selects[2],unique(h.map(s=>s.context.protocol.model)));
    const matches=h.filter(s=>s.context.protocol.model===selects[2].value);
    fill(selects[3],matches.map(s=>s.key),key=>{
      const g=matches.find(s=>s.key===key),w=g.context.protocol.workload,b=g.context.system_boundary;
      return "ISL "+w.isl+" / OSL "+w.osl+" · "+w.precision+" · "+g.context.software.framework+" · P/D "+b.physical_prefill_gpus+"/"+b.physical_decode_gpus+" · "+(matches.indexOf(g)+1);
    });
    render(matches.find(s=>s.key===selects[3].value));
  }
  const svg=(tag,attributes={},text)=>{const n=document.createElementNS("http://www.w3.org/2000/svg",tag);for(const [k,v] of Object.entries(attributes))n.setAttribute(k,String(v));if(text!==undefined)n.textContent=text;return n;};
  const fmt=v=>Number(v.toPrecision(6)).toString();
  function render(g) {
    const chart=$("[data-sweep-chart]"),table=$("[data-sweep-table]"),records=$("[data-sweep-records]");
    chart.replaceChildren();table.replaceChildren();records.replaceChildren();$("[data-sweep-details]").textContent="";
    if(!g){$("[data-sweep-description]").textContent="No matching series has two published concurrency levels.";return;}
    $("[data-sweep-description]").textContent=g.context.hardware+" · "+g.context.protocol.model+" · "+g.metric+" ("+g.unit+") · "+g.points.length+" observed levels";
    $("[data-sweep-details]").textContent=JSON.stringify(g.context,null,2);
    const width=720,height=330,left=85,right=25,top=25,bottom=55;
    const xmin=g.points[0].concurrency,xmax=g.points.at(-1).concurrency,ymax=Math.max(...g.points.map(p=>p.max))||1;
    const x=v=>left+(v-xmin)/(xmax-xmin)*(width-left-right),y=v=>height-bottom-v/ymax*(height-top-bottom);
    const plot=svg("svg",{viewBox:"0 0 720 330",role:"img","aria-label":"Published "+g.metric+" observations by concurrency",style:"width:100%;min-width:440px;max-width:900px;color:inherit"});
    for(let i=0;i<=5;i++){const val=ymax*i/5,py=y(val);plot.append(svg("line",{x1:left,x2:width-right,y1:py,y2:py,stroke:"currentColor",opacity:.15}),svg("text",{x:left-8,y:py+4,"text-anchor":"end",fill:"currentColor","font-size":11},fmt(val)));}
    plot.append(svg("line",{x1:left,x2:width-right,y1:y(0),y2:y(0),stroke:"currentColor"}),svg("text",{x:width/2,y:height-8,"text-anchor":"middle",fill:"currentColor","font-size":12},"Concurrency (requests)"));
    const tickStep=Math.ceil(g.points.length/8);
    for(const [i,p] of g.points.entries()){
      const px=x(p.concurrency);
      if(i%tickStep===0||i===g.points.length-1)plot.append(svg("text",{x:px,y:height-bottom+20,"text-anchor":"middle",fill:"currentColor","font-size":11},p.concurrency));
      plot.append(svg("line",{x1:px,x2:px,y1:y(p.min),y2:y(p.max),stroke:"#64748b","stroke-width":2}));
      for(const o of p.observations){const dot=svg("circle",{cx:px,cy:y(o.value),r:3.5,fill:"#2563eb",opacity:.65});dot.append(svg("title",{},o.record_id+": "+o.value+" "+g.unit));plot.append(dot);}
      const py=y(p.median);plot.append(svg("path",{d:"M "+px+" "+(py-5)+" l 5 5 -5 5 -5 -5 Z",fill:"#d97706"}));
      const tr=document.createElement("tr");for(const v of [p.concurrency,p.count,fmt(p.min),fmt(p.median),fmt(p.max)]){const td=document.createElement("td");td.textContent=v;tr.append(td);}table.append(tr);
      for(const o of p.observations){const div=document.createElement("div");div.textContent=p.concurrency+" · "+o.record_id+" · "+fmt(o.value)+" "+g.unit+" · "+(o.publication_date||"Date not reported")+" ";try{const url=new URL(o.source_url);if(["https:","http:"].includes(url.protocol)){const a=document.createElement("a");a.href=url.href;a.textContent="Source ↗";a.rel="noopener noreferrer";a.target="_blank";div.append(a);}}catch{}records.append(div);}
    }
    chart.append(plot);
  }
  for(const s of selects)s.addEventListener("change",refresh);
  button.addEventListener("click",async()=>{
    button.disabled=true;status.textContent="Loading published registry…";
    try{
      const response=await fetch(root.dataset.source);
      if(!response.ok)throw Error("HTTP "+response.status);
      if(!response.body)throw Error("Registry body unavailable");
      // Static registry is a gzip file, not an HTTP content-encoding.
      const buffer=await response.arrayBuffer(),bytes=new Uint8Array(buffer);
      const data=bytes[0]===31&&bytes[1]===139?
        await new Response(new Blob([buffer]).stream().pipeThrough(new DecompressionStream("gzip"))).json():
        JSON.parse(new TextDecoder().decode(buffer));
      if(!Array.isArray(data.records))throw Error("Invalid benchmark registry");
      sweeps=build(data.records);refresh();
      status.textContent="Loaded "+sweeps.length+" matching-context metric series.";
    }catch(e){sweeps=[];refresh();status.textContent="Unable to load registry: "+e.message;button.disabled=false;}
  });
})();
