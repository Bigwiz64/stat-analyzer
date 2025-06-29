window.chartInstance = null;

document.addEventListener("DOMContentLoaded", () => {
  const matchId = window.MATCH_ID;
  const homeTeamId = window.HOME_TEAM_ID;
  const awayTeamId = window.AWAY_TEAM_ID;

  // ✅ Forcer le filtre par défaut sur "goals" (X1) sans recharger le chart
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
});
