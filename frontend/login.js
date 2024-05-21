document.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const clientId = urlParams.get('client_id');
    const redirectUri = urlParams.get('redirect_uri');
    const responseType = urlParams.get('response_type');
    const state = urlParams.get('state');

    document.getElementById('client_id').value = clientId;
    document.getElementById('redirect_uri').value = redirectUri;
    document.getElementById('response_type').value = responseType;
    document.getElementById('state').value = state;
});

document.getElementById('loginForm').addEventListener('submit', async (event) => {
    event.preventDefault();

    const formData = new FormData(document.getElementById('loginForm'));

    try {
        const response = await fetch('https://api.udm.ai/oauth2/login', {
            method: 'POST',
            body: formData,
        });

        if (response.ok) {
            const data = await response.json();
            if (data.redirect_url) {
                alert('로그인성공!');
                window.location.href = data.redirect_url;
            } else {
                alert('Login failed: No redirect URL found.');
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
