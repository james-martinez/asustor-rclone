import os
import urllib.request
import zipfile
import tarfile
import shutil
import time
import io

# Configuration
RCLONE_VERSION = "v1.72.0"
ARCH = "linux-arm64"
DOWNLOAD_URL = f"https://downloads.rclone.org/{RCLONE_VERSION}/rclone-{RCLONE_VERSION}-{ARCH}.zip"
APK_NAME = f"rclone_{RCLONE_VERSION}_arm64.apk"
ICON_URL = "https://raw.githubusercontent.com/rclone/rclone/master/graphics/logo/logo_symbol/logo_symbol_color_256px.png"

def download_file(url, filename):
    print(f"Downloading {filename}...")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response, open(filename, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)

def make_tarfile(output_filename, source_dir, arcname_prefix=""):
    """
    Creates a tar.gz file from a directory.
    Replicates logic from apkg-tools: 
    - CONTROL tar contains contents of CONTROL dir
    - DATA tar contains contents of App root (excluding CONTROL)
    """
    with tarfile.open(output_filename, "w:gz") as tar:
        # Walk the directory
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                full_path = os.path.join(root, file)
                # Calculate relative path for archive
                rel_path = os.path.relpath(full_path, source_dir)
                
                # If we have a prefix (used if we needed to shift paths, usually empty for this)
                arcname = os.path.join(arcname_prefix, rel_path)
                
                # Get Stat info
                st = os.stat(full_path)
                
                # Create TarInfo manually to enforce permissions (Reference: apkg-tools)
                ti = tarfile.TarInfo(name=arcname)
                ti.size = st.st_size
                ti.mtime = time.time()
                
                # Permissions Logic (Replicating apkg-tools logic)
                if file.endswith('.sh') or file.endswith('.py') or os.access(full_path, os.X_OK):
                    ti.mode = 0o755
                else:
                    ti.mode = 0o644
                
                # Force user/group to root (0)
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

    # 1. Prepare clean build directory
    if os.path.exists(build_root): shutil.rmtree(build_root)
    os.makedirs(control_dir)
    os.makedirs(bin_dir)

    # 2. Download and Extract Rclone
    zip_path = "rclone_temp.zip"
    if not os.path.exists("rclone_bin"):
        download_file(DOWNLOAD_URL, zip_path)
        print("Extracting rclone binary...")
        with zipfile.ZipFile(zip_path, 'r') as z:
            bin_member = [m for m in z.namelist() if m.endswith("rclone") and not m.endswith(".1")][0]
            with open("rclone_bin", "wb") as f_out:
                f_out.write(z.read(bin_member))
        os.remove(zip_path)
    
    # Move binary to build_env/bin/
    shutil.move("rclone_bin", os.path.join(bin_dir, "rclone"))
    # Make executable locally so python detects it for permissions later
    os.chmod(os.path.join(bin_dir, "rclone"), 0o755)

    # 3. Prepare CONTROL files
    if not os.path.exists("config.json") or not os.path.exists("start-stop.sh"):
        print("ERROR: config.json or start-stop.sh missing!")
        return

    # Copy Config
    shutil.copy("config.json", os.path.join(control_dir, "config.json"))

    # Copy Script (Fixing Windows Line Endings to Unix LF)
    with open("start-stop.sh", "rb") as infile:
        content = infile.read().replace(b"\r\n", b"\n")
    with open(os.path.join(control_dir, "start-stop.sh"), "wb") as outfile:
        outfile.write(content)
    os.chmod(os.path.join(control_dir, "start-stop.sh"), 0o755)

    # Create Description/Changelog
    with open(os.path.join(control_dir, "description.txt"), "w") as f: f.write("Rclone for Asustor")
    with open(os.path.join(control_dir, "changelog.txt"), "w") as f: f.write("Initial Version")

    # Icon
    if not os.path.exists("icon.png"):
        download_file(ICON_URL, "icon.png")
    shutil.copy("icon.png", os.path.join(control_dir, "icon.png"))

    # 4. Create Internal Archives (The "Nested" Structure)
    print("Creating internal tarballs...")
    
    # A. control.tar.gz (Contents of CONTROL folder)
    make_tarfile("control.tar.gz", control_dir)

    # B. data.tar.gz (Contents of build_root EXCLUDING CONTROL)
    # We temporarily move CONTROL out to avoid including it in data
    shutil.move(control_dir, "CONTROL_TEMP")
    make_tarfile("data.tar.gz", build_root)
    shutil.move("CONTROL_TEMP", control_dir) # Put it back just in case

    # C. apkg-version
    with open("apkg-version", "w") as f:
        f.write("2.0\n")

    # 5. Create Final APK (Zip of the 3 components)
    print(f"Zipping final package {APK_NAME}...")
    with zipfile.ZipFile(APK_NAME, 'w', zipfile.ZIP_DEFLATED) as apk:
        apk.write("apkg-version")
        apk.write("control.tar.gz")
        apk.write("data.tar.gz")

    # Cleanup
    os.remove("apkg-version")
    os.remove("control.tar.gz")
    os.remove("data.tar.gz")
    if os.path.exists("icon.png"): os.remove("icon.png")
    shutil.rmtree(build_root)

    print("Success! Package created compatible with ADM 2.0+ structure.")

if __name__ == "__main__":
    build_apkg()