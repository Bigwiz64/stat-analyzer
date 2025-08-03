let compareMode = null;
let selectedPlayers = [];

function activateCompareMode(mode) {
  compareMode = mode;
  selectedPlayers = [];
  updatePlayerSelectionUI();

  // Affiche le bouton de sortie
  const exitBtn = document.getElementById("exitCompareBtn");
  if (exitBtn) exitBtn.style.display = "inline-block";
}

function togglePlayerSelection(playerId) {
  if (!compareMode) return;

  const index = selectedPlayers.indexOf(playerId);
  if (index > -1) {
    selectedPlayers.splice(index, 1);
  } else {
    const max = compareMode === "duo" ? 2 : 3;
    if (selectedPlayers.length < max) {
      selectedPlayers.push(playerId);
    }
  }

  updatePlayerSelectionUI();

  const requiredCount = compareMode === "duo" ? 2 : 3;
  if (selectedPlayers.length === requiredCount) {
    fetch(`/compare_players?players=${selectedPlayers.join(",")}&match_id=${window.MATCH_ID}`)
      .then(res => res.json())
      .then(data => {
        // Forcer affichage graphique uniquement
        const container = document.getElementById("player-chart");
        container.style.display = "block";
        container.classList.remove("chart-hidden");

        renderComparisonChart(data);
      });
  }
}

function updatePlayerSelectionUI() {
  document.querySelectorAll(".player-item").forEach((row) => {
    row.classList.remove("active");
    const playerId = row.dataset.id;
    if (selectedPlayers.includes(playerId)) {
      row.classList.add("active");
    }
  });
}

function resetCompareMode() {
  compareMode = null;
  selectedPlayers = [];
  updatePlayerSelectionUI();

  const container = document.getElementById("player-chart");
  container.classList.add("chart-hidden");
  container.style.display = "none";

  const exitBtn = document.getElementById("exitCompareBtn");
  if (exitBtn) exitBtn.style.display = "none";

  if (window.currentChart) {
    window.currentChart.destroy();
    window.currentChart = null;
  }
}

function renderComparisonChart(data) {
  const ctx = document.getElementById("chartCanvas").getContext("2d");

  if (window.currentChart) {
    window.currentChart.destroy();
  }

  const colors = ["#39FF14", "#006400", "#888"];

  const datasets = data.players.map((player, index) => ({
    label: player.name,
    data: player.matches.map((m) => m.value),
    backgroundColor: player.matches.map((m) => {
      if (m.status === "goal") return colors[index];
      if (m.status === "played") return "red";
      return "lightgray";
    }),
  }));

  window.currentChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: data.matches,
      datasets,
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: "bottom",
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: { stepSize: 1 },
        },
      },
    },
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const duoBtn = document.getElementById("duo-mode-btn");
  const trioBtn = document.getElementById("trio-mode-btn");
  const exitBtn = document.getElementById("exitCompareBtn");

  if (duoBtn) duoBtn.addEventListener("click", () => activateCompareMode("duo"));
  if (trioBtn) trioBtn.addEventListener("click", () => activateCompareMode("trio"));
  if (exitBtn) exitBtn.addEventListener("click", resetCompareMode);

  document.querySelectorAll(".player-item").forEach((row) => {
    row.addEventListener("click", () => {
      const playerId = row.dataset.id;
      togglePlayerSelection(playerId);
    });
  });
});
