import os
import zipfile
import shutil
import threading
import base64
import hashlib
import binascii
import webbrowser
import urllib.parse
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ExifTags

# --- CONFIGURATION ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green") 

# =============================================================================
# 1. TOOL: ZIP MANAGER
# =============================================================================
class ZipToolFrame(ctk.CTkFrame):
    def __init__(self, master, return_callback):
        super().__init__(master)
        self.return_callback = return_callback
        self.extract_folder = "CTF_EXTRACTED"
        self.compress_folder = "CTF_COMPRESSED"
        self.setup_ui()

    def setup_ui(self):
        # Header
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(top, text="< Back", command=self.return_callback, width=80, fg_color="#333333").pack(side="left")
        ctk.CTkLabel(self, text="Zip Manager", font=("Roboto", 24, "bold")).pack(pady=5)

        # Tabs
        self.tabview = ctk.CTkTabview(self, width=900, height=500)
        self.tabview.pack(pady=10)
        self.tab_ext = self.tabview.add("Extract (Unzip)")
        self.tab_comp = self.tabview.add("Compress (Zip)")

        # --- EXTRACT UI ---
        fr_ext = self.tab_ext
        ctk.CTkLabel(fr_ext, text="Recursive Unzip Limit (Layers):").pack(pady=10)
        self.ext_layers = ctk.CTkEntry(fr_ext, width=60, justify="center"); self.ext_layers.insert(0, "50"); self.ext_layers.pack(pady=5)
        
        ctk.CTkButton(fr_ext, text="Select File & Extract", command=self.run_extract, fg_color="#2E8B57", width=200).pack(pady=20)
        
        # --- COMPRESS UI ---
        fr_comp = self.tab_comp
        ctk.CTkLabel(fr_comp, text="Create Recursive Zip (Zip Bomb)", text_color="orange").pack(pady=10)
        ctk.CTkLabel(fr_comp, text="Number of Layers:").pack()
        self.comp_layers = ctk.CTkEntry(fr_comp, width=60, justify="center"); self.comp_layers.insert(0, "10"); self.comp_layers.pack(pady=5)
        ctk.CTkButton(fr_comp, text="Select File & Compress", command=self.run_compress, fg_color="#E59400", width=200).pack(pady=20)

        # Log
        self.log_box = ctk.CTkTextbox(self, width=800, height=150)
        self.log_box.pack(pady=10)

    def log(self, txt):
        self.log_box.insert("end", txt + "\n"); self.log_box.see("end")

    def run_extract(self):
        f = filedialog.askopenfilename(filetypes=[("Zip", "*.zip")])
        if not f: return
        threading.Thread(target=self.do_extract, args=(f,)).start()

    def do_extract(self, filename):
        try:
            limit = int(self.ext_layers.get())
            work_dir = os.path.join(os.path.dirname(filename), self.extract_folder)
            if os.path.exists(work_dir): shutil.rmtree(work_dir)
            os.makedirs(work_dir)
            
            curr = os.path.join(work_dir, os.path.basename(filename))
            shutil.copy2(filename, curr)
            
            count = 0
            while count < limit:
                if not zipfile.is_zipfile(curr): break
                with zipfile.ZipFile(curr, 'r') as z: z.extractall(work_dir)
                os.remove(curr)
                files = os.listdir(work_dir)
                if not files: break
                curr = os.path.join(work_dir, files[0])
                count += 1
                self.log(f"Layer {count} extracted...")
            
            self.log(f"Done! Files located at: {work_dir}")
            os.startfile(work_dir)
        except Exception as e: self.log(f"Error: {e}")

    def run_compress(self):
        f = filedialog.askopenfilename()
        if not f: return
        threading.Thread(target=self.do_compress, args=(f,)).start()

    def do_compress(self, filename):
        try:
            limit = int(self.comp_layers.get())
            base_dir = os.path.dirname(filename)
            work_dir = os.path.join(base_dir, self.compress_folder)
            if os.path.exists(work_dir): shutil.rmtree(work_dir)
            os.makedirs(work_dir)

            curr_name = os.path.basename(filename)
            curr_path = os.path.join(work_dir, curr_name)
            shutil.copy2(filename, curr_path)

            for i in range(1, limit + 1):
                zip_name = f"layer_{i}.zip" if i < limit else "FINAL.zip"
                zip_path = os.path.join(work_dir, zip_name)
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
                    z.write(curr_path, arcname=os.path.basename(curr_path))
                os.remove(curr_path)
                curr_path = zip_path
                self.log(f"Compressed layer {i}...")
            
            self.log(f"Done! {work_dir}")
            os.startfile(work_dir)
        except Exception as e: self.log(f"Error: {e}")


