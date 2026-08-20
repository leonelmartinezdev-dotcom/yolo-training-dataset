# YOLO Local Annotator

Herramienta local para etiquetar imágenes a mano (bounding boxes) y generar un dataset listo para entrenar modelos YOLO, sin depender de servicios externos tipo Roboflow.

Flujo completo: **etiquetar → exportar → entrenar**.

## 1. Instalación

Requiere Python 3.9+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Esto instala solo lo necesario para la app de etiquetado (FastAPI, Pillow, PyYAML). El entrenamiento usa una dependencia aparte (ver [sección 4](#4-entrenar-un-modelo)).

## 2. Preparar el workspace

Antes de arrancar la app necesitás:

1. **Definir las clases** en `workspace/classes.txt`, una por línea:
   ```
   person
   car
   dog
   cat
   ```
2. **Copiar tus imágenes** a `workspace/images/` (o apuntar a otra carpeta con `--images`, ver abajo).

## 3. Etiquetar

```bash
source .venv/bin/activate
python app.py
```

Abrí `http://127.0.0.1:8000` en el navegador.

### Controles

| Acción | Cómo |
|---|---|
| Dibujar caja | Click y arrastrar sobre la imagen |
| Seleccionar caja | Click sobre ella |
| Mover caja | Arrastrar desde el interior |
| Redimensionar | Arrastrar desde un borde/esquina |
| Asignar clase | Teclas `1`-`9`, `0` (hasta 10 clases) o el dropdown del panel lateral |
| Ciclar clase | `[` / `]` |
| Borrar caja seleccionada | `Delete` / `Backspace` |
| Imagen siguiente / anterior | `d` / `a` (o flechas) — autoguarda al cambiar |
| Guardar manualmente | `s` |
| Deseleccionar / cancelar dibujo | `Esc` |
| Zoom | rueda del mouse |
| Pan | `Space` + arrastrar |

El progreso se guarda como archivos `.txt` en `workspace/labels/` (formato YOLO estándar: `class_id x_center y_center width height`, normalizado 0–1). Podés cerrar la app y retomar cuando quieras — el estado "etiquetada/pendiente" se calcula por la presencia de ese archivo, no hay sesión ni base de datos.

Guardar una imagen sin ninguna caja también cuenta como "etiquetada" (ejemplo negativo/background), a diferencia de una imagen nunca tocada.

### Apuntar a otras carpetas

```bash
python app.py --images /ruta/a/mis/fotos --classes /ruta/a/classes.txt --port 8080
```

## 4. Exportar el dataset

Desde la UI, botón **"Exportar dataset"**: definís los porcentajes de train/val/test (por defecto 80/20/0) y confirmás.

Esto genera (o regenera desde cero — es idempotente) la carpeta `dataset/` en formato estándar de Ultralytics:

```
dataset/
├── data.yaml
├── images/
│   ├── train/
│   └── val/
└── labels/
    ├── train/
    └── val/
```

Solo se incluyen las imágenes ya etiquetadas; las pendientes quedan afuera.

## 5. Entrenar un modelo

El entrenamiento usa [Ultralytics](https://docs.ultralytics.com/), que trae PyTorch — es pesado, por eso está en un requirements aparte:

```bash
pip install -r requirements-train.txt
python train.py
```

Por defecto usa `dataset/data.yaml`, el modelo base `yolov8n.pt`, 100 épocas e imgsz 640. Opciones:

```bash
python train.py --model yolov8s.pt --epochs 50 --imgsz 640 --batch 16 --device mps
```

(`--device` acepta `cpu`, `0` para GPU NVIDIA, `mps` para Apple Silicon; por defecto lo detecta Ultralytics solo.)

Al terminar, imprime la ruta de los mejores pesos (`runs/train/exp/weights/best.pt`) y el comando para probarlos:

```bash
yolo predict model=runs/train/exp/weights/best.pt source=<imagen_o_carpeta>
```

## Estructura del proyecto

```
yolo-training-dataset/
├── app.py                  # entry point de la app de etiquetado
├── train.py                # entry point del entrenamiento
├── requirements.txt        # deps de la app (livianas)
├── requirements-train.txt  # deps de entrenamiento (ultralytics/torch)
├── backend/                # API FastAPI + lógica de storage y export
├── frontend/               # UI (HTML/CSS/JS plano, canvas para dibujar cajas)
├── workspace/
│   ├── images/              # tus imágenes crudas
│   ├── labels/               # .txt YOLO generados al etiquetar
│   └── classes.txt           # lista de clases
├── dataset/                 # generado por "Exportar dataset"
└── runs/                    # generado por train.py
```
