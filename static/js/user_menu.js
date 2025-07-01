// Obsługa rozwijanego menu użytkownika (avatar)
function toggleUserMenu() {
  const menu = document.getElementById('user-menu');
  menu.style.display = (menu.style.display === 'block') ? 'none' : 'block';
}

document.addEventListener('click', function(e) {
  const avatar = document.getElementById('user-avatar-dropdown');
  const menu = document.getElementById('user-menu');
  if (avatar && menu && !avatar.contains(e.target)) {
    menu.style.display = 'none';
  }
});
