(() => {
  "use strict";
  const root = document.querySelector("[data-evidence-workbench]");
  if (!root) return;
  const $ = selector => root.querySelector(selector);
  const ui = {
    selected:$("[data-ew-selected]"), decision:$("[data-ew-decision]"),
    decisionNote:$("[data-ew-decision-note]"), decisionStatus:$("[data-ew-decision-status]"),
    exportDecisions:$("[data-ew-export-decisions]"), profiles:$("[data-ew-profiles]"),
    company:$("[data-ew-company]"), existing:$("[data-ew-existing]"),
    approvalId:$("[data-ew-approval-id]"), evidenceId:$("[data-ew-evidence-id]"),
    reviewer:$("[data-ew-reviewer]"), reviewed:$("[data-ew-reviewed]"),
    title:$("[data-ew-title]"), publisher:$("[data-ew-publisher-input]"),
    sourceType:$("[data-ew-source-type]"), independence:$("[data-ew-independence]"),
    published:$("[data-ew-published]"), checked:$("[data-ew-checked]"),
    evidenceNotes:$("[data-ew-evidence-notes]"), reviewNotes:$("[data-ew-review-notes]"),
    confirm:$("[data-ew-confirm]"), approvalStatus:$("[data-ew-approval-status]"),
    exportManifest:$("[data-ew-export-manifest]")
  };
  const SLUG = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
  const choices = new Set(["needs_more_evidence", "rejected", "accepted_for_evidence_attachment"]);
  let selected = null, profiles = null;
  const decisions = new Map();
  const html = (tag, label, value) => {
    const el = document.createElement(tag);
    el.textContent = label;
    if (value !== undefined) el.value = value;
    return el;
  };
  const validDate = value => {
    if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
    const parsed = new Date(value + "T00:00:00Z");
    return Number.isFinite(parsed.valueOf()) && parsed.toISOString().slice(0, 10) === value;
  };
  const canonical = value => {
    if (Array.isArray(value)) return "[" + value.map(canonical).join(",") + "]";
    if (value && typeof value === "object") {
      return "{" + Object.keys(value).sort().map(key => JSON.stringify(key) + ":" + canonical(value[key])).join(",") + "}";
    }
    return JSON.stringify(value);
  };
  const sha256 = async value => {
    if (!window.crypto?.subtle) throw new Error("Secure browser context required for SHA256.");
    const buffer = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(canonical(value)));
    return [...new Uint8Array(buffer)].map(x => x.toString(16).padStart(2, "0")).join("");
  };
  const saveJson = (name, object) => {
    const payload = new Blob([JSON.stringify(object, null, 2) + "\n"], {type:"application/json"});
    const url = URL.createObjectURL(payload);
    const anchor = html("a", "");
    anchor.href = url;
    anchor.download = name;
    document.body.append(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 3000);
  };
  const currentCompany = () => profiles?.companies.find(x => x.id === ui.company.value);
  const currentClaim = () => currentCompany()?.claims.find(x => x.id === ui.existing.value);
  const message = (text, error = false) => {
    ui.approvalStatus.textContent = text;
    ui.approvalStatus.classList.toggle("is-error", error);
  };
  const clearApprovalConsent = () => {
    ui.confirm.checked = false;
    ui.exportManifest.disabled = true;
  };
  const updateAvailability = () => {
    const enabled = !!selected && ui.decision.value === "accepted_for_evidence_attachment";
    ui.exportManifest.disabled = !enabled || !profiles || !ui.confirm.checked;
    if (!selected) message("Select a Claim above before preparing a manifest.");
    else if (!enabled) message("A local decision of 'Accept for evidence attachment review' is required.");
    else if (!profiles) message("Load the current company-profiles.json to select an existing Claim.");
    else if (!ui.confirm.checked) message("Explicitly confirm original-source and existing-Claim human review before export.");
    else message("Ready to validate the completed manifest form. Export will fail closed on missing or conflicting fields.");
  };
  const fillCompanyList = () => {
    ui.company.replaceChildren(html("option", "Select existing company", ""));
    if (profiles) {
      for (const company of profiles.companies) ui.company.append(html("option", company.name || company.id, company.id));
    }
    ui.company.disabled = !profiles;
    fillClaims();
  };
  const fillClaims = () => {
    ui.existing.replaceChildren(html("option", "Select existing Claim", ""));
    const company = currentCompany();
    if (company) {
      for (const claim of company.claims) ui.existing.append(html("option", claim.id + " · " + claim.statement.slice(0, 75), claim.id));
    }
    ui.existing.disabled = !company;
  };
  const resetReview = () => {
    selected = null;
    decisions.clear();
    ui.decision.value = "";
    ui.decision.disabled = true;
    ui.decisionNote.value = "";
    ui.decisionNote.disabled = true;
    ui.selected.textContent = "No Claim selected. Use “Review this claim” in a card above.";
    ui.decisionStatus.textContent = "No review decision recorded. Decisions remain in this browser session.";
    ui.exportDecisions.disabled = true;
    clearApprovalConsent();
    updateAvailability();
  };
  root.addEventListener("ew-clear-review", resetReview);
  root.addEventListener("ew-select-claim", event => {
    selected = event.detail?.claim || null;
    if (!selected || selected.review_status !== "unverified_candidate") {
      resetReview();
      return;
    }
    ui.selected.textContent = "Selected " + selected.claim_id + ": " + selected.statement;
    const previous = decisions.get(selected.claim_id);
    ui.decision.disabled = false;
    ui.decisionNote.disabled = false;
    ui.decision.value = previous?.decision || "";
    ui.decisionNote.value = previous?.notes || "";
    clearApprovalConsent();
    updateAvailability();
  });
  ui.decision.addEventListener("change", () => {
    clearApprovalConsent();
    updateAvailability();
  });
  ui.decisionNote.addEventListener("input", clearApprovalConsent);
  const saveDecision = () => {
    if (!selected || !choices.has(ui.decision.value)) return;
    const notes = ui.decisionNote.value.trim();
    if (notes.length < 30) {
      ui.decisionStatus.textContent = "Please write at least 30 characters of review notes.";
      return;
    }
    decisions.set(selected.claim_id, {
      claim_id:selected.claim_id, decision:ui.decision.value,
      notes, original_source_url:selected.source.url,
      decision_kind:"local_reviewer_draft_not_formal_approval"
    });
    ui.exportDecisions.disabled = false;
    ui.decisionStatus.textContent = "Local decision recorded for " + selected.claim_id +
      ". Decisions can be exported but are not formal approvals.";
    clearApprovalConsent();
    updateAvailability();
  };
  const record = html("button", "Record local decision");
  record.type = "button";
  record.dataset.ewRecordDecision = "";
  record.className = "text-button";
  ui.decisionStatus.before(record);
  record.addEventListener("click", saveDecision);
  ui.exportDecisions.addEventListener("click", () => {
    saveJson("ai-chip-local-review-decisions.json", {
      schema_version:"1.0", status:"local_draft_only",
      decisions:[...decisions.values()]
    });
  });
  ui.profiles.addEventListener("change", async () => {
    profiles = null;
    clearApprovalConsent();
    try {
      const file = ui.profiles.files[0];
      if (!file || file.size > 12 * 1024 * 1024) throw new Error("Choose a company-profiles JSON smaller than 12 MiB.");
      const data = JSON.parse(await file.text());
      if (!Array.isArray(data.companies) || !data.schema_version ||
          data.companies.some(c => !SLUG.test(c.id) || !Array.isArray(c.claims) ||
            !Array.isArray(c.evidence) || c.claims.some(x => !SLUG.test(x.id)))) {
        throw new Error("Invalid company profile structure.");
      }
      profiles = data;
      message("Company registry loaded locally. Select an existing company and Claim.");
    } catch (error) {
      message("Cannot load company profile: " + error.message, true);
    }
    fillCompanyList();
    updateAvailability();
  });
  ui.company.addEventListener("change", () => { fillClaims(); clearApprovalConsent(); updateAvailability(); });
  ui.existing.addEventListener("change", () => { clearApprovalConsent(); updateAvailability(); });
  ui.confirm.addEventListener("change", updateAvailability);
  const inputs = [ui.approvalId, ui.evidenceId, ui.reviewer, ui.reviewed, ui.title,
    ui.publisher, ui.sourceType, ui.independence, ui.published, ui.checked,
    ui.evidenceNotes, ui.reviewNotes];
  inputs.forEach(el => el.addEventListener("input", clearApprovalConsent));
  ui.exportManifest.addEventListener("click", async () => {
    try {
      const local = selected && decisions.get(selected.claim_id);
      if (!local || local.decision !== "accepted_for_evidence_attachment" ||
          ui.decision.value !== "accepted_for_evidence_attachment" || !ui.confirm.checked) {
        throw new Error("Record an accepted local decision and explicitly confirm human review.");
      }
      const company = currentCompany(), claim = currentClaim();
      if (!company || !claim || !selected) throw new Error("Select a real company and existing Claim.");
      const approvalId = ui.approvalId.value.trim(), evidenceId = ui.evidenceId.value.trim();
      if (!SLUG.test(approvalId) || !SLUG.test(evidenceId) ||
          !SLUG.test(selected.claim_id)) throw new Error("Approval, evidence and extracted Claim IDs must be lowercase slug identifiers.");
      if (!ui.reviewer.value.trim() || ui.reviewNotes.value.trim().length < 30 ||
          ui.evidenceNotes.value.trim().length === 0 || !ui.title.value.trim() || !ui.publisher.value.trim()) {
        throw new Error("Provide a real reviewer, publisher, title and meaningful review/evidence notes.");
      }
      if (!validDate(ui.reviewed.value) || !validDate(ui.checked.value) ||
          (ui.published.value && !validDate(ui.published.value))) {
        throw new Error("Review, checked and publication dates must be valid ISO dates.");
      }
      if (ui.checked.value > ui.reviewed.value) throw new Error("Evidence checked date cannot follow review date.");
      if (company.evidence.some(x => x.id === evidenceId || x.url === selected.source.url) ||
          claim.evidence_ids.includes(evidenceId)) throw new Error("Evidence ID or URL already exists in this company.");
      if (!selected.evidence_quote || !selected.evidence_quote.trim()) {
        throw new Error("Extracted source quote is missing.");
      }
      const approval = {
        schema_version:"1.0", approval_id:approvalId,
        reviewer:ui.reviewer.value.trim(), reviewed_at:ui.reviewed.value,
        decision:"approved_evidence_attachment",
        company_id:company.id, existing_claim_id:claim.id,
        expected_claim_sha256:await sha256(claim),
        extracted_claim_id:selected.claim_id,
        evidence:{
          id:evidenceId, title:ui.title.value.trim(),
          url:selected.source.url, publisher:ui.publisher.value.trim(),
          source_type:ui.sourceType.value, independence:ui.independence.value,
          published_at:ui.published.value || null, checked_at:ui.checked.value,
          review_status:"reviewed", notes:ui.evidenceNotes.value.trim()
        },
        review_notes:ui.reviewNotes.value.trim()
      };
      saveJson(approvalId + ".json", approval);
      message("Manifest exported locally. No GitHub action or formal database change occurred. Commit the reviewed manifest and its matching source report before manual dispatch.");
      clearApprovalConsent();
    } catch (error) {
      message("Cannot export: " + error.message, true);
    }
  });
  resetReview();
  fillCompanyList();
})();