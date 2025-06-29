document.addEventListener("DOMContentLoaded", () => {
  const statOptions = {
    goals: [
      { label: "X1", cut: 1, filter: "goals" },
      { label: "X2", cut: 2, filter: "" },
      { label: "MT", cut: 1, filter: "first_half" },
      { label: "2MT", cut: 1, filter: "both_halves" }
    ],
    assists: [
      { label: "X1", cut: 1, filter: "" },
      { label: "X2", cut: 2, filter: "" }
    ],
    intervalle: [
      { label: "0-15", cut: 1, filter: "0-15" },
      { label: "15-30", cut: 1, filter: "15-30" },
      { label: "30-45", cut: 1, filter: "30-45" },
      { label: "45-60", cut: 1, filter: "45-60" },
      { label: "60-75", cut: 1, filter: "60-75" },
      { label: "75-90", cut: 1, filter: "75-90" }
    ],
    minutes: [
      { label: "30+", cut: 30, filter: "" },
      { label: "60+", cut: 60, filter: "" },
      { label: "90", cut: 90, filter: "" }
    ]
  };

  const statButtonsContainer = document.getElementById("stat-buttons");
  if (!statButtonsContainer) return;

  statButtonsContainer.innerHTML = Object.keys(statOptions).map(stat =>
    `<button class="stat-btn" data-stat="${stat}" type="button">${stat.charAt(0).toUpperCase() + stat.slice(1)}</button>`
  ).join("");

  document.querySelectorAll(".stat-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const stat = btn.dataset.stat;
      const trueStat = (stat === "intervalle") ? "goals" : stat;
      document.getElementById("stat").value = trueStat;

      document.querySelectorAll(".stat-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");

      const sub = document.getElementById("sub-options");
      sub.innerHTML = "";

      const options = statOptions[stat] || [];
      options.forEach(opt => {
        const subBtn = document.createElement("button");
        subBtn.textContent = opt.label;
        subBtn.className = "sub-btn";
        subBtn.type = "button";
        subBtn.onclick = () => {
          document.getElementById("cut").value = opt.cut;
          document.getElementById("filter").value = opt.filter;

          document.querySelectorAll(".sub-btn").forEach(b => b.classList.remove("active"));
          subBtn.classList.add("active");

          if (window.loadChartConfig && window.currentPlayerId && window.MATCH_ID) {
            window.loadChartConfig(window.currentPlayerId, window.MATCH_ID);
          }
        };
        sub.appendChild(subBtn);
      });

      sub.style.display = options.length > 0 ? "block" : "none";
    });
  });
});
