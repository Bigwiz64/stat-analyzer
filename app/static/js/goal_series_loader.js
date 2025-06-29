function loadTeamGoalSeries(teamId, targetId, fixtureId) {
  fetch(`/team/${teamId}/goal_series?fixture_id=${fixtureId}`)
    .then(res => res.json())
    .then(data => {
      const container = document.getElementById(targetId);
      if (!container) return;

      container.innerHTML = '';

      const streakDiv = document.createElement("div");
      streakDiv.className = "goal-streak";
      data.series.forEach(item => {
        const card = document.createElement("div");
        card.className = "goal-box";
        card.textContent = item.goals;
        streakDiv.appendChild(card);
      });

      const rankDiv = document.createElement("div");
      rankDiv.className = "attack-rank";
      if (data.attack_rank) {
        rankDiv.textContent = `${data.attack_rank}ᵉ`;
        if (data.attack_rank <= 3) rankDiv.classList.add("rank-top");
        else if (data.attack_rank >= data.team_count - 2) rankDiv.classList.add("rank-bottom");
        else rankDiv.classList.add("rank-mid");
      }

      const wrapper = document.createElement("div");
      wrapper.className = "goal-streak-wrapper";
      wrapper.appendChild(rankDiv);
      wrapper.appendChild(streakDiv);
      container.appendChild(wrapper);
    });
}
