document.addEventListener("DOMContentLoaded", () => {
    const toggles = document.querySelectorAll(".toggle-league");

    toggles.forEach(button => {
        button.addEventListener("click", () => {
            const target = document.getElementById(button.dataset.target);
            if (target) {
                target.classList.toggle("hidden");
                button.innerText = target.classList.contains("hidden") ? "➕" : "➖";
            }
        });
    });
});

document.addEventListener("DOMContentLoaded", () => {
    const toggles = document.querySelectorAll(".toggle-league");

    toggles.forEach(button => {
        button.addEventListener("click", () => {
            const target = document.getElementById(button.dataset.target);
            if (target) {
                target.classList.toggle("hidden");
                button.innerText = target.classList.contains("hidden") ? "➕" : "➖";
            }
        });
    });

    const toggleAllButton = document.getElementById("toggle-all");
    let allVisible = true;

    if (toggleAllButton) {
        toggleAllButton.addEventListener("click", () => {
            const sections = document.querySelectorAll(".league-section");
            const toggles = document.querySelectorAll(".toggle-league");

            sections.forEach(section => {
                if (allVisible) {
                    section.classList.add("hidden");
                } else {
                    section.classList.remove("hidden");
                }
            });

            toggles.forEach(btn => {
                btn.innerText = allVisible ? "➕" : "➖";
            });

            toggleAllButton.innerText = allVisible ? "➕ Tout afficher" : "➖ Tout replier";
            allVisible = !allVisible;
        });
    }
});
