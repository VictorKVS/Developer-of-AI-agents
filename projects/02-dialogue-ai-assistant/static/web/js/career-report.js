document.addEventListener("DOMContentLoaded", () => {
  if (window.location.pathname !== "/career/") return;

  const resultHeading = [...document.querySelectorAll(".section-head .eyebrow")]
    .find(node => node.textContent.trim().toLowerCase() === "result");
  if (!resultHeading) return;

  const resultCard = [...document.querySelectorAll("section.module-card")]
    .find(section => section.querySelector("h3")?.textContent.trim() === "Персональный трек");
  if (!resultCard) return;

  const actions = resultCard.querySelector("div[style*='display:flex']");
  if (!actions || actions.querySelector("[data-career-report-link]")) return;

  const link = document.createElement("a");
  link.className = "button";
  link.href = "/career/report/";
  link.dataset.careerReportLink = "true";
  link.innerHTML = "Скачать PDF-отчёт <span>↓</span>";
  actions.prepend(link);
});
