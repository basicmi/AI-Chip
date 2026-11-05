(() => {
  const root = document.querySelector("[data-benchmark-explorer]");
  if (!root) return;

  const $ = (selector) => root.querySelector(selector);
  const search = $("[data-benchmark-search]");
  const category = $("[data-benchmark-category]");
  const kind = $("[data-benchmark-kind]");
  const cards = $("[data-benchmark-cards]");
  const load = $("[data-benchmark-load]");

  const element = (tag, className, content) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (content !== undefined) node.textContent = content;
    return node;
  };

  const safeUrl = (value) => {
    try {
      const url = new URL(value);
      return ["https:", "http:"].includes(url.protocol) ? url.href : null;
    } catch (_) {
      return null;
    }
  };

  const makeLink = (url, label) => {
    const node = element("a", "benchmark-source-link", label);
    const href = safeUrl(url);
    if (href) {
      node.href = href;
      node.target = "_blank";
      node.rel = "noopener noreferrer";
    } else {
      node.setAttribute("aria-disabled", "true");
    }
    return node;
  };

  const kindLabels = {
    standardized_suite: "Standardized benchmark",
    public_benchmark: "Public result portal",
    ranking: "Published ranking",
    research_benchmark: "Research benchmark",
    measurement_harness: "Measurement tool",
    microbenchmark: "Microbenchmark",
    vendor_tool: "Vendor tool",
    vendor_ecosystem: "Software ecosystem"
  };

  let database;

  const renderCard = (project) => {
    const card = element("article", "benchmark-card");
    const top = element("div", "benchmark-card-top");
    top.append(element("span", "eyebrow", project.category_label));
    top.append(element("span", "benchmark-kind", project.kind_label));
    card.append(top);

    card.append(element("h3", "", project.name));
    card.append(element("p", "benchmark-maintainer", project.maintainer));
    card.append(element("p", "benchmark-description", project.description));

    const metrics = element("div", "benchmark-metrics");
    project.metrics.forEach((metric) => {
      metrics.append(element("span", "compat-tag", metric));
    });
    card.append(metrics);

    card.append(element("p", "benchmark-comparability", project.comparability));

    const links = element("div", "benchmark-links");
    links.append(makeLink(project.official_url, "Official site / docs ↗"));
    if (project.repository_url) {
      links.append(makeLink(project.repository_url, "Repository ↗"));
    }
    if (project.results_url) {
      links.append(makeLink(project.results_url, "Published results ↗"));
    }
    card.append(links);
    return card;
  };

  const render = () => {
    if (!database) return;

    const query = search.value.trim().toLowerCase();
    const selectedCategory = category.value;
    const selectedKind = kind.value;

    const filtered = database.projects.filter((project) => {
      if (selectedCategory && project.category !== selectedCategory) return false;
      if (selectedKind && project.kind !== selectedKind) return false;

      const searchable = [
        project.name,
        project.maintainer,
        project.description,
        project.comparability,
        ...project.metrics
      ].join(" ").toLowerCase();

      return !query || searchable.includes(query);
    });

    cards.replaceChildren(...filtered.map(renderCard));
    $("[data-benchmark-count]").textContent = String(filtered.length);
    $("[data-benchmark-summary]").textContent =
      filtered.length + " of " + database.projects.length + " public resources";
    $("[data-benchmark-empty]").hidden = filtered.length > 0;
  };

  const reset = () => {
    search.value = "";
    category.value = "";
    kind.value = "";
    render();
  };

  search.addEventListener("input", render);
  category.addEventListener("change", render);
  kind.addEventListener("change", render);
  $("[data-benchmark-reset]").addEventListener("click", reset);

  fetch(root.dataset.source)
    .then((response) => {
      if (!response.ok) {
        throw new Error("Benchmark catalogue request failed: " + response.status);
      }
      return response.json();
    })
    .then((data) => {
      if (!Array.isArray(data.projects) || !Array.isArray(data.categories)) {
        throw new Error("Benchmark catalogue has an invalid structure.");
      }

      database = data;
      const categoryLabels = new Map(
        data.categories.map((item) => [item.id, item.label])
      );

      data.projects.forEach((project) => {
        project.category_label = categoryLabels.get(project.category) || project.category;
        project.kind_label = kindLabels[project.kind] || project.kind;
      });

      [...new Set(data.projects.map((project) => project.kind))]
        .sort()
        .forEach((value) => {
          const option = element("option", "", kindLabels[value] || value);
          option.value = value;
          kind.append(option);
        });

      data.categories.forEach((item) => {
        const option = element("option", "", item.label);
        option.value = item.id;
        category.append(option);
      });

      $("[data-benchmark-version]").textContent = data.database_version || "—";
      $("[data-benchmark-reviewed]").textContent = data.last_reviewed || "—";
      $("[data-benchmark-stat='projects']").textContent = data.projects.length;
      $("[data-benchmark-stat='categories']").textContent = data.categories.length;
      $("[data-benchmark-stat='portals']").textContent = data.projects.filter(
        (project) => ["public_benchmark", "ranking"].includes(project.kind)
      ).length;
      $("[data-benchmark-stat='tools']").textContent = data.projects.filter(
        (project) => !["public_benchmark", "ranking"].includes(project.kind)
      ).length;

      load.hidden = true;
      render();
    })
    .catch((error) => {
      load.classList.add("is-error");
      load.textContent = error.message;
    });
  const root=document.querySelector("[data-benchmark-explorer]");
  if(!root)return;
  const $=s=>root.querySelector(s);
  const search=$("[data-benchmark-search]"),category=$("[data-benchmark-category]"),kind=$("[data-benchmark-kind]");
  const cards=$("[data-benchmark-cards]"),load=$("[data-benchmark-load]");
  const el=(tag,cls,text)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n;};
  const safeUrl=value=>{try{const u=new URL(value);return ["https:","http:"].includes(u.protocol)?u.href:null;}catch(_){return null;}};
  const link=(url,label)=>{const n=el("a","benchmark-source-link",label);const href=safeUrl(url);if(href){n.href=href;n.target="_blank";n.rel="noopener noreferrer";}return n;};
  let db;
  const renderCard=p=>{
    const card=el("article","benchmark-card");
    const top=el("div","benchmark-card-top");
    top.append(el("span","eyebrow",p.category_label));
    top.append(el("span","benchmark-kind",p.kind_label));
    card.append(top);
    card.append(el("h3","",p.name));
    card.append(el("p","benchmark-maintainer",p.maintainer));
    card.append(el("p","benchmark-description",p.description));
    const metrics=el("div","benchmark-metrics");
    p.metrics.forEach(m=>metrics.append(el("span","compat-tag",m)));
    card.append(metrics);
    card.append(el("p","benchmark-comparability",p.comparability));
    const links=el("div","benchmark-links");
    links.append(link(p.official_url,"Official site / docs ↗"));
    if(p.repository_url)links.append(link(p.repository_url,"Repository ↗"));
    if(p.results_url)links.append(link(p.results_url,"Published results ↗"));
    card.append(links);
    return card;
  };
  const render=()=>{
    const q=search.value.trim().toLowerCase(),c=category.value,k=kind.value;
    const filtered=db.projects.filter(p=>{
      if(c&&p.category!==c)return false;
      if(k&&p.kind!==k)return false;
      return !q||[p.name,p.maintainer,p.description,p.comparability,...p.metrics].join(" ").toLowerCase().includes(q);
    });
    cards.replaceChildren(...filtered.map(renderCard));
    $("[data-benchmark-count]").textContent=String(filtered.length);
    $("[data-benchmark-summary]").textContent=filtered.length+" of "+db.projects.length+" public resources";
    $("[data-benchmark-empty]").hidden=filtered.length>0;
  };
  const reset=()=>{search.value="";category.value="";kind.value="";render();};
  [search,category,kind].forEach(c=>c.addEventListener(c===search?"input":"change",render));
  $("[data-benchmark-reset]").addEventListener("click",reset);
  fetch(root.dataset.source).then(r=>{if(!r.ok)throw new Error("Catalogue request failed: "+r.status);return r.json();}).then(data=>{
    db=data;
    const categoryMap=new Map(data.categories.map(c=>[c.id,c.label]));
    data.projects.forEach(p=>p.category_label=categoryMap.get(p.category)||p.category);
    const kindLabels={standardized_suite:"Standardized benchmark",public_benchmark:"Public result portal",ranking:"Published ranking",research_benchmark:"Research benchmark",measurement_harness:"Measurement tool",microbenchmark:"Microbenchmark",vendor_tool:"Vendor tool",vendor_ecosystem:"Software ecosystem"};
    const kinds=[...new Set(data.projects.map(p=>p.kind))].sort();
    kinds.forEach(k=>{const o=el("option","",kindLabels[k]||k);o.value=k;kind.append(o);});
    data.projects.forEach(p=>p.kind_label=kindLabels[p.kind]||p.kind);
    data.categories.forEach(c=>{const o=el("option","",c.label);o.value=c.id;category.append(o);});
    $("[data-benchmark-version]").textContent=data.database_version;
    $("[data-benchmark-reviewed]").textContent=data.last_reviewed;
    document.querySelector('[data-benchmark-stat="projects"]').textContent=data.projects.length;
    document.querySelector('[data-benchmark-stat="categories"]').textContent=data.categories.length;
    document.querySelector('[data-benchmark-stat="portals"]').textContent=data.projects.filter(p=>p.kind==="public_benchmark"||p.kind==="ranking").length;
    document.querySelector('[data-benchmark-stat="tools"]').textContent=data.projects.filter(p=>p.kind!=="public_benchmark"&&p.kind!=="ranking").length;
    load.hidden=true;render();
  }).catch(e=>{load.classList.add("is-error");load.textContent=e.message;});
})();
