# 🎥 Automazione YouTube → TikTok Reels con n8n

Questo progetto automatizza la creazione di Reels TikTok partendo da un link YouTube.

## 📦 Cosa fa?

1. Riceve un link YouTube tramite Webhook
2. Scarica il video
3. Analizza le scene più interessanti
4. Genera un Reel in formato TikTok (9:16, max 60s)
5. Salva il risultato

---

## 🔧 Requisiti

- Docker e Docker Compose installati
- Accesso a Internet per scaricare dipendenze

---

## 🚀 Avvio

### 1. Clona il repository
```bash
git clone https://github.com/and734/n8n-youtube-tik-reel.git

### 2. Avvia il servizio
docker-compose up -d
### 3. Accedi a n8n
Vai su: http://localhost:5678
Importa il workflow: workflows/youtube-to-tiktok.json
### 4. Webhook
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID"
}


# n8n YouTube to TikTok Reel Automation (ENGLISH VERSION)

This project automates the creation of TikTok Reels from YouTube videos using n8n. It takes a YouTube URL, downloads the video, analyzes scenes, generates a reel, and saves the final result to a Docker volume.

## How it Works

1.  Receives a YouTube URL via webhook.
2.  Downloads the video using `yt-dlp`.
3.  Calls `analyze_scenes.py` to get scene timestamps.
4.  Calls `process_video.py` to generate the reel.
5.  The final reel is saved to a Docker volume.

## Prerequisites

*   Docker and Docker Compose installed.
*   Internet access to download dependencies.

## Setup

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/and734/n8n-youtube-tik-reel.git
    cd n8n-youtube-tik-reel
    ```

2.  **Start the service:**

    ```bash
    docker-compose up -d
    ```

3.  **Access n8n:**

    Open your browser and go to: `http://localhost:5678`

4.  **Import the workflow:**

    Import the workflow file located at `workflows/youtube-to-tiktok.json`.  You can do this through the n8n UI.

## Usage

1.  **Configure the Webhook:**

    The n8n workflow is triggered by a webhook.  You'll need to configure the webhook URL in n8n.

2.  **Send a YouTube URL:**

    Send a JSON payload to the webhook with the YouTube URL.  For example:

    ```json
    {
      "url": "https://www.youtube.com/watch?v=VIDEO_ID"
    }
    ```

## Output

The final TikTok Reel will be saved in the Docker volume named `output_reels`, which is mounted to `/app/output` inside the container. You can retrieve the reel from the host machine by accessing the Docker volume's location.


## MIT License

Copyright (c) 2025 Andrea Lamberti

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
