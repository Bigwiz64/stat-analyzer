function initPlayerListSorting() {
  const headers = document.querySelectorAll(".player-table th[data-sort]");

  headers.forEach(header => {
    header.addEventListener("click", () => {
      const sortKey = header.dataset.sort;
      const rows = Array.from(document.querySelectorAll(".player-table tbody tr"));

      const currentOrder = header.dataset.order || "asc";
      const nextOrder = currentOrder === "asc" ? "desc" : "asc";

      rows.sort((a, b) => {
        const aValue = a.querySelector(`td:nth-child(${header.cellIndex + 1})`).textContent.trim();
        const bValue = b.querySelector(`td:nth-child(${header.cellIndex + 1})`).textContent.trim();

        const aNum = parseFloat(aValue);
        const bNum = parseFloat(bValue);

        if (!isNaN(aNum) && !isNaN(bNum)) {
          return currentOrder === "asc" ? aNum - bNum : bNum - aNum;
        } else {
          return currentOrder === "asc" ? aValue.localeCompare(bValue) : bValue.localeCompare(aValue);
        }
      });

      const tbody = document.querySelector(".player-table tbody");
      tbody.innerHTML = "";
      rows.forEach(row => tbody.appendChild(row));

      headers.forEach(h => h.removeAttribute("data-order"));
      header.setAttribute("data-order", nextOrder);
    });
  });
}
