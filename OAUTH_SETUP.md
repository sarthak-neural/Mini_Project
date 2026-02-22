# OAuth Social Authentication Setup Guide

Social authentication has been enabled for Google, Microsoft, and Apple sign-in. To fully configure these providers, follow the steps below:

## 🔐 Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google+ API
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
5. Configure OAuth consent screen
6. Add authorized redirect URI: `http://localhost:5000/auth/callback/google`
7. Copy the **Client ID** and replace `YOUR_GOOGLE_CLIENT_ID` in `app.py`
8. Add **Client Secret** to environment variables

**Required Scopes:**
- `openid`
- `email`
- `profile`

## 🪟 Microsoft OAuth Setup

1. Go to [Azure Portal](https://portal.azure.com/)
2. Navigate to **Azure Active Directory** → **App registrations**
3. Click **New registration**
4. Add redirect URI: `http://localhost:5000/auth/callback/microsoft`
5. Go to **Certificates & secrets** and create a client secret
6. Copy the **Application (client) ID** and replace `YOUR_MICROSOFT_CLIENT_ID` in `app.py`
7. Store client secret securely

**Required Permissions:**
- `openid`
- `email`
- `profile`

## 🍎 Apple Sign In Setup

1. Go to [Apple Developer Portal](https://developer.apple.com/)
2. Navigate to **Certificates, Identifiers & Profiles**
3. Create a new **Services ID**
4. Enable **Sign in with Apple**
5. Configure return URLs: `http://localhost:5000/auth/callback/apple`
6. Create a **Key** for Sign in with Apple
7. Download the key and note the Key ID
8. Copy the **Service ID** and replace `YOUR_APPLE_CLIENT_ID` in `app.py`

**Required Scopes:**
- `email`
- `name`

## 📝 Environment Configuration

Create a `.env` file in the project root:

```env
# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here

# Microsoft OAuth
MICROSOFT_CLIENT_ID=your_microsoft_client_id_here
MICROSOFT_CLIENT_SECRET=your_microsoft_client_secret_here

# Apple OAuth
APPLE_CLIENT_ID=your_apple_service_id_here
APPLE_TEAM_ID=your_team_id_here
APPLE_KEY_ID=your_key_id_here
APPLE_PRIVATE_KEY_PATH=path/to/AuthKey_XXXXX.p8

# Flask Secret
SECRET_KEY=your_secret_key_for_production
```

## 🔧 Production Configuration

For production deployment:

1. Update redirect URIs to use your production domain
2. Use environment variables instead of hardcoded values
3. Implement proper OAuth token exchange
4. Store user data in a database (not in-memory)
5. Add proper error handling and logging
6. Implement token refresh logic
7. Add HTTPS requirement

## 📦 Required Packages

Install additional OAuth libraries:

```bash
pip install python-dotenv requests oauthlib
```

## 🚀 Current Implementation Status

✅ **Enabled:**
- OAuth flow routing (`/auth/<provider>`)
- Callback handling (`/auth/callback/<provider>`)
- Session management for social users
- UI integration (buttons work)

⚠️ **To Configure:**
- Replace placeholder Client IDs with real credentials
- Add environment variable loading
- Implement full OAuth token exchange
- Add database storage for users

## 🧪 Testing

For testing without real OAuth credentials, the system will:
- Create demo social users automatically
- Allow you to test the flow with mock data
- Store users temporarily in memory

**Test Users Created:**
- `social.user@google.com` (Google login)
- `social.user@microsoft.com` (Microsoft login)
- `social.user@apple.com` (Apple login)

## 📚 Additional Resources

- [Google OAuth Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Microsoft Identity Platform](https://docs.microsoft.com/en-us/azure/active-directory/develop/)
- [Apple Sign In Documentation](https://developer.apple.com/sign-in-with-apple/)
