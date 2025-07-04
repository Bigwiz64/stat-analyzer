document.addEventListener("DOMContentLoaded", () => {
  const statCard = document.querySelector('.stat-card');
  if (!statCard) return;

  const groups = statCard.querySelectorAll('.filter-toggle-group');

  const state = {
    "lieu-home": "Tous",
    "type-home": "Marqué",
    "lieu-away": "Tous",
    "type-away": "Marqué"
  };

  function setBar(barElement, value, label = null) {
    if (!barElement) return;

    barElement.style.opacity = "1";
    barElement.style.width = `${value}%`;

    const oldLabel = barElement.parentElement.querySelector(".bar-label");
    if (oldLabel) oldLabel.remove();

    const newLabel = document.createElement("div");
    newLabel.className = "bar-label";
    newLabel.textContent = label ?? `${Math.round(value)}%`;
    barElement.parentElement.appendChild(newLabel);
  }

  function updateBars() {
    const homeBar = document.getElementById("home_goal_ratio_bar");
    const awayBar = document.getElementById("away_goal_ratio_bar");

    if (homeBar) {
      const loc = state["lieu-home"] === "Tous" ? "" : (state["lieu-home"] === "Domicile" ? "home" : "away");
      const type = state["type-home"] === "Marqué" ? "for" : "against";
      fetch(`/team/${window.HOME_TEAM_ID}/goal_ratio?location=${loc}&type=${type}&season=${window.CURRENT_SEASON}`)
        .then(res => res.json())
        .then(data => setBar(homeBar, data.ratio)); // valeur en %
    }

    if (awayBar) {
      const loc = state["lieu-away"] === "Tous" ? "" : (state["lieu-away"] === "Domicile" ? "home" : "away");
      const type = state["type-away"] === "Marqué" ? "for" : "against";
      fetch(`/team/${window.AWAY_TEAM_ID}/goal_ratio?location=${loc}&type=${type}&season=${window.CURRENT_SEASON}`)
        .then(res => res.json())
        .then(data => setBar(awayBar, data.ratio));
    }

    updateAvgBars(); // met aussi à jour les barres de moyennes
  }

  function updateAvgBars() {
    const homeAvgBar = document.getElementById("home_avg_goals_bar");
    const awayAvgBar = document.getElementById("away_avg_goals_bar");

    if (homeAvgBar) {
      const loc = state["lieu-home"] === "Tous" ? "" : (state["lieu-home"] === "Domicile" ? "home" : "away");
      const type = state["type-home"] === "Marqué" ? "for" : "against";
      fetch(`/team/${window.HOME_TEAM_ID}/goal_avg?location=${loc}&type=${type}&season=${window.CURRENT_SEASON}`)
        .then(res => res.json())
        .then(data => {
          const average = parseFloat(data.ratio);
          const width = Math.min((average / 3) * 100, 100); // 3 buts = 100%
          const label = average.toFixed(2).replace('.', ',');
          setBar(homeAvgBar, width, label);
        });
    }

    if (awayAvgBar) {
      const loc = state["lieu-away"] === "Tous" ? "" : (state["lieu-away"] === "Domicile" ? "home" : "away");
      const type = state["type-away"] === "Marqué" ? "for" : "against";
      fetch(`/team/${window.AWAY_TEAM_ID}/goal_avg?location=${loc}&type=${type}&season=${window.CURRENT_SEASON}`)
        .then(res => res.json())
        .then(data => {
          const average = parseFloat(data.ratio);
          const width = Math.min((average / 3) * 100, 100); // 3 buts = 100%
          const label = average.toFixed(2).replace('.', ',');
          setBar(awayAvgBar, width, label);
        });
    }
  }

  groups.forEach(group => {
    const buttons = group.querySelectorAll('.filter-btn');
    buttons.forEach(button => {
      button.addEventListener('click', () => {
        buttons.forEach(btn => btn.classList.remove('active'));
        button.classList.add('active');

        const groupClass = [...group.classList].find(cls => cls.startsWith("filter-group-"));
        const key = groupClass.replace("filter-group-", "");
        state[key] = button.textContent.trim();

        updateBars();
      });
    });
  });

  updateBars();
});
