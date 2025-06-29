function initPlayerPanel(matchId) {
  const statPanel = document.getElementById("statPanel");
  const playerListBlock = document.getElementById("playerListBlock");
  const statContent = document.getElementById("statContent");
  const chartBlock = document.getElementById("player-chart");
  const formBlock = document.getElementById("player-form");
  const playerNameEl = document.getElementById("selected-player-name");
  const playerRows = document.querySelectorAll(".player-item");
  let currentPlayerId = null;

  console.log("[INIT] Initialisation du panneau joueur…");

  // Ajout du listener sur chaque joueur
  playerRows.forEach((row) => {
    row.addEventListener("click", () => {
      console.log(`[CLICK] Joueur cliqué : ID ${row.dataset.id} - Nom : ${row.dataset.name}`);

      // Met à jour le joueur actif
      playerRows.forEach(r => r.classList.remove("active"));
      row.classList.add("active");

      currentPlayerId = row.dataset.id;
      window.currentPlayerId = currentPlayerId;  // Stockage global pour d'autres scripts
      playerNameEl.textContent = row.dataset.name;

      // Ouvre le panneau stats
      statPanel.classList.replace("collapsed", "expanded");
      playerListBlock.classList.replace("expanded", "collapsed");
      statContent.style.display = "block";
      formBlock.style.display = "block";
      chartBlock.classList.replace("chart-hidden", "chart-visible");
      chartBlock.style.display = "block";
      statPanel.scrollIntoView({ behavior: "smooth", block: "start" });

      // Appel du graphique (si la fonction existe déjà)
      if (window.loadChartConfig) {
        console.log(`[LOAD] Chargement des stats pour joueur ${currentPlayerId} sur match ${matchId}`);
        window.loadChartConfig(currentPlayerId, matchId);
      } else {
        console.warn("[ERREUR] Fonction window.loadChartConfig non trouvée !");
      }
    });
  });

  // Toggle pour ouvrir/fermer le panneau manuellement
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

  // Soumission du formulaire
  document.getElementById("statForm").addEventListener("submit", e => {
    e.preventDefault();
    if (currentPlayerId && window.loadChartConfig) {
      window.loadChartConfig(currentPlayerId, matchId);
    }
  });

  // Boutons slider
  document.getElementById("slider-left").addEventListener("click", () => {
    document.getElementById("performance-cards").scrollBy({ left: -150, behavior: "smooth" });
  });
  document.getElementById("slider-right").addEventListener("click", () => {
    document.getElementById("performance-cards").scrollBy({ left: 150, behavior: "smooth" });
  });

  console.log("[INIT] initPlayerPanel terminé.");
}
