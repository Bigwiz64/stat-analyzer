document.addEventListener("DOMContentLoaded", function () {
    const allRows = Array.from(document.querySelectorAll("#playerStatsBody tr"));
    const rowsPerPage = 10;
    let currentPage = 1;
    let sortDirection = false; // false = DESC (par défaut)
    let sortedColumnIndex = null;

    function renderTable() {
        const tbody = document.getElementById("playerStatsBody");
        tbody.innerHTML = "";

        const start = (currentPage - 1) * rowsPerPage;
        const end = start + rowsPerPage;
        const visibleRows = allRows.slice(start, end);

        visibleRows.forEach(row => tbody.appendChild(row));

        renderPagination();
    }

    function renderPagination() {
        const totalPages = Math.ceil(allRows.length / rowsPerPage);
        const pagination = document.getElementById("pagination");
        pagination.innerHTML = "";

        for (let i = 1; i <= totalPages; i++) {
            const btn = document.createElement("button");
            btn.textContent = i;
            btn.classList.toggle("active", i === currentPage);
            btn.addEventListener("click", () => {
                currentPage = i;
                renderTable();
            });
            pagination.appendChild(btn);
        }
    }

    function updateSortArrows(colIndex) {
        const thElements = document.querySelectorAll("thead th");
        thElements.forEach((th, i) => {
            const arrow = th.querySelector(".sort-arrow");
            if (!arrow) return;
            if (i === colIndex) {
                arrow.textContent = sortDirection ? "▲" : "▼";
            } else {
                arrow.textContent = "";
            }
        });
        sortedColumnIndex = colIndex;
    }

    window.sortTable = function (colIndex) {
        allRows.sort((a, b) => {
            const aText = a.children[colIndex].innerText;
            const bText = b.children[colIndex].innerText;

            const aVal = isNaN(aText) ? aText.toLowerCase() : parseFloat(aText);
            const bVal = isNaN(bText) ? bText.toLowerCase() : parseFloat(bText);

            if (aVal < bVal) return sortDirection ? -1 : 1;
            if (aVal > bVal) return sortDirection ? 1 : -1;
            return 0;
        });

        updateSortArrows(colIndex);
        sortDirection = !sortDirection; // toggle pour prochain clic
        currentPage = 1;
        renderTable();
    };

    // 👉 tri par défaut à l'ouverture : colonne 3 ("Buts")
    sortTable(3);
});
