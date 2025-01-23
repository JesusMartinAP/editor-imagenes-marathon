import os
import zipfile
from PIL import Image
import tempfile
from concurrent.futures import ThreadPoolExecutor
import flet as ft
import sys
import logging

# Configuración de logging para evitar conflictos
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def resource_path(relative_path):
    try:
        # PyInstaller utiliza esta variable para almacenar la ruta base temporal
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def resize_image(img, output_size=(2500, 2500)):
    aspect_ratio = img.width / img.height
    if aspect_ratio > 1:
        new_width = output_size[0]
        new_height = int(new_width / aspect_ratio)
    else:
        new_height = output_size[1]
        new_width = int(new_height * aspect_ratio)

    img_resized = img.resize((new_width, new_height), Image.LANCZOS)
    background = Image.new("RGB", output_size, (255, 255, 255))
    offset = ((output_size[0] - new_width) // 2, (output_size[1] - new_height) // 2)
    background.paste(img_resized, offset)
    return background

def process_image(image_path, output_folder, output_format, original_name, output_size=(2500, 2500)):
    try:
        with Image.open(image_path) as img:
            img_resized = resize_image(img, output_size)
            output_path = os.path.join(output_folder, os.path.basename(original_name))
            if output_format.lower() == "jpg":
                img_resized.save(output_path, "JPEG")
            elif output_format.lower() == "png":
                img_resized.save(output_path, "PNG")
            elif output_format.lower() == "webp":
                img_resized.save(output_path, "WEBP")
            else:
                raise ValueError(f"Formato no soportado: {output_format}")
        return output_path
    except Exception as e:
        logger.error(f"Error procesando {image_path}: {str(e)}")
        return None

def extract_and_process_images(zip_file, output_folder, output_format):
    processed_images = []
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_file.extractall(temp_dir)
        for root, _, files in os.walk(temp_dir):
            image_files = [os.path.join(root, f) for f in files]
            with ThreadPoolExecutor() as executor:
                futures = [executor.submit(process_image, img, output_folder, output_format, img) for img in image_files]
                for future in futures:
                    result = future.result()
                    if result:
                        processed_images.append(result)
    return processed_images

def process_images(input_path, output_folder, output_format):
    os.makedirs(output_folder, exist_ok=True)
    processed_images = []
    if os.path.isfile(input_path) and input_path.lower().endswith(('.zip', '.rar')):
        with zipfile.ZipFile(input_path, 'r') as zip_file:
            processed_images = extract_and_process_images(zip_file, output_folder, output_format)
    elif os.path.isdir(input_path):
        for root, _, files in os.walk(input_path):
            image_files = [os.path.join(root, f) for f in files]
            with ThreadPoolExecutor() as executor:
                futures = [executor.submit(process_image, img, output_folder, output_format, img) for img in image_files]
                for future in futures:
                    result = future.result()
                    if result:
                        processed_images.append(result)
    else:
        raise ValueError("La entrada debe ser un archivo ZIP, RAR o una carpeta")
    return processed_images

def main(page: ft.Page):
    page.title = "Procesador de Imágenes"
    page.scroll = ft.ScrollMode.AUTO
    page.bgcolor = ft.colors.WHITE

    input_path = ft.TextField(label="Ruta de entrada", width=600, read_only=True)
    format_dropdown = ft.Dropdown(label="Formato de salida", options=[ft.dropdown.Option("jpg"), ft.dropdown.Option("png"), ft.dropdown.Option("webp")])
    output_label = ft.Text(value="", color=ft.colors.GREEN)

    # Crear el FilePicker
    file_picker = ft.FilePicker(on_result=lambda e: set_input_path(e.files[0].path if e.files else ""))
    page.overlay.append(file_picker)

    def set_input_path(path_value):
        input_path.value = path_value
        page.update()

    def select_input(e):
        file_picker.pick_files(dialog_title="Seleccionar archivo ZIP o carpeta")

    def open_output_folder(e):
        output_folder = os.path.join(os.getcwd(), "processed_images")
        if os.path.exists(output_folder):
            os.startfile(output_folder) if os.name == 'nt' else os.system(f'open "{output_folder}"')
        else:
            output_label.value = "La carpeta de salida no existe."
            page.update()

    def process_images_event(e):
        if not input_path.value:
            output_label.value = "Por favor, selecciona una entrada."
            page.update()
            return

        output_folder = os.path.join(os.getcwd(), "processed_images")
        output_format = format_dropdown.value

        try:
            processed_images = process_images(input_path.value, output_folder, output_format)
            output_label.value = f"Se procesaron {len(processed_images)} imágenes."
            page.update()
        except Exception as e:
            output_label.value = f"Error: {str(e)}"
            page.update()

    select_button = ft.ElevatedButton("Seleccionar entrada", on_click=select_input)
    process_button = ft.ElevatedButton("Procesar Imágenes", on_click=process_images_event)
    open_folder_button = ft.ElevatedButton("Abrir carpeta de salida", on_click=open_output_folder)

    signature = ft.TextButton(
        text="Desarrollado por JesusMartinAP",
        on_click=lambda e: page.launch_url("https://www.linkedin.com/in/jesus-apolaya-8814b11b8/"),
        style=ft.ButtonStyle(color=ft.colors.BLUE, padding=5),
    )

    page.add(
        ft.Row([input_path, select_button]),
        format_dropdown,
        ft.Row([process_button, open_folder_button]),
        output_label,
        ft.Row([signature], alignment=ft.MainAxisAlignment.END),
    )

if __name__ == "__main__":
    ft.app(target=main, view=ft.FLET_APP)
