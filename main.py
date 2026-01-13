import os
import zipfile
import shutil
import threading
import base64
import hashlib
import binascii
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ExifTags

# Configuration
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# --- 1. TOOL: ZIP MANAGER (EXTRACT & COMPRESS) ---
class ZipToolFrame(ctk.CTkFrame):
    def __init__(self, master, return_callback):
        super().__init__(master)
        self.return_callback = return_callback
        self.extract_folder = "CTF_EXTRACTED"
        self.compress_folder = "CTF_COMPRESSED"
        self.selected_file = None

        self.setup_ui()

    def setup_ui(self):
        # Header & Back
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(top, text="< Back", command=self.return_callback, width=80, fg_color="gray").pack(side="left")
        ctk.CTkLabel(self, text="Zip Manager", font=("Roboto", 24, "bold")).pack(pady=5)

        # TABS: Extract vs Compress
        self.tabview = ctk.CTkTabview(self, width=900, height=500)
        self.tabview.pack(pady=10)
        
        self.tab_extract = self.tabview.add("Extract (Unzip)")
        self.tab_compress = self.tabview.add("Compress (Create Zip)")

        # --- TAB 1: EXTRACT ---
        self.setup_extract_tab()
        # --- TAB 2: COMPRESS ---
        self.setup_compress_tab()

        # Status & Log (Shared)
        self.log_box = ctk.CTkTextbox(self, width=900, height=200)
        self.log_box.pack(pady=10)
        self.log_box.configure(state="disabled")

    def log(self, message):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    # --- EXTRACT LOGIC ---
    def setup_extract_tab(self):
        frame = self.tab_extract
        
        # Settings
        set_frame = ctk.CTkFrame(frame, fg_color="transparent")
        set_frame.pack(pady=10)
        ctk.CTkLabel(set_frame, text="Max Layers:").pack(side="left", padx=5)
        self.ext_layers = ctk.CTkEntry(set_frame, width=60)
        self.ext_layers.insert(0, "100")
        self.ext_layers.pack(side="left")

        # Buttons
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(pady=10)
        self.btn_ext_sel = ctk.CTkButton(btn_frame, text="Select File", command=self.browse_extract)
        self.btn_ext_sel.grid(row=0, column=0, padx=10)
        self.btn_ext_run = ctk.CTkButton(btn_frame, text="Start Extraction", command=self.run_extract, state="disabled", fg_color="green")
        self.btn_ext_run.grid(row=0, column=1, padx=10)

    def browse_extract(self):
        f = filedialog.askopenfilename(filetypes=[("Zip files", "*.zip"), ("All files", "*.*")])
        if f:
            self.selected_file = f
            self.btn_ext_run.configure(state="normal")
            self.log(f"[Extract] Selected: {f}")

    def run_extract(self):
        threading.Thread(target=self.process_extract).start()

    def process_extract(self):
        self.btn_ext_run.configure(state="disabled")
        try:
            max_layers = int(self.ext_layers.get())
            work_dir = os.path.join(os.path.dirname(self.selected_file), self.extract_folder)
            if os.path.exists(work_dir): shutil.rmtree(work_dir)
            os.makedirs(work_dir)

            curr = os.path.join(work_dir, os.path.basename(self.selected_file))
            shutil.copy2(self.selected_file, curr)
            
            layer = 0
            while layer < max_layers:
                if not zipfile.is_zipfile(curr): break
                layer += 1
                if layer % 10 == 0 or layer == 1: self.log(f"Extracting layer {layer}...")
                with zipfile.ZipFile(curr, 'r') as z: z.extractall(work_dir)
                os.remove(curr)
                files = os.listdir(work_dir)
                if not files: break
                curr = os.path.join(work_dir, files[0])

            self.log(f"Done! Extracted {layer} layers.")
            os.startfile(work_dir)
        except Exception as e: self.log(f"Error: {e}")
        finally: self.btn_ext_run.configure(state="normal")

    # --- COMPRESS LOGIC ---
    def setup_compress_tab(self):
        frame = self.tab_compress
        
        ctk.CTkLabel(frame, text="Create a 'Zip Bomb' (Recursive Zip)", text_color="orange").pack(pady=5)
        
        set_frame = ctk.CTkFrame(frame, fg_color="transparent")
        set_frame.pack(pady=10)
        ctk.CTkLabel(set_frame, text="How many layers to Zip:").pack(side="left", padx=5)
        self.comp_layers = ctk.CTkEntry(set_frame, width=60)
        self.comp_layers.insert(0, "10")
        self.comp_layers.pack(side="left")

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(pady=10)
        self.btn_comp_sel = ctk.CTkButton(btn_frame, text="Select File to Hide", command=self.browse_compress)
        self.btn_comp_sel.grid(row=0, column=0, padx=10)
        self.btn_comp_run = ctk.CTkButton(btn_frame, text="Start Compression", command=self.run_compress, state="disabled", fg_color="orange")
        self.btn_comp_run.grid(row=0, column=1, padx=10)

        self.comp_file = None

    def browse_compress(self):
        f = filedialog.askopenfilename()
        if f:
            self.comp_file = f
            self.btn_comp_run.configure(state="normal")
            self.log(f"[Compress] Selected file to hide: {f}")

    def run_compress(self):
        threading.Thread(target=self.process_compress).start()

    def process_compress(self):
        self.btn_comp_run.configure(state="disabled")
        try:
            layers = int(self.comp_layers.get())
            base_dir = os.path.dirname(self.comp_file)
            work_dir = os.path.join(base_dir, self.compress_folder)
            
            if os.path.exists(work_dir): shutil.rmtree(work_dir)
            os.makedirs(work_dir)

            # 1. Copy original file
            current_name = os.path.basename(self.comp_file)
            current_path = os.path.join(work_dir, current_name)
            shutil.copy2(self.comp_file, current_path)

            self.log("Starting compression...")

            # 2. Loop zip
            for i in range(1, layers + 1):
                zip_name = f"layer_{i}.zip" if i < layers else "FINAL_RESULT.zip"
                zip_path = os.path.join(work_dir, zip_name)
                
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    zf.write(current_path, arcname=os.path.basename(current_path))
                
                if i % 5 == 0 or i == 1: self.log(f"Zipping layer {i}...")
                
                os.remove(current_path)
                current_path = zip_path 

            self.log(f"Done! Created {layers} layers.")
            messagebox.showinfo("Success", f"File created at:\n{current_path}")
            os.startfile(work_dir)

        except Exception as e: self.log(f"Error: {e}")
        finally: self.btn_comp_run.configure(state="normal")


