import customtkinter as ctk
from PIL import Image
from src.models.video import Video

class VideoPreview(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) # Allow image area to stretch
        
        self.placeholder_label = ctk.CTkLabel(
            self, 
            text="No Video Selected\n\nClick 'Browse Video' to begin", 
            font=ctk.CTkFont(size=16), 
            text_color="gray"
        )
        self.placeholder_label.grid(row=0, column=0, rowspan=2)
        
        self.image_label = None
        self.info_frame = None
        self.ctk_image = None

    def show_video_info(self, video: Video, preview_image: Image.Image):
        """Displays the video preview image and metadata."""
        self.placeholder_label.grid_remove()
        
        # Clean up previous widgets
        if self.info_frame:
            self.info_frame.destroy()
        if self.image_label:
            self.image_label.destroy()

        # Resize image to fit nicely without breaking aspect ratio
        img_width, img_height = preview_image.size
        max_w, max_h = 450, 350
        
        ratio = min(max_w / img_width, max_h / img_height)
        new_w = int(img_width * ratio)
        new_h = int(img_height * ratio)
        
        resized_img = preview_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        self.ctk_image = ctk.CTkImage(light_image=resized_img, dark_image=resized_img, size=(new_w, new_h))
        
        self.image_label = ctk.CTkLabel(self, image=self.ctk_image, text="")
        self.image_label.grid(row=0, column=0, pady=(20, 10))

        # Info Frame
        self.info_frame = ctk.CTkFrame(self)
        self.info_frame.grid(row=1, column=0, sticky="n", padx=20, pady=(0, 20))
        self.info_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            self.info_frame, 
            text=video.filename, 
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, pady=5)
        
        details_text = (
            f"Duration: {video.formatted_duration}  |  "
            f"Resolution: {video.resolution}  |  "
            f"FPS: {video.fps:.2f}  |  "
            f"Size: {video.formatted_file_size}"
        )
        ctk.CTkLabel(
            self.info_frame, 
            text=details_text, 
            font=ctk.CTkFont(size=13), 
            text_color="gray"
        ).grid(row=1, column=0)

    def reset(self):
        """Clears the preview and shows the placeholder."""
        if self.info_frame:
            self.info_frame.destroy()
            self.info_frame = None
        if self.image_label:
            self.image_label.destroy()
            self.image_label = None
        self.ctk_image = None
        self.placeholder_label.grid(row=0, column=0, rowspan=2)