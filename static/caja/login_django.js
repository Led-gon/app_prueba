document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const loginMessage = document.getElementById('loginMessage');

    // Si hay un mensaje de error pre-existente (ej. de un redirect de Django con error), no lo borres inmediatamente
    // El login_view de Django ahora puede pasar error_message en el contexto, lo que es mejor.

    
    if (loginForm) {
        loginForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;

            loginMessage.textContent = ''; 
            loginMessage.className = 'message';

            try {
                const response = await fetch(LOGIN_URL, { // LOGIN_URL se define en el HTML
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest', // Importante para que Django sepa que es AJAX
                        'X-CSRFToken': CSRF_TOKEN, // CSRF_TOKEN se define en el HTML
                    },
                    body: JSON.stringify({ username, password }),
                });
                const data = await response.json();

                if (response.ok && data.redirect_url) {
                    loginMessage.textContent = data.message || 'Login exitoso!';
                    loginMessage.classList.add('success');
                    window.location.href = data.redirect_url;
                } else {
                    loginMessage.textContent = data.error || 'Login fallido. Verifique sus credenciales.';
                    loginMessage.classList.add('error');
                }
            } catch (error) {
                console.error('Login error:', error);
                loginMessage.textContent = 'Error de conexión durante el login. Intente nuevamente.';
                loginMessage.classList.add('error');
            }
        });

    }

    // Función para obtener el valor de una cookie por su nombre
    function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
    }
    const CSRF_TOKEN = getCookie('csrftoken');

});