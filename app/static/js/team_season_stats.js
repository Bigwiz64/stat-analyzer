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

  // Récupération du filtre actif (Marqué ou Encaissé)
  const isHome = barElement.id.includes("home");
  const typeKey = isHome ? "type-home" : "type-away";
  const currentType = state[typeKey]; // "Marqué" ou "Encaissé"

  // Supprimer anciennes classes de couleur
  barElement.classList.remove("marquer", "encaisser");

  // Ajouter la classe selon le type
  if (currentType === "Marqué") {
    barElement.classList.add("marquer");
  } else {
    barElement.classList.add("encaisser");
  }

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
    updateGoalRatioBars();
    updateAvgBars();
    updateHalfTimeBars();
    updateHalfTimeAvgBars();
  }

  function updateGoalRatioBars() {
    const homeBar = document.getElementById("home_goal_ratio_bar");
    const awayBar = document.getElementById("away_goal_ratio_bar");

    if (homeBar) {
      const loc = state["lieu-home"] === "Tous" ? "" : (state["lieu-home"] === "Domicile" ? "home" : "away");
      const type = state["type-home"] === "Marqué" ? "for" : "against";
      fetch(`/team/${window.HOME_TEAM_ID}/goal_ratio?location=${loc}&type=${type}&season=${window.CURRENT_SEASON}`)
        .then(res => res.json())
        .then(data => {
          console.log("🏠 Ratio buts total (home):", data.ratio);
          setBar(homeBar, data.ratio);
        });
    }

    if (awayBar) {
      const loc = state["lieu-away"] === "Tous" ? "" : (state["lieu-away"] === "Domicile" ? "home" : "away");
      const type = state["type-away"] === "Marqué" ? "for" : "against";
      fetch(`/team/${window.AWAY_TEAM_ID}/goal_ratio?location=${loc}&type=${type}&season=${window.CURRENT_SEASON}`)
        .then(res => res.json())
        .then(data => {
          console.log("🛫 Ratio buts total (away):", data.ratio);
          setBar(awayBar, data.ratio);
        });
    }
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
          console.log("🏠 Moyenne buts (home):", average);
          const width = Math.min((average / 3) * 100, 100);
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
          console.log("🛫 Moyenne buts (away):", average);
          const width = Math.min((average / 3) * 100, 100);
          const label = average.toFixed(2).replace('.', ',');
          setBar(awayAvgBar, width, label);
        });
    }
  }

  function updateHalfTimeBars() {
    const homeBar = document.getElementById("home_half_time_bar");
    const awayBar = document.getElementById("away_half_time_bar");

    const locHome = state["lieu-home"] === "Tous" ? "" : (state["lieu-home"] === "Domicile" ? "home" : "away");
    const typeHome = state["type-home"] === "Marqué" ? "for" : "against";

    const locAway = state["lieu-away"] === "Tous" ? "" : (state["lieu-away"] === "Domicile" ? "home" : "away");
    const typeAway = state["type-away"] === "Marqué" ? "for" : "against";

    if (homeBar) {
      fetch(`/team/${window.HOME_TEAM_ID}/half_time_goal_ratio?location=${locHome}&type=${typeHome}&season=${window.CURRENT_SEASON}`)
        .then(res => res.json())
        .then(data => {
          console.log("🏠 Ratio Mi-Temps (home):", data.ratio);
          setBar(homeBar, data.ratio);
        });
    }

    if (awayBar) {
      fetch(`/team/${window.AWAY_TEAM_ID}/half_time_goal_ratio?location=${locAway}&type=${typeAway}&season=${window.CURRENT_SEASON}`)
        .then(res => res.json())
        .then(data => {
          console.log("🛫 Ratio Mi-Temps (away):", data.ratio);
          setBar(awayBar, data.ratio);
        });
    }
  }

  function updateHalfTimeAvgBars() {
    const homeBar = document.getElementById("home_avg_half_time_bar");
    const awayBar = document.getElementById("away_avg_half_time_bar");

    const locHome = state["lieu-home"] === "Tous" ? "" : (state["lieu-home"] === "Domicile" ? "home" : "away");
    const typeHome = state["type-home"] === "Marqué" ? "for" : "against";

    const locAway = state["lieu-away"] === "Tous" ? "" : (state["lieu-away"] === "Domicile" ? "home" : "away");
    const typeAway = state["type-away"] === "Marqué" ? "for" : "against";

    if (homeBar) {
      fetch(`/team/${window.HOME_TEAM_ID}/half_time_goal_avg?location=${locHome}&type=${typeHome}&season=${window.CURRENT_SEASON}`)
        .then(res => res.json())
        .then(data => {
          const average = parseFloat(data.ratio);
          console.log("🏠 Moyenne Mi-Temps (home):", average);
          const width = Math.min((average / 2) * 100, 100);
          const label = average.toFixed(2).replace('.', ',');
          setBar(homeBar, width, label);
        });
    }

    if (awayBar) {
      fetch(`/team/${window.AWAY_TEAM_ID}/half_time_goal_avg?location=${locAway}&type=${typeAway}&season=${window.CURRENT_SEASON}`)
        .then(res => res.json())
        .then(data => {
          const average = parseFloat(data.ratio);
          console.log("🛫 Moyenne Mi-Temps (away):", average);
          const width = Math.min((average / 2) * 100, 100);
          const label = average.toFixed(2).replace('.', ',');
          setBar(awayBar, width, label);
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
