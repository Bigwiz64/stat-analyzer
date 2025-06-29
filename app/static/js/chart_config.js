function loadChartConfig(playerId, matchId) {
  const stat = document.getElementById("stat").value;
  const cut = parseInt(document.getElementById("cut").value);
  let limit = parseInt(document.getElementById("limit").value);
  const filter = document.getElementById("filter").value;
  const chartCanvas = document.getElementById("chartCanvas");

  if (isNaN(limit) || limit < 1) limit = 5;

  fetch(`/player/${playerId}/history?stat=${stat}&limit=${limit}&filter=${filter}&cut=${cut}&fixture_id=${matchId}`)
    .then(res => res.json())
    .then(data => {
      // ✅ Supprimer l'ancien graphique
      if (window.chartInstance) {
        window.chartInstance.destroy();
      }

      const labels = data.history.map(m => m.date);
      const values = data.history.map(m => parseFloat(m.value));

      const currentFilter = document.getElementById("filter").value;
      const colors = data.history.map(m => {
        const isX1 = currentFilter === "goals";
        const isX2 = currentFilter === "" || currentFilter === null;
        const isMT = currentFilter === "first_half";
        const is2MT = currentFilter === "both_halves";

        if (isX1) return (m.value >= cut) ? "#4CAF50" : "#F44336";
        if (isX2) {
          if (m.has_goal_but_not_first_half) return "#ccc";
          return (m.value >= cut) ? "#4CAF50" : "#F44336";
        }
        if ((isMT || is2MT) && m.has_goal_but_not_first_half) return "#ccc";
        return (m.value >= cut) ? "#4CAF50" : "#F44336";
      });

      window.chartInstance = new Chart(chartCanvas, {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [{
            label: stat,
            data: values,
            backgroundColor: colors
          }]
        },
        options: {
          responsive: true,
          animation: { duration: 400 },
          plugins: {
            legend: { display: false }
          },
          scales: {
            y: {
              beginAtZero: true,
              suggestedMin: 0,
              suggestedMax: Math.max(cut + 1, Math.max(...values) + 1),
              ticks: {
                stepSize: 1,
                callback: value => Number.isInteger(value) ? value : null
              }
            },
            x: {
              ticks: {
                callback: function(value) {
                  const label = this.getLabelForValue(value);
                  const [year, month, day] = label.split("-");
                  return `${day}/${month}/${year}`;
                },
                font: { family: "'Chakra Petch', sans-serif", size: 12 }
              }
            }
          },
          onClick: (e, elements) => {
            if (elements.length > 0) {
              const index = elements[0].index;
              const fixtureId = data.history[index].fixture_id;
              if (fixtureId) {
                window.location.href = `/match/${fixtureId}`;
              }
            }
          }
        }
      });


      // ✅ Cartes de performance (Last5, Last10, etc)
      const perf = data.performance;
      const container = document.getElementById("performance-cards");
      container.innerHTML = "";

      const cards = [
        { label: "Ls 5", data: perf.last_5 },
        { label: "Ls 10", data: perf.last_10 },
        { label: "Ls 20", data: perf.last_20 },
        { label: "H2H", data: perf.h2h },
        { label: "Dom", data: perf.home },
        { label: "Ext", data: perf.away },
        { label: "Saison", data: perf.season }
      ];

      cards.forEach(card => {
        const div = document.createElement("div");
        div.className = "performance-card";
        let ratio = "-", percent = "-", total_goals = "-";

        if (card.data && typeof card.data === "string") {
          const detailed = card.data.match(/(\d+)\/(\d+)\s\((\d+)%\)\s\|\s(\d+)\sBut/);
          const legacy = card.data.match(/(\d+)\/(\d+)\s\((\d+)%\)/);

          if (detailed) {
            ratio = `${detailed[1]}/${detailed[2]}`;
            percent = detailed[3];
            total_goals = detailed[4];
          } else if (legacy) {
            ratio = `${legacy[1]}/${legacy[2]}`;
            percent = legacy[3];
          }
        }

        div.innerHTML = `
          <div class="performance-card-title">${card.label}</div>
          <div class="progress-ring">
            <div class="progress-circle" style="--percent: ${percent !== "-" ? percent : 0};"></div>
            <div class="percent-text">${percent !== "-" ? percent + "%" : "-"}</div>
          </div>
          <div class="performance-bottom">
            <div class="ratio-text">${ratio}</div>
            <div class="total-goals-text">${total_goals !== "-" ? total_goals + " But" + (total_goals > 1 ? "s" : "") : ""}</div>
          </div>
        `;

        if (card.label.startsWith("Ls")) {
          const limitValue = parseInt(card.label.replace("Ls ", "")) || 5;
          div.style.cursor = "pointer";
          if (limitValue === limit) div.classList.add("active");
          div.addEventListener("click", () => {
            document.getElementById("limit").value = limitValue;
            document.querySelectorAll(".performance-card").forEach(c => c.classList.remove("active"));
            div.classList.add("active");
            window.loadChartConfig(playerId, matchId);
          });
        }

        container.appendChild(div);
      });
    });
}

window.loadChartConfig = loadChartConfig;
