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