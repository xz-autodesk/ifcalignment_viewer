# Static Files Directory

This directory is for static assets like:
- CSS files
- JavaScript files
- Images
- Fonts

Currently, all CSS and JavaScript is embedded in the HTML template for simplicity.

If you want to separate them, create:
- `style.css` - Main stylesheet
- `app.js` - Application JavaScript
- `images/` - Image assets

Then reference them in `templates/index.html`:

```html
<link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
<script src="{{ url_for('static', filename='app.js') }}"></script>
```

