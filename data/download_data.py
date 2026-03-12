import os
import shutil
import gdown

# Configuration
FOLDERS = {
    "Polymarket": "1k04QXUITT8H2XgRNNBjzK0kO7plXNL5E",
    "Statsbomb": "1QpFf8qASVVtKz1B93mEx34phL1vtGcO6"
}
DATA_DIR = "data/raw"
ALLOWED_EXTENSIONS = {".parquet", ".md"}

def download_folder(folder_name, folder_id):
    """Downloads a GDrive folder and filters contents."""
    print(f"--- Processing {folder_name} ---")
    dest_path = os.path.join(DATA_DIR, folder_name)
    
    # Create temporary directory for download
    tmp_dir = f"tmp_{folder_name}"
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    os.makedirs(tmp_dir)
    
    try:
        # Download folder content
        print(f"Downloading {folder_name} from GDrive...")
        gdown.download_folder(id=folder_id, output=tmp_dir, quiet=False, remaining_ok=True)
        
        # Create destination directory
        if not os.path.exists(dest_path):
            os.makedirs(dest_path)
            
        # Move allowed files and clean up
        print(f"Organizing files for {folder_name}...")
        for root, dirs, files in os.walk(tmp_dir):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in ALLOWED_EXTENSIONS:
                    src_file = os.path.join(root, file)
                    dst_file = os.path.join(dest_path, file)
                    print(f"  Keeping: {file}")
                    shutil.move(src_file, dst_file)
                else:
                    print(f"  Skipping: {file}")
                    
    finally:
        # Clean up temporary directory
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)
    print(f"--- Finished {folder_name} ---\n")

def main():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
        
    for name, folder_id in FOLDERS.items():
        download_folder(name, folder_id)
    
    print("Data download and organization complete.")

if __name__ == "__main__":
    main()
