import numpy
import io
from PIL import Image
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

# Пример функции
def sum_two_args(x, y):
    return x + y

# Hello World route
@app.get("/")
def read_root():
    return {"Hello": "World"}

# Монтируем статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")

# Инициализация шаблонов
templates = Jinja2Templates(directory="templates")

# Пример маршрута с параметром
@app.get("/some_url/{something}", response_class=HTMLResponse)
async def read_something(request: Request, something: str):
    return templates.TemplateResponse("some.html", {"request": request, "something": something})

# Функция для создания изображения
def create_some_image(some_difs):
    imx = 200
    imy = 200
    image = numpy.zeros((imx, imy, 3), dtype=numpy.uint8)  # Используем uint8
    image[0:imy//2, 0:imx//2, 0] = some_difs
    image[imy//2:, imx//2:, 2] = 240
    image[imy//2:, 0:imx//2, 1] = 240
    return image

# Маршрут для динамического изображения
@app.get("/bimage", response_class=StreamingResponse)
async def b_image(request: Request):
    image = create_some_image(100)  # Пример значения
    im = Image.fromarray(image, mode="RGB")
    imgio = io.BytesIO()
    im.save(imgio, 'JPEG')
    imgio.seek(0)
    return StreamingResponse(content=imgio, media_type="image/jpeg")

# Маршрут для статического изображения
@app.get("/image", response_class=HTMLResponse)
async def make_image(request: Request):
    image_n = "image.jpg"
    image_dyn = request.base_url.path + "bimage"
    image_st = request.url_for("static", path=f'/{image_n}')
    image = create_some_image(250)  # Пример значения
    im = Image.fromarray(image, mode="RGB")
    im.save(f"./static/{image_n}")
    # Передаем в шаблон две переменные, к которым сохранили URL
    return templates.TemplateResponse("image.html", {"request": request, "im_st": image_st, "im_dyn": image_dyn})