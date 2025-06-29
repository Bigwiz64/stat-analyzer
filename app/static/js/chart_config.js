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
            
        // ✅ X1 : Vert si but, rouge sinon
        if (isX1) {
          return (m.value >= cut) ? "#4CAF50" : "#F44336";
        }
      
        // ✅ X2 : Gris si 1 but (has_goal_but_not_first_half == true), Vert si 2+, Rouge si 0
        if (isX2) {
          if (m.has_goal_but_not_first_half) {
            return "#ccc";  // Gris pour les 1 but
          } else if (m.value >= cut) {
            return "#4CAF50";  // Vert si 2 buts ou plus
          } else {
            return "#F44336";  // Rouge si 0 but
          }
        }
      
        // ✅ MT et 2MT : Gris si has_goal_but_not_first_half, sinon logique normale
        if ((isMT || is2MT) && m.has_goal_but_not_first_half) {
          return "#ccc";
        }
      
        // ✅ Cas par défaut : logique verte ou rouge
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
                callback: function(value) {
                  return Number.isInteger(value) ? value : null;
                }
              }
            },
            x: {
              ticks: {
                callback: function(value) {
                  const label = this.getLabelForValue(value);
                  const [year, month, day] = label.split("-");
                  return `${day}/${month}/${year}`;
                },
                font: {
                  family: "'Chakra Petch', sans-serif",
                  size: 12
                }
              }
            }
          }
        }
      });

      // === Bloc des cartes de performance ===
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
          const match = card.data.match(/(\d+)\/(\d+)\s\((\d+)%\)\s\|\s(\d+)\sBut/);
          if (match) {
            ratio = `${match[1]}/${match[2]}`;
            percent = match[3];
            total_goals = match[4];
          } else {
            const legacyMatch = card.data.match(/(\d+)\/(\d+)\s\((\d+)%\)/);
            if (legacyMatch) {
              ratio = `${legacyMatch[1]}/${legacyMatch[2]}`;
              percent = legacyMatch[3];
            }
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
