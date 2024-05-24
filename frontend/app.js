// 탭 기능
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

    document.getElementById('loading').style.display = 'block';

    const response = await fetch('https://api.udm.ai/uploadfiles/', {
        method: 'POST',
        body: formData,
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    document.getElementById('loading').style.display = 'none';

    if (response.ok) {
        const result = await response.json();
        document.getElementById('companyIntroText').value = result.company_intro;
        document.getElementById('brandIntroText').value = result.brand_intro;
        document.getElementById('productIntroText').value = result.product_intro;
    } else {
        alert('Failed to generate profiles.');
    }
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
    const additionalFileInputs = document.getElementsByClassName('additionalFileInput');
    const additionalFiles = [];

    for (let i = 0; i < additionalFileInputs.length; i++) {
        const filePurpose = additionalFileInputs[i].querySelector('[name="file_purpose"]').value;
        const fileName = additionalFileInputs[i].querySelector('[name="file_name"]').value;
        const fileContent = additionalFileInputs[i].querySelector('[name="file_content"]').value;
        additionalFiles.push(`${filePurpose}|${fileName}|${fileContent}`);
    }

    const formData = new FormData();
    formData.append('company_intro', companyIntro);
    formData.append('brand_intro', brandIntro);
    formData.append('product_intro', productIntro);
    additionalFiles.forEach((file, index) => {
        formData.append(`additional_files_${index}`, file);
    });

    const response = await fetch('https://api.udm.ai/saveeditedtext/', {
        method: 'POST',
        body: formData,
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    if (response.ok) {
        const result = await response.json();
        alert(result.message);
    } else {
        alert('Failed to save texts.');
    }
});

document.getElementById('additionalForm').addEventListener('submit', async (event) => {
    event.preventDefault();

    const token = localStorage.getItem('token');
    if (!token) {
        alert('Please log in first.');
        window.location.href = 'login.html';
        return;
    }

    const additionalFileInputs = document.getElementsByClassName('additionalFileInput');
    const additionalFiles = [];

    for (let i = 0; i < additionalFileInputs.length; i++) {
        const filePurpose = additionalFileInputs[i].querySelector('[name="file_purpose"]').value;
        const fileName = additionalFileInputs[i].querySelector('[name="file_name"]').value;
        const fileContent = additionalFileInputs[i].querySelector('[name="file_content"]').value;
        additionalFiles.push(`${filePurpose}|${fileName}|${fileContent}`);
    }

    const formData = new FormData();
    additionalFiles.forEach((file, index) => {
        formData.append(`additional_files`, file);
    });

    const response = await fetch('https://api.udm.ai/saveadditionaltext/', {
        method: 'POST',
        body: formData,
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    if (response.ok) {
        const result = await response.json();
        alert(result.message);
    } else {
        alert('Failed to upload additional file.');
    }
});

async function loadTexts() {
    const token = localStorage.getItem('token');
    if (!token) {
        alert('Please log in first.');
        window.location.href = 'login.html';
        return;
    }

    const response = await fetch('https://api.udm.ai/gettexts/', {
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

        const categories = ["product_introduction_files", "preferred_blog_content_files", "preferred_press_release_content_files", "learning_ad_copy_files", "learning_email_files"];
        categories.forEach(category => {
            const fileInputsDiv = document.getElementById(`${category}Container`);
            result.additional_files[category].forEach((file, index) => {
                const newFileInput = document.createElement('div');
                newFileInput.classList.add('additionalFileInput');
                newFileInput.innerHTML = `
                    <input type="hidden" id="filePurpose${index + 1}" name="file_purpose" value="${category.replace('_files', '')}">
                    <label for="fileName${index + 1}">파일 이름:</label>
                    <input type="text" id="fileName${index + 1}" name="file_name" value="${file.name}" required><br>
                    <textarea id="fileContent${index + 1}" name="file_content" rows="10" cols="50" required>${file.content}</textarea><br>
                    <button type="button" onclick="removeFileInput(this)">Remove this file</button><br>
                `;
                fileInputsDiv.appendChild(newFileInput);
            });
        });
    } else {
        alert('Failed to load texts.');
    }
    categories.forEach(category => addFileInput(category));
}

document.addEventListener('DOMContentLoaded', loadTexts);

function addFileInput(category) {
    const fileInputsDiv = document.getElementById(`${category}Container`);
    const newIndex = fileInputsDiv.children.length + 1;
    const newFileInput = document.createElement('div');
    newFileInput.classList.add('additionalFileInput');
    newFileInput.innerHTML = `
        <input type="hidden" id="filePurpose${newIndex}" name="file_purpose" value="${category.replace('_files', '')}">
        <label for="fileName${newIndex}">파일 이름:</label>
        <input type="text" id="fileName${newIndex}" name="file_name" required><br>
        <textarea id="fileContent${newIndex}" name="file_content" rows="10" cols="50" required></textarea><br>
        <button type="button" onclick="removeFileInput(this)">Remove this file</button><br>
    `;
    fileInputsDiv.appendChild(newFileInput);
}

function removeFileInput(button) {
    const fileInputDiv = button.parentNode;
    fileInputDiv.remove();
}

function logout() {
    localStorage.removeItem('token');
    window.location.href = 'login.html';
}

// 챗봇 링크 로드
async function loadChatbotLinks() {
    const response = await fetch('https://api.udm.ai/listchatbots/', {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
    });

    if (response.ok) {
        const chatbots = await response.json();
        const chatbotList = document.getElementById('chatbotList');
        chatbotList.innerHTML = '';

        chatbots.forEach(chatbot => {
            const listItem = document.createElement('li');
            const link = document.createElement('a');
            link.href = chatbot.url;
            link.target = '_blank';
            link.textContent = chatbot.name;
            listItem.appendChild(link);
            chatbotList.appendChild(listItem);
        });
    } else {
        alert('Failed to load chatbot links.');
    }
}

document.addEventListener('DOMContentLoaded', loadChatbotLinks);
