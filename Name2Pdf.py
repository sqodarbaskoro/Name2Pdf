"""
PDF Renamer by Visible Title
A production-ready desktop application for renaming PDF files based on visible title text.
"""
import json
import logging
import re
import shutil
import sys
import threading
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Optional

from pypdf import PdfReader

# --- GUI Libraries ---
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
APP_NAME = "PDF Renamer by Visible Title"
VERSION = "1.0.0"
CONFIG_FILE = Path(__file__).parent / "config.json"
LOG_DIR = Path(__file__).parent / "logs"
LOG_FILE = LOG_DIR / "pdf_renamer.log"

# Default configuration (used if config.json is missing)
DEFAULT_CONFIG = {
    "app": {
        "name": APP_NAME,
        "version": VERSION
    },
    "author": {
        "name": "Sri Yanto Qodarbaskoro",
        "email": "sqodarbaskoro@gmail.com",
        "linkedin_url": "https://www.linkedin.com/in/sqodarbaskoro"
    },
    "settings": {
        "log_level": "INFO",
        "log_to_file": True,
        "max_filename_length": 255
    }
}


# ----------------------------------------------------------------------
# Configuration and Logging Setup
# ----------------------------------------------------------------------
def load_config() -> dict:
    """Load configuration from config.json or return defaults."""
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Merge with defaults to ensure all keys exist
                merged_config = DEFAULT_CONFIG.copy()
                merged_config.update(config)
                return merged_config
        else:
            # Create default config file
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(DEFAULT_CONFIG, f, indent=2)
            return DEFAULT_CONFIG
    except Exception as e:
        logging.warning(f"Error loading config: {e}. Using defaults.")
        return DEFAULT_CONFIG


def setup_logging(config: dict) -> None:
    """Setup logging configuration."""
    log_level = getattr(logging, config.get("settings", {}).get("log_level", "INFO").upper(), logging.INFO)
    log_to_file = config.get("settings", {}).get("log_to_file", True)
    
    # Create logs directory if needed
    if log_to_file:
        LOG_DIR.mkdir(exist_ok=True)
    
    # Configure logging
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_to_file:
        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        handlers.append(file_handler)
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=handlers
    )


