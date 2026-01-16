# --- Automaatne teekide installeerimine ---
try:
    from setup import install_requirements
    install_requirements()
except ImportError:
    pass

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
# 1. TOOL: ZIP MANAGER (TURVATUD / SECURED)
# =============================================================================
class ZipToolFrame(ctk.CTkFrame):
    def __init__(self, master, return_callback):
        super().__init__(master)
        self.return_callback = return_callback
        self.extract_folder = "CTF_EXTRACTED"
        self.compress_folder = "CTF_COMPRESSED"
        
        # --- SECURITY LIMITS ---
        self.MAX_FILES = 2000
        self.MAX_TOTAL_SIZE = 200 * 1024 * 1024  # 200 MB
        self.MAX_SINGLE_FILE = 50 * 1024 * 1024  # 50 MB
        
        self.setup_ui()

    def setup_ui(self):
        # Header
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(top, text="< Back", command=self.return_callback, width=80, fg_color="#333333").pack(side="left")
        ctk.CTkLabel(self, text="Zip Manager (Secured)", font=("Roboto", 24, "bold")).pack(pady=5)

        # Tabs
        self.tabview = ctk.CTkTabview(self, width=900, height=550)
        self.tabview.pack(pady=10)
        self.tab_ext = self.tabview.add("Extract (Unzip)")
        self.tab_comp = self.tabview.add("Compress (Zip)")

        # --- EXTRACT UI ---
        fr_ext = self.tab_ext
        
        # Input Section
        ctk.CTkLabel(fr_ext, text="Input File (Path):", anchor="w").pack(fill="x", padx=50)
        self.ext_input = ctk.CTkEntry(fr_ext, width=700)
        self.ext_input.pack(pady=5)
        
        # Settings & Buttons
        ctrl_ext = ctk.CTkFrame(fr_ext, fg_color="transparent")
        ctrl_ext.pack(pady=10)
        ctk.CTkLabel(ctrl_ext, text="Layers Limit:").pack(side="left", padx=5)
        self.ext_layers = ctk.CTkEntry(ctrl_ext, width=50, justify="center"); self.ext_layers.insert(0, "50"); self.ext_layers.pack(side="left", padx=5)
        ctk.CTkButton(ctrl_ext, text="Browse & Extract (Safe)", command=self.run_extract, fg_color="#2E8B57", width=200).pack(side="left", padx=20)

        # Output Section
        ctk.CTkLabel(fr_ext, text="Output / Log:", anchor="w").pack(fill="x", padx=50)
        self.ext_log = ctk.CTkTextbox(fr_ext, width=800, height=200)
        self.ext_log.pack(pady=5)
        
        # --- COMPRESS UI ---
        fr_comp = self.tab_comp
        
        # Input Section
        ctk.CTkLabel(fr_comp, text="Input File (Path):", anchor="w").pack(fill="x", padx=50)
        self.comp_input = ctk.CTkEntry(fr_comp, width=700)
        self.comp_input.pack(pady=5)

        # Settings & Buttons
        ctrl_comp = ctk.CTkFrame(fr_comp, fg_color="transparent")
        ctrl_comp.pack(pady=10)
        ctk.CTkLabel(ctrl_comp, text="Zip Bomb Layers:").pack(side="left", padx=5)
        self.comp_layers = ctk.CTkEntry(ctrl_comp, width=50, justify="center"); self.comp_layers.insert(0, "10"); self.comp_layers.pack(side="left", padx=5)
        ctk.CTkButton(ctrl_comp, text="Browse & Compress", command=self.run_compress, fg_color="#E59400", width=200).pack(side="left", padx=20)

        # Output Section
        ctk.CTkLabel(fr_comp, text="Output / Log:", anchor="w").pack(fill="x", padx=50)
        self.comp_log = ctk.CTkTextbox(fr_comp, width=800, height=200)
        self.comp_log.pack(pady=5)

    def log(self, box, txt):
        box.insert("end", txt + "\n"); box.see("end")

    # --- SECURITY HELPER FUNCTIONS ---
    def is_within_directory(self, base_dir, target_path):
        # Teeb kindlaks, et target_path on tõesti base_dir sees
        abs_base = os.path.abspath(base_dir)
        abs_target = os.path.abspath(target_path)
        return os.path.commonpath([abs_base]) == os.path.commonpath([abs_base, abs_target])

    def validate_zip_safety(self, zip_ref, extract_path):
        """
        Kontrollib Zip-Pomme ja Zip-Slip rünnakuid enne lahtipakkimist.
        """
        infos = zip_ref.infolist()
        
        # 1. Failide arvu piirang
        if len(infos) > self.MAX_FILES:
            raise RuntimeError(f"SECURITY WARNING: Too many files ({len(infos)} > {self.MAX_FILES})")

        total_size = 0
        
        for info in infos:
            # 2. Üksiku faili suuruse piirang
            if info.file_size > self.MAX_SINGLE_FILE:
                raise RuntimeError(f"SECURITY WARNING: File too large: {info.filename} ({info.file_size / 1024 / 1024:.2f} MB)")
            
            total_size += info.file_size
            
            # 3. Zip Slip kaitse (Path Traversal)
            out_path = os.path.join(extract_path, info.filename)
            if not self.is_within_directory(extract_path, out_path):
                raise RuntimeError(f"SECURITY WARNING: Path traversal attempt detected (Zip Slip): {info.filename}")

        # 4. Kogumahu piirang
        if total_size > self.MAX_TOTAL_SIZE:
             raise RuntimeError(f"SECURITY WARNING: Total extracted size too large ({total_size / 1024 / 1024:.2f} MB)")

    # --- EXTRACT LOGIC ---
    def run_extract(self):
        f = filedialog.askopenfilename(filetypes=[("Zip", "*.zip")])
        if not f: return
        self.ext_input.delete(0, "end"); self.ext_input.insert(0, f)
        self.ext_log.delete("0.0", "end")
        threading.Thread(target=self.do_extract, args=(f,)).start()

    def do_extract(self, filename):
        try:
            limit = int(self.ext_layers.get())
            work_dir = os.path.join(os.path.dirname(filename), self.extract_folder)
            
            # Puhastame eelmise töö kausta
            if os.path.exists(work_dir): shutil.rmtree(work_dir)
            os.makedirs(work_dir)
            
            # Kopeerime algse faili
            curr = os.path.join(work_dir, os.path.basename(filename))
            shutil.copy2(filename, curr)
            
            count = 0
            self.log(self.ext_log, f"Starting Safe Extraction in: {work_dir}")

            while count < limit:
                if not zipfile.is_zipfile(curr): break
                
                try:
                    with zipfile.ZipFile(curr, 'r') as z:
                        # KÄIVITAME TURVAKONTROLLI
                        self.validate_zip_safety(z, work_dir)
                        
                        # Kui kõik on korras, pakime lahti
                        z.extractall(work_dir)
                        self.log(self.ext_log, f"[Layer {count+1}] Verified & Extracted.")
                        
                except RuntimeError as e:
                    self.log(self.ext_log, f"❌ {e}")
                    self.log(self.ext_log, "ABORTING EXTRACTION DUE TO SECURITY RISK.")
                    return # Lõpetame töö kohe
                except Exception as e:
                    self.log(self.ext_log, f"Error: {e}")
                    return

                # Kustutame vana zipi
                os.remove(curr)
                
                # Otsime uut faili (recursive)
                files = [f for f in os.listdir(work_dir) if not f.startswith('.')] # ignore hidden
                if not files: break
                
                # Võtame esimese leitud faili järgmiseks ringiks
                curr = os.path.join(work_dir, files[0])
                count += 1
            
            self.log(self.ext_log, f"✅ DONE! Files located at: {work_dir}")
            os.startfile(work_dir)
        except Exception as e: self.log(self.ext_log, f"Global Error: {e}")

    # --- COMPRESS LOGIC ---
    def run_compress(self):
        f = filedialog.askopenfilename()
        if not f: return
        self.comp_input.delete(0, "end"); self.comp_input.insert(0, f)
        self.comp_log.delete("0.0", "end")
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
                self.log(self.comp_log, f"Compressed layer {i}...")
            
            self.log(self.comp_log, f"DONE! {work_dir}")
            os.startfile(work_dir)
        except Exception as e: self.log(self.comp_log, f"Error: {e}")


