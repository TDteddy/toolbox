from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from datetime import timedelta
from typing import List
import fitz  # PyMuPDF
import io
import os
import dotenv
from openai import OpenAI
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import asyncio

from auth import authenticate_user, get_current_active_user, fake_users_db, ACCESS_TOKEN_EXPIRE_MINUTES
from oauth2 import router as oauth2_router, create_access_token

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:8000",
    "https://localhost",
    "https://localhost:8080",
    "https://localhost:8000",
    "https://chat.openai.com",
    "https://api.udm.ai",
    "https://udm.ai",
    "http://udm.ai",
    "http://api.udm.ai",
    "http://udm.ai:8000",
    "https://chatgpt.com",
    "http://chatgpt.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # 모든 메서드 허용
    allow_headers=["*"],
    expose_headers=["location", "Location"],  # 리디렉션 URL을 클라이언트에서 접근할 수 있도록 허용
)

app.mount("/static", StaticFiles(directory="../frontend"), name="static")

#env
load_dotenv()
# OpenAI API 키 설정
openai=OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
    )
    return response.choices[0].message.content.strip()

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
    write a detailed company profile to korean.
    """
    brand_intro_prompt = f"""
    Based on the following information: {role_and_goals}, {extracted_text}, 
    write a detailed brand introduction to korean.
    """

    company_intro = generate_text_from_gpt(company_intro_prompt)
    brand_intro = generate_text_from_gpt(brand_intro_prompt)

    # 사용자별 저장할 디렉토리
    user_dir = os.path.join("generated_texts", current_user["username"])
    os.makedirs(user_dir, exist_ok=True)

    # 파일 저장
    with open(os.path.join(user_dir, "company_intro.txt"), "w", encoding="utf-8") as f:
        f.write(company_intro)

    with open(os.path.join(user_dir, "brand_intro.txt"), "w", encoding="utf-8") as f:
        f.write(brand_intro)

    return {
        "company_intro": company_intro,
        "brand_intro": brand_intro
    }

@app.post("/saveadditionaltext")
async def save_additional_text(
        additional_files: List[str] = Form([]),
        current_user: dict = Depends(get_current_active_user)
):
    user_dir = os.path.join("generated_texts", current_user["username"])
    os.makedirs(user_dir, exist_ok=True)

    logger.info(f"additional_files: {additional_files}")

    for file_info in additional_files:
        try:
            file_purpose, file_name, file_content = file_info.split('|')
            file_path = os.path.join(user_dir, f"{file_purpose}_{file_name}.txt")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(file_content)
            logger.info(f"File saved: {file_path}")
        except Exception as e:
            logger.error(f"Error saving file: {file_path}, Error: {e}")
            raise HTTPException(status_code=500, detail=f"Error saving file: {file_name}")

    return {"message": "Additional text saved successfully"}


@app.post("/saveeditedtext")
async def save_edited_text(
        company_intro: str = Form(...),
        brand_intro: str = Form(...),
        additional_files: List[str] = Form([]),
        current_user: dict = Depends(get_current_active_user)
):
    # 사용자별 저장할 디렉토리
    user_dir = os.path.join("generated_texts", current_user["username"])
    os.makedirs(user_dir, exist_ok=True)

    # 수정된 파일 저장
    with open(os.path.join(user_dir, "company_intro.txt"), "w", encoding="utf-8") as f:
        f.write(company_intro)

    with open(os.path.join(user_dir, "brand_intro.txt"), "w", encoding="utf-8") as f:
        f.write(brand_intro)


    # 추가 파일 저장
    for file_info in additional_files:
        try:
            file_purpose, file_name, file_content = file_info.split('|', 2)
            category_dir = os.path.join(user_dir, file_purpose.replace(" ", "_").lower())
            os.makedirs(category_dir, exist_ok=True)
            file_path = os.path.join(category_dir, f"{file_name}.txt")
            with open(file_path, "w") as f:
                f.write(file_content)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid file information format")

    return {"message": "Texts saved successfully"}

@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
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

@app.get("/gettexts")
async def get_texts(current_user: dict = Depends(get_current_active_user)):
    user_dir = os.path.join("generated_texts", current_user["username"])
    company_intro = ""
    brand_intro = ""
    additional_files = {
        "product_introduction_files": [],
        "preferred_blog_content_files": [],
        "preferred_press_release_content_files": [],
        "learning_ad_copy_files": [],
        "learning_email_files": []
    }

    # 디렉토리가 존재하지 않으면 생성
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)

    # 회사, 브랜드, 제품 소개 파일 읽기
    if os.path.exists(os.path.join(user_dir, "company_intro.txt")):
        with open(os.path.join(user_dir, "company_intro.txt"), "r", encoding="utf-8") as f:
            company_intro = f.read()

    if os.path.exists(os.path.join(user_dir, "brand_intro.txt")):
        with open(os.path.join(user_dir, "brand_intro.txt"), "r", encoding="utf-8") as f:
            brand_intro = f.read()

    # 추가 파일 읽기
    for file_name in os.listdir(user_dir):
        if file_name not in ["company_intro.txt", "brand_intro.txt"]:
            file_path = os.path.join(user_dir, file_name)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    purpose, name = file_name.rsplit('_', 1)
                    name = name.replace('.txt', '')
                    additional_files[f"{purpose}_files"].append({
                        "name": name,
                        "content": content
                    })
                    logger.info(f"Loaded file: {file_path}")
            except Exception as e:
                logger.error(f"Error loading file: {file_path}, Error: {e}")

    return {
        "company_intro": company_intro,
        "brand_intro": brand_intro,
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