# --- 2. TOOL: CONVERTER (BASE64/HEX) - ENCODE & DECODE ---
class ConverterFrame(ctk.CTkFrame):
    def __init__(self, master, return_callback):
        super().__init__(master)
        self.return_callback = return_callback
        
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(top, text="< Back", command=self.return_callback, width=80, fg_color="gray").pack(side="left")
        ctk.CTkLabel(self, text="Text Converter", font=("Roboto", 24, "bold")).pack(pady=5)

        self.tabview = ctk.CTkTabview(self, width=900, height=500)
        self.tabview.pack(pady=10)
        self.tab_decode = self.tabview.add("Decode")
        self.tab_encode = self.tabview.add("Encode")

        self.setup_decode_ui()
        self.setup_encode_ui()

    def setup_decode_ui(self):
        f = self.tab_decode
        ctk.CTkLabel(f, text="Input (Base64 / Hex):").pack()
        self.dec_input = ctk.CTkTextbox(f, height=100, width=800)
        self.dec_input.pack(pady=5)

        ctrl = ctk.CTkFrame(f, fg_color="transparent")
        ctrl.pack(pady=5)
        ctk.CTkLabel(ctrl, text="Loops:").grid(row=0,column=0)
        self.dec_loops = ctk.CTkEntry(ctrl, width=50); self.dec_loops.insert(0,"1"); self.dec_loops.grid(row=0,column=1, padx=5)

        btns = ctk.CTkFrame(f, fg_color="transparent")
        btns.pack(pady=5)
        
        ctk.CTkButton(btns, text="Decode Base64", command=lambda: self.process("decode", "b64")).grid(row=0, column=0, padx=5)
        ctk.CTkButton(btns, text="Decode Hex", command=lambda: self.process("decode", "hex")).grid(row=0, column=1, padx=5)
        ctk.CTkButton(btns, text="Clear", fg_color="red", command=lambda: self.dec_out.delete("0.0","end")).grid(row=0, column=2, padx=5)

        self.dec_out = ctk.CTkTextbox(f, height=150, width=800)
        self.dec_out.pack(pady=5)

    def setup_encode_ui(self):
        f = self.tab_encode
        ctk.CTkLabel(f, text="Input (Plain Text):").pack()
        ctk.CTkLabel(f, text="(Note: Avoid special chars like Ä, Ö, Ü. Use standard ASCII)", text_color="orange", font=("Arial", 12)).pack()

        self.enc_input = ctk.CTkTextbox(f, height=100, width=800)
        self.enc_input.pack(pady=5)

        ctrl = ctk.CTkFrame(f, fg_color="transparent")
        ctrl.pack(pady=5)
        ctk.CTkLabel(ctrl, text="Loops:").grid(row=0,column=0)
        self.enc_loops = ctk.CTkEntry(ctrl, width=50); self.enc_loops.insert(0,"1"); self.enc_loops.grid(row=0,column=1, padx=5)

        btns = ctk.CTkFrame(f, fg_color="transparent")
        btns.pack(pady=5)
        
        ctk.CTkButton(btns, text="Encode Base64", fg_color="orange", command=lambda: self.process("encode", "b64")).grid(row=0, column=0, padx=5)
        ctk.CTkButton(btns, text="Encode Hex", fg_color="orange", command=lambda: self.process("encode", "hex")).grid(row=0, column=1, padx=5)
        ctk.CTkButton(btns, text="Clear", fg_color="red", command=lambda: self.enc_out.delete("0.0","end")).grid(row=0, column=2, padx=5)

        self.enc_out = ctk.CTkTextbox(f, height=150, width=800)
        self.enc_out.pack(pady=5)

    def process(self, action, mode):
        if action == "decode":
            inp_box, out_box, loop_entry = self.dec_input, self.dec_out, self.dec_loops
        else:
            inp_box, out_box, loop_entry = self.enc_input, self.enc_out, self.enc_loops

        text = inp_box.get("0.0", "end").strip()
        if not text: return
        
        try: loops = int(loop_entry.get())
        except: loops = 1

        out_box.delete("0.0", "end")
        out_box.insert("end", f"Starting {action.upper()} ({loops} times)...\n")
        out_box.insert("end", "="*50 + "\n\n")

        curr = "".join(text.split()) if action == "decode" else text

        for i in range(loops):
            try:
                if action == "decode":
                    if mode == "b64":
                        pad = len(curr)%4
                        if pad: curr += '='*(4-pad)
                        curr = base64.b64decode(curr).decode('utf-8', 'ignore')
                    elif mode == "hex":
                        curr = bytes.fromhex(curr).decode('utf-8', 'ignore')
                else: # ENCODE
                    if mode == "b64":
                        curr = base64.b64encode(curr.encode('utf-8')).decode('utf-8')
                    elif mode == "hex":
                        curr = binascii.hexlify(curr.encode('utf-8')).decode('utf-8')
                
                # --- CHANGE HERE: Print EVERY step ---
                out_box.insert("end", f"--- Layer {i+1} ---\n")
                out_box.insert("end", curr + "\n\n")
                out_box.see("end") # Auto-scroll to bottom

            except Exception as e:
                out_box.insert("end", f"Error on loop {i+1}: {e}\n")
                return

        out_box.insert("end", "="*50 + "\n")
        out_box.insert("end", "DONE!")


