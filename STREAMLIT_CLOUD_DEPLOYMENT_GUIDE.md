# Streamlit Cloud Deployment Guide

**App:** Cross-RAG Query Interface v3.0.0 (Supabase + GraphRAG)
**Created:** November 23, 2025
**Status:** Ready for deployment

---

## Prerequisites

1. **GitHub Repository:**
   - Code must be pushed to a GitHub repository
   - Repository can be private or public

2. **Streamlit Cloud Account:**
   - Sign up at https://streamlit.io/cloud
   - Connect your GitHub account

3. **API Keys Ready:**
   - Supabase URL and Service Key
   - Anthropic API Key
   - GraphRAG API Key (if using)

---

## Step 1: Prepare Repository

### Files Required (Already Created ✅)

```
3-RAG-Systems/
├── cross_rag_query_app.py           # Main Streamlit app
├── supabase_query.py                # Supabase query module (NEW)
├── cross_rag_orchestrator_FIXED.py  # GraphRAG queries
├── requirements.txt                 # Python dependencies
└── .streamlit/
    └── secrets.toml.example         # Secrets template
```

### Verify .gitignore

Ensure `.gitignore` includes:
```
.env
.streamlit/secrets.toml
__pycache__/
*.pyc
```

### Commit and Push

```bash
cd C:\Projects\Legal\3-RAG-Systems

git add cross_rag_query_app.py
git add supabase_query.py
git add requirements.txt
git add .streamlit/secrets.toml.example
git add STREAMLIT_CLOUD_DEPLOYMENT_GUIDE.md

git commit -m "Migrate from Gemini RAG to Supabase - v3.0.0

- Replace Gemini (48hr expiration) with Supabase (permanent storage)
- Update query functions to use Supabase vector search
- Create supabase_query.py module for database queries
- Add requirements.txt with Supabase dependencies
- Test locally: App runs successfully at localhost:8502
- Ready for Streamlit Cloud deployment

Database Stats:
- 288 court documents indexed
- 7,074 searchable chunks
- 3.06 MB permanent storage
- Semantic search with 384-dim embeddings"

git push origin main
```

---

## Step 2: Deploy to Streamlit Cloud

### 2.1 Create New App

1. Go to https://share.streamlit.io/
2. Click **"New app"**
3. Select your repository
4. Configure deployment:
   - **Repository:** Your GitHub repo (e.g., `bencoote/legal-case-prep`)
   - **Branch:** `main`
   - **Main file path:** `3-RAG-Systems/cross_rag_query_app.py`
   - **App URL:** Choose a custom URL (e.g., `court-rag-query`)

### 2.2 Configure Secrets

1. Click **"Advanced settings"**
2. Click **"Secrets"**
3. Paste the following (with your actual values):

```toml
# Supabase Configuration
SUPABASE_URL = "https://dstgclyqxacrmzmmrohy.supabase.co"
SUPABASE_SERVICE_KEY = "your-actual-service-key-here"

# Anthropic API
ANTHROPIC_API_KEY = "sk-ant-your-actual-key-here"

# GraphRAG API (optional - only if using GraphRAG queries)
GRAPHRAG_API_KEY = "your-graphrag-key-here"
```

4. Click **"Save"**

### 2.3 Deploy

1. Click **"Deploy!"**
2. Wait for deployment (usually 2-5 minutes)
3. Watch build logs for any errors

---

## Step 3: Verify Deployment

### 3.1 Check App Status

Once deployed, verify:
- ✅ App loads without errors
- ✅ Supabase connection shows "✅ Connected" in API status
- ✅ Anthropic API shows "✅ Connected"
- ✅ Query interface displays correctly

### 3.2 Test Functionality

Run a test query:
1. Enter query: "medical cannabis prescription evidence"
2. Select "Court Documents Only" mode
3. Click "Run Query"
4. Verify results display from Supabase (should show chunks from indexed documents)

### 3.3 Expected Output

```
Court Documents (Supabase): ✅ SUCCESS

Chunks Found: 15
Total in Index: 288

Search Results for: medical cannabis prescription evidence

Found 15 relevant passages from 5 documents
---
1. Medical_Cannabis_Evidence_2023.pdf
   Type: Expert Report | Relevance: 87.3%
   ...
```

---

## Step 4: Update Deployment (Future Changes)

### Automatic Deployment

