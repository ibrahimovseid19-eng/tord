import requests
import zipfile
import io
import os
import shutil

def install_bettercap():
    print("Searching for Bettercap for Windows...")
    try:
        # Get latest release info
        api_url = "https://api.github.com/repos/bettercap/bettercap/releases/latest"
        resp = requests.get(api_url)
        resp.raise_for_status()
        data = resp.json()
        
        assets = data.get("assets", [])
        download_url = None
        for asset in assets:
            name = asset.get("name", "").lower()
            if "windows" in name and "amd64" in name and name.endswith(".zip"):
                download_url = asset.get("browser_download_url")
                break
        
        if not download_url:
            print("[-] Could not find a Windows binary in the latest release.")
            return

        print(f"[*] Downloading {download_url}...")
        r = requests.get(download_url)
        r.raise_for_status()
        
        print("[*] Extracting...")
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            for filename in z.namelist():
                if filename.endswith("bettercap.exe"):
                    # Extract to backend folder
                    target_dir = os.path.join(os.getcwd(), "backend")
                    source = z.open(filename)
                    target = open(os.path.join(target_dir, "bettercap.exe"), "wb")
                    with source, target:
                        shutil.copyfileobj(source, target)
                    print(f"[+] Installed bettercap.exe to {target_dir}")
                    return

        print("[-] bettercap.exe not found in the zip file.")

    except Exception as e:
        print(f"[-] Installation failed: {e}")
        print("[-] Please download manually from: https://github.com/bettercap/bettercap/releases")

if __name__ == "__main__":
    install_bettercap()
