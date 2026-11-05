(() => {
  const root = document.documentElement;
  const themeButton = document.querySelector("[data-theme-toggle]");
  const navButton = document.querySelector("[data-nav-toggle]");
  const nav = document.querySelector("[data-site-nav]");

  let savedTheme = null;
  try { savedTheme = localStorage.getItem("ai-chip-theme"); } catch (_) {}
  const preferredTheme = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  const setTheme = (theme) => {
    root.dataset.theme = theme;
    if (themeButton) {
      themeButton.textContent = theme === "dark" ? "Light mode" : "Dark mode";
      themeButton.setAttribute("aria-pressed", String(theme === "dark"));
    }
  };
  setTheme(savedTheme === "dark" || savedTheme === "light" ? savedTheme : preferredTheme);

  // Load homepage coverage once. Theme changes should not trigger data requests.
  const homeStats = document.querySelector("[data-home-stats]");
  if (homeStats) {
    const sources = [
      homeStats.dataset.compatSource,
      homeStats.dataset.workloadSource,
      homeStats.dataset.benchmarkSource
    ];
    Promise.all(sources.map((url) => fetch(url).then((response) => {
      if (!response.ok) throw new Error("Homepage coverage data request failed: " + response.status);
      return response.json();
    })))
      .then(([compatibility, workloads, benchmarks]) => {
        if (!Array.isArray(compatibility.platforms) ||
            !Array.isArray(compatibility.integrations) ||
            !Array.isArray(workloads.workloads) ||
            !Array.isArray(benchmarks.projects)) {
          throw new Error("Homepage coverage data has an unexpected structure.");
        }
        const values = {
          platforms: compatibility.platforms.length,
          integrations: compatibility.integrations.length,
          workloads: workloads.workloads.length,
          benchmarks: benchmarks.projects.length
        };
        Object.entries(values).forEach(([key, value]) => {
          const node = homeStats.querySelector('[data-home-stat="' + key + '"]');
          if (node) node.textContent = String(value);
        });
        homeStats.dataset.statsLoaded = "true";
        homeStats.removeAttribute("data-stats-stale");
      })
      .catch(() => homeStats.setAttribute("data-stats-stale", "true"));
  }

  if (themeButton) {
    themeButton.addEventListener("click", () => {
      const next = root.dataset.theme === "dark" ? "light" : "dark";
      setTheme(next);
      try { localStorage.setItem("ai-chip-theme", next); } catch (_) {}
    });
  }

  const closeNav = () => {
    if (!navButton || !nav) return;
    navButton.setAttribute("aria-expanded", "false");
    nav.classList.remove("is-open");
  };
  if (navButton && nav) {
    navButton.addEventListener("click", () => {
      const open = navButton.getAttribute("aria-expanded") !== "true";
      navButton.setAttribute("aria-expanded", String(open));
      nav.classList.toggle("is-open", open);
    });
    nav.querySelectorAll("a").forEach((link) => link.addEventListener("click", closeNav));
    document.addEventListener("keydown", (event) => { if (event.key === "Escape") closeNav(); });
    document.addEventListener("click", (event) => {
      if (!event.target.closest(".site-header")) closeNav();
    });
  }
})();
