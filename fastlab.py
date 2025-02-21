import fastapi.responses
import numpy
import io
from PIL import Image
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
app = FastAPI()
def sum_two_args(x,y):
 return x+y
# Hello World route
@app.get("/")
def read_root():
 return {"Hello": "World"}
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
# возвращаем some.html, сгенерированный из шаблона
# передав туда одно значение something
@app.get("/some_url/{something}", response_class=HTMLResponse)
async def read_something(request: Request, something: str):
 return templates.TemplateResponse("some.html", {"request": request,
"something": something})
def create_some_image(some_difs):
 imx = 200
 imy = 200
 image = numpy.zeros((imx, imy, 3), dtype=numpy.int8)
 image[0:imy // 2, 0:imx // 2, 0] = some_difs
 image[imy // 2:, imx // 2:, 2] = 240
 image[imy // 2:, 0:imx // 2, 1] = 240
 return image



@app.get("/bimage", response_class=fastapi.responses.StreamingResponse)
async def b_image(request: Request):
 image = create_some_image(100)
 im = Image.fromarray(image, mode="RGB")

 imgio = io.BytesIO()
 im.save(imgio, 'JPEG')
 imgio.seek(0)

 return fastapi.responses.StreamingResponse(content=imgio, media_type="image/jpeg")

@app.get("/image", response_class=HTMLResponse)
async def make_image(request: Request):
 image_n = "image.jpg"
 image_dyn = request.base_url.path+"bimage"
 image_st = request.url_for("static", path = f'/{image_n}')
 image = create_some_image(250)
 im = Image.fromarray(image, mode="RGB")
 im.save(f"./static/{image_n}")
 # передаем в шаблон две переменные, к которым сохранили url
 return templates.TemplateResponse("image.html", {"request": request,
"im_st":image_st, "im_dyn": image_dyn})