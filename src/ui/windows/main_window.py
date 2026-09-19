import queue
import customtkinter as ctk
from tkinter import messagebox

from src.config.ui_config import WINDOW_WIDTH, WINDOW_HEIGHT, MIN_WIDTH, MIN_HEIGHT
from src.engine import ProcessingEngine
from src.services.file_service import FileService
from src.services.video_service import VideoService
from src.ui.components.progress_panel import ProgressPanel
from src.ui.components.settings_panel import SettingsPanel
from src.ui.components.sidebar import Sidebar
from src.ui.components.status_bar import StatusBar
from src.ui.components.video_preview import VideoPreview
from src.utils.logger import get_logger

logger = get_logger(__name__)

# How often (ms) the GUI polls the engine event queue
_POLL_INTERVAL_MS = 100


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("ClipForge AI")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(MIN_WIDTH, MIN_HEIGHT)

        self.selected_video_path = None
        self.selected_video = None

        self.file_service = FileService()

        # Thread-safe bridge between the engine and the GUI
        self.event_queue: queue.Queue = queue.Queue()
        self.engine = ProcessingEngine(self.event_queue)

        self._setup_grid()
        self._create_components()

        # Start polling for engine events on the GUI thread
        self.after(_POLL_INTERVAL_MS, self._poll_engine_events)

        logger.info("Main window initialized.")

    def _setup_grid(self):
        self.grid_columnconfigure(0, weight=0, minsize=220)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0, minsize=280)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

    def _create_components(self):
        # Sidebar
        self.sidebar = Sidebar(
            self,
            on_browse=self.on_browse_video,
            on_process=self.on_start_process,
            on_settings=self.on_open_settings,
            on_cancel=self.on_cancel_process,
        )
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=10, pady=10)

        # Video Preview
        self.video_preview = VideoPreview(self)
        self.video_preview.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        # Settings Panel
        self.settings_panel = SettingsPanel(self)
        self.settings_panel.grid(row=0, column=2, rowspan=2, sticky="nsew", padx=10, pady=10)

        # Bottom Bar Frame
        self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_frame.grid(row=1, column=1, columnspan=2, sticky="ew", padx=(0, 10), pady=(0, 10))
        self.bottom_frame.grid_columnconfigure(0, weight=1)
        self.bottom_frame.grid_columnconfigure(1, weight=2)

        self.status_bar = StatusBar(self.bottom_frame)
        self.status_bar.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self.progress_panel = ProgressPanel(self.bottom_frame)
        self.progress_panel.grid(row=0, column=1, sticky="ew")

    # -- Callbacks ---------------------------------------------------------

    def on_browse_video(self):
        logger.info("Browse video clicked.")
        path = self.file_service.open_video_dialog()

        if path:
            self.status_bar.set_status("Loading video...")
            self.update()

            try:
                video = VideoService.get_video_metadata(path)
                preview_timestamp = 1.0 if video.duration > 1.0 else 0.0
                preview_img = VideoService.get_preview_frame(path, timestamp=preview_timestamp)

                self.selected_video_path = path
                self.selected_video = video

                self.sidebar.set_selected_file(video.filename)
                self.video_preview.show_video_info(video, preview_img)

                self.status_bar.set_status("Video loaded")
                logger.info(f"Video loaded successfully: {video.filename}")

            except Exception as exc:  # noqa: BLE001
                logger.error(f"Failed to load video: {exc}", exc_info=True)
                self.status_bar.set_status("Error loading video")
                messagebox.showerror("Video Load Error", f"Failed to load video:\n\n{exc}")

                self.video_preview.reset()
                self.selected_video_path = None
                self.selected_video = None
                self.sidebar.set_selected_file("No video selected")
                self.sidebar.set_idle_state()

    def on_start_process(self):
        if self.selected_video_path is None:
            messagebox.showwarning("No Video", "Please select a video first.")
            return

        logger.info("Start process clicked.")
        self.sidebar.set_processing_state()
        self.status_bar.set_status("Starting...")
        self.progress_panel.set_progress(0.0, "Starting...")

        # Launch the engine on a background thread
        self.engine.start(self.selected_video_path)

    def on_cancel_process(self):
        logger.info("Cancel clicked.")
        self.engine.cancel()
        self.status_bar.set_status("Cancelling...")
        self.sidebar.cancel_btn.configure(state="disabled")

    def on_open_settings(self):
        logger.info("Settings button clicked. (Settings window not yet implemented)")

    # -- Engine event handling (GUI thread) --------------------------------

    def _poll_engine_events(self):
        """Drain the engine event queue and update the UI. Runs on GUI thread."""
        try:
            while True:
                event = self.event_queue.get_nowait()
                self._handle_engine_event(event)
        except queue.Empty:
            pass

        # Reschedule polling
        self.after(_POLL_INTERVAL_MS, self._poll_engine_events)

    def _handle_engine_event(self, event):
        """Apply a single ProgressEvent to the UI."""
        if event.error:
            self.status_bar.set_status(f"Error: {event.stage}")
            self.progress_panel.set_progress(event.progress, event.stage)
            messagebox.showerror("Processing Error", event.error)
            self.sidebar.set_idle_state()
            return

        self.status_bar.set_status(event.message or event.stage)
        self.progress_panel.set_progress(event.progress, event.stage)

        if event.is_finished:
            self.sidebar.set_idle_state()
            logger.info(f"Engine finished. Stage: {event.stage}")