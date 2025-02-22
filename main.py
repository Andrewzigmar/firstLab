from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageDraw
import hashlib
import io
import os
from typing import List

app = FastAPI()

# Монтируем статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")

# Инициализация шаблонов
templates = Jinja2Templates(directory="templates")

# Корневой маршрут
@app.get("/")
def read_root():
    return {"Hello": "World"}

# Маршрут с параметром
@app.get("/some_url/{something}", response_class=HTMLResponse)
async def read_something(request: Request, something: str):
    return templates.TemplateResponse("some.html", {"request": request, "something": something})

# Маршрут для формы
@app.get("/forms", response_class=HTMLResponse)
async def make_image(request: Request):
    return templates.TemplateResponse("forms.html", {"request": request})

# Маршрут для обработки формы
@app.post("/image_form", response_class=HTMLResponse)
async def make_image(
    request: Request,
    name_op: str = Form(),
    number_op: int = Form(),
    r: int = Form(),
    g: int = Form(),
    b: int = Form(),
    files: List[UploadFile] = File(description="Multiple files as UploadFile"),
):
    ready = False
    if files and len(files) > 0 and files[0].filename:
        ready = True

    images = []
    if ready:
        # Преобразуем имена файлов в хеш-строку
        images = ["static/" + hashlib.sha256(file.filename.encode('utf-8')).hexdigest() + ".jpg" for file in files]

        # Чтение содержимого файлов
        content = [await file.read() for file in files]

        # Создаем объекты Image типа RGB размером 200 на 200
        p_images = [Image.open(io.BytesIO(con)).convert("RGB").resize((200, 200)) for con in content]

        # Сохраняем изображения в папке static
        for i in range(len(p_images)):
            draw = ImageDraw.Draw(p_images[i])
            # Рисуем эллипс с заданным цветом и окантовкой
            draw.ellipse((100, 100, 150, 200 + number_op), fill=(r, g, b), outline=(0, 0, 0))
            # Сохраняем изображение
            p_images[i].save(images[i], 'JPEG')

    # Возвращаем HTML с параметрами-ссылками на изображения
    return templates.TemplateResponse("forms.html", {"request": request, "ready": ready, "images": images})