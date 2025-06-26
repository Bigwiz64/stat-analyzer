document.addEventListener("DOMContentLoaded", () => {
  /**
   * Charge et affiche les statistiques saison d'une équipe
   * @param {number} teamId - ID de l'équipe
   * @param {string} prefix - Préfixe des IDs HTML (ex: "home" ou "away")
   */
  function loadTeamSeasonStats(teamId, prefix) {
    fetch(`/team/${teamId}/season_stats`)
      .then(response => {
        if (!response.ok) {
          throw new Error(`Erreur HTTP ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        // Champs de base
        document.getElementById(`${prefix}_total_matches`).textContent = data.total_matches ?? "-";
        document.getElementById(`${prefix}_goals`).textContent = data.goals ?? "-";
        document.getElementById(`${prefix}_avg_goals`).textContent = data.avg_goals ?? "-";

        // Nouvelles stats
        document.getElementById(`${prefix}_no_goal_matches`).textContent = data.no_goal_matches ?? "-";
        document.getElementById(`${prefix}_goal_ratio`).textContent = `${data.goal_ratio}%` ?? "-";
        document.getElementById(`${prefix}_over_1_5_pct`).textContent = `${data.over_1_5_pct}%` ?? "-";
        document.getElementById(`${prefix}_over_2_5_pct`).textContent = `${data.over_2_5_pct}%` ?? "-";
        document.getElementById(`${prefix}_first_half_goals`).textContent = data.first_half_goals ?? "-";
        document.getElementById(`${prefix}_second_half_goals`).textContent = data.second_half_goals ?? "-";
        document.getElementById(`${prefix}_matches_with_goal_first_half`).textContent = data.matches_with_goal_first_half ?? "-";
        document.getElementById(`${prefix}_matches_with_goal_second_half`).textContent = data.matches_with_goal_second_half ?? "-";
      })
      .catch(error => {
        console.error(`❌ Erreur lors du chargement des stats pour l'équipe ${teamId}:`, error);
      });
  }

  // IDs d'équipe récupérés depuis les variables globales définies dans le template HTML
  const homeTeamId = window.homeTeamId;
  const awayTeamId = window.awayTeamId;

  if (homeTeamId) loadTeamSeasonStats(homeTeamId, "home");
  if (awayTeamId) loadTeamSeasonStats(awayTeamId, "away");
});
