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
            redirect: 'manual'  // 리디렉션을 수동으로 처리하도록 설정
        });

        if (response.status === 302 || response.status === 307) {
            const redirectUrl = response.headers.get('location'); // 소문자 'location' 사용
            if (redirectUrl) {
                alert('Login successful. Redirecting...');
                window.location.href = redirectUrl;
            } else {
                alert('Login failed: No redirect URL found.');
            }
        } else {
            // 응답 내용을 텍스트로 출력
            const responseText = await response.text();
            console.error('Login failed:', response.status, response.statusText, responseText);
            console.log(response.status, response.statusText, responseText);
            alert('Login failed: ' + responseText);
        }
    } catch (error) {
        console.error('Unexpected error:', error);
        alert('An unexpected error occurred. Please try again.');
    }
});
