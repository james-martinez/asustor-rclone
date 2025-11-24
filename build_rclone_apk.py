import os
import urllib.request
import zipfile
import shutil
import tarfile
import stat

# Configuration
RCLONE_VERSION = "v1.72.0"
ARCH = "linux-arm64" # Change to 'linux-arm64' for ARM NAS devices
DOWNLOAD_URL = f"https://downloads.rclone.org/{RCLONE_VERSION}/rclone-{RCLONE_VERSION}-{ARCH}.zip"
APK_NAME = f"rclone_{RCLONE_VERSION}_arm64.apk"

def create_icon():
    # Create a simple 90x90 placeholder icon if one doesn't exist
    if not os.path.exists("icon.png"):
        print("Generating placeholder icon.png...")
        from PIL import Image, ImageDraw
        img = Image.new('RGB', (90, 90), color = (73, 109, 137))
        d = ImageDraw.Draw(img)
        d.text((10,35), "Rclone", fill=(255,255,0))
        img.save('icon.png')
    else:
        print("Using existing icon.png")

def download_rclone():
    print(f"Downloading rclone {RCLONE_VERSION}...")
    zip_path = "rclone_temp.zip"
    urllib.request.urlretrieve(DOWNLOAD_URL, zip_path)
    
    print("Extracting binary...")
    with zipfile.ZipFile(zip_path, 'r') as z:
        # Find the binary inside the zip (it's usually in a subfolder)
        bin_member = [m for m in z.namelist() if m.endswith("rclone") and not m.endswith(".1")][0]
        with open("rclone_bin", "wb") as f_out:
            f_out.write(z.read(bin_member))
    
    # Cleanup zip
    os.remove(zip_path)
    
    # Make executable
    st = os.stat("rclone_bin")
    os.chmod("rclone_bin", st.st_mode | stat.S_IEXEC)
    return "rclone_bin"

def build_apkg():
    # 1. Create Directory Structure
    build_dir = "build_pkg"
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    
    control_dir = os.path.join(build_dir, "CONTROL")
    bin_dir = os.path.join(build_dir, "bin")
    
    os.makedirs(control_dir)
    os.makedirs(bin_dir)

    # 2. Copy/Create Control Files
    # Check if user provided config and script, otherwise warn
    if not os.path.exists("config.json") or not os.path.exists("start-stop.sh"):
        print("Error: config.json or start-stop.sh missing. Please save the code blocks above first.")
        return

    shutil.copy("config.json", os.path.join(control_dir, "config.json"))
    shutil.copy("start-stop.sh", os.path.join(control_dir, "start-stop.sh"))
    
    # Ensure start-stop.sh is executable
    st = os.stat(os.path.join(control_dir, "start-stop.sh"))
    os.chmod(os.path.join(control_dir, "start-stop.sh"), st.st_mode | stat.S_IEXEC)

    # Icon
    try:
        create_icon()
        shutil.copy("icon.png", os.path.join(control_dir, "icon.png"))
    except ImportError:
        print("Warning: PIL (Pillow) not installed. Please provide an 'icon.png' manually or install pillow: pip install pillow")
        # Create a dummy text file as icon just to prevent crash, user should replace
        with open(os.path.join(control_dir, "icon.png"), "wb") as f:
            f.write(b'')

    # Description/Changelog (Required by some versions of ADM)
    with open(os.path.join(control_dir, "description.txt"), "w") as f:
        f.write("Rclone: RSYNC for Cloud Storage")
    with open(os.path.join(control_dir, "changelog.txt"), "w") as f:
        f.write("Initial release")

    # 3. Place Binary
    bin_path = download_rclone()
    shutil.move(bin_path, os.path.join(bin_dir, "rclone"))

    # 4. Zip it up (Asustor APK is just a zip)
    print(f"Packaging {APK_NAME}...")
    with zipfile.ZipFile(APK_NAME, 'w', zipfile.ZIP_DEFLATED) as apk:
        for root, dirs, files in os.walk(build_dir):
            for file in files:
                abs_path = os.path.join(root, file)
                # Archive name should be relative to build_dir
                arcname = os.path.relpath(abs_path, build_dir)
                apk.write(abs_path, arcname)

    # Cleanup
    shutil.rmtree(build_dir)
    print("Done! App package created.")

if __name__ == "__main__":
    build_apkg()
