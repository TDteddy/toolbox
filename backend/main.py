import asyncio

from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from datetime import timedelta
from typing import List
import openai
import fitz  # PyMuPDF
import io
import os
from auth import authenticate_user, get_current_active_user, fake_users_db, ACCESS_TOKEN_EXPIRE_MINUTES
from oauth2 import router as oauth2_router, create_access_token

app = FastAPI()
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 출처 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files 설정
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

# OpenAI API 키 설정
openai.api_key = 'YOUR_OPENAI_API_KEY'

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

@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/uploadfiles")
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

    # 사용자별 저장할 디렉토리
    user_dir = os.path.join("generated_texts", current_user["username"])
    os.makedirs(user_dir, exist_ok=True)

    # 파일 저장
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

@app.post("/saveadditionaltext")
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

@app.post("/saveeditedtext")
async def save_edited_text(
        company_intro: str = Form(...),
        brand_intro: str = Form(...),
        product_intro: str = Form(...),
        additional_files: List[str] = Form([]),
        current_user: dict = Depends(get_current_active_user)
):
    # 사용자별 저장할 디렉토리
    user_dir = os.path.join("generated_texts", current_user["username"])
    os.makedirs(user_dir, exist_ok=True)

    # 수정된 파일 저장
    with open(os.path.join(user_dir, "company_intro.txt"), "w") as f:
        f.write(company_intro)

    with open(os.path.join(user_dir, "brand_intro.txt"), "w") as f:
        f.write(brand_intro)

    with open(os.path.join(user_dir, "product_intro.txt"), "w") as f:
        f.write(product_intro)

    # 추가 파일 저장
    for file_info in additional_files:
        file_purpose, file_name, file_content = file_info.split('|')
        file_path = os.path.join(user_dir, f"{file_purpose}_{file_name}.txt")
        with open(file_path, "w") as f:
            f.write(file_content)

    return {"message": "Texts saved successfully"}

@app.get("/gettexts")
async def get_texts(current_user: dict = Depends(get_current_active_user)):
    user_dir = os.path.join("generated_texts", current_user["username"])
    company_intro = ""
    brand_intro = ""
    product_intro = ""
    additional_files = []

    # 디렉토리가 존재하지 않으면 생성
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

app.include_router(oauth2_router, prefix="/oauth2", tags=["oauth2"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="debug",
        ssl_certfile="../certificates/certificate.crt",
        ssl_keyfile="../certificates/private.key"
    )