# --- 3. TOOL: CAESAR CIPHER ---
class CaesarFrame(ctk.CTkFrame):
    def __init__(self, master, return_callback):
        super().__init__(master)
        self.return_callback = return_callback
        
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(top, text="< Back", command=self.return_callback, width=80, fg_color="gray").pack(side="left")
        ctk.CTkLabel(self, text="Caesar Cipher", font=("Roboto", 24, "bold")).pack(pady=5)

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.setup_breaker(self.tabview.add("Breaker (Decode)"))
        self.setup_creator(self.tabview.add("Creator (Encode)"))

    def setup_breaker(self, frame):
        ctk.CTkLabel(frame, text="(ONLY A-Z supported. Special chars like Ä, Ö, Ü will not change!)", text_color="orange").pack(pady=(10,0))
        
        self.brute_in = ctk.CTkEntry(frame, width=600, placeholder_text="Enter text to break...")
        self.brute_in.pack(pady=10)
        ctk.CTkButton(frame, text="BRUTE FORCE (Show all 25)", command=self.brute_force, fg_color="orange").pack()
        self.brute_out = ctk.CTkTextbox(frame, width=800, height=300)
        self.brute_out.pack(pady=20)

    def setup_creator(self, frame):
        ctk.CTkLabel(frame, text="(ONLY A-Z supported. Special chars like Ä, Ö, Ü will not change!)", text_color="orange").pack(pady=(10,0))

        self.create_in = ctk.CTkEntry(frame, width=600, placeholder_text="Enter clear text...")
        self.create_in.pack(pady=10)
        
        row = ctk.CTkFrame(frame, fg_color="transparent")
        row.pack(pady=10)
        ctk.CTkLabel(row, text="Shift (1-25):").pack(side="left")
        self.shift_entry = ctk.CTkEntry(row, width=50)
        self.shift_entry.insert(0, "13")
        self.shift_entry.pack(side="left", padx=10)
        
        ctk.CTkButton(frame, text="ENCODE", command=self.encode_caesar).pack(pady=10)
        self.create_out = ctk.CTkEntry(frame, width=600)
        self.create_out.pack(pady=20)

    def brute_force(self):
        text = self.brute_in.get()
        self.brute_out.delete("0.0", "end")
        res = ""
        for shift in range(1, 26):
            res += f"ROT {shift:02}: {self.rot(text, shift)}\n"
        self.brute_out.insert("0.0", res)

    def encode_caesar(self):
        text = self.create_in.get()
        try: shift = int(self.shift_entry.get())
        except: shift = 13
        res = self.rot(text, shift)
        self.create_out.delete(0, "end")
        self.create_out.insert(0, res)

    def rot(self, text, shift):
        res = ""
        for char in text:
            if char.isalpha() and char.isascii():
                start = ord('a') if char.islower() else ord('A')
                res += chr((ord(char) - start + shift) % 26 + start)
            else: res += char
        return res


