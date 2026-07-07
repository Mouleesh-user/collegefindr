# CollegeFindr Frontend

Static frontend for CollegeFindr, an AI-powered college search assistant. The app is built with plain HTML, CSS, and JavaScript and connects to the CollegeFindr Flask backend.

## Project Structure

```text
index.html      Main page and app markup
style.css       UI styling
script.js       Frontend behavior and API calls
render.yaml     Render static-site deployment config
*.png, *.webp   UI images and logo assets
```

## Run Locally

Open `index.html` directly in a browser, or serve the folder with any static file server.

For example:

```bash
python -m http.server 5500
```

Then open:

```text
http://localhost:5500
```

When running locally, `script.js` defaults API calls to:

```text
http://127.0.0.1:5000
```

Start the backend locally before using login, signup, chat, settings, or application features.

## Backend URL

Production API base URL is configured in `index.html`:

```html
window.COLLEGEFINDR_API_BASE_URL = "https://collegefindr-backend.onrender.com";
```

Update this value if the backend Render service URL changes.

## Deploy

The root `../render.yaml` defines the Render static site.

```yaml
staticPublishPath: .
```

Push to the branch Render watches to deploy.

## Monorepo

The Flask backend lives in `../backend`.
