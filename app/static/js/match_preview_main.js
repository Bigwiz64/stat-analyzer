window.chartInstance = null;

document.addEventListener("DOMContentLoaded", () => {
  const matchId = window.MATCH_ID;
  const homeTeamId = window.HOME_TEAM_ID;
  const awayTeamId = window.AWAY_TEAM_ID;

  // ✅ Forcer le filtre par défaut sur "goals" (X1)
  const filterInput = document.getElementById("filter");
  if (filterInput) filterInput.value = "goals";

  // ✅ Chargement des séries de buts par équipe
  loadTeamGoalSeries(homeTeamId, "home-goal-series", matchId);
  loadTeamGoalSeries(awayTeamId, "away-goal-series", matchId);

  // ✅ Initialisation des tris et filtres sur la liste des joueurs
  initPlayerListSorting();
  initPlayerListFiltering();

  // ✅ Initialisation du panneau de stats joueur
  initPlayerPanel(matchId);

  // ✅ Gestion du menu à onglets (onglets dynamiques)
  const tabButtons = document.querySelectorAll(".tab-btn");
  const tabContents = document.querySelectorAll(".tab-content");

  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const tab = btn.dataset.tab;

      // Met à jour les classes actives des boutons
      tabButtons.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");

      // Affiche uniquement la section liée à l’onglet cliqué
      tabContents.forEach(c => {
        c.classList.remove("active");
        if (c.classList.contains(`tab-${tab}`)) {
          c.classList.add("active");
        }
      });
    });
  });
});

