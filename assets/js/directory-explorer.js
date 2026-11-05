(() => {
  const root = document.querySelector("[data-directory-explorer]");
  if (!root) return;

  const search = root.querySelector("[data-directory-search]");
  const group = root.querySelector("[data-directory-group]");
  const evidenceFilter = root.querySelector("[data-directory-evidence-filter]");
  const count = root.querySelector("[data-directory-count]");
  const summary = root.querySelector("[data-directory-summary]");
  const reviewSummary = root.querySelector("[data-directory-review-summary]");
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
      searchable,
      profile: null,
      referenceCount: 0,
      evidenceCount: 0,
      claimCount: 0,
      freshnessStatus: "not_reviewed"
    };
  });

  const categories = [...new Set(entries.map((entry) => entry.category))]
    .sort((a, b) => a.localeCompare(b));

  const freshnessFor = (profile, policy) => {
    if (!profile || profile.profile_status === "not_reviewed" ||
        !Array.isArray(profile.claims) || profile.claims.length === 0 ||
        !Array.isArray(profile.evidence) || profile.evidence.length === 0) {
      return "not_reviewed";
    }
    if (profile.claims.some((claim) => claim.claim_status === "disputed") ||
        profile.evidence.some((item) => item.review_status === "disputed")) {
      return "disputed";
    }
    const ages = profile.evidence.map((item) => {
      if (!item.checked_at) return Infinity;
      return Math.floor((Date.now() - new Date(item.checked_at + "T00:00:00Z").getTime()) / 86400000);
    });
    const oldestAge = Math.max(...ages);
    if (!Number.isFinite(oldestAge)) return "not_reviewed";
    if (oldestAge > policy.stale_after_days) return "stale";
    if (oldestAge > policy.fresh_within_days) return "review_due";
    return "fresh";
  };

  const finishIndex = (database) => {
    const profiles = Array.isArray(database?.companies) ? database.companies : [];
    const byAnchor = new Map(profiles.map((profile) => [profile.directory_anchor, profile]));
    entries.forEach((entry) => {
      const profile = byAnchor.get(entry.anchor);
      if (!profile) return;
      entry.profile = profile;
      entry.description = profile.summary || entry.description;
      entry.referenceCount = Array.isArray(profile.references) ? profile.references.length : 0;
      entry.evidenceCount = Array.isArray(profile.evidence) ? profile.evidence.length : 0;
      entry.claimCount = Array.isArray(profile.claims) ? profile.claims.length : 0;
      entry.freshnessStatus = freshnessFor(profile, database.freshness_policy || {
        fresh_within_days: 90, stale_after_days: 180
      });
      entry.searchable = [
        entry.searchable,
        profile.display_name,
        profile.summary,
        ...(profile.references || []).map((item) => item.label),
        ...(profile.products || []).map((item) => item.name),
        ...(profile.claims || []).map((item) => item.statement)
      ].join(" ").toLowerCase();
    });

    const totalReferences = profiles.reduce((sum, profile) => sum + (profile.references?.length || 0), 0);
    const totalEvidence = profiles.reduce((sum, profile) => sum + (profile.evidence?.length || 0), 0);
    const totalClaims = profiles.reduce((sum, profile) => sum + (profile.claims?.length || 0), 0);
    const pending = profiles.filter((profile) => profile.profile_status === "not_reviewed").length;

    reviewSummary.textContent = profiles.length + " profiles · " + totalReferences +
      " source links carried over · " + totalEvidence + " audited evidence records · " +
      totalClaims + " structured claims · " + pending + " profiles not yet reviewed.";
    root.dataset.profileRegistryLoaded = "true";
    root.dataset.profileCount = String(profiles.length);
    root.dataset.referenceCount = String(totalReferences);
    root.dataset.evidenceCount = String(totalEvidence);
    root.dataset.claimCount = String(totalClaims);
  };

  categories.forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    group.append(option);
  });

  const render = () => {
    const query = search.value.trim().toLowerCase();
    const selectedGroup = group.value;
    const selectedFreshness = evidenceFilter.value;
    const hasFilter = Boolean(query || selectedGroup || selectedFreshness);

    if (!hasFilter) {
      results.hidden = true;
      empty.hidden = true;
      summary.textContent = entries.length + " companies across " + categories.length +
        " groups. Search company names, chips, architectures or recent updates.";
      return;
    }

    const matches = entries.filter((entry) => {
      if (selectedGroup && entry.category !== selectedGroup) return false;
      if (selectedFreshness && entry.freshnessStatus !== selectedFreshness) return false;
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
      const evidence = document.createElement("span");
      evidence.className = "directory-result-evidence";
      const freshnessLabels = {
        not_reviewed: "Not reviewed",
        fresh: "Fresh evidence",
        review_due: "Review due",
        stale: "Stale evidence",
        disputed: "Disputed evidence"
      };
      evidence.textContent = freshnessLabels[entry.freshnessStatus] + " · " +
        entry.referenceCount + " source links · " + entry.evidenceCount + " evidence records · " +
        entry.claimCount + " audited claims";
      copy.append(categoryLabel, title, description, evidence);
      link.append(copy);
      card.append(link);
      results.append(card);
    });

    results.hidden = matches.length === 0;
    empty.hidden = matches.length > 0;
    const statusLabel = selectedFreshness
      ? " · " + selectedFreshness.replace("_", " ")
      : "";
    summary.textContent = matches.length + " of " + entries.length + " companies" +
      (selectedGroup ? " · " + selectedGroup : "") + statusLabel;
  };

  const initialize = () => {
    count.textContent = entries.length + " companies · " + categories.length + " groups";
    count.dataset.count = String(entries.length);
    count.dataset.ready = "true";
    summary.textContent = entries.length + " companies across " + categories.length +
      " groups. Search company names, chips, architectures or recent updates.";
    search.addEventListener("input", render);
    group.addEventListener("change", render);
    evidenceFilter.addEventListener("change", render);
    reset.addEventListener("click", () => {
      search.value = "";
      group.value = "";
      evidenceFilter.value = "";
      render();
      search.focus();
    });
    render();
  };

  fetch(root.dataset.profileSource)
    .then((response) => {
      if (!response.ok) throw new Error("Company profile registry request failed: " + response.status);
      return response.json();
    })
    .then((database) => {
      if (!Array.isArray(database.companies) || !database.freshness_policy) {
        throw new Error("Company profile registry has an invalid structure.");
      }
      finishIndex(database);
      initialize();
    })
    .catch((error) => {
      reviewSummary.textContent = "Structured company registry unavailable: " + error.message;
      root.dataset.profileRegistryError = "true";
      root.dataset.profileRegistryLoaded = "true";
      initialize();
    });
})();