# --- 4. TOOL: EXIF VIEWER ---
class ExifFrame(ctk.CTkFrame):
    def __init__(self, master, return_callback):
        super().__init__(master)
        self.return_callback = return_callback
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(top, text="< Back", command=self.return_callback, width=80, fg_color="gray").pack(side="left")

        ctk.CTkLabel(self, text="Image Metadata (EXIF)", font=("Roboto", 24, "bold")).pack(pady=5)
        ctk.CTkButton(self, text="Select Image", command=self.get_exif).pack(pady=10)
        self.output_box = ctk.CTkTextbox(self, width=900, height=400)
        self.output_box.pack(pady=10)

    def get_exif(self):
        filename = filedialog.askopenfilename()
        if not filename: return
        self.output_box.delete("0.0", "end")
        self.output_box.insert("end", f"FILE: {filename}\n\n")
        try:
            img = Image.open(filename)
            exif = img._getexif()
            if not exif:
                self.output_box.insert("end", "No EXIF data found.")
                return
            for tag, value in exif.items():
                tag_name = ExifTags.TAGS.get(tag, tag)
                self.output_box.insert("end", f"{tag_name}: {value}\n")
        except Exception as e: self.output_box.insert("end", f"Error: {e}")


# --- 5. TOOL: HASH CALCULATOR ---
class HashFrame(ctk.CTkFrame):
    def __init__(self, master, return_callback):
        super().__init__(master)
        self.return_callback = return_callback
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(top, text="< Back", command=self.return_callback, width=80, fg_color="gray").pack(side="left")

        ctk.CTkLabel(self, text="File Hash Calculator", font=("Roboto", 24, "bold")).pack(pady=5)
        ctk.CTkButton(self, text="Select File", command=self.calc_hash).pack(pady=10)
        self.output_box = ctk.CTkTextbox(self, width=900, height=300)
        self.output_box.pack(pady=10)

    def calc_hash(self):
        filename = filedialog.askopenfilename()
        if not filename: return
        self.output_box.delete("0.0", "end")
        self.output_box.insert("end", f"Calculating: {os.path.basename(filename)}...\n")
        try:
            md5, sha1, sha256 = hashlib.md5(), hashlib.sha1(), hashlib.sha256()
            with open(filename, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    md5.update(chunk); sha1.update(chunk); sha256.update(chunk)
            self.output_box.insert("end", f"MD5:    {md5.hexdigest()}\nSHA1:   {sha1.hexdigest()}\nSHA256: {sha256.hexdigest()}\n")
        except Exception as e: self.output_box.insert("end", f"Error: {e}")


# --- MAIN APP ---
class MultiToolApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("CTF-Toolkit")
        self.geometry("1100x800")
        
        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)
        
        self.watermark = ctk.CTkLabel(self, text="Joonas", text_color="white", font=("Arial", 16, "bold"))
        self.watermark.place(relx=0.98, rely=0.98, anchor="se")
        
        self.show_menu()

    def clear_container(self):
        for widget in self.container.winfo_children(): widget.destroy()

    def show_menu(self):
        self.clear_container()
        
        bg_path = "taust.jpg"
        menu_frame = ctk.CTkFrame(self.container)
        menu_frame.pack(fill="both", expand=True)
        
        if os.path.exists(bg_path):
            try:
                img = ctk.CTkImage(Image.open(bg_path), size=(1100, 800))
                ctk.CTkLabel(menu_frame, image=img, text="").place(x=0, y=0, relwidth=1, relheight=1)
            except: pass

        ctk.CTkLabel(menu_frame, text="SELECT TOOL", font=("Roboto", 40, "bold"), text_color="white", fg_color="transparent").pack(pady=(80, 40))
        
        btn_opts = {"width": 350, "height": 65, "font": ("Roboto", 18)}
        ctk.CTkButton(menu_frame, text="1. Zip Manager (Extract/Compress)", command=lambda: self.switch(ZipToolFrame), **btn_opts).pack(pady=10)
        ctk.CTkButton(menu_frame, text="2. Text Converter (Decode/Encode)", command=lambda: self.switch(ConverterFrame), **btn_opts).pack(pady=10)
        ctk.CTkButton(menu_frame, text="3. Caesar Cipher (Break/Create)", command=lambda: self.switch(CaesarFrame), **btn_opts).pack(pady=10)
        ctk.CTkButton(menu_frame, text="4. EXIF Viewer", command=lambda: self.switch(ExifFrame), **btn_opts).pack(pady=10)
        ctk.CTkButton(menu_frame, text="5. File Hash", command=lambda: self.switch(HashFrame), **btn_opts).pack(pady=10)
        ctk.CTkButton(menu_frame, text="Exit", command=self.destroy, width=350, height=50, fg_color="darkred", hover_color="red").pack(pady=40)
        self.watermark.lift()

    def switch(self, frame_class):
        self.clear_container()
        frame_class(self.container, self.show_menu).pack(fill="both", expand=True)

if __name__ == "__main__":
    app = MultiToolApp()
    app.mainloop()