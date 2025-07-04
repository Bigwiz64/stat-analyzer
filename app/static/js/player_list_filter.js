function initPlayerListFiltering() {
  const teamFilterButtons = document.querySelectorAll(".team-toggle-buttons .filter-btn"); // 🔧 Limite la portée

  teamFilterButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const team = btn.dataset.team;

      teamFilterButtons.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");

      document.querySelectorAll(".player-item").forEach(row => {
        const rowTeam = row.dataset.team;
        row.style.display = (team === "all" || rowTeam === team) ? "" : "none";
      });
    });
  });
}
document.addEventListener("DOMContentLoaded", () => {
  initPlayerListFiltering();
});
