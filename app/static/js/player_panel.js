function initPlayerPanel(matchId) {
  const statPanel = document.getElementById("statPanel");
  const playerListBlock = document.getElementById("playerListBlock");
  const statContent = document.getElementById("statContent");
  const chartBlock = document.getElementById("player-chart");
  const formBlock = document.getElementById("player-form");
  const playerNameEl = document.getElementById("selected-player-name");
  const playerRows = document.querySelectorAll(".player-item");
  let currentPlayerId = null;

  const toggleBtn = document.getElementById("togglePanel");
  toggleBtn.addEventListener("click", () => {
    const isCollapsed = statPanel.classList.contains("collapsed");
    statPanel.classList.toggle("collapsed", !isCollapsed);
    statPanel.classList.toggle("expanded", isCollapsed);
    playerListBlock.classList.toggle("collapsed", isCollapsed);
    playerListBlock.classList.toggle("expanded", !isCollapsed);
    statContent.style.display = isCollapsed ? "block" : "none";
    document.getElementById("toggle-icon").textContent = isCollapsed ? "▲" : "▼";
    document.body.classList.toggle("chart-visible", isCollapsed);
  });

  playerRows.forEach((row, i) => {
    row.addEventListener("click", () => {
      playerRows.forEach(r => r.classList.remove("active"));
      row.classList.add("active");
      currentPlayerId = row.dataset.id;
      window.currentPlayerId = currentPlayerId;
      playerNameEl.textContent = row.dataset.name;
      statPanel.classList.replace("collapsed", "expanded");
      playerListBlock.classList.replace("expanded", "collapsed");
      statContent.style.display = "block";
      formBlock.style.display = "block";
      chartBlock.classList.replace("chart-hidden", "chart-visible");
      chartBlock.style.display = "block";
      statPanel.scrollIntoView({ behavior: "smooth", block: "start" });
      setTimeout(() => { window.loadChartConfig(currentPlayerId, matchId); }, 300);
    });
  });

  document.getElementById("statForm").addEventListener("submit", e => {
    e.preventDefault();
    if (currentPlayerId) {
      window.loadChartConfig(currentPlayerId, matchId);
    }
  });

  document.getElementById("slider-left").addEventListener("click", () => {
    document.getElementById("performance-cards").scrollBy({ left: -150, behavior: "smooth" });
  });
  document.getElementById("slider-right").addEventListener("click", () => {
    document.getElementById("performance-cards").scrollBy({ left: 150, behavior: "smooth" });
  });

  // ✅ ✅ CORRECTION pour éviter le "flash" de X2 au démarrage :
  const filterInput = document.getElementById("filter");
  if (filterInput && (!filterInput.value || filterInput.value.trim() === "")) {
    filterInput.value = "goals";

    // ✅ Optionnel : activer visuellement le bouton X1
    const x1Button = document.querySelector('button[data-filter="goals"]');
    if (x1Button) {
      document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
      x1Button.classList.add('active');
    }
  }

  // ✅ Ensuite on charge le 1er joueur directement avec X1
  const firstPlayer = document.querySelector(".player-item");
  if (firstPlayer) {
    currentPlayerId = firstPlayer.getAttribute("data-id");
    window.currentPlayerId = currentPlayerId;
    playerNameEl.textContent = firstPlayer.getAttribute("data-name");
    setTimeout(() => { window.loadChartConfig(currentPlayerId, matchId); }, 300);
  }
}
