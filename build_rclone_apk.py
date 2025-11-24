import os
import urllib.request
import zipfile
import tarfile
import shutil
import time

# Configuration
RCLONE_VERSION = "v1.72.0"
ARCH = "linux-arm64"
DOWNLOAD_URL = f"https://downloads.rclone.org/{RCLONE_VERSION}/rclone-{RCLONE_VERSION}-{ARCH}.zip"
APK_NAME = f"rclone_{RCLONE_VERSION}_arm64.apk"
ICON_URL = "https://raw.githubusercontent.com/rclone/rclone/master/graphics/logo/logo_symbol/logo_symbol_color_256px.png"

def download_file(url, filename):
    print(f"Downloading {filename}...")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(filename, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        raise

def make_tarfile(output_filename, source_dir):
    with tarfile.open(output_filename, "w:gz") as tar:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, source_dir)
                st = os.stat(full_path)
                ti = tarfile.TarInfo(name=rel_path)
                ti.size = st.st_size
                ti.mtime = time.time()
                
                # Permissions: 755 for scripts/binaries, 644 for others
                if file.endswith('.sh') or file.endswith('.py') or os.access(full_path, os.X_OK):
                    ti.mode = 0o755
                else:
                    ti.mode = 0o644
                
                ti.uid = 0
                ti.gid = 0
                ti.uname = "root"
                ti.gname = "root"

                with open(full_path, "rb") as f:
                    tar.addfile(ti, f)

def build_apkg():
    print(f"--- Building Asustor Package: {APK_NAME} ---")
    
    build_root = "build_env"
    control_dir = os.path.join(build_root, "CONTROL")
    bin_dir = os.path.join(build_root, "bin")

    # 1. Clean Build Env
    if os.path.exists(build_root): shutil.rmtree(build_root)
    os.makedirs(control_dir)
    os.makedirs(bin_dir)

    # 2. Download Rclone
    zip_path = "rclone_temp.zip"
    if not os.path.exists("rclone_bin"):
        download_file(DOWNLOAD_URL, zip_path)
        with zipfile.ZipFile(zip_path, 'r') as z:
            bin_member = [m for m in z.namelist() if m.endswith("rclone") and not m.endswith(".1")][0]
            with open("rclone_bin", "wb") as f_out:
                f_out.write(z.read(bin_member))
        os.remove(zip_path)
    
    shutil.move("rclone_bin", os.path.join(bin_dir, "rclone"))
    os.chmod(os.path.join(bin_dir, "rclone"), 0o755)

    # 3. Process CONTROL Files
    required_files = ["config.json", "start-stop.sh"]
    for f in required_files:
        if not os.path.exists(f):
            print(f"ERROR: {f} missing! Ensure it is in this folder.")
            return
        shutil.copy(f, os.path.join(control_dir, f))

    # Fix Line Endings for Script
    script_path = os.path.join(control_dir, "start-stop.sh")
    with open(script_path, "rb") as infile:
        content = infile.read().replace(b"\r\n", b"\n")
    with open(script_path, "wb") as outfile:
        outfile.write(content)
    os.chmod(script_path, 0o755)

    # 4. Smart File Handling (Changelog/Description)
    # Use local files if they exist, otherwise create defaults
    if os.path.exists("description.txt"):
        shutil.copy("description.txt", os.path.join(control_dir, "description.txt"))
    else:
        with open(os.path.join(control_dir, "description.txt"), "w") as f: f.write("Rclone for Asustor")

    if os.path.exists("changelog.txt"):
        shutil.copy("changelog.txt", os.path.join(control_dir, "changelog.txt"))
    else:
        with open(os.path.join(control_dir, "changelog.txt"), "w") as f: f.write("Initial Version")

    # 5. Smart Icon Handling (The Fix)
    # Priority: icon.png > icon-enable.png > Download
    if os.path.exists("icon.png"):
        print("Using local icon.png")
        shutil.copy("icon.png", os.path.join(control_dir, "icon.png"))
    elif os.path.exists("icon-enable.png"):
        print("Using local icon-enable.png as icon.png")
        shutil.copy("icon-enable.png", os.path.join(control_dir, "icon.png"))
    else:
        print("No icon found, downloading default...")
        download_file(ICON_URL, "icon.png")
        shutil.copy("icon.png", os.path.join(control_dir, "icon.png"))

    # 6. Create Package
    print("Creating internal tarballs...")
    make_tarfile("control.tar.gz", control_dir)
    
    # Exclude CONTROL from data.tar.gz
    shutil.move(control_dir, "CONTROL_TEMP")
    make_tarfile("data.tar.gz", build_root)
    shutil.move("CONTROL_TEMP", control_dir)

    with open("apkg-version", "w") as f:
        f.write("2.0\n")

    print(f"Zipping final package {APK_NAME}...")
    with zipfile.ZipFile(APK_NAME, 'w', zipfile.ZIP_DEFLATED) as apk:
        apk.write("apkg-version")
        apk.write("control.tar.gz")
        apk.write("data.tar.gz")

    # Cleanup
    os.remove("apkg-version")
    os.remove("control.tar.gz")
    os.remove("data.tar.gz")
    if os.path.exists("rclone_bin"): os.remove("rclone_bin")
    # Note: We do NOT remove local icon.png if we downloaded it, so you can keep it
    shutil.rmtree(build_root)

    print("Success! Package created.")

if __name__ == "__main__":
    build_apkg()