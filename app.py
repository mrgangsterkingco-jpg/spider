from flask import Flask, render_template, request, send_file
import yt_dlp
import os
import time
import glob
import re

app = Flask(__name__)

# --- Configuration ---
DOWNLOAD_FOLDER = 'downloads'
# Create download folder if it doesn't exist
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def cleanup_server():
    """
    Deletes files older than 10 minutes to keep the Render server clean.
    Free tier has limited disk space.
    """
    current_time = time.time()
    try:
        for f in os.listdir(DOWNLOAD_FOLDER):
            file_path = os.path.join(DOWNLOAD_FOLDER, f)
            # Delete if file is older than 600 seconds (10 mins)
            if os.stat(file_path).st_mtime < current_time - 600:
                os.remove(file_path)
    except Exception as e:
        print(f"Cleanup Error: {e}")

def sanitize_filename(name):
    """Removes special characters to avoid file path errors."""
    return re.sub(r'[\\/*?:"<>|]', "", name)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download_video():
    # 1. Clean up old files to free space
    cleanup_server()

    # 2. Get URL from form
    url = request.form.get('url')
    if not url:
        return render_template('index.html', error="Please provide a valid URL.")

    # 3. Generate a unique timestamp for this download
    timestamp = int(time.time())
    
    # 4. Configure yt-dlp
    ydl_opts = {
        # Download best video and best audio, then merge them
        'format': 'bestvideo+bestaudio/best',
        # Save path: downloads/Title_Timestamp.ext
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, f'%(title)s_{timestamp}.%(ext)s'),
        'merge_output_format': 'mp4', # Force MP4 container
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        # Geo-bypass and User-Agent spoofing to avoid blocking
        'geo_bypass': True,
        'nocheckcertificate': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info first
            info = ydl.extract_info(url, download=True)
            
            # Prepare the expected filename
            filename = ydl.prepare_filename(info)
            
            # Fix extension issues (yt-dlp might switch .webm to .mp4 after merge)
            base_name = os.path.splitext(filename)[0]
            final_file = f"{base_name}.mp4"

            # Double check if the specific merged file exists
            if not os.path.exists(final_file):
                # Fallback: Search for any file with this timestamp
                search_pattern = os.path.join(DOWNLOAD_FOLDER, f"*{timestamp}.mp4")
                found_files = glob.glob(search_pattern)
                if found_files:
                    final_file = found_files[0]
                else:
                    # If conversion failed, try sending the original download
                    final_file = filename

            # Send the file to the user
            return send_file(final_file, as_attachment=True)

    except Exception as e:
        error_message = str(e)
        print(f"Download Error: {error_message}")
        return render_template('index.html', error="Error: Could not download video. It might be private or too long.")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
