import os
from fastapi import FastAPI, Depends, HTTPException, Request, Form, File, UploadFile
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm, OAuth2AuthorizationCodeBearer
from fastapi.middleware.cors import CORSMiddleware
from authlib.integrations.starlette_client import OAuth
from dotenv import load_dotenv
import httpx
from typing import List
from auth import authenticate_user, create_access_token, get_current_active_user, fake_users_db
import openai
import fitz  # PyMuPDF
from datetime import timedelta

load_dotenv()

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://api.udm.kr", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI API 키 설정
openai.api_key = os.getenv('YOUR_OPENAI_API_KEY')

# OAuth 설정
oauth = OAuth()
oauth.register(
    name='server',
    client_id=os.getenv('OAUTH_CLIENT_ID'),
    client_secret=os.getenv('OAUTH_CLIENT_SECRET'),
    authorize_url=os.getenv('OAUTH_AUTHORIZATION_URL'),
    authorize_params=None,
    access_token_url=os.getenv('OAUTH_TOKEN_URL'),
    access_token_params=None,
    redirect_uri=os.getenv('OAUTH_REDIRECT_URI'),
    client_kwargs={'scope': 'openid email profile'},
)

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=os.getenv('OAUTH_AUTHORIZATION_URL'),
    tokenUrl=os.getenv('OAUTH_TOKEN_URL')
)

REDIRECT_URI = os.getenv('REDIRECT_URI')


def extract_info_from_pdfs(files: List[UploadFile]):
    text = ""
    for file in files:
        contents = file.file.read()
        pdf_document = fitz.open(stream=contents, filetype="pdf")
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            text += page.get_text()

    return text


def generate_text_from_gpt(prompt: str):
    response = openai.Completion.create(
        model="gpt-4",
        prompt=prompt,
        max_tokens=500,
        temperature=0.7
    )
    return response.choices[0].text.strip()


@app.get('/login')
async def login(request: Request):
    redirect_uri = request.url_for('auth')
    return await oauth.server.authorize_redirect(request, redirect_uri)


@app.route('/callback')
async def auth(request: Request):
    token = await oauth.server.authorize_access_token(request)
    user = token.get('userinfo')
    access_token = create_access_token(data={"sub": user["email"]})
    return RedirectResponse(url=f"{REDIRECT_URI}?token={access_token}")


@app.get('/me')
async def me(current_user: dict = Depends(get_current_active_user)):
    return current_user


@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/uploadfiles/")
async def create_upload_files(
        role_and_goals: str = Form(...),
        files: List[UploadFile] = File(...),
        current_user: dict = Depends(get_current_active_user)
):
    extracted_text = extract_info_from_pdfs(files)

    company_intro_prompt = f"""
    Based on the following information: {role_and_goals}, {extracted_text}, 
    write a detailed company profile.
    """
    brand_intro_prompt = f"""
    Based on the following information: {role_and_goals}, {extracted_text}, 
    write a detailed brand introduction.
    """
    product_intro_prompt = f"""
    Based on the following information: {role_and_goals}, {extracted_text}, 
    write a detailed product introduction.
    """

    company_intro = generate_text_from_gpt(company_intro_prompt)
    brand_intro = generate_text_from_gpt(brand_intro_prompt)
    product_intro = generate_text_from_gpt(product_intro_prompt)

    user_dir = os.path.join("generated_texts", current_user["username"])
    os.makedirs(user_dir, exist_ok=True)

    with open(os.path.join(user_dir, "company_intro.txt"), "w") as f:
        f.write(company_intro)

    with open(os.path.join(user_dir, "brand_intro.txt"), "w") as f:
        f.write(brand_intro)

    with open(os.path.join(user_dir, "product_intro.txt"), "w") as f:
        f.write(product_intro)

    return {
        "company_intro": company_intro,
        "brand_intro": brand_intro,
        "product_intro": product_intro
    }


@app.post("/saveadditionaltext/")
async def save_additional_text(
        file_purpose: str = Form(...),
        file_name: str = Form(...),
        file_content: str = Form(...),
        current_user: dict = Depends(get_current_active_user)
):
    user_dir = os.path.join("generated_texts", current_user["username"])
    os.makedirs(user_dir, exist_ok=True)

    file_path = os.path.join(user_dir, f"{file_purpose}_{file_name}.txt")
    with open(file_path, "w") as f:
        f.write(file_content)

    return {"message": "Additional text saved successfully"}


@app.post("/saveeditedtext/")
async def save_edited_text(
        company_intro: str = Form(...),
        brand_intro: str = Form(...),
        product_intro: str = Form(...),
        additional_files: List[str] = Form([]),
        current_user: dict = Depends(get_current_active_user)
):
    user_dir = os.path.join("generated_texts", current_user["username"])
    os.makedirs(user_dir, exist_ok=True)

    with open(os.path.join(user_dir, "company_intro.txt"), "w") as f:
        f.write(company_intro)

    with open(os.path.join(user_dir, "brand_intro.txt"), "w") as f:
        f.write(brand_intro)

    with open(os.path.join(user_dir, "product_intro.txt"), "w") as f:
        f.write(product_intro)

    for file_info in additional_files:
        file_purpose, file_name, file_content = file_info.split('|')
        file_path = os.path.join(user_dir, f"{file_purpose}_{file_name}.txt")
        with open(file_path, "w") as f:
            f.write(file_content)

    return {"message": "Texts saved successfully"}


@app.get("/gettexts/")
async def get_texts(current_user: dict = Depends(get_current_active_user)):
    user_dir = os.path.join("generated_texts", current_user["username"])
    company_intro = ""
    brand_intro = ""
    product_intro = ""
    additional_files = []

    if not os.path.exists(user_dir):
        os.makedirs(user_dir)

    if os.path.exists(os.path.join(user_dir, "company_intro.txt")):
        with open(os.path.join(user_dir, "company_intro.txt"), "r") as f:
            company_intro = f.read()

    if os.path.exists(os.path.join(user_dir, "brand_intro.txt")):
        with open(os.path.join(user_dir, "brand_intro.txt"), "r") as f:
            brand_intro = f.read()

    if os.path.exists(os.path.join(user_dir, "product_intro.txt")):
        with open(os.path.join(user_dir, "product_intro.txt"), "r") as f:
            product_intro = f.read()

    for file_name in os.listdir(user_dir):
        if file_name not in ["company_intro.txt", "brand_intro.txt", "product_intro.txt"]:
            with open(os.path.join(user_dir, file_name), "r") as f:
                content = f.read()
                purpose, name = file_name.rsplit('_', 1)
                name = name.replace('.txt', '')
                additional_files.append({
                    "purpose": purpose,
                    "name": name,
                    "content": content
                })

    return {
        "company_intro": company_intro,
        "brand_intro": brand_intro,
        "product_intro": product_intro,
        "additional_files": additional_files
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, ssl_keyfile="private.key",
                ssl_certfile="certificate.crt", log_level="debug")
