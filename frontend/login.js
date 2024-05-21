document.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const clientId = urlParams.get('client_id');
    const redirectUri = urlParams.get('redirect_uri');
    const responseType = urlParams.get('response_type');
    const state = urlParams.get('state');

    if (clientId) {
        document.getElementById('client_id').value = clientId;
        document.getElementById('redirect_uri').value = redirectUri;
        document.getElementById('response_type').value = responseType;
        document.getElementById('state').value = state;
    }
});

document.getElementById('loginForm').addEventListener('submit', async (event) => {
    event.preventDefault();

    const formData = new FormData(document.getElementById('loginForm'));
    const clientId = document.getElementById('client_id').value;

    try {
        const loginUrl = clientId ? 'https://api.udm.ai/oauth2/login' : 'https://api.udm.ai/login';
        const response = await fetch(loginUrl, {
            method: 'POST',
            body: formData,
        });

        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('token', data.access_token); // 토큰 저장
            if (data.redirect_url) {
                alert('Login successful. Redirecting...');
                window.location.href = data.redirect_url;
            } else {
                alert('Login successful.');
                window.location.href = 'index.html'; // 로그인 후 index.html로 리다이렉션
            }
        } else {
            const responseText = await response.text();
            console.error('Login failed:', response.status, response.statusText, responseText);
            alert('Login failed: ' + responseText);
        }
    } catch (error) {
        console.error('Unexpected error:', error);
        alert('An unexpected error occurred. Please try again.');
    }
});