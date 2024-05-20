document.addEventListener('DOMContentLoaded', async () => {
    const token = localStorage.getItem('token');
    if (token) {
        const response = await fetch('https://api.udm.kr/me', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            window.location.href = 'index.html';
            return;
        }
    }

    document.getElementById('oauthLoginButton').addEventListener('click', () => {
        window.location.href = 'https://api.udm.kr/login';
    });

    document.getElementById('loginForm').addEventListener('submit', async (event) => {
        event.preventDefault();

        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        const response = await fetch('https://api.udm.kr/token', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (response.ok) {
            localStorage.setItem('token', result.access_token);
            window.location.href = 'index.html';
        } else {
            alert(result.detail);
        }
    });
});