# ----------------------------------------------------------------------
# Main Application Class
# ----------------------------------------------------------------------
class PdfRenamerApp:
    """Main application class for PDF Renamer."""
    
    def __init__(self, root: tk.Tk, config: dict):
        """
        Initialize the PDF Renamer application.
        
        Args:
            root: Tkinter root window
            config: Configuration dictionary
        """
        self.root = root
        self.config = config
        self.app_name = config.get("app", {}).get("name", APP_NAME)
        self.version = config.get("app", {}).get("version", VERSION)
        self.author_info = config.get("author", {})
        self.max_filename_length = config.get("settings", {}).get("max_filename_length", 255)
        
        # Color scheme
        self.colors = {
            'bg_primary': '#f0f0f0',
            'bg_secondary': '#ffffff',
            'accent': '#4a90e2',
            'accent_hover': '#357abd',
            'success': '#28a745',
            'warning': '#ffc107',
            'error': '#dc3545',
            'text_primary': '#212529',
            'text_secondary': '#6c757d',
            'border': '#dee2e6'
        }
        
        self.root.title(f"{self.app_name} v{self.version}")
        self.root.geometry("750x700")
        self.root.minsize(700, 600)
        self.root.configure(bg=self.colors['bg_primary'])
        
        # Initialize Tkinter variables
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.in_place = tk.BooleanVar()
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="Ready")
        self.file_count_var = tk.StringVar(value="0 PDF files found")
        
        # Processing state
        self.is_processing = False
        self.total_files = 0
        self.processed_files = 0
        
        self._setup_styles()
        self._create_ui()
        self._setup_tooltips()
        logging.info(f"{self.app_name} v{self.version} started")

    def _setup_styles(self) -> None:
        """Setup custom styles for ttk widgets."""
        style = ttk.Style()
        
        # Configure styles
        style.configure('Title.TLabel', font=('Segoe UI', 14, 'bold'), background=self.colors['bg_primary'])
        style.configure('Heading.TLabel', font=('Segoe UI', 10, 'bold'), background=self.colors['bg_secondary'])
        style.configure('Accent.TButton', font=('Segoe UI', 10, 'bold'))
        style.configure('Action.TButton', font=('Segoe UI', 11, 'bold'))
        
        # Configure button colors
        style.map('Accent.TButton',
                 background=[('active', self.colors['accent_hover']),
                            ('!disabled', self.colors['accent'])])
        
        style.map('Action.TButton',
                 background=[('active', self.colors['accent_hover']),
                            ('!disabled', self.colors['accent'])])
    
    def _create_ui(self) -> None:
        """Create the user interface."""
        # Create Menu Bar
        self.menubar = tk.Menu(self.root, bg=self.colors['bg_secondary'], fg=self.colors['text_primary'])
        self.root.config(menu=self.menubar)
        
        # Help menu
        self.help_menu = tk.Menu(self.menubar, tearoff=0, bg=self.colors['bg_secondary'], fg=self.colors['text_primary'])
        self.menubar.add_cascade(label="Help", menu=self.help_menu)
        self.help_menu.add_command(label="About", command=self.show_about_window)
        
        # Header Frame with Title
        header_frame = tk.Frame(self.root, bg=self.colors['bg_primary'], pady=15)
        header_frame.pack(fill="x")
        
        title_label = tk.Label(
            header_frame,
            text="📄 PDF Renamer",
            font=('Segoe UI', 18, 'bold'),
            bg=self.colors['bg_primary'],
            fg=self.colors['accent']
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            header_frame,
            text="Rename PDFs based on visible title text",
            font=('Segoe UI', 9),
            bg=self.colors['bg_primary'],
            fg=self.colors['text_secondary']
        )
        subtitle_label.pack(pady=(5, 0))
        
        # Main Frame
        main_frame = tk.Frame(self.root, bg=self.colors['bg_primary'], padx=15, pady=10)
        main_frame.pack(fill="both", expand=True)
        
        # Input Folder Selection
        input_frame = tk.LabelFrame(
            main_frame,
            text=" 📁 Step 1: Select Input Folder",
            font=('Segoe UI', 10, 'bold'),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary'],
            padx=15,
            pady=12,
            relief='flat',
            bd=1
        )
        input_frame.pack(fill="x", expand=True, pady=(0, 10))
        
        input_inner = tk.Frame(input_frame, bg=self.colors['bg_secondary'])
        input_inner.pack(fill="x")
        
        self.input_entry = tk.Entry(
            input_inner,
            textvariable=self.input_path,
            font=('Segoe UI', 9),
            bg='white',
            fg=self.colors['text_primary'],
            relief='solid',
            bd=1,
            insertbackground=self.colors['accent']
        )
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(0, 10), ipady=5)
        
        self.input_button = tk.Button(
            input_inner,
            text="📂 Browse",
            command=self.select_input_folder,
            font=('Segoe UI', 9, 'bold'),
            bg=self.colors['accent'],
            fg='white',
            activebackground=self.colors['accent_hover'],
            activeforeground='white',
            relief='flat',
            padx=15,
            pady=5,
            cursor='hand2',
            bd=0
        )
        self.input_button.pack(side="left")
        self._add_hover_effect(self.input_button, self.colors['accent'], self.colors['accent_hover'])
        
        # Output Folder Selection
        self.output_frame = tk.LabelFrame(
            main_frame,
            text=" 💾 Step 2: Select Output Folder",
            font=('Segoe UI', 10, 'bold'),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary'],
            padx=15,
            pady=12,
            relief='flat',
            bd=1
        )
        self.output_frame.pack(fill="x", expand=True, pady=(0, 10))
        
        output_inner = tk.Frame(self.output_frame, bg=self.colors['bg_secondary'])
        output_inner.pack(fill="x")
        
        self.output_entry = tk.Entry(
            output_inner,
            textvariable=self.output_path,
            font=('Segoe UI', 9),
            bg='white',
            fg=self.colors['text_primary'],
            relief='solid',
            bd=1,
            insertbackground=self.colors['accent']
        )
        self.output_entry.pack(side="left", fill="x", expand=True, padx=(0, 10), ipady=5)
        
        self.output_button = tk.Button(
            output_inner,
            text="📂 Browse",
            command=self.select_output_folder,
            font=('Segoe UI', 9, 'bold'),
            bg=self.colors['accent'],
            fg='white',
            activebackground=self.colors['accent_hover'],
            activeforeground='white',
            relief='flat',
            padx=15,
            pady=5,
            cursor='hand2',
            bd=0
        )
        self.output_button.pack(side="left")
        self._add_hover_effect(self.output_button, self.colors['accent'], self.colors['accent_hover'])
        
        # In-Place Option
        option_frame = tk.Frame(main_frame, bg=self.colors['bg_primary'])
        option_frame.pack(fill="x", pady=(0, 15))
        
        self.in_place_check = tk.Checkbutton(
            option_frame,
            text="🔄 Save in the same folder (renames original files)",
            variable=self.in_place,
            command=self.toggle_output_folder,
            font=('Segoe UI', 9),
            bg=self.colors['bg_primary'],
            fg=self.colors['text_primary'],
            activebackground=self.colors['bg_primary'],
            activeforeground=self.colors['accent'],
            selectcolor='white',
            cursor='hand2'
        )
        self.in_place_check.pack(anchor="w")
        
        # Statistics Frame
        stats_frame = tk.Frame(main_frame, bg=self.colors['bg_secondary'], relief='flat', bd=1, padx=15, pady=10)
        stats_frame.pack(fill="x", pady=(0, 10))
        
        self.file_count_label = tk.Label(
            stats_frame,
            textvariable=self.file_count_var,
            font=('Segoe UI', 9),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_secondary']
        )
        self.file_count_label.pack(side="left")
        
        # Progress Section
        progress_frame = tk.Frame(main_frame, bg=self.colors['bg_primary'])
        progress_frame.pack(fill="x", pady=(0, 10))
        
        # Status Label
        self.status_label = tk.Label(
            progress_frame,
            textvariable=self.status_var,
            font=('Segoe UI', 9, 'bold'),
            bg=self.colors['bg_primary'],
            fg=self.colors['accent']
        )
        self.status_label.pack(anchor="w", pady=(0, 5))
        
        # Progress Bar Container
        progress_container = tk.Frame(progress_frame, bg='white', relief='solid', bd=1)
        progress_container.pack(fill="x", ipady=2)
        
        self.progress_bar = ttk.Progressbar(
            progress_container,
            variable=self.progress_var,
            maximum=100,
            length=400,
            mode='determinate',
            style='TProgressbar'
        )
        self.progress_bar.pack(fill="x", padx=2, pady=2)
        
        # Style the progress bar
        style = ttk.Style()
        style.configure("TProgressbar", background=self.colors['accent'], troughcolor='#e0e0e0', borderwidth=0)
        
        # Run Button
        self.run_button = tk.Button(
            main_frame,
            text="🚀 Start Renaming",
            command=self.start_renaming_thread,
            font=('Segoe UI', 12, 'bold'),
            bg=self.colors['success'],
            fg='white',
            activebackground='#218838',
            activeforeground='white',
            relief='flat',
            padx=20,
            pady=12,
            cursor='hand2',
            bd=0
        )
        self.run_button.pack(fill="x", pady=(0, 10))
        self._add_hover_effect(self.run_button, self.colors['success'], '#218838')
        
        # Log/Status Area
        log_frame = tk.LabelFrame(
            main_frame,
            text=" 📋 Activity Log",
            font=('Segoe UI', 10, 'bold'),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary'],
            padx=10,
            pady=10,
            relief='flat',
            bd=1
        )
        log_frame.pack(fill="both", expand=True)
        
        # Log text area with custom styling
        log_container = tk.Frame(log_frame, bg='white', relief='solid', bd=1)
        log_container.pack(fill="both", expand=True, padx=2, pady=2)
        
        self.log_area = scrolledtext.ScrolledText(
            log_container,
            wrap=tk.WORD,
            height=12,
            state="disabled",
            font=('Consolas', 9),
            bg='#fafafa',
            fg=self.colors['text_primary'],
            relief='flat',
            bd=0,
            padx=10,
            pady=10,
            insertbackground=self.colors['accent']
        )
        self.log_area.pack(fill="both", expand=True)
        
        # Configure text tags for colored logging
        self.log_area.tag_config('success', foreground=self.colors['success'])
        self.log_area.tag_config('error', foreground=self.colors['error'])
        self.log_area.tag_config('warning', foreground=self.colors['warning'])
        self.log_area.tag_config('info', foreground=self.colors['accent'])
        self.log_area.tag_config('timestamp', foreground=self.colors['text_secondary'])
    
    def _add_hover_effect(self, button: tk.Button, normal_color: str, hover_color: str) -> None:
        """Add hover effect to a button."""
        def on_enter(e):
            button.config(bg=hover_color)
        
        def on_leave(e):
            button.config(bg=normal_color)
        
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
    
    def _setup_tooltips(self) -> None:
        """Setup tooltips for UI elements."""
        # Tooltip will be shown on hover
        pass  # Can be extended with a tooltip class if needed

    def show_about_window(self) -> None:
        """Display the About window."""
        about_win = tk.Toplevel(self.root)
        about_win.title("About")
        about_win.geometry("450x320")
        about_win.resizable(False, False)
        about_win.transient(self.root)
        about_win.grab_set()
        
        about_frame = ttk.Frame(about_win, padding="20")
        about_frame.pack(fill="both", expand=True)
        
        title_label = ttk.Label(
            about_frame,
            text=self.app_name,
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 5))
        
        version_label = ttk.Label(about_frame, text=f"Version {self.version}")
        version_label.pack(pady=(0, 10))
        
        desc_label = ttk.Label(
            about_frame,
            text="This tool renames PDF files based on the\nvisible text 'Title' found on the first page.",
            justify="center"
        )
        desc_label.pack(pady=(0, 20))
        
        separator = ttk.Separator(about_frame, orient='horizontal')
        separator.pack(fill='x', pady=10)
        
        name_label = ttk.Label(about_frame, text=f"Created by: {self.author_info.get('name', 'Unknown')}")
        name_label.pack(anchor="w", pady=2)
        
        email_frame = ttk.Frame(about_frame)
        email_frame.pack(fill="x", pady=2)
        email_label = ttk.Label(email_frame, text="Email:")
        email_label.pack(side="left", anchor="w")
        email_entry = ttk.Entry(email_frame, width=40)
        email_entry.insert(0, self.author_info.get('email', ''))
        email_entry.config(state="readonly")
        email_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        link_frame = ttk.Frame(about_frame)
        link_frame.pack(fill="x", pady=2)
        linkedin_label = ttk.Label(link_frame, text="LinkedIn:")
        linkedin_label.pack(side="left", anchor="w")
        
        link_label = ttk.Label(
            link_frame,
            text="View Profile",
            foreground="blue",
            cursor="hand2"
        )
        link_label.pack(side="left", padx=5)
        link_label.bind("<Button-1>", lambda e: self.open_link(self.author_info.get('linkedin_url', '')))
        
        ok_button = ttk.Button(about_frame, text="OK", command=about_win.destroy)
        ok_button.pack(pady=(20, 0))

    def open_link(self, url: str) -> None:
        """Open a URL in the default web browser."""
        if url and "https://" in url:
            try:
                webbrowser.open_new(url)
            except Exception as e:
                logging.error(f"Error opening URL: {e}")
                messagebox.showerror("Error", f"Could not open URL: {e}")
        else:
            messagebox.showwarning("Invalid URL", "The LinkedIn URL is not set correctly.")

    def select_input_folder(self) -> None:
        """Open folder dialog to select input folder."""
        folder = filedialog.askdirectory(title="Select Input Folder")
        if folder:
            self.input_path.set(folder)
            # Update file count
            self._update_file_count()
            logging.info(f"Input folder selected: {folder}")

    def select_output_folder(self) -> None:
        """Open folder dialog to select output folder."""
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_path.set(folder)
            logging.info(f"Output folder selected: {folder}")

    def toggle_output_folder(self) -> None:
        """Toggle output folder based on in-place option."""
        if self.in_place.get():
            self.output_entry.config(state="disabled", bg='#f5f5f5')
            self.output_button.config(state="disabled", bg='#cccccc')
            self.output_path.set(self.input_path.get())
        else:
            self.output_entry.config(state="normal", bg='white')
            self.output_button.config(state="normal", bg=self.colors['accent'])
            if self.output_path.get() == self.input_path.get():
                self.output_path.set("")
    
    def _update_file_count(self) -> None:
        """Update the file count display."""
        input_folder = self.input_path.get().strip()
        if input_folder:
            try:
                path = Path(input_folder)
                if path.exists() and path.is_dir():
                    pdf_count = len([f for f in path.iterdir() 
                                   if f.is_file() and f.suffix.lower() == '.pdf'])
                    self.file_count_var.set(f"📊 {pdf_count} PDF file(s) found in input folder")
                else:
                    self.file_count_var.set("📊 0 PDF files found")
            except Exception:
                self.file_count_var.set("📊 0 PDF files found")
        else:
            self.file_count_var.set("📊 0 PDF files found")

    def log_message(self, message: str, tag: str = 'info') -> None:
        """Thread-safe logging to GUI log area with color coding."""
        def _log():
            self.log_area.config(state="normal")
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Insert timestamp
            self.log_area.insert(tk.END, f"[{timestamp}] ", 'timestamp')
            
            # Insert message with appropriate tag
            self.log_area.insert(tk.END, f"{message}\n", tag)
            
            self.log_area.config(state="disabled")
            self.log_area.see(tk.END)
        
        # Thread-safe GUI update
        self.root.after(0, _log)
        logging.info(message)

    def update_progress(self, current: int, total: int) -> None:
        """Update progress bar with animation."""
        def _update():
            if total > 0:
                progress = (current / total) * 100
                self.progress_var.set(progress)
                percentage = int(progress)
                self.status_var.set(f"⏳ Processing: {current}/{total} files ({percentage}%)")
            else:
                self.progress_var.set(0)
                self.status_var.set("✅ Ready")
        
        self.root.after(0, _update)

    def start_renaming_thread(self) -> None:
        """Start the renaming process in a background thread."""
        if self.is_processing:
            messagebox.showwarning("Warning", "Processing is already in progress.")
            return
        
        input_folder = self.input_path.get().strip()
        if self.in_place.get():
            output_folder = input_folder
        else:
            output_folder = self.output_path.get().strip()
        
        # Validation
        if not input_folder:
            messagebox.showerror("Error", "Please select an input folder.")
            return
        
        if not output_folder:
            messagebox.showerror("Error", "Please select an output folder or check the 'in-place' option.")
            return
        
        input_path = Path(input_folder)
        if not input_path.exists():
            messagebox.showerror("Error", f"Input folder does not exist: {input_folder}")
            return
        
        if not input_path.is_dir():
            messagebox.showerror("Error", f"Input path is not a directory: {input_folder}")
            return
        
        # Disable UI during processing
        self.is_processing = True
        self.run_button.config(state="disabled", text="⏳ Processing...", bg='#6c757d')
        self.input_button.config(state="disabled", bg='#cccccc')
        self.output_button.config(state="disabled", bg='#cccccc')
        self.log_area.config(state="normal")
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state="disabled")
        self.progress_var.set(0)
        self.status_var.set("🔄 Initializing...")
        
        # Start background thread
        thread = threading.Thread(
            target=self.run_renaming_process,
            args=(input_folder, output_folder),
            daemon=True
        )
        thread.start()
        logging.info(f"Renaming process started: {input_folder} -> {output_folder}")

    def run_renaming_process(self, input_folder_str: str, output_folder_str: str) -> None:
        """Core renaming logic running in background thread."""
        rename_count = 0
        skip_count = 0
        error_count = 0
        
        try:
            input_folder = Path(input_folder_str)
            output_folder = Path(output_folder_str)
            
            is_inplace = (input_folder.resolve() == output_folder.resolve())
            
            # Create output folder if needed
            if not is_inplace:
                try:
                    output_folder.mkdir(parents=True, exist_ok=True)
                except PermissionError:
                    self.log_message(f"❌ Permission denied: Cannot create output folder", 'error')
                    messagebox.showerror("Error", f"Permission denied: Cannot create output folder\n{output_folder}")
                    return
                except Exception as e:
                    self.log_message(f"❌ Error creating output folder: {e}", 'error')
                    messagebox.showerror("Error", f"Error creating output folder: {e}")
                    return
            
            self.log_message(f"📂 Scanning folder: {input_folder}", 'info')
            self.log_message(f"💾 Output folder: {output_folder}", 'info')
            self.log_message(f"🔧 Mode: {'In-place Rename' if is_inplace else 'Copy and Rename'}\n", 'info')
            
            # Get all PDF files
            pdf_files = [f for f in input_folder.iterdir() 
                        if f.is_file() and f.suffix.lower() == '.pdf']
            self.total_files = len(pdf_files)
            
            if self.total_files == 0:
                self.log_message("⚠️ No PDF files found in the input folder.", 'warning')
                messagebox.showinfo("Info", "No PDF files found in the input folder.")
                return
            
            self.log_message(f"📄 Found {self.total_files} PDF file(s)\n", 'info')
            
            # Process each file
            for idx, file_path in enumerate(pdf_files, 1):
                original_name = file_path.name
                self.processed_files = idx
                self.update_progress(idx, self.total_files)
                
                try:
                    # Extract title
                    title = self.extract_title_from_pdf(file_path)
                    
                    if not title:
                        self.log_message(f"  ⚠ Skipping '{original_name}': Could not find 'Title' line on page 1.", 'warning')
                        skip_count += 1
                        continue
                    
                    # Generate new filename
                    new_name_base = self.sanitize_filename(title)
                    new_name = f"{new_name_base}.pdf"
                    new_file_path = output_folder / new_name
                    
                    # Handle duplicates
                    counter = 1
                    while new_file_path.exists():
                        new_name = f"{new_name_base} ({counter}).pdf"
                        new_file_path = output_folder / new_name
                        counter += 1
                    
                    # Skip if already correctly named (in-place mode)
                    if is_inplace and file_path.resolve() == new_file_path.resolve():
                        self.log_message(f"  ✓ Skipping '{original_name}': Already correctly named.", 'info')
                        skip_count += 1
                        continue
                    
                    # Rename or copy
                    if is_inplace:
                        try:
                            file_path.rename(new_file_path)
                            self.log_message(f"  ✅ Renamed '{original_name}' -> '{new_name}'", 'success')
                            rename_count += 1
                        except PermissionError:
                            self.log_message(f"  ❌ Permission denied: Cannot rename '{original_name}'", 'error')
                            error_count += 1
                        except Exception as e:
                            self.log_message(f"  ❌ Error renaming '{original_name}': {e}", 'error')
                            error_count += 1
                    else:
                        try:
                            shutil.copy2(file_path, new_file_path)
                            self.log_message(f"  ✅ Copied '{original_name}' -> '{new_name}'", 'success')
                            rename_count += 1
                        except PermissionError:
                            self.log_message(f"  ❌ Permission denied: Cannot copy '{original_name}'", 'error')
                            error_count += 1
                        except Exception as e:
                            self.log_message(f"  ❌ Error copying '{original_name}': {e}", 'error')
                            error_count += 1
                
                except Exception as e:
                    self.log_message(f"  ❌ Error processing '{original_name}': {e}", 'error')
                    logging.exception(f"Error processing {original_name}")
                    error_count += 1
            
            # Summary
            self.log_message(f"\n{'='*50}", 'info')
            self.log_message(f"🎉 Done! Summary:", 'success')
            self.log_message(f"  ✅ Processed: {rename_count} file(s)", 'success')
            self.log_message(f"  ⏭️  Skipped: {skip_count} file(s)", 'info')
            if error_count > 0:
                self.log_message(f"  ❌ Errors: {error_count} file(s)", 'error')
            self.log_message(f"{'='*50}", 'info')
            
            summary = f"Process complete!\n\nProcessed: {rename_count}\nSkipped: {skip_count}"
            if error_count > 0:
                summary += f"\nErrors: {error_count}"
            
            messagebox.showinfo("Success", summary)
            logging.info(f"Process complete: {rename_count} processed, {skip_count} skipped, {error_count} errors")
        
        except Exception as e:
            error_msg = f"Fatal error: {e}"
            self.log_message(f"\n{'='*50}", 'error')
            self.log_message(f"❌ FATAL ERROR", 'error')
            self.log_message(f"{error_msg}", 'error')
            self.log_message(f"{'='*50}", 'error')
            logging.exception("Fatal error in renaming process")
            messagebox.showerror("Error", f"An unexpected error occurred:\n{error_msg}")
        
        finally:
            # Re-enable UI
            def _reset_ui():
                self.is_processing = False
                self.run_button.config(state="normal", text="🚀 Start Renaming", bg=self.colors['success'])
                self.input_button.config(state="normal", bg=self.colors['accent'])
                self.output_button.config(state="normal", bg=self.colors['accent'])
                self.update_progress(0, 0)
                self.status_var.set("✅ Ready")
                self._update_file_count()
            
            self.root.after(0, _reset_ui)

    def extract_title_from_pdf(self, file_path: Path) -> Optional[str]:
        """
        Extract title from PDF file.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted title or None if not found
        """
        try:
            reader = PdfReader(str(file_path))
            
            if not reader.pages:
                return None
            
            page1_text = reader.pages[0].extract_text()
            if not page1_text:
                return None
            
            lines = [line.strip() for line in page1_text.split('\n')]
            
            # Search for "title" line (case-insensitive)
            for i, line in enumerate(lines):
                if line.lower() == 'title':
                    # Get next non-empty line
                    for j in range(i + 1, len(lines)):
                        potential_title = lines[j].strip()
                        if potential_title:
                            return potential_title
                    break
            
            return None
        
        except Exception as e:
            logging.error(f"Error extracting title from {file_path.name}: {e}")
            raise

    def sanitize_filename(self, name: str) -> str:
        """
        Sanitize filename by removing illegal characters.
        
        Args:
            name: Original filename
            
        Returns:
            Sanitized filename
        """
        if not name:
            return "Untitled Manual"
        
        # Remove illegal characters for Windows/Unix
        sanitized = re.sub(r'[\\/:*?"<>|]', "", name)
        
        # Remove leading/trailing dots and spaces
        sanitized = sanitized.strip(" .")
        
        # Truncate if too long
        if len(sanitized) > self.max_filename_length:
            sanitized = sanitized[:self.max_filename_length].rstrip()
        
        # Ensure not empty
        return sanitized if sanitized else "Untitled Manual"


# ----------------------------------------------------------------------
# Main Entry Point
# ----------------------------------------------------------------------
def main() -> None:
    """Main entry point for the application."""
    try:
        # Load configuration
        config = load_config()
        
        # Setup logging
        setup_logging(config)
        
        # Create and run application
        root = tk.Tk()
        app = PdfRenamerApp(root, config)
        root.mainloop()
        
    except KeyboardInterrupt:
        logging.info("Application interrupted by user")
    except Exception as e:
        logging.exception("Fatal error starting application")
        messagebox.showerror("Fatal Error", f"Failed to start application:\n{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
