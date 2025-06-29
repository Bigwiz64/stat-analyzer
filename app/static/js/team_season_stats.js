document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll('.filter-toggle-group').forEach(group => {
    const buttons = group.querySelectorAll('.filter-btn');

    buttons.forEach(button => {
      button.addEventListener('click', () => {
        buttons.forEach(btn => btn.classList.remove('active'));
        button.classList.add('active');
        console.log(`✅ Groupe : ${[...group.classList].join(' ')}, bouton actif : ${button.textContent}`);
      });
    });
  });
});
