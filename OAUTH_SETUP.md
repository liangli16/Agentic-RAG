# OAuth 2.0 Setup Guide

This project now uses OAuth 2.0 authentication instead of service accounts, allowing it to work with personal Gmail accounts.

## ✅ What You've Done So Far

1. ✅ Created OAuth consent screen in Google Cloud Console
2. ✅ Created OAuth 2.0 credentials (Desktop app)
3. ✅ Downloaded `oauth_credentials.json`
4. ✅ Updated Python dependencies

## 📋 Next Steps

### Step 1: Place Your OAuth Credentials

Make sure your downloaded OAuth credentials file is saved as:
```
credentials/oauth_credentials.json
```

### Step 2: Update Your .env File

Edit your `.env` file and update/add these variables:

```env
# ===========================================
# GOOGLE API CONFIGURATION (OAuth 2.0)
# ===========================================
GOOGLE_OAUTH_CREDENTIALS_PATH=credentials/oauth_credentials.json
GOOGLE_TOKEN_PATH=credentials/token.json
GOOGLE_CALENDAR_ID=primary
```

You can remove or comment out these old variables (no longer needed):
```env
# GOOGLE_SERVICE_ACCOUNT_PATH=credentials/service_account.json
# GOOGLE_CALENDAR_EMAIL=your-email@yourcompany.com
```

### Step 3: Start Your Server

```bash
uvicorn main:app --reload --port 8000
```

### Step 4: Test the OAuth Flow

Make a request that uses the Calendar or Email tools:

```bash
curl -X POST http://localhost:8000/agent \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Schedule a test meeting tomorrow at 2pm for 30 minutes"
  }'
```

**On first use:**
- A browser window will automatically open
- You'll be asked to sign in to your Google account
- Review and approve the permissions (Calendar and Gmail access)
- Click "Allow"
- The token will be saved to `credentials/token.json`

**Future requests:**
- Will use the saved token automatically
- No browser popup needed
- Token auto-refreshes when expired

## 🔒 Security Notes

- `oauth_credentials.json` - Contains your OAuth client ID/secret (gitignored)
- `token.json` - Contains your personal access token (gitignored)
- Never commit these files to git
- Users can revoke access anytime at: https://myaccount.google.com/permissions

## 🔄 Re-authorization

If you need to re-authorize (e.g., changed scopes, testing):

```bash
# Delete the token file
rm credentials/token.json

# Restart your server - browser will open again on next API call
uvicorn main:app --reload --port 8000
```

## ❓ Troubleshooting

### "OAuth credentials not found"
- Make sure `credentials/oauth_credentials.json` exists
- Check the file path in your `.env` matches

### "Access blocked: This app's request is invalid"
- Make sure you added yourself as a test user in OAuth consent screen
- Go to Google Cloud Console > APIs & Services > OAuth consent screen > Test users

### Browser doesn't open automatically
- Check the console output for the authorization URL
- Copy and paste the URL into your browser manually
- Check firewall settings

### "Insufficient Permission" error
- Make sure you approved both Calendar and Gmail scopes
- Delete `token.json` and re-authorize

## 🎯 What Changed?

**Before (Service Account):**
- Required Google Workspace account
- Required domain-wide delegation setup
- Required admin access
- Service account JSON with private key

**After (OAuth 2.0):**
- ✅ Works with personal Gmail accounts
- ✅ No admin access needed
- ✅ User approves permissions directly
- ✅ More secure (user-controlled access)

## 📚 Additional Resources

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Gmail API Python Quickstart](https://developers.google.com/gmail/api/quickstart/python)
- [Calendar API Python Quickstart](https://developers.google.com/calendar/api/quickstart/python)
