function openTab(evt, tabName) {
    var i, tabcontent, tablinks;
    tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }
    tablinks = document.getElementsByClassName("tablinks");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }
    document.getElementById(tabName).style.display = "block";
    evt.currentTarget.className += " active";
}

// Default open tab
document.getElementsByClassName('tablinks')[0].click();

document.getElementById('uploadForm').addEventListener('submit', async (event) => {
    event.preventDefault();

    const token = localStorage.getItem('token');
    if (!token) {
        alert('Please log in first.');
        window.location.href = 'login.html';
        return;
    }

    const roleAndGoals = document.getElementById('roleAndGoals').value;
    const fileInput = document.getElementById('fileInput');
    const files = fileInput.files;
    const formData = new FormData();
    formData.append('role_and_goals', roleAndGoals);
    for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
    }

    const response = await fetch('http://127.0.0.1:8000/uploadfiles/', {
        method: 'POST',
        body: formData,
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    const result = await response.json();
    document.getElementById('companyIntroText').value = result.company_intro;
    document.getElementById('brandIntroText').value = result.brand_intro;
    document.getElementById('productIntroText').value = result.product_intro;
});

document.getElementById('saveForm').addEventListener('submit', async (event) => {
    event.preventDefault();

    const token = localStorage.getItem('token');
    if (!token) {
        alert('Please log in first.');
        window.location.href = 'login.html';
        return;
    }

    const companyIntro = document.getElementById('companyIntroText').value;
    const brandIntro = document.getElementById('brandIntroText').value;
    const productIntro = document.getElementById('productIntroText').value;
    const formData = new FormData();
    formData.append('company_intro', companyIntro);
    formData.append('brand_intro', brandIntro);
    formData.append('product_intro', productIntro);

    const response = await fetch('http://127.0.0.1:8000/saveeditedtext/', {
        method: 'POST',
        body: formData,
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    const result = await response.json();
    alert(result.message);
});

async function loadTexts() {
    const token = localStorage.getItem('token');
    if (!token) {
        alert('Please log in first.');
        window.location.href = 'login.html';
        return;
    }

    const response = await fetch('http://127.0.0.1:8000/gettexts/', {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    if (response.ok) {
        const result = await response.json();
        document.getElementById('companyIntroText').value = result.company_intro;
        document.getElementById('brandIntroText').value = result.brand_intro;
        document.getElementById('productIntroText').value = result.product_intro;
    } else {
        alert('Failed to load texts.');
    }
}

document.addEventListener('DOMContentLoaded', loadTexts);

function logout() {
    localStorage.removeItem('token');
    window.location.href = 'login.html';
}
