

import subprocess
import sys


def install_requirements():
    
    # Teegide nimekiri
    required_packages = [
        'customtkinter',
        'Pillow',
    ]
    
    print("=" * 60)
    print("CTF-Toolkit: Installeerime vajalikke teeke...")
    print("=" * 60)
    
    for package in required_packages:
        try:
            __import__(package.split()[0].replace('-', '_').lower())
            print(f"✓ {package} on juba installeeritud")
        except ImportError:
            print(f"\n📦 Installeerin: {package}")
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", package],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                print(f"✓ {package} edukalt installeeritud!")
            except subprocess.CalledProcessError as e:
                print(f"✗ VIGA: {package} installeerimine ebaõnnestus!")
                print(f"   Proovi käsitsi: pip install {package}")
                sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✓ Kõik teegid on installeeritud!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    install_requirements()
