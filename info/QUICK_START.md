# Site_proj - Quick Start Guide

## 🚀 Performance Optimizations Quick Reference

### CSS/JS Minification

#### For Development (Auto-watch for changes)
```bash
python utils/asset_manager.py --watch
```

#### For Production (One-time minification)
```bash
python utils/asset_manager.py
```

#### Clean and Rebuild All Assets
```bash
python utils/asset_manager.py --clean
```

### File Editing Workflow

1. **Edit original files**: `static/css/style.css`, `static/js/app.js`, etc.
2. **Run minification**: `python utils/asset_manager.py`
3. **Application automatically serves** the minified versions

**DO NOT manually edit .min.css or .min.js files** - they are auto-generated!

### Application Startup

```bash
python app.py
```

The application automatically:
- ✅ Serves minified CSS/JS when available (falls back to originals)
- ✅ Uses local caching for improved performance
- ✅ Sends emails asynchronously (non-blocking UI)
- ✅ Processes background tasks

### File Structure

```
Site_proj/
├── app.py                          # Main application
├── utils/                          # 🆕 Organized utilities
│   ├── cache_manager.py           # Caching functionality
│   ├── async_manager.py           # Async operations
│   └── asset_manager.py           # CSS/JS minification
├── deprecated/                     # Old files (for reference)
├── static/
│   ├── css/
│   │   ├── style.css              # ✏️ Edit these files
│   │   └── style.min.css          # 🤖 Auto-generated
│   └── js/
│       ├── app.js                 # ✏️ Edit these files
│       └── app.min.js             # 🤖 Auto-generated
└── PERFORMANCE_OPTIMIZATION.md    # 📖 Detailed documentation
```

### Performance Benefits

- **36.1% smaller** CSS/JS files
- **~50ms faster** API responses (caching)
- **Non-blocking** email sending
- **Improved** user experience

### Monitoring

Check application logs for:
- Cache hit/miss statistics
- Async email queue status
- Asset serving information

---

📖 **For detailed documentation**: See `PERFORMANCE_OPTIMIZATION.md`