# =============================================================================
# 2. TOOL: TEXT CONVERTER (Base64/Hex/Bin/URL)
# =============================================================================
class DecoderFrame(ctk.CTkFrame):
    def __init__(self, master, return_callback):
        super().__init__(master)
        self.return_callback = return_callback
        self.setup_ui()

    def setup_ui(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(top, text="< Back", command=self.return_callback, width=80, fg_color="#333333").pack(side="left")
        ctk.CTkLabel(self, text="Text Converter", font=("Roboto", 24, "bold")).pack(pady=5)

        ctk.CTkLabel(self, text="Input:").pack(anchor="w", padx=100)
        self.inp = ctk.CTkTextbox(self, height=120, width=900)
        self.inp.pack(pady=5)

        ctrl = ctk.CTkFrame(self)
        ctrl.pack(pady=10)
        
        btn_opts = {"width": 120, "height": 35}
        
        # Encode row
        ctk.CTkLabel(ctrl, text="ENCODE:").grid(row=0, column=0, padx=10, pady=5)
        ctk.CTkButton(ctrl, text="To Base64", command=lambda: self.run("enc", "b64"), **btn_opts).grid(row=0, column=1, padx=5, pady=5)
        ctk.CTkButton(ctrl, text="To Hex", command=lambda: self.run("enc", "hex"), **btn_opts).grid(row=0, column=2, padx=5, pady=5)
        ctk.CTkButton(ctrl, text="To Binary", command=lambda: self.run("enc", "bin"), **btn_opts).grid(row=0, column=3, padx=5, pady=5)
        ctk.CTkButton(ctrl, text="URL Encode", command=lambda: self.run("enc", "url"), **btn_opts).grid(row=0, column=4, padx=5, pady=5)

        # Decode row
        ctk.CTkLabel(ctrl, text="DECODE:").grid(row=1, column=0, padx=10, pady=5)
        ctk.CTkButton(ctrl, text="From Base64", command=lambda: self.run("dec", "b64"), fg_color="#2E8B57", **btn_opts).grid(row=1, column=1, padx=5, pady=5)
        ctk.CTkButton(ctrl, text="From Hex", command=lambda: self.run("dec", "hex"), fg_color="#2E8B57", **btn_opts).grid(row=1, column=2, padx=5, pady=5)
        ctk.CTkButton(ctrl, text="From Binary", command=lambda: self.run("dec", "bin"), fg_color="#2E8B57", **btn_opts).grid(row=1, column=3, padx=5, pady=5)
        ctk.CTkButton(ctrl, text="URL Decode", command=lambda: self.run("dec", "url"), fg_color="#2E8B57", **btn_opts).grid(row=1, column=4, padx=5, pady=5)

        ctk.CTkLabel(self, text="Output:").pack(anchor="w", padx=100)
        self.out = ctk.CTkTextbox(self, height=250, width=900)
        self.out.pack(pady=5)
        ctk.CTkButton(self, text="Clear All", command=self.clear_all, fg_color="#8B0000", width=200).pack(pady=10)

    def clear_all(self):
        self.inp.delete("0.0", "end")
        self.out.delete("0.0", "end")

    def run(self, action, mode):
        txt = self.inp.get("0.0", "end").strip()
        if not txt: return
        res = ""
        try:
            if action == "enc":
                if mode == "b64": res = base64.b64encode(txt.encode()).decode()
                elif mode == "hex": res = binascii.hexlify(txt.encode()).decode()
                elif mode == "bin": res = ' '.join(format(ord(c), '08b') for c in txt)
                elif mode == "url": res = urllib.parse.quote(txt)
            else: # decode
                if mode == "b64": 
                    pad = len(txt) % 4
                    if pad: txt += "=" * (4 - pad)
                    res = base64.b64decode(txt).decode('utf-8', 'ignore')
                elif mode == "hex": res = bytes.fromhex(txt).decode('utf-8', 'ignore')
                elif mode == "bin": 
                    txt = txt.replace(" ", "")
                    n = int(txt, 2)
                    res = n.to_bytes((n.bit_length() + 7) // 8, 'big').decode('utf-8', 'ignore')
                elif mode == "url": res = urllib.parse.unquote(txt)
            
            self.out.insert("0.0", f"--- {action.upper()} {mode.upper()} ---\n{res}\n\n")
        except Exception as e:
            self.out.insert("0.0", f"ERROR: {e}\n\n")


# =============================================================================
# 3. TOOL: CAESAR CIPHER (1-25)
# =============================================================================
class CaesarFrame(ctk.CTkFrame):
    def __init__(self, master, return_callback):
        super().__init__(master)
        self.return_callback = return_callback
        self.setup_ui()

    def setup_ui(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(top, text="< Back", command=self.return_callback, width=80, fg_color="#333333").pack(side="left")
        ctk.CTkLabel(self, text="Caesar Cipher (1-25 Shift)", font=("Roboto", 24, "bold")).pack(pady=5)
        
        ctk.CTkLabel(self, text="Note: Works on English Alphabet (A-Z) only.", text_color="orange").pack()

        self.inp = ctk.CTkTextbox(self, height=150, width=900)
        self.inp.pack(pady=10)
        
        ctrl = ctk.CTkFrame(self, fg_color="transparent")
        ctrl.pack(pady=10)
        
        ctk.CTkLabel(ctrl, text="Shift (1-25):").pack(side="left")
        self.shift_val = ctk.CTkEntry(ctrl, width=50, justify="center"); self.shift_val.insert(0, "13"); self.shift_val.pack(side="left", padx=5)
        
        ctk.CTkButton(ctrl, text="Apply Shift", command=self.run_caesar, fg_color="#E59400").pack(side="left", padx=10)
        ctk.CTkButton(ctrl, text="BRUTE FORCE (Try All)", command=self.run_brute, fg_color="#8B0000").pack(side="left", padx=10)

        self.out = ctk.CTkTextbox(self, height=300, width=900)
        self.out.pack(pady=10)
        ctk.CTkButton(self, text="Clear", command=lambda: self.out.delete("0.0","end"), fg_color="#8B0000").pack()

    def run_caesar(self):
        txt = self.inp.get("0.0", "end").strip()
        try: s = int(self.shift_val.get())
        except: s = 13
        self.out.insert("0.0", f"--- ROT {s} ---\n{self.rot(txt, s)}\n\n")

    def run_brute(self):
        txt = self.inp.get("0.0", "end").strip()
        self.out.delete("0.0", "end")
        res = "--- BRUTE FORCE RESULTS ---\n"
        for i in range(1, 26):
            res += f"Shift {i:02}: {self.rot(txt, i)}\n"
        self.out.insert("0.0", res)

    def rot(self, text, s):
        r = ""
        for c in text:
            if c.isalpha() and c.isascii():
                base = ord('a') if c.islower() else ord('A')
                r += chr((ord(c) - base + s) % 26 + base)
            else: r += c
        return r


# =============================================================================
# 4. TOOL: FILE ANALYSIS (EXIF & HASH)
# =============================================================================
class AnalysisFrame(ctk.CTkFrame):
    def __init__(self, master, return_callback):
        super().__init__(master)
        self.return_callback = return_callback
        self.setup_ui()

    def setup_ui(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(top, text="< Back", command=self.return_callback, width=80, fg_color="#333333").pack(side="left")
        ctk.CTkLabel(self, text="File Analysis (Hash & EXIF)", font=("Roboto", 24, "bold")).pack(pady=5)

        ctk.CTkButton(self, text="Select File to Analyze", command=self.analyze, fg_color="#2E8B57", width=200).pack(pady=20)
        self.out = ctk.CTkTextbox(self, width=900, height=500)
        self.out.pack(pady=10)

    def analyze(self):
        f = filedialog.askopenfilename()
        if not f: return
        self.out.delete("0.0", "end")
        self.out.insert("end", f"FILE: {os.path.basename(f)}\n{'='*40}\n")
        try:
            # Hashes
            md5, sha1, sha256 = hashlib.md5(), hashlib.sha1(), hashlib.sha256()
            with open(f, "rb") as file:
                chunk = file.read(4096)
                while chunk:
                    md5.update(chunk); sha1.update(chunk); sha256.update(chunk)
                    chunk = file.read(4096)
            self.out.insert("end", "[HASH VALUES]\n")
            self.out.insert("end", f"MD5:    {md5.hexdigest()}\n")
            self.out.insert("end", f"SHA1:   {sha1.hexdigest()}\n")
            self.out.insert("end", f"SHA256: {sha256.hexdigest()}\n\n")
            
            # EXIF
            try:
                img = Image.open(f)
                exif = img._getexif()
                if exif:
                    self.out.insert("end", "[EXIF METADATA]\n")
                    for tag, val in exif.items():
                        tag_name = ExifTags.TAGS.get(tag, tag)
                        self.out.insert("end", f"{tag_name}: {val}\n")
                else: self.out.insert("end", "[EXIF] No metadata found (or not an image).\n")
            except: self.out.insert("end", "[EXIF] Skipped (Not an image file).\n")
        except Exception as e: self.out.insert("end", f"Error reading file: {e}")


# =============================================================================
# 5. TOOL: REPOSITORY (SPLIT: BROWSER vs DOWNLOAD)
# =============================================================================
class RepoFrame(ctk.CTkFrame):
    def __init__(self, master, return_callback):
        super().__init__(master)
        self.return_callback = return_callback
        self.setup_ui()

    def setup_ui(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(top, text="< Back", command=self.return_callback, width=80, fg_color="#333333").pack(side="left")
        ctk.CTkLabel(self, text="Tool Repository", font=("Roboto", 24, "bold")).pack(pady=5)
        
        self.scroll = ctk.CTkScrollableFrame(self, width=950, height=600)
        self.scroll.pack(pady=10, fill="both", expand=True)

        # -------------------------------------------------------------
        # CATEGORY 1: BROWSER-BASED (Instant Input/Output)
        # -------------------------------------------------------------
        self.add_section_header("🌐 Browser-Based Tools (Instant Input/Output)", "#2E8B57")
        
        browser_tools = [
            ("CyberChef", "The 'Swiss Army Knife'. Paste hex, base64, or any data and transform it instantly.", "https://gchq.github.io/CyberChef/"),
            ("CrackStation", "Massive pre-computed rainbow tables. Paste a hash, get the password instantly.", "https://crackstation.net/"),
            ("RevShells.com", "Online Reverse Shell generator. Select OS and IP, get the command.", "https://www.revshells.com/"),
            ("Aperisolve", "Online Steganography platform. Upload image, it runs zsteg, steghide, etc.", "https://www.aperisolve.com/"),
            ("VirusTotal", "Upload a file or URL to scan it against 70+ antivirus engines.", "https://www.virustotal.com/gui/home/upload"),
        ]

        for name, desc, url in browser_tools:
            self.add_tool_row(name, desc, url)

        # -------------------------------------------------------------
        # CATEGORY 2: DOWNLOADABLE SOFTWARE (Local Install)
        # -------------------------------------------------------------
        self.add_section_header("⬇️ Downloadable Software (Requires Install)", "#E59400")

        download_tools = [
            ("Ghidra", "NSA's Reverse Engineering Suite. Best free alternative to IDA Pro.", "https://ghidra-sre.org/"),
            ("x64dbg", "Open-source x64/x32 debugger for Windows. Modern and powerful.", "https://x64dbg.com/"),
            ("Wireshark", "Network Protocol Analyzer. Capture and inspect packets deeply.", "https://www.wireshark.org/download.html"),
            ("Burp Suite", "Leading software for web security testing (Proxy/Scanner).", "https://portswigger.net/burp/communitydownload"),
            ("Jadx", "Decompile Android APK files to Java code. Drag and drop interface.", "https://github.com/skylot/jadx/releases"),
            ("Hashcat", "The fastest password cracker. Uses your GPU to brute-force hashes.", "https://hashcat.net/hashcat/"),
        ]

        for name, desc, url in download_tools:
            self.add_tool_row(name, desc, url)

    def add_section_header(self, text, color):
        ctk.CTkLabel(self.scroll, text=text, font=("Roboto", 20, "bold"), text_color=color, anchor="w").pack(fill="x", padx=10, pady=(30, 10))
        ctk.CTkFrame(self.scroll, height=2, fg_color="gray").pack(fill="x", padx=10, pady=(0, 10))

    def add_tool_row(self, name, desc, url):
        row = ctk.CTkFrame(self.scroll, fg_color="#2b2b2b")
        row.pack(fill="x", padx=10, pady=3)
        ctk.CTkLabel(row, text=name, font=("Roboto", 14, "bold"), width=150, anchor="w").pack(side="left", padx=10)
        ctk.CTkLabel(row, text=desc, text_color="gray80", anchor="w").pack(side="left", padx=10, fill="x", expand=True)
        ctk.CTkButton(row, text="Open Website", width=120, command=lambda u=url: webbrowser.open(u), fg_color="#4B0082").pack(side="right", padx=10, pady=8)


# =============================================================================
# MAIN APP MENU
# =============================================================================
class CTFApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("CTF-Toolkit")
        self.geometry("1100x800")
        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)
        self.show_menu()

    def clear(self):
        for w in self.container.winfo_children(): w.destroy()

    def show_menu(self):
        self.clear()
        
        # Background
        if os.path.exists("taust.jpg"):
            try:
                bg = ctk.CTkImage(Image.open("taust.jpg"), size=(1100, 800))
                ctk.CTkLabel(self.container, image=bg, text="").place(x=0, y=0, relwidth=1, relheight=1)
            except: pass

        # Title
        title_fr = ctk.CTkFrame(self.container, fg_color="transparent")
        title_fr.pack(pady=(60, 40))
        ctk.CTkLabel(title_fr, text="CTF-TOOLKIT", font=("Orbitron", 50, "bold"), text_color="#00ff00").pack()
        ctk.CTkLabel(title_fr, text="The Ultimate Hacking Suite", font=("Arial", 16), text_color="gray80").pack()

        # Buttons
        opts = {"width": 450, "height": 60, "font": ("Roboto", 18, "bold"), "fg_color": "#1f1f1f", "border_color": "#00ff00", "border_width": 2, "hover_color": "#333333"}
        
        ctk.CTkButton(self.container, text="1. Zip Manager (Pack & Unpack)", command=lambda: self.switch(ZipToolFrame), **opts).pack(pady=10)
        ctk.CTkButton(self.container, text="2. Text Converter (B64/Hex/Bin)", command=lambda: self.switch(DecoderFrame), **opts).pack(pady=10)
        ctk.CTkButton(self.container, text="3. Caesar Cipher (1-25 Shift)", command=lambda: self.switch(CaesarFrame), **opts).pack(pady=10)
        ctk.CTkButton(self.container, text="4. File Analysis (Hash & EXIF)", command=lambda: self.switch(AnalysisFrame), **opts).pack(pady=10)
        
        repo_opts = opts.copy(); repo_opts.update({"fg_color": "#2a0040", "border_color": "#9400D3"})
        ctk.CTkButton(self.container, text="5. Tool Repository (Links)", command=lambda: self.switch(RepoFrame), **repo_opts).pack(pady=20)

        ctk.CTkButton(self.container, text="EXIT", command=self.destroy, width=200, height=40, fg_color="#8B0000", hover_color="red").pack(pady=30)
        
        ctk.CTkLabel(self.container, text="Joonas v10.1", text_color="gray40").place(relx=0.98, rely=0.98, anchor="se")

    def switch(self, frame_class):
        self.clear()
        frame_class(self.container, self.show_menu).pack(fill="both", expand=True)

if __name__ == "__main__":
    app = CTFApp()
    app.mainloop()