Streamlit Cloud auto-deploys when you push to GitHub:
```bash
git add [files]
git commit -m "Update: [description]"
git push origin main
```

App will automatically rebuild in 2-5 minutes.

### Manual Reboot

If needed, reboot from Streamlit Cloud dashboard:
1. Go to https://share.streamlit.io/
2. Find your app
3. Click **"☰"** → **"Reboot app"**

---

## Step 5: Manage Secrets

### Update API Keys

If you need to update secrets:
1. Go to https://share.streamlit.io/
2. Select your app
3. Click **"Settings"** → **"Secrets"**
4. Update values
5. Click **"Save"**
6. App will automatically restart

### Security Best Practices

- ✅ Use Service Role key for Supabase (has full access)
- ✅ Never commit secrets to GitHub
- ✅ Rotate API keys periodically
- ✅ Use Row-Level Security (RLS) in Supabase
- ✅ Monitor API usage limits

---

## Troubleshooting

### Issue: ModuleNotFoundError

**Problem:** Missing dependency in requirements.txt

**Solution:**
1. Add missing module to `requirements.txt`
2. Commit and push
3. Wait for automatic rebuild

### Issue: Supabase Connection Failed

**Problem:** Invalid credentials or URL

**Solution:**
1. Verify `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` in secrets
2. Check Supabase project status
3. Verify service role key has correct permissions

### Issue: App Crashes on Startup

**Problem:** Import errors or missing files

**Solution:**
1. Check build logs in Streamlit Cloud dashboard
2. Verify all required files are in repository
3. Ensure `cross_rag_orchestrator_FIXED.py` is present (GraphRAG dependency)

### Issue: Slow Query Performance

**Problem:** Cold start or large result sets

**Solution:**
1. Reduce `match_count` slider (default 20)
2. Increase `match_threshold` (default 0.3)
3. Use caching (`@st.cache_data` already implemented)

---

## Monitoring

### Check Logs

View real-time logs:
1. Go to https://share.streamlit.io/
2. Select your app
3. Click **"Manage app"** → **"Logs"**

### Usage Metrics

Monitor app usage:
1. Streamlit Cloud dashboard shows:
   - Active users
   - Request counts
   - Error rates
2. Supabase dashboard shows:
   - Query counts
   - Database size
   - API usage

---

## Cost Considerations

**Streamlit Cloud (Free Tier):**
- ✅ 1 private app
- ✅ Unlimited public apps
- ✅ 1 GB resources
- ✅ Community support

**Supabase (Free Tier):**
- ✅ 500 MB database
- ✅ 1 GB file storage
- ✅ 50 MB database backup
- ✅ 2 GB bandwidth

**Current Usage:**
- Database: 3.06 MB (0.6% of free tier)
- Plenty of headroom for growth

---

## Migration Summary

**What Changed:**

| Feature | Before (Gemini) | After (Supabase) |
|---------|----------------|------------------|
| Storage | 48-hour expiration | **Permanent** ✅ |
| Files | 1,452 files | 288 court documents ✅ |
| Search | Semantic only | Semantic + Full-text + Hybrid ✅ |
| Speed | Fast | **Very fast** (indexed) ✅ |
| Reliability | Files expire | **Always available** ✅ |
| Audit Trail | None | **Full query logging** ✅ |

**Performance Improvements:**
- ✅ No re-indexing every 48 hours
- ✅ Faster query response times
- ✅ More reliable search results
- ✅ Legal audit trail for court compliance

---

## Next Steps After Deployment

1. **Test thoroughly** with various queries
2. **Share URL** with legal team for feedback
3. **Monitor performance** over first week
4. **Iterate** based on usage patterns
5. **Add features** as needed (e.g., export to PDF, email results)

---

## Support

**Streamlit Cloud Issues:**
- Documentation: https://docs.streamlit.io/streamlit-cloud
- Community: https://discuss.streamlit.io/

**Supabase Issues:**
- Documentation: https://supabase.com/docs
- Community: https://github.com/supabase/supabase/discussions

**App-Specific Issues:**
- Check logs in Streamlit Cloud dashboard
- Review build output for errors
- Verify secrets configuration

---

**Deployment Prepared By:** Claude Code
**Date:** November 23, 2025
**App Version:** v3.0.0 (Supabase + GraphRAG)
**Status:** ✅ Ready for deployment

