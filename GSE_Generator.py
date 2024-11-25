import os
import sys
import queue
import threading
import tkinter as tk
from tkinter import ttk
from appID_finder import get_steam_app_by_id, get_steam_app_by_name
from achievements import fetch_from_steamcommunity, fetch_from_steamdb

def get_resource_path(filename):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.dirname(__file__), filename)
icon_path = get_resource_path('icon.ico')

class RedirectText:
    def __init__(self, text_widget: tk.Text, queue: queue.Queue):
        self.text_widget = text_widget
        self.queue = queue
        self.last_line = ""
    
    def write(self, string: str):
        cleaned_string = string.replace('\r', '').replace('\n', '').strip()
        if cleaned_string:
            self.queue.put(cleaned_string + '\n')
    
    def flush(self):
        pass

class AchievementFetcherGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("GSE Generator")
        self.root.geometry("700x500")
        self.root.minsize(500, 500)
        self.root.iconbitmap(icon_path)
        # self.root.wm_attributes('-toolwindow', 'True')
        
        self.msg_queue = queue.Queue()
        
        self.assets_dir = os.path.join(os.getcwd(), "assets")
        os.makedirs(self.assets_dir, exist_ok=True)
        
        self.username_file = os.path.join(self.assets_dir, "username.txt")
        
        self.create_widgets()
        self.load_saved_username()
        self.check_queue()
    
    def load_saved_username(self):
        if os.path.exists(self.username_file):
            with open(self.username_file, 'r', encoding='utf-8') as f:
                saved_username = f.read().strip()
                if saved_username:
                    self.user_account_var.set(saved_username)
    
    def save_username(self, *args):
        username = self.user_account_var.get().strip()
        try:
            with open(self.username_file, 'w', encoding='utf-8') as f:
                f.write(username)
        except Exception as e:
            self.set_status(f"Failed to save username: {str(e)}", True)
        
    # --------------- GUI-start ---------------
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        input_frame = ttk.Frame(main_frame)
        input_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        input_frame.columnconfigure(1, weight=1)
        
        # User Account Name
        ttk.Label(input_frame, text="Account Name:", anchor='w').grid(row=0, column=0, padx=(0, 10), sticky=tk.W)
        self.user_account_var = tk.StringVar()
        self.user_account_entry = ttk.Entry(input_frame, textvariable=self.user_account_var)
        self.user_account_entry.grid(row=0, column=1, sticky=(tk.W, tk.E))

        # Game Name
        ttk.Label(input_frame, text="Game Name:", anchor='w').grid(row=1, column=0, padx=(0, 10), pady=(5, 0), sticky=tk.W)
        self.game_name_var = tk.StringVar()
        self.game_name_entry = ttk.Entry(input_frame, textvariable=self.game_name_var)
        self.game_name_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(5, 0))

        # AppID
        ttk.Label(input_frame, text="AppID:", anchor='w').grid(row=2, column=0, padx=(0, 10), pady=(5, 0), sticky=tk.W)
        self.app_id_var = tk.StringVar()
        self.app_id_entry = ttk.Entry(input_frame, textvariable=self.app_id_var)
        self.app_id_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=(5, 0))
        
        self.user_account_var.trace_add('write', self.save_username)
        self.game_name_var.trace_add('write', self.on_game_name_change)
        self.app_id_var.trace_add('write', self.on_app_id_change)
        
        # Checkbox layout
        checkbox_frame = ttk.Frame(input_frame)
        checkbox_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        checkbox_frame.columnconfigure(2, weight=1)

        # Left column
        # Use Steam chkbox
        self.use_steam = tk.BooleanVar(value=False)
        steam_checkbox = ttk.Checkbutton(checkbox_frame, text="Use Steam", variable=self.use_steam)
        steam_checkbox.grid(row=0, column=0, sticky=tk.W)

        # Tooltip for Steam chkbox
        steam_tooltip = "Use Steam Community for fetching achievements"
        self.bind_tooltip(steam_checkbox, steam_tooltip)

        # Local Save chkbox
        self.use_local_save = tk.BooleanVar(value=False)
        local_save_checkbox = ttk.Checkbutton(checkbox_frame, text="Local Save", variable=self.use_local_save)
        local_save_checkbox.grid(row=0, column=1, sticky=tk.W, padx=(20, 0))

        # Tooltip for Local Save chkbox
        local_save_tooltip = "Save game data locally in the GSE Saves folder"
        self.bind_tooltip(local_save_checkbox, local_save_tooltip)

        # Second row
        # Disable LAN chkbox
        self.disable_lan_only = tk.BooleanVar(value=False)
        lan_checkbox = ttk.Checkbutton(checkbox_frame, text="Disable LAN Only", variable=self.disable_lan_only)
        lan_checkbox.grid(row=1, column=0, sticky=tk.W)

        # Tooltip for Lan chkbox
        lan_tooltip = "Allows the emulator to connect to the internet instead of being LAN only"
        self.bind_tooltip(lan_checkbox, lan_tooltip)

        # Achievements Only chkbox
        self.achievements_only = tk.BooleanVar(value=False)
        ach_checkbox = ttk.Checkbutton(checkbox_frame, text="Achievements Only", variable=self.achievements_only)
        ach_checkbox.grid(row=1, column=1, sticky=tk.W, padx=(20, 0))

        # Tooltip for Achievements Only chkbox
        achievements_tooltip = "Only fetch achievements, no GSE"
        self.bind_tooltip(ach_checkbox, achievements_tooltip)

        # Third row
        # Disable Overlay chkbox
        self.disable_overlay = tk.BooleanVar(value=False)
        overlay_checkbox = ttk.Checkbutton(checkbox_frame, text="Disable Overlay", variable=self.disable_overlay)
        overlay_checkbox.grid(row=2, column=0, sticky=tk.W)

        # Tooltip for Disable Overlay chkbox
        overlay_tooltip = "Disable overlay functionality. Use if game keeps crashing"
        self.bind_tooltip(overlay_checkbox, overlay_tooltip)
        
        # Generate Button
        self.generate_btn = ttk.Button(checkbox_frame, text="Generate", command=self.start_generate)
        self.generate_btn.grid(row=1, column=3, sticky=tk.E)

        # Progress frame
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        progress_frame.columnconfigure(0, weight=1)
        progress_frame.rowconfigure(0, weight=1)
        
        # Output
        self.output_text = tk.Text(progress_frame, wrap=tk.WORD, height=10, bg='white', fg='black',  state='disabled')
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(progress_frame, orient=tk.VERTICAL, command=self.output_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.output_text['yscrollcommand'] = scrollbar.set
        
        # Status bar
        status_frame = ttk.Frame(main_frame, relief=tk.RIDGE, borderwidth=1)
        status_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        status_frame.columnconfigure(0, weight=1)

        self.status_var = tk.StringVar(value="Status: Ready")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, padding=(8, 4), background='#f0f0f0')
        self.status_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

    def bind_tooltip(self, widget, text):
        widget._tooltip_text = text
        widget._tooltip = None
        widget._tooltip_timer = None
        widget.bind("<Enter>", self.start_tooltip_timer)
        widget.bind("<Leave>", self.hide_tooltip)
        
    def start_tooltip_timer(self, event):
        widget = event.widget
        if widget._tooltip_timer:
            widget.after_cancel(widget._tooltip_timer)
        widget._tooltip_timer = widget.after(1000, lambda: self.show_tooltip(event))
        
    def show_tooltip(self, event):
        widget = event.widget
        x = widget.winfo_rootx() + widget.winfo_width() // 2
        y = widget.winfo_rooty() + widget.winfo_height()

        if hasattr(widget, '_tooltip') and widget._tooltip:
            return

        widget._tooltip = tk.Toplevel()
        widget._tooltip.wm_overrideredirect(True)
        widget._tooltip.wm_geometry(f"+{x}+{y}")

        label = ttk.Label(widget._tooltip, text=widget._tooltip_text, justify=tk.LEFT, background="#ffffe0", relief="solid", borderwidth=1, padding=(5, 3))
        label.pack()

    def hide_tooltip(self, event):
        widget = event.widget
        if widget._tooltip_timer:
            widget.after_cancel(widget._tooltip_timer)
            widget._tooltip_timer = None
            
        if widget._tooltip:
            widget._tooltip.destroy()
            widget._tooltip = None
    # --------------- END ---------------

    # --------------- Status-bar ---------------
    def set_status(self, message, is_error=False):
        prefix = "Error: " if is_error else "Status: "
        self.status_var.set(prefix + message)
        if is_error:
            self.status_label.configure(foreground='#d32f2f', background='#fde7e7')
        elif "successfully" in message.lower():
            self.status_label.configure(foreground='#2e7d32', background='#edf7ed')
        else:
            self.status_label.configure(foreground='#000000', background='#f0f0f0')

    def write_output(self, message):
        self.msg_queue.put(message + '\n')
        
    def on_game_name_change(self, *args):
        game_name = self.game_name_var.get().strip()
        if game_name:
            self.app_id_entry.configure(state='readonly')
        else:
            self.app_id_entry.configure(state='normal')

    def on_app_id_change(self, *args):
        app_id = self.app_id_var.get().strip()
        if app_id:
            self.game_name_entry.configure(state='readonly')
        else:
            self.game_name_entry.configure(state='normal')
    
    def check_queue(self):
        while True:
            try:
                msg = self.msg_queue.get_nowait()
                self.output_text.configure(state='normal')
                self.output_text.insert(tk.END, msg)
                self.output_text.see(tk.END)
                self.output_text.configure(state='disabled')

            except queue.Empty:
                break

        self.root.after(100, self.check_queue)
    # --------------- END ---------------
    
    def create_user_config(self, settings_dir: str):
        user_account = self.user_account_var.get().strip()
        use_local_save = self.use_local_save.get()

        if self.disable_lan_only.get() and not self.achievements_only.get():
            config_main_path = os.path.join(settings_dir, "configs.main.ini")
            with open(config_main_path, "w", encoding="utf-8") as f:
                f.write("[main::connectivity]\ndisable_lan_only=1\n")
    
        if not user_account and not use_local_save:
            return

        config_content = ""

        if user_account:
            config_content += f"[user::general]\naccount_name={user_account}\nlanguage=english\n"

        if use_local_save:
            config_content += "[user::saves]\nlocal_save_path=./GSE Saves\n"
            
        if config_content and not self.achievements_only.get():
            config_path = os.path.join(settings_dir, "configs.user.ini")
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(config_content)

    def start_generate(self):
        game_name = self.game_name_var.get().strip()
        app_id = self.app_id_var.get().strip()

        if not game_name and not app_id:
            self.set_status("Please enter a game name or AppID", True)
            return

        process_complete_event = threading.Event()
        input_found_event = threading.Event()

        def process_input_wrapper():
            if app_id:
                try:
                    self.write_output("Parsing AppID...")
                    app_index = get_steam_app_by_id(app_id)
                    iw_game_name = app_index['name'] if app_index else None

                    if iw_game_name is None:
                        self.root.after(0, lambda: self.set_status(f"Could not find game name for AppID '{app_id}'", True))
                        process_complete_event.set()
                        return

                    self.root.after(0, lambda: self.game_name_var.set(iw_game_name))
                    self.root.after(0, lambda: self.game_name_entry.configure(state='readonly'))
                    input_found_event.set()

                except Exception as e:
                    error_msg = f"Failed to find game name: {str(e)}"
                    self.root.after(0, lambda: self.set_status(error_msg, True))
                    process_complete_event.set()
                    return
                
            elif game_name:
                try:
                    self.write_output("Parsing game name...")
                    app_info = get_steam_app_by_name(game_name)
                    iw_app_id = str(app_info['appid']) if app_info else None

                    if iw_app_id is None:
                        self.root.after(0, lambda: self.set_status(f"Could not find AppID for '{game_name}'", True))
                        process_complete_event.set()
                        return
                    
                    self.root.after(0, lambda: self.app_id_var.set(iw_app_id))
                    self.root.after(0, lambda: self.app_id_entry.configure(state='readonly'))
                    input_found_event.set()
                
                except Exception as e:
                    error_msg = f"Failed to find AppID: {str(e)}"
                    self.root.after(0, lambda: self.set_status(error_msg, True))
                    process_complete_event.set()
                    return
                
            process_complete_event.set()

        def generate_gse_wrapper():
            process_complete_event.wait()
            
            if input_found_event.is_set():
                app_id = self.app_id_var.get().strip()
                self.generate_gse(app_id, self.use_steam.get())
            else:
                self.root.after(0, lambda: self.generate_btn.state(['!disabled']))

        self.set_status("Generating GSE...")
        self.generate_btn.state(['disabled'])
        self.output_text.configure(state='normal')
        self.output_text.delete(1.0, tk.END)
        self.output_text.configure(state='disabled')
        sys.stdout = RedirectText(self.output_text, self.msg_queue)

        threading.Thread(target=process_input_wrapper, daemon=True).start()
        threading.Thread(target=generate_gse_wrapper, daemon=True).start()
    
    def generate_gse(self, app_id: str, use_steam: bool):
        app_index = get_steam_app_by_id(app_id)
        game_name = app_index['name'] if app_index else None
        
        game_dir = f"{game_name} ({app_id})"
        os.makedirs(game_dir, exist_ok=True)

        settings_dir = os.path.join(game_dir, "steam_settings")
        os.makedirs(settings_dir, exist_ok=True)

        try:
            if not self.achievements_only.get():
                # Generate Goldberg files
                self.write_output("Generating GSE...")
                from goldberg_gen import generate_emu
                if not generate_emu(game_dir, app_id, self.disable_overlay.get()):
                    raise Exception("Failed to generate Goldberg emu files")

            # Generate achievements
            self.write_output("Generating achievements...")
            original_cwd = os.getcwd()
            try:
                os.chdir(settings_dir)
                if use_steam:
                    try:
                        achievements = fetch_from_steamcommunity(app_id, silent=True)
                        if not achievements:
                            self.write_output("No achievements found.")
                            achievements = fetch_from_steamdb(app_id, silent=True)
                    except Exception as e:
                        self.write_output(f"Achievements fetch failed: {str(e)}")
                else:
                    try:
                        achievements = fetch_from_steamdb(app_id, silent=True)
                        if not achievements:
                            self.write_output("No achievements found.")
                            achievements = fetch_from_steamcommunity(app_id, silent=True)
                    except Exception as e:
                        self.write_output(f"Achievements fetch failed: {str(e)}")

            finally:
                os.chdir(original_cwd)
            
            self.create_user_config(settings_dir)
            
            self.write_output("Done generating GSE!")
            self.root.after(0, lambda: self.set_status("GSE generated successfully"))
                
        except Exception as e:
            error_message = str(e)
            self.root.after(0, lambda msg=error_message: self.set_status(msg, True))
        finally:
            self.root.after(0, lambda: self.generate_btn.state(['!disabled']))
            sys.stdout = sys.__stdout__

def main():
    root = tk.Tk()
    AchievementFetcherGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()