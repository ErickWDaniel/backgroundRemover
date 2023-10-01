import io
import warnings
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.uic import loadUi
from rembg import remove
from PIL import Image, ImageEnhance
from backgroundremoverdesign import Ui_MainWindow

class BackgroundRemoverApp(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.upload_image_btn.clicked.connect(self.upload_image)
        self.remove_background_btn.clicked.connect(self.remove_and_display_background)
        self.save_btn.clicked.connect(self.save_image)
        self.exit_btn.clicked.connect(self.close)
        self.saturation_slider.valueChanged.connect(self.update_preview)
        self.brightness_slider.valueChanged.connect(self.update_preview)
        self.contrast_slider.valueChanged.connect(self.update_preview)
        self.reset_btn.clicked.connect(self.reset_sliders)
        self.remove_and_replace_background_btn.clicked.connect(self.replace_background)

        self.input_path = ""
        self.background_path = ""  # Added: Store the path to the background image
        self.model_path = "u2net.onnx"  # Update the model path

        # Suppress DeprecationWarning for PyQt5
        warnings.filterwarnings("ignore", category=DeprecationWarning)

    def upload_image(self):
        try:
            options = QtWidgets.QFileDialog.Options()
            options |= QtWidgets.QFileDialog.DontUseNativeDialog
            self.input_path, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, "Upload Image", "", "Image Files (*.png *.jpg *.bmp)", options=options)

            if self.input_path:
                self.update_preview()
        except Exception as e:
            print(f"An error occurred during image upload: {str(e)}")

    def update_preview(self):
        if self.input_path:
            try:
                input_image = Image.open(self.input_path)

                saturation = self.saturation_slider.value() / 100.0
                brightness = self.brightness_slider.value() / 50.0 - 1.0
                contrast = self.contrast_slider.value() / 50.0

                adjusted_image = input_image.copy()

                enhancer = ImageEnhance.Color(adjusted_image)
                adjusted_image = enhancer.enhance(saturation)

                enhancer = ImageEnhance.Brightness(adjusted_image)
                adjusted_image = enhancer.enhance(1 + brightness)

                enhancer = ImageEnhance.Contrast(adjusted_image)
                adjusted_image = enhancer.enhance(contrast)

                # Display the adjusted image in the preview panel
                self.display_image(adjusted_image)

            except Exception as e:
                print(f"An error occurred during preview update: {str(e)}")

    def remove_and_display_background(self):
        if self.input_path:
            try:
                input_image = Image.open(self.input_path)

                # Get the adjusted image from the preview
                pixmap = self.preview_panel_graphic_view.scene().items()[0].pixmap()
                adjusted_image = Image.fromqimage(pixmap.toImage())

                # Remove background from the adjusted image
                output_image = remove(adjusted_image, model_path=self.model_path)

                # Display the background-removed image in the preview panel
                self.display_image(output_image)

            except Exception as e:
                print(f"An error occurred during background removal: {str(e)}")
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "Please upload an image first.")

    def replace_background(self):
        try:
            options = QtWidgets.QFileDialog.Options()
            options |= QtWidgets.QFileDialog.DontUseNativeDialog
            self.background_path, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, "Select Background Image", "", "Image Files (*.png *.jpg *.bmp)", options=options)

            if self.background_path and self.input_path:
                # Load the images
                input_image = Image.open(self.input_path)
                background_image = Image.open(self.background_path)

                # Remove the background from the input image
                removed_bg_image = remove(input_image, model_path=self.model_path)

                # Resize the images to match dimensions
                background_image = background_image.resize(removed_bg_image.size)

                # Convert images to RGBA mode for blending
                removed_bg_image = removed_bg_image.convert('RGBA')
                background_image = background_image.convert('RGBA')

                # Set the alpha (transparency) value for the input image
                alpha_value = 100  # Adjust as needed
                input_with_alpha = Image.new('RGBA', removed_bg_image.size, (0, 0, 0, alpha_value))
                input_with_alpha.paste(removed_bg_image, (0, 0), removed_bg_image)

                # Blend the images (overlay removed background on the selected background)
                blended_image = Image.alpha_composite(background_image, input_with_alpha)

                # Display the blended image
                self.display_image(blended_image)

            elif self.background_path and not self.input_path:
                QtWidgets.QMessageBox.warning(self, "Error", "Please upload an input image first.")
            elif self.input_path and not self.background_path:
                QtWidgets.QMessageBox.warning(self, "Error", "Please select a background image.")
            else:
                QtWidgets.QMessageBox.warning(self, "Error",
                                              "Please upload an input image and select a background first.")

        except Exception as e:
            print(f"An error occurred during background replacement: {str(e)}")

    def display_image(self, image):
        try:
            # Convert the image to RGB mode (if not already)
            image = image.convert("RGB")

            # Convert the PIL image to a byte array
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)

            # Create a QPixmap from the byte array
            pixmap = QtGui.QPixmap()
            pixmap.loadFromData(img_byte_arr.getvalue())

            pixmap_item = QtWidgets.QGraphicsPixmapItem(pixmap)
            scene = QtWidgets.QGraphicsScene()
            scene.addItem(pixmap_item)
            self.preview_panel_graphic_view.setScene(scene)
            self.preview_panel_graphic_view.fitInView(pixmap_item, QtCore.Qt.KeepAspectRatio)

        except Exception as e:
            print(f"An error occurred during preview update: {str(e)}")

    def save_image(self):
        if self.input_path:
            # Retrieve the displayed pixmap from the preview panel
            pixmap_item = self.preview_panel_graphic_view.scene().items()[0]
            displayed_pixmap = pixmap_item.pixmap()

            # Convert the displayed pixmap to a PIL image
            displayed_image = displayed_pixmap.toImage()
            displayed_pil_image = Image.fromqimage(displayed_image)

            # Save the displayed image
            default_output_path = "displayed_output.png"
            output_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Image", default_output_path, "PNG Files (*.png)")

            if output_path:
                displayed_pil_image.save(output_path)
                QtWidgets.QMessageBox.information(self, "Success", "Displayed image saved successfully.")
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "No image to save.")

    def reset_sliders(self):
        self.saturation_slider.setValue(50)
        self.brightness_slider.setValue(50)
        self.contrast_slider.setValue(50)

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    MainWindow = BackgroundRemoverApp()
    MainWindow.show()
    app.exec_()
