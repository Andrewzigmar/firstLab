from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from PIL import Image
import numpy as np
import io
import uuid
import matplotlib.pyplot as plt
from typing import List
import httpx
import logging
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Монтирование статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


RECAPTCHA_SITE_KEY = "6LcN1d8qAAAAADptWviC_Vi3Aq7oLg38gCLJ6Ru3"
RECAPTCHA_SECRET_KEY = "6LcN1d8qAAAAANp1TcYaCt01bLyg8gp-gEP1dGSH"

def apply_periodic_function(image: Image.Image, function: str, period: float) -> Image.Image:
    """
    Применяет периодическую функцию (sin или cos) к изображению.
    """
    img_array = np.array(image)
    height, width, _ = img_array.shape

    # Создаем сетку координат
    x = np.arange(width)
    y = np.arange(height)
    x, y = np.meshgrid(x, y)

    # Вычисляем аргумент функции
    argument = 2 * np.pi * (x + y) / period

    # Применяем выбранную функцию
    if function == "sin":
        multiplier = np.sin(argument)
    elif function == "cos":
        multiplier = np.cos(argument)
    else:
        raise ValueError("Неизвестная функция. Допустимые значения: 'sin', 'cos'")

    # Нормировка в диапазон [0, 1]
    multiplier = (multiplier + 1) / 2

    # Применяем функцию к каждому каналу (R, G, B)
    for channel in range(3):
        img_array[:, :, channel] = np.clip(img_array[:, :, channel] * multiplier, 0, 255)

    return Image.fromarray(img_array.astype(np.uint8))

def plot_color_distribution(image: Image.Image, title: str, filename: str):
    """
    Строит график распределения цветов для изображения.
    """
    img_array = np.array(image)
    colors = ('r', 'g', 'b')
    channel_ids = (0, 1, 2)

    plt.figure()
    for channel_id, color in zip(channel_ids, colors):
        histogram, _ = np.histogram(img_array[:, :, channel_id], bins=256, range=(0, 256))
        plt.plot(histogram, color=color)
    plt.title(title)
    plt.xlabel("Значение цвета")
    plt.ylabel("Частота")
    plt.savefig(filename)
    plt.close()

async def verify_recaptcha(token: str) -> bool:
    """
    Проверяет токен reCAPTCHA через API Google.
    """
    if not token:
        logger.error("Токен reCAPTCHA отсутствует")
        return False

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://www.google.com/recaptcha/api/siteverify",
                data={"secret": RECAPTCHA_SECRET_KEY, "response": token}
            )
            result = response.json()
            logger.info(f"Результат проверки reCAPTCHA: {result}")
            return result.get("success", False)
        except Exception as e:
            logger.error(f"Ошибка при проверке reCAPTCHA: {e}")
            return False

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Главная страница.
    """
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/forms", response_class=HTMLResponse)
async def show_form(request: Request):
    """
    Отображает форму с reCAPTCHA.
    """
    return templates.TemplateResponse("forms.html", {"request": request, "recaptcha_site_key": RECAPTCHA_SITE_KEY})

@app.post("/forms", response_class=HTMLResponse)
async def process_image(
    request: Request,
    function: str = Form(),
    period: float = Form(),
    files: List[UploadFile] = File(...),
    g_recaptcha_response: str = Form(None),  # Токен reCAPTCHA
):


    images = []

    for file in files:
        try:
            content = await file.read()
            original_image = Image.open(io.BytesIO(content)).convert("RGB")

            # Применяем периодическую функцию
            processed_image = apply_periodic_function(original_image, function, period)

            # Генерация уникальных имен файлов
            original_filename = f"static/{uuid.uuid4().hex}_original.jpg"
            processed_filename = f"static/{uuid.uuid4().hex}_processed.jpg"
            original_histogram_filename = f"static/{uuid.uuid4().hex}_original_histogram.png"
            processed_histogram_filename = f"static/{uuid.uuid4().hex}_processed_histogram.png"

            # Сохраняем изображения и графики
            original_image.save(original_filename)
            processed_image.save(processed_filename)
            plot_color_distribution(original_image, "Распределение цветов (исходное)", original_histogram_filename)
            plot_color_distribution(processed_image, "Распределение цветов (обработанное)", processed_histogram_filename)

            images.append({
                "original": original_filename,
                "processed": processed_filename,
                "original_histogram": original_histogram_filename,
                "processed_histogram": processed_histogram_filename,
            })
        except Exception as e:
            logger.error(f"Ошибка обработки файла {file.filename}: {e}")
            raise HTTPException(status_code=400, detail=f"Ошибка обработки файла {file.filename}: {str(e)}")

    return templates.TemplateResponse("forms.html", {
        "request": request,
        "images": images,
    })