# =============================================================================
# 2. TOOL: TEXT CONVERTER (UPDATED: SHOW ALL LOOPS)
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

        # Input
        ctk.CTkLabel(self, text="Input Text:", anchor="w").pack(fill="x", padx=100)
        self.inp = ctk.CTkTextbox(self, height=120, width=900)
        self.inp.pack(pady=5)

        ctrl = ctk.CTkFrame(self)
        ctrl.pack(pady=10)
        
        btn_opts = {"width": 120, "height": 35}
        
        # Loop control
        loop_frame = ctk.CTkFrame(ctrl, fg_color="transparent")
        loop_frame.grid(row=0, column=0, columnspan=5, pady=(5, 15))
        ctk.CTkLabel(loop_frame, text="Repeats (Loops):", text_color="#E59400", font=("Roboto", 14, "bold")).pack(side="left", padx=5)
        self.loop_entry = ctk.CTkEntry(loop_frame, width=50, justify="center"); self.loop_entry.insert(0, "1"); self.loop_entry.pack(side="left", padx=5)

        # Encode row
        ctk.CTkLabel(ctrl, text="ENCODE:").grid(row=1, column=0, padx=10, pady=5)
        ctk.CTkButton(ctrl, text="To Base64", command=lambda: self.run("enc", "b64"), **btn_opts).grid(row=1, column=1, padx=5, pady=5)
        ctk.CTkButton(ctrl, text="To Hex", command=lambda: self.run("enc", "hex"), **btn_opts).grid(row=1, column=2, padx=5, pady=5)
        ctk.CTkButton(ctrl, text="To Binary", command=lambda: self.run("enc", "bin"), **btn_opts).grid(row=1, column=3, padx=5, pady=5)
        ctk.CTkButton(ctrl, text="URL Encode", command=lambda: self.run("enc", "url"), **btn_opts).grid(row=1, column=4, padx=5, pady=5)

        # Decode row
        ctk.CTkLabel(ctrl, text="DECODE:").grid(row=2, column=0, padx=10, pady=5)
        ctk.CTkButton(ctrl, text="From Base64", command=lambda: self.run("dec", "b64"), fg_color="#2E8B57", **btn_opts).grid(row=2, column=1, padx=5, pady=5)
        ctk.CTkButton(ctrl, text="From Hex", command=lambda: self.run("dec", "hex"), fg_color="#2E8B57", **btn_opts).grid(row=2, column=2, padx=5, pady=5)
        ctk.CTkButton(ctrl, text="From Binary", command=lambda: self.run("dec", "bin"), fg_color="#2E8B57", **btn_opts).grid(row=2, column=3, padx=5, pady=5)
        ctk.CTkButton(ctrl, text="URL Decode", command=lambda: self.run("dec", "url"), fg_color="#2E8B57", **btn_opts).grid(row=2, column=4, padx=5, pady=5)

        # Output
        ctk.CTkLabel(self, text="Output Text:", anchor="w").pack(fill="x", padx=100)
        self.out = ctk.CTkTextbox(self, height=250, width=900)
        self.out.pack(pady=5)
        ctk.CTkButton(self, text="Clear All", command=self.clear_all, fg_color="#8B0000", width=200).pack(pady=10)

    def clear_all(self):
        self.inp.delete("0.0", "end")
        self.out.delete("0.0", "end")

    def single_step(self, txt, action, mode):
        if action == "enc":
            if mode == "b64": return base64.b64encode(txt.encode()).decode()
            elif mode == "hex": return binascii.hexlify(txt.encode()).decode()
            elif mode == "bin": return ' '.join(format(ord(c), '08b') for c in txt)
            elif mode == "url": return urllib.parse.quote(txt)
        else: # decode
            if mode == "b64": 
                pad = len(txt) % 4
                if pad: txt += "=" * (4 - pad)
                return base64.b64decode(txt).decode('utf-8', 'ignore')
            elif mode == "hex": return bytes.fromhex(txt).decode('utf-8', 'ignore')
            elif mode == "bin": 
                txt = txt.replace(" ", "")
                n = int(txt, 2)
                return n.to_bytes((n.bit_length() + 7) // 8, 'big').decode('utf-8', 'ignore')
            elif mode == "url": return urllib.parse.unquote(txt)
        return txt

    def run(self, action, mode):
        txt = self.inp.get("0.0", "end").strip()
        if not txt: return
        try:
            limit = int(self.loop_entry.get())
            if limit < 1: limit = 1
        except ValueError: limit = 1
        
        # LOGGING ALL STEPS
        full_log = f"--- STARTING {action.upper()} {mode.upper()} ({limit} Loops) ---\n"
        
        current_val = txt
        count = 0
        try:
            for i in range(limit):
                try: 
                    new_val = self.single_step(current_val, action, mode)
                except: 
                    full_log += f"[Step {i+1}] ❌ Error/Invalid Format\n"
                    break
                
                if not new_val or new_val == current_val: 
                    full_log += f"[Step {i+1}] 🛑 No Change / End.\n"
                    break
                
                current_val = new_val.strip()
                count += 1
                
                # APPEND STEP TO LOG
                full_log += f"[{i+1}]: {current_val}\n"
            
            full_log += f"--- FINISHED ---\n\n"
            self.out.insert("0.0", full_log)
        except Exception as e: 
            self.out.insert("0.0", f"CRITICAL ERROR: {e}\n\n")


# =============================================================================
# 3. TOOL: CAESAR CIPHER
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
        ctk.CTkLabel(self, text="Caesar Cipher", font=("Roboto", 24, "bold")).pack(pady=5)
        
        ctk.CTkLabel(self, text="Note: Works on English Alphabet (A-Z).", text_color="orange").pack()

        # Input
        ctk.CTkLabel(self, text="Input Text:", anchor="w").pack(fill="x", padx=100)
        self.inp = ctk.CTkTextbox(self, height=120, width=900)
        self.inp.pack(pady=5)
        
        # Buttons
        ctrl_spec = ctk.CTkFrame(self, fg_color="transparent")
        ctrl_spec.pack(pady=5)
        
        ctk.CTkLabel(ctrl_spec, text="Specific Shift:").pack(side="left")
        self.shift_val = ctk.CTkEntry(ctrl_spec, width=50, justify="center"); self.shift_val.insert(0, "13"); self.shift_val.pack(side="left", padx=5)
        ctk.CTkButton(ctrl_spec, text="Encrypt (+)", command=lambda: self.run_caesar(1), fg_color="#2E8B57", width=100).pack(side="left", padx=5)
        ctk.CTkButton(ctrl_spec, text="Decrypt (-)", command=lambda: self.run_caesar(-1), fg_color="#2E8B57", width=100).pack(side="left", padx=5)

        ctk.CTkButton(self, text="DECRYPT ALL (Try 1-25)", command=self.run_brute, fg_color="#E59400", width=400, height=40, font=("Roboto", 16, "bold")).pack(pady=10)

        # Output
        ctk.CTkLabel(self, text="Output Text:", anchor="w").pack(fill="x", padx=100)
        self.out = ctk.CTkTextbox(self, height=300, width=900)
        self.out.pack(pady=5)
        ctk.CTkButton(self, text="Clear", command=lambda: self.out.delete("0.0","end"), fg_color="#8B0000").pack(pady=5)

    def run_caesar(self, direction):
        txt = self.inp.get("0.0", "end").strip()
        try: 
            val = int(self.shift_val.get())
            shift = val * direction 
        except: 
            shift = 13 * direction
        
        mode_str = "ENCRYPT" if direction == 1 else "DECRYPT"
        self.out.insert("0.0", f"--- {mode_str} (Shift {shift}) ---\n{self.rot(txt, shift)}\n\n")

    def run_brute(self):
        txt = self.inp.get("0.0", "end").strip()
        self.out.delete("0.0", "end")
        res = "--- DECRYPT ALL (Showing all 25 Possibilities) ---\n"
        for i in range(1, 26):
            decoded_line = self.rot(txt, i)
            res += f"ROT +{i:02}: {decoded_line}\n"
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
# 4. TOOL: FILE ANALYSIS
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

        # Input
        ctk.CTkLabel(self, text="Input File (Path):", anchor="w").pack(fill="x", padx=100)
        self.inp_entry = ctk.CTkEntry(self, width=900)
        self.inp_entry.pack(pady=5)

        # Button
        ctk.CTkButton(self, text="Select File & Analyze", command=self.analyze, fg_color="#2E8B57", width=200).pack(pady=20)
        
        # Output
        ctk.CTkLabel(self, text="Analysis Results (Output):", anchor="w").pack(fill="x", padx=100)
        self.out = ctk.CTkTextbox(self, width=900, height=450)
        self.out.pack(pady=5)

    def analyze(self):
        f = filedialog.askopenfilename()
        if not f: return
        
        # Update Input Box
        self.inp_entry.delete(0, "end")
        self.inp_entry.insert(0, f)
        
        # Clear Output
        self.out.delete("0.0", "end")
        self.out.insert("end", f"FILE: {os.path.basename(f)}\n{'='*40}\n")
        
        try:
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
# 5. TOOL: REPOSITORY
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

        self.add_section_header("🌐 Browser-Based Tools", "#2E8B57")
        browser_tools = [
            ("CyberChef", "The 'Swiss Army Knife'. Transform data instantly.", "https://gchq.github.io/CyberChef/"),
            ("CrackStation", "Massive rainbow tables for hash cracking.", "https://crackstation.net/"),
            ("RevShells.com", "Online Reverse Shell generator.", "https://www.revshells.com/"),
            ("Aperisolve", "Online Steganography platform (zsteg, steghide).", "https://www.aperisolve.com/"),
            ("VirusTotal", "Scan files/URLs against antivirus engines.", "https://www.virustotal.com/gui/home/upload"),
        ]
        for name, desc, url in browser_tools: self.add_tool_row(name, desc, url)

        self.add_section_header("⬇️ Downloadable Software", "#E59400")
        download_tools = [
            ("Ghidra", "NSA's Reverse Engineering Suite.", "https://ghidra-sre.org/"),
            ("x64dbg", "Open-source x64/x32 debugger for Windows.", "https://x64dbg.com/"),
            ("Wireshark", "Network Protocol Analyzer.", "https://www.wireshark.org/download.html"),
            ("Burp Suite", "Web security testing (Proxy/Scanner).", "https://portswigger.net/burp/communitydownload"),
            ("Jadx", "Decompile Android APK to Java.", "https://github.com/skylot/jadx/releases"),
            ("Hashcat", "GPU Password cracker.", "https://hashcat.net/hashcat/"),
        ]
        for name, desc, url in download_tools: self.add_tool_row(name, desc, url)

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
        if os.path.exists("taust.jpg"):
            try:
                bg = ctk.CTkImage(Image.open("taust.jpg"), size=(1100, 800))
                ctk.CTkLabel(self.container, image=bg, text="").place(x=0, y=0, relwidth=1, relheight=1)
            except: pass

        title_fr = ctk.CTkFrame(self.container, fg_color="transparent")
        title_fr.pack(pady=(60, 40))
        ctk.CTkLabel(title_fr, text="CTF-TOOLKIT", font=("Orbitron", 50, "bold"), text_color="#00ff00").pack()
        
        # UUS ALAMPEALKIRI
        ctk.CTkLabel(title_fr, text="Essential Toolkit for CTF Challenges", font=("Arial", 16), text_color="gray80").pack()

        opts = {"width": 450, "height": 60, "font": ("Roboto", 18, "bold"), "fg_color": "#1f1f1f", "border_color": "#00ff00", "border_width": 2, "hover_color": "#333333"}
        
        ctk.CTkButton(self.container, text="1. Zip Manager (Pack & Unpack)", command=lambda: self.switch(ZipToolFrame), **opts).pack(pady=10)
        ctk.CTkButton(self.container, text="2. Text Converter (B64/Hex/Bin)", command=lambda: self.switch(DecoderFrame), **opts).pack(pady=10)
        ctk.CTkButton(self.container, text="3. Caesar Cipher (Decrypt All)", command=lambda: self.switch(CaesarFrame), **opts).pack(pady=10)
        ctk.CTkButton(self.container, text="4. File Analysis (Hash & EXIF)", command=lambda: self.switch(AnalysisFrame), **opts).pack(pady=10)
        
        repo_opts = opts.copy(); repo_opts.update({"fg_color": "#2a0040", "border_color": "#9400D3"})
        ctk.CTkButton(self.container, text="5. Tool Repository (Links)", command=lambda: self.switch(RepoFrame), **repo_opts).pack(pady=20)

        ctk.CTkButton(self.container, text="EXIT", command=self.destroy, width=200, height=40, fg_color="#8B0000", hover_color="red").pack(pady=30)
        
        # UUS VESIMÄRK
        ctk.CTkLabel(self.container, text="Joonas 2026", text_color="gray40").place(relx=0.98, rely=0.98, anchor="se")

    def switch(self, frame_class):
        self.clear()
        frame_class(self.container, self.show_menu).pack(fill="both", expand=True)

if __name__ == "__main__":
    app = CTFApp()
    app.mainloop()
