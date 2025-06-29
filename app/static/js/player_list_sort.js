function sortPlayerList(sortBy, order) {
  const tbody = document.querySelector(".player-table tbody");
  const rows = Array.from(tbody.querySelectorAll("tr"));

  rows.sort((a, b) => {
    const aValue = getCellValue(a, sortBy);
    const bValue = getCellValue(b, sortBy);

    const aNum = parseFloat(aValue);
    const bNum = parseFloat(bValue);

    if (!isNaN(aNum) && !isNaN(bNum)) {
      return order === "asc" ? aNum - bNum : bNum - aNum;
    } else {
      return order === "asc" ? aValue.localeCompare(bValue) : bValue.localeCompare(aValue);
    }
  });

  // Ré-injecte les lignes triées dans le tableau
  tbody.innerHTML = "";
  rows.forEach(row => tbody.appendChild(row));
}

function getCellValue(row, sortBy) {
  const indexMap = {
    name: 0,
    position: 1,
    team: 2,
    appearances: 3,
    goals: 4,
    assists: 5,
    penalty_scored: 6,
    yellow_cards: 7,
    red_cards: 8
  };

  const cellIndex = indexMap[sortBy];
  const cell = row.children[cellIndex];
  return cell ? cell.textContent.trim() : "";
}

function initPlayerListSorting() {
  const headers = document.querySelectorAll(".player-table th[data-sort]");

  headers.forEach(header => {
    header.addEventListener("click", () => {
      const sortKey = header.dataset.sort;
      const currentOrder = header.dataset.order || "desc";
      const nextOrder = currentOrder === "asc" ? "desc" : "asc";

      sortPlayerList(sortKey, nextOrder);

      // Mise à jour de l'attribut pour le prochain clic
      headers.forEach(h => h.removeAttribute("data-order"));
      header.setAttribute("data-order", nextOrder);
    });
  });

  // ✅ Tri par défaut au chargement : Buts (colonne "goals"), ordre décroissant
  sortPlayerList("goals", "desc");
}
