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
