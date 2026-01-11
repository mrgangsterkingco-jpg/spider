from flask import Flask, render_template, request, send_file
import yt_dlp
import os
import time
import glob
import random

app = Flask(__name__)

DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def cleanup_server():
    try:
        current_time = time.time()
        for f in os.listdir(DOWNLOAD_FOLDER):
            file_path = os.path.join(DOWNLOAD_FOLDER, f)
            if os.stat(file_path).st_mtime < current_time - 600:
                os.remove(file_path)
    except Exception:
        pass

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download_video():
    cleanup_server()
    
    url = request.form.get('url')
    if not url:
        return render_template('index.html', error="Please enter a valid URL.")

    timestamp = int(time.time())
    
    # ইউজার এজেন্ট লিস্ট (YouTube কে বোকা বানানোর জন্য)
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
    ]

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, f'%(title)s_{timestamp}.%(ext)s'),
        'merge_output_format': 'mp4',
        
        # --- এন্টি-ব্লক সেটিংস ---
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'geo_bypass': True,
        # সোর্স আইপি লুকানোর চেষ্টা
        'source_address': '0.0.0.0', 
        # র‍্যান্ডম ইউজার এজেন্ট
        'user_agent': random.choice(user_agents),
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # এক্সটেনশন ফিক্স করা
            base = os.path.splitext(filename)[0]
            final_file = f"{base}.mp4"

            if not os.path.exists(final_file):
                # যদি ফাইল না পাওয়া যায়, তবে যেটা ডাউনলোড হয়েছে সেটাই খোঁজা
                found = glob.glob(os.path.join(DOWNLOAD_FOLDER, f"*{timestamp}*"))
                if found:
                    final_file = found[0]
                else:
                    raise Exception("File conversion failed.")

            return send_file(final_file, as_attachment=True)

    except Exception as e:
        error_msg = str(e)
        print(f"Server Error Log: {error_msg}")
        
        # এরর মেসেজ ক্লিন করে দেখানো
        if "Sign in" in error_msg:
            clean_error = "YouTube is blocking the server IP (Bot protection). Try a different video."
        elif "too long" in error_msg:
            clean_error = "Video is too long for the free server memory."
        else:
            # আসল কারণটি স্ক্রিনে দেখানো হবে যাতে আপনি বুঝতে পারেন
            clean_error = f"Error: {error_msg[0:100]}..." 

        return render_template('index.html', error=clean_error)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
