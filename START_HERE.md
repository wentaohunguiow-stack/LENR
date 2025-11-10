# 🚀 LENR Collection System - START HERE

## Which Setup Should You Use?

### ✨ Option 1: Direct n8n (RECOMMENDED for n8n users)

**Best if you:** Use n8n and want everything inside n8n

**What you get:**
- ✅ No external services needed
- ✅ No Docker, Python, or API required
- ✅ Works in n8n cloud or self-hosted
- ✅ 100% free
- ✅ Setup in 5 minutes

**📖 Guide:** [N8N_DIRECT_SETUP.md](N8N_DIRECT_SETUP.md)

**🎯 Quick Start:**
```
1. Open n8n
2. Import: n8n-workflows/lenr-scraper-minimal.json
3. Click "Execute Workflow"
4. Done! See papers in output
```

---

### 🔧 Option 2: REST API (For developers/integrations)

**Best if you:** Need an API for custom integrations

**What you get:**
- ✅ REST API with Swagger docs
- ✅ Docker deployment
- ✅ Can integrate with n8n via HTTP Request
- ✅ Background job processing

**📖 Guide:** [README_N8N.md](README_N8N.md)

**🎯 Quick Start:**
```bash
docker-compose up -d
curl http://localhost:8000/health
```

---

### 🐍 Option 3: Python Package (For Python developers)

**Best if you:** Want to use Python directly

**What you get:**
- ✅ Full Python library
- ✅ Command-line tools
- ✅ Jupyter notebooks
- ✅ Customizable code

**📖 Guide:** [README.md](README.md) or [QUICKSTART.md](QUICKSTART.md)

**🎯 Quick Start:**
```bash
pip install -r requirements.txt
python run_collection.py
```

---

## 🎯 Comparison

| Feature | Direct n8n | REST API | Python Package |
|---------|-----------|----------|----------------|
| **No coding** | ✅ | ✅ | ❌ |
| **No Docker** | ✅ | ❌ | ✅ |
| **n8n ready** | ✅✅✅ | ✅✅ | ❌ |
| **Free** | ✅ | ✅ | ✅ |
| **Setup time** | 5 min | 10 min | 15 min |
| **Customizable** | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 🏃 I Just Want Papers NOW!

### Fastest Path (2 minutes):

1. **Open n8n**

2. **Create new workflow**

3. **Add Manual Trigger node**

4. **Add HTTP Request node:**
   - URL: `https://lenr-canr.org/wordpress/?page_id=3009`
   - Method: GET

5. **Add Code node:**
   ```javascript
   const html = $input.item.json.data;
   const rowRegex = /<tr[^>]*>(.*?)<\/tr>/gis;
   const papers = [];
   let i = 0;

   let match;
   while ((match = rowRegex.exec(html)) !== null && i < 10) {
     i++;
     if (i === 1) continue;

     const row = match[1];
     const cells = [];
     const cellRe = /<td[^>]*>(.*?)<\/td>/gis;
     let m;

     while ((m = cellRe.exec(row)) !== null) {
       cells.push(m[1].replace(/<[^>]*>/g, '').trim());
     }

     const urlMatch = row.match(/href=["'](.*?\.pdf)["']/i);
     let url = urlMatch ? urlMatch[1] : '';
     if (url && !url.startsWith('http')) {
       url = 'https://lenr-canr.org/' + url.replace(/^\//, '');
     }

     if (cells[5] && url) {
       papers.push({
         Title: cells[5],
         Authors: cells[4],
         URL: url
       });
     }
   }

   return papers.map(p => ({ json: p }));
   ```

6. **Click "Execute Workflow"**

7. **See papers!** 🎉

---

## 📖 Documentation Index

- **[N8N_DIRECT_SETUP.md](N8N_DIRECT_SETUP.md)** - n8n-only setup (no external services)
- **[README_N8N.md](README_N8N.md)** - REST API + Docker + n8n
- **[N8N_INTEGRATION.md](N8N_INTEGRATION.md)** - Advanced n8n integration
- **[README.md](README.md)** - Full Python package documentation
- **[QUICKSTART.md](QUICKSTART.md)** - Python quick start

---

## 🎓 Learning Path

### Beginner (Just want papers)
1. Read: N8N_DIRECT_SETUP.md
2. Import: `lenr-scraper-minimal.json`
3. Run and see results

### Intermediate (Save to database)
1. Read: N8N_DIRECT_SETUP.md (Example 2)
2. Setup Airtable account
3. Import: `lenr-to-airtable-complete.json`
4. Configure and automate

### Advanced (Custom integrations)
1. Read: README_N8N.md
2. Deploy REST API with Docker
3. Build custom workflows
4. Add AI verification

---

## ❓ FAQ

**Q: I use n8n. Which option?**
A: **Direct n8n** (Option 1) - [N8N_DIRECT_SETUP.md](N8N_DIRECT_SETUP.md)

**Q: Do I need Python?**
A: **No!** Option 1 (Direct n8n) requires zero Python

**Q: Do I need Docker?**
A: **No!** Option 1 works with just n8n

**Q: Does it cost money?**
A: **No!** Everything is free

**Q: How long to setup?**
A: **5 minutes** with Option 1

**Q: Can I save to Google Sheets?**
A: **Yes!** See N8N_DIRECT_SETUP.md Example 2

**Q: Can I save to Airtable?**
A: **Yes!** Import `lenr-to-airtable-complete.json`

**Q: Does it work in n8n cloud?**
A: **Yes!** All workflows work in cloud or self-hosted

**Q: Can I customize what data is collected?**
A: **Yes!** Edit the Code node in the workflow

**Q: How do I add more sources?**
A: Add more HTTP Request nodes for other sites

---

## 🆘 Help

**Stuck?**

1. ✅ Read: [N8N_DIRECT_SETUP.md](N8N_DIRECT_SETUP.md)
2. ✅ Import: `lenr-scraper-minimal.json`
3. ✅ Click "Execute Workflow"
4. ✅ Check n8n execution logs
5. ✅ Ask in n8n community: https://community.n8n.io

**Still stuck?**

Share:
- Which workflow you imported
- What error message you see
- Screenshot of n8n execution

---

## ✅ Recommended Path for n8n Users

```
1. Read N8N_DIRECT_SETUP.md (5 min)
   ↓
2. Import lenr-scraper-minimal.json
   ↓
3. Test workflow (see papers!)
   ↓
4. Connect Airtable/Sheets
   ↓
5. Schedule daily collection
   ↓
6. Done! 🎉
```

---

**Choose your path above and click the guide link to get started!**
