(function () {
    var feedback = document.getElementById('authFeedback');
    var loginForm = document.getElementById('loginForm');
    var registerForm = document.getElementById('registerForm');
    var authForms = document.getElementById('authForms');
    var signedInPanel = document.getElementById('signedInPanel');

    function returnPage() {
        var requestedPage = new URLSearchParams(window.location.search).get('next');
        var allowedPages = ['menu.html', 'reservation.html', 'order.html'];
        return allowedPages.indexOf(requestedPage) !== -1 ? requestedPage : 'index.html';
    }

    function showFeedback(message, isError) {
        feedback.textContent = message;
        feedback.className = isError ? 'alert alert-danger' : 'alert alert-success';
    }

    function handleResponse(response) {
        return response.json().then(function (data) {
            if (!response.ok) {
                throw new Error(data.error || 'Account request failed.');
            }
            return data;
        });
    }

    function submitAccountForm(form, endpoint) {
        form.addEventListener('submit', function (event) {
            event.preventDefault();
            if (!form.reportValidity()) {
                return;
            }

            var submitButton = form.querySelector('[type="submit"]');
            submitButton.disabled = true;
            var formValues = Object.fromEntries(new FormData(form).entries());

            fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formValues)
            })
                .then(handleResponse)
                .then(function () {
                    window.location.href = returnPage();
                })
                .catch(function (error) {
                    showFeedback(error.message, true);
                })
                .finally(function () {
                    submitButton.disabled = false;
                });
        });
    }

    document.getElementById('showLoginButton').addEventListener('click', function () {
        loginForm.hidden = false;
        registerForm.hidden = true;
        this.className = 'btn btn-primary w-50';
        this.setAttribute('aria-pressed', 'true');
        var registerButton = document.getElementById('showRegisterButton');
        registerButton.className = 'btn btn-outline-primary w-50';
        registerButton.setAttribute('aria-pressed', 'false');
        feedback.textContent = '';
        feedback.className = '';
    });

    document.getElementById('showRegisterButton').addEventListener('click', function () {
        loginForm.hidden = true;
        registerForm.hidden = false;
        this.className = 'btn btn-primary w-50';
        this.setAttribute('aria-pressed', 'true');
        var loginButton = document.getElementById('showLoginButton');
        loginButton.className = 'btn btn-outline-primary w-50';
        loginButton.setAttribute('aria-pressed', 'false');
        feedback.textContent = '';
        feedback.className = '';
    });

    submitAccountForm(loginForm, '/api/auth/login');
    submitAccountForm(registerForm, '/api/auth/register');

    document.getElementById('logoutButton').addEventListener('click', function () {
        fetch('/api/auth/logout', { method: 'POST' })
            .then(handleResponse)
            .then(function () {
                window.location.reload();
            })
            .catch(function (error) {
                showFeedback(error.message, true);
            });
    });

    fetch('/api/auth/me')
        .then(handleResponse)
        .then(function (data) {
            if (!data.authenticated) {
                return;
            }
            authForms.hidden = true;
            signedInPanel.hidden = false;
            document.getElementById('signedInDetails').textContent =
                data.user.name + ' · ' + data.user.email + ' · ' + data.user.phone;
        })
        .catch(function (error) {
            showFeedback(error.message, true);
        });
}());