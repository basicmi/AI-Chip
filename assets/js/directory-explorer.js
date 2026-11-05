(() => {
  const root = document.querySelector("[data-directory-explorer]");
  if (!root) return;

  const search = root.querySelector("[data-directory-search]");
  const group = root.querySelector("[data-directory-group]");
  const count = root.querySelector("[data-directory-count]");
  const summary = root.querySelector("[data-directory-summary]");
  const results = root.querySelector("[data-directory-results]");
  const empty = root.querySelector("[data-directory-empty]");
  const reset = root.querySelector("[data-directory-reset]");
  const vendorTitles = [...document.querySelectorAll(".vendor-title")];
  const sectionHeadings = [...document.querySelectorAll(".section-title h2")];

  const categoryFor = (title) => {
    let category = "Other";
    sectionHeadings.forEach((heading) => {
      if (heading.compareDocumentPosition(title) & Node.DOCUMENT_POSITION_FOLLOWING) {
        category = heading.textContent.trim().replace(/^[IVXLCDM]+\.\s*/, "");
      }
    });
    return category;
  };

  const entries = vendorTitles.map((title, index) => {
    const bodyNodes = [];
    let node = title.nextElementSibling;
    const nextTitle = vendorTitles[index + 1] || null;
    while (node && node !== nextTitle && !node.matches(".section-title")) {
      bodyNodes.push(node);
      node = node.nextElementSibling;
    }

    let previous = title.previousElementSibling;
    let logo = null;
    let anchor = "";
    while (previous && !previous.matches(".section-title") && !previous.matches(".vendor-title")) {
      if (!logo && previous.matches(".vendor-logo")) logo = previous.querySelector("img");
      if (previous.matches("a[name], a[id]")) {
        anchor = previous.getAttribute("name") || previous.id;
        break;
      }
      previous = previous.previousElementSibling;
    }

    const name = title.querySelector("h3")?.textContent.trim() || "Unnamed company";
    const category = categoryFor(title);
    const descriptionNode = bodyNodes.find((item) => item.matches(".vendor-blurb")) ||
      bodyNodes.find((item) => item.matches("p"));
    const description = descriptionNode?.textContent.trim() || "";
    const searchable = [name, category, ...bodyNodes.map((item) => item.textContent || "")]
      .join(" ")
      .toLowerCase();

    return {
      name,
      category,
      anchor,
      logoSrc: logo?.getAttribute("src") || "",
      logoAlt: logo?.getAttribute("alt") || name,
      description,
      searchable
    };
  });

  const categories = [...new Set(entries.map((entry) => entry.category))]
    .sort((a, b) => a.localeCompare(b));
  categories.forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    group.append(option);
  });

  count.textContent = entries.length + " companies · " + categories.length + " groups";
  count.dataset.count = String(entries.length);
  count.dataset.ready = "true";
  summary.textContent = entries.length + " companies across " + categories.length +
    " groups. Search company names, chips, architectures or recent updates.";

  const render = () => {
    const query = search.value.trim().toLowerCase();
    const selectedGroup = group.value;
    if (!query && !selectedGroup) {
      results.hidden = true;
      empty.hidden = true;
      summary.textContent = entries.length + " companies across " + categories.length +
        " groups. Search company names, chips, architectures or recent updates.";
      return;
    }

    const matches = entries.filter((entry) => {
      if (selectedGroup && entry.category !== selectedGroup) return false;
      return !query || entry.searchable.includes(query);
    });

    results.replaceChildren();
    matches.forEach((entry) => {
      const card = document.createElement("article");
      card.className = "directory-result-card";
      const link = document.createElement(entry.anchor ? "a" : "div");
      link.className = "directory-result-link";
      if (entry.anchor) link.href = "#" + entry.anchor;

      if (entry.logoSrc) {
        const image = document.createElement("img");
        image.className = "directory-result-logo";
        image.src = entry.logoSrc;
        image.alt = entry.logoAlt;
        image.loading = "lazy";
        image.decoding = "async";
        link.append(image);
      }

      const copy = document.createElement("div");
      copy.className = "directory-result-copy";
      const categoryLabel = document.createElement("span");
      categoryLabel.className = "directory-result-group";
      categoryLabel.textContent = entry.category;
      const title = document.createElement("h3");
      title.className = "directory-result-title";
      title.textContent = entry.name;
      const description = document.createElement("p");
      description.className = "directory-result-description";
      const text = entry.description;
      description.textContent = text.length > 190 ? text.slice(0, 187) + "…" : text;
      copy.append(categoryLabel, title, description);
      link.append(copy);
      card.append(link);
      results.append(card);
    });

    results.hidden = matches.length === 0;
    empty.hidden = matches.length > 0;
    summary.textContent = matches.length + " of " + entries.length + " companies" +
      (selectedGroup ? " · " + selectedGroup : "");
  };

  search.addEventListener("input", render);
  group.addEventListener("change", render);
  reset.addEventListener("click", () => {
    search.value = "";
    group.value = "";
    render();
    search.focus();
  });
})();
