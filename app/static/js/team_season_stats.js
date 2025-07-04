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

  function setBar(barElement, ratio) {
    if (!barElement) return;

    const percentage = Math.round(Math.min(ratio * 20, 100)); // max 100%
    barElement.style.opacity = "1";
    barElement.style.width = `${percentage}%`;

    // Supprimer l'ancien label
    const oldLabel = barElement.parentElement.querySelector(".bar-label");
    if (oldLabel) oldLabel.remove();

    // Créer un nouveau label
    const label = document.createElement("div");
    label.className = "bar-label";
    label.textContent = `${percentage}%`;
    barElement.parentElement.appendChild(label);
  }

  function updateBars() {
    const homeBar = document.getElementById("home_goal_ratio_bar");
    const awayBar = document.getElementById("away_goal_ratio_bar");

    if (homeBar) {
      const loc = state["lieu-home"] === "Tous" ? "" : (state["lieu-home"] === "Domicile" ? "home" : "away");
      const type = state["type-home"] === "Marqué" ? "for" : "against";
      fetch(`/team/${window.HOME_TEAM_ID}/goal_ratio?location=${loc}&type=${type}`)
        .then(res => res.json())
        .then(data => setBar(homeBar, data.ratio));
    }

    if (awayBar) {
      const loc = state["lieu-away"] === "Tous" ? "" : (state["lieu-away"] === "Domicile" ? "home" : "away");
      const type = state["type-away"] === "Marqué" ? "for" : "against";
      fetch(`/team/${window.AWAY_TEAM_ID}/goal_ratio?location=${loc}&type=${type}`)
        .then(res => res.json())
        .then(data => setBar(awayBar, data.ratio));
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
