# ✋ AirDraw Studio

> **Draw in the air. Create without limits.**

AirDraw Studio transforms your hand into the most natural drawing tool ever made. No stylus, no mouse, no touch — just raise your hand in front of any camera and start creating.

[![Live App](https://img.shields.io/badge/Live%20App-Open%20Studio-8b5cf6?style=for-the-badge)](https://newgesture.vercel.app)
[![License](https://img.shields.io/badge/License-MIT-34d399?style=for-the-badge)](LICENSE)

---

## 🎨 What You Can Do

- **Draw freely** — point your index finger and paint across the canvas in real time
- **Erase instantly** — open your palm to wipe strokes clean
- **Move artwork** — pinch any stroke and drag it anywhere on the canvas
- **Switch colors** — flash a peace sign to cycle through the full color palette
- **Undo anytime** — a quick "call me" gesture rolls back your last stroke
- **Pause drawing** — close your fist to enter idle mode without losing your work
- **Save & revisit** — store sessions to the cloud and export as PNG from your History gallery

---

## ✋ Gesture Reference

| Gesture | Action |
|---|---|
| ☝️ Index finger only | Draw on canvas |
| 🤚 Open palm | Erase nearby strokes |
| 🤏 Pinch | Grab and move a stroke |
| ✌️ Peace sign | Cycle through colors |
| 🤙 "Call me" | Undo last stroke |
| ✊ Fist | Pause / idle mode |

---

## 🚀 Getting Started

**All you need is a browser and a camera.**

1. Open the [Live Studio](https://newgesture.vercel.app/app.html) in Chrome or Edge
2. Click **Allow** when prompted for camera access
3. Hold your hand up in front of the camera — the tracker activates instantly
4. Start drawing

> 💡 **Best results:** good lighting, hand 30–60 cm from the camera, plain background preferred.

---

## 🖼️ Canvas & Brush Options

| Option | Choices |
|---|---|
| Brush style | Round · Square · Spray · Calligraphy |
| Canvas theme | Dark · Light · Grid · Chalkboard |
| Brush size | Adjustable in real time |
| Colors | 7 preset colors + gesture cycling |

---

## 💾 Saving Your Work

- **Download PNG** — export your current canvas as a full-resolution image
- **Save to Cloud** — store your session for later; access everything in the **History** gallery
- **Revisit anytime** — saved sessions appear with thumbnails and timestamps

---

## 🌐 Deployment

### Frontend
Hosted on **Vercel** — deploys automatically on every push to `main`.

### Backend
Hosted on **Render** — always-on API handling session storage.

#### Self-host the backend on Render
1. Go to [render.com](https://render.com) → **New → Web Service**
2. Connect the `koyeliya2004/newgesture` repository
3. Set the following:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. After deploy, copy your backend URL and update `API_BASE` in `frontend/index.html`

---

## 🤝 Collaboration

Want to contribute, extend AirDraw, or integrate it into your own project?

- **Fork the repo** and open a pull request — all contributions are welcome
- **Feature ideas?** Open an issue with the `enhancement` label
- **Found a bug?** Report it via GitHub Issues
- **Want to build something bigger together?** Reach out directly via GitHub — always open to interesting ideas

This project is fully open source under the MIT license.

---

## 📁 Project Structure

```
newgesture/
├── frontend/
│   ├── index.html       ← Homepage & landing page
│   ├── app.html         ← Drawing studio
│   └── history.html     ← Saved sessions gallery
├── backend/
│   ├── app/
│   │   └── main.py      ← API server
│   └── requirements.txt
├── render.yaml          ← One-click Render deploy config
└── README.md
```

---

Built with ❤️ by [@koyeliya2004](https://github.com/koyeliya2004)
