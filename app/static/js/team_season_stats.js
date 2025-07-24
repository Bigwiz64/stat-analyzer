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

  let currentIntervalTeam = "home";  // ✅ équipe sélectionnée pour les graphiques

  function setBar(barElement, value, label = null) {
    if (!barElement) return;

    const isHome = barElement.id.includes("home");
    const typeKey = isHome ? "type-home" : "type-away";
    const currentType = state[typeKey];

    barElement.classList.remove("marquer", "encaisser");
    barElement.classList.add(currentType === "Marqué" ? "marquer" : "encaisser");
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
        .then(data => setBar(homeBar, data.ratio));
    }

    if (awayBar) {
      const loc = state["lieu-away"] === "Tous" ? "" : (state["lieu-away"] === "Domicile" ? "home" : "away");
      const type = state["type-away"] === "Marqué" ? "for" : "against";
      fetch(`/team/${window.AWAY_TEAM_ID}/goal_ratio?location=${loc}&type=${type}&season=${window.CURRENT_SEASON}`)
        .then(res => res.json())
        .then(data => setBar(awayBar, data.ratio));
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
          const avg = parseFloat(data.ratio);
          setBar(homeAvgBar, Math.min((avg / 3) * 100, 100), avg.toFixed(2).replace('.', ','));
        });
    }

    if (awayAvgBar) {
      const loc = state["lieu-away"] === "Tous" ? "" : (state["lieu-away"] === "Domicile" ? "home" : "away");
      const type = state["type-away"] === "Marqué" ? "for" : "against";
      fetch(`/team/${window.AWAY_TEAM_ID}/goal_avg?location=${loc}&type=${type}&season=${window.CURRENT_SEASON}`)
        .then(res => res.json())
        .then(data => {
          const avg = parseFloat(data.ratio);
          setBar(awayAvgBar, Math.min((avg / 3) * 100, 100), avg.toFixed(2).replace('.', ','));
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
        .then(data => setBar(homeBar, data.ratio));
    }

    if (awayBar) {
      fetch(`/team/${window.AWAY_TEAM_ID}/half_time_goal_ratio?location=${locAway}&type=${typeAway}&season=${window.CURRENT_SEASON}`)
        .then(res => res.json())
        .then(data => setBar(awayBar, data.ratio));
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
          const avg = parseFloat(data.ratio);
          setBar(homeBar, Math.min((avg / 2) * 100, 100), avg.toFixed(2).replace('.', ','));
        });
    }

    if (awayBar) {
      fetch(`/team/${window.AWAY_TEAM_ID}/half_time_goal_avg?location=${locAway}&type=${typeAway}&season=${window.CURRENT_SEASON}`)
        .then(res => res.json())
        .then(data => {
          const avg = parseFloat(data.ratio);
          setBar(awayBar, Math.min((avg / 2) * 100, 100), avg.toFixed(2).replace('.', ','));
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

  const saisonGroup = document.querySelector('.filter-group-statsaison');
  let currentSaisonLocation = "";

  if (saisonGroup) {
    const saisonButtons = saisonGroup.querySelectorAll('.filter-btn');
    saisonButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        saisonButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentSaisonLocation = btn.dataset.value;
        updateSeasonStatsBars();
      });
    });
  }

  function updateSeasonStatsBars() {
    const stats = [
      { id: "over_1_5" },
      { id: "over_2_5" },
      { id: "over_3_5" },
      { id: "btts" },
      { id: "clean_sheet", type: "against" },
      { id: "total_goals_avg", type: "combined" }
    ];

    stats.forEach(stat => {
      const suffix = stat.id;
      const type = stat.type || "for";

      const homeBar = document.getElementById(`home_${suffix}`);
      const awayBar = document.getElementById(`away_${suffix}`);

      if (suffix === "total_goals_avg") {
        if (homeBar) {
          homeBar.classList.add("season-home");
          fetch(`/team/${window.HOME_TEAM_ID}/season_stat/total_goals_avg?location=${currentSaisonLocation}&season=${window.CURRENT_SEASON}`)
            .then(res => res.json())
            .then(data => {
              const label = data.ratio.toFixed(2).replace('.', ',');
              setBar(homeBar, Math.min((data.ratio / 5) * 100, 100), label);
            });
        }
        if (awayBar) {
          awayBar.classList.add("season-away");
          fetch(`/team/${window.AWAY_TEAM_ID}/season_stat/total_goals_avg?location=${currentSaisonLocation}&season=${window.CURRENT_SEASON}`)
            .then(res => res.json())
            .then(data => {
              const label = data.ratio.toFixed(2).replace('.', ',');
              setBar(awayBar, Math.min((data.ratio / 5) * 100, 100), label);
            });
        }
      } else {
        if (homeBar) {
          homeBar.classList.add("season-home");
          fetch(`/team/${window.HOME_TEAM_ID}/season_stat?type=${suffix}&location=${currentSaisonLocation}&season=${window.CURRENT_SEASON}`)
            .then(res => res.json())
            .then(data => setBar(homeBar, data.ratio));
        }
        if (awayBar) {
          awayBar.classList.add("season-away");
          fetch(`/team/${window.AWAY_TEAM_ID}/season_stat?type=${suffix}&location=${currentSaisonLocation}&season=${window.CURRENT_SEASON}`)
            .then(res => res.json())
            .then(data => setBar(awayBar, data.ratio));
        }
      }
    });
  }

  updateSeasonStatsBars();
  loadAllIntervalCharts();

  document.getElementById("chart_home").closest(".chart-container").style.display = "block";
  document.getElementById("chart_away").closest(".chart-container").style.display = "none";

  function loadAllIntervalCharts() {
  const selectedIsHome = currentIntervalTeam === "home";
  const teamId = selectedIsHome ? window.HOME_TEAM_ID : window.AWAY_TEAM_ID;
  const opponentId = selectedIsHome ? window.AWAY_TEAM_ID : window.HOME_TEAM_ID;

  const teamName = selectedIsHome ? window.HOME_TEAM_NAME : window.AWAY_TEAM_NAME;
  const opponentName = selectedIsHome ? window.AWAY_TEAM_NAME : window.HOME_TEAM_NAME;

  const chartConfigs = [
    { canvasId: "chart_all", teamLoc: "", opponentLoc: "" },
    { canvasId: "chart_home", teamLoc: "home", opponentLoc: "away" },
    { canvasId: "chart_away", teamLoc: "away", opponentLoc: "home" },
  ];

  chartConfigs.forEach(config => {
    const canvas = document.getElementById(config.canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    Promise.all([
      fetch(`/team/${teamId}/goals_by_interval?location=${config.teamLoc}&season=${window.CURRENT_SEASON}`).then(res => res.json()),
      fetch(`/team/${opponentId}/goals_by_interval?location=${config.opponentLoc}&season=${window.CURRENT_SEASON}`).then(res => res.json())
    ])
    .then(([forData, againstData]) => {
      const labels = Object.keys(forData);
      const goalsFor = labels.map(k => forData[k]["for"]);
      const goalsAgainst = labels.map(k => againstData[k]["against"]);

      if (canvas.chart && typeof canvas.chart.destroy === "function") {
        canvas.chart.destroy();
      }

      canvas.chart = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [
            {
              label: `Buts marqués ${teamName}`,
              data: goalsFor,
              backgroundColor: context => {
                const value = context.raw;
                if (value <= 1) return "#4DFF62";
                if (value <= 3) return "#04C71B";
                if (value <= 5) return "#48A527";
                if (value <= 7) return "#35811D";
                if (value <= 9) return "#005201";
                return "#003300";
              }
            },
            {
              label: `Buts encaissés ${opponentName}`,
              data: goalsAgainst,
              backgroundColor: context => {
                const value = context.raw;
                if (value <= 1) return "#E97B7B";
                if (value <= 3) return "#E3504F";
                if (value <= 5) return "#C61F1F";
                if (value <= 7) return "#B11B1B";
                if (value <= 9) return "#841616";
                return "#C62828";
              }
            }
          ]
        },
        options: {
          responsive: true,
          plugins: {
            legend: {
              display: false // ✅ on désactive la légende interne
            },
            title: { display: false }
          },
          scales: {
            y: {
              beginAtZero: true,
              ticks: { stepSize: 1 }
            }
          }
        }
      });

      // 🔽 Créer la légende personnalisée juste après le canvas
      const legendHtml = `
        <div class="legend-item">
          <span class="legend-dot" style="background-color:#04C71B;"></span>
          Buts marqués ${teamName}
        </div>
        <div class="legend-item">
          <span class="legend-dot" style="background-color:#C62828;"></span>
          Buts encaissés ${opponentName}
        </div>
      `;
      const legendContainer = document.getElementById(`legend_${config.canvasId}`);
      if (legendContainer) {
        legendContainer.innerHTML = legendHtml;
      }
    })
    .catch(err => console.error(`Erreur chart ${config.canvasId} :`, err));
  });
}



  document.querySelectorAll(".interval-team-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".interval-team-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");

    currentIntervalTeam = btn.dataset.team;
    loadAllIntervalCharts();

    // Affichage conditionnel des blocs
    const chartAll = document.getElementById("chart_all").closest(".chart-container");
    const chartHome = document.getElementById("chart_home").closest(".chart-container");
    const chartAway = document.getElementById("chart_away").closest(".chart-container");

    if (currentIntervalTeam === "home") {
      chartAll.style.display = "block";
      chartHome.style.display = "block";
      chartAway.style.display = "none";
    } else {
      chartAll.style.display = "block";
      chartHome.style.display = "none";
      chartAway.style.display = "block";
    }
  });
});


});
