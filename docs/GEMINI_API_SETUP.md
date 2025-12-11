# How to Get Your Google Gemini API Key (JIO Free Subscription)

Since you have a free Gemini Pro subscription backed by JIO for 18 months, here's how to get your API key:

## Step 1: Access Google AI Studio

1. Go to **Google AI Studio**: https://makersuite.google.com/app/apikey
2. Sign in with your Google account (the one linked to your JIO subscription)

## Step 2: Create an API Key

1. Click on **"Get API Key"** or **"Create API Key"**
2. Select your Google Cloud project (or create a new one)
3. Click **"Create API key in new project"** if you don't have one
4. Copy your API key - it will look like: `AIzaSy...`

## Step 3: Verify Your Subscription

1. Check that you have access to **Gemini Pro** (free model)
2. Confirm your JIO free tier is active
3. Note the rate limits for the free tier:
   - **60 requests per minute**
   - **1,500 requests per day**
   - FREE for 18 months!

## Step 4: Configure the Platform

Once you have your API key, add it to your environment files:

### In `.env` file:
```bash
GEMINI_API_KEY=AIzaSy...your-actual-key-here
GEMINI_MODEL=gemini-pro
```

### In `backend/.env` file:
```bash
GEMINI_API_KEY=AIzaSy...your-actual-key-here
GEMINI_MODEL=gemini-pro
```

## Available Models

You have access to these models with your free subscription:

1. **gemini-pro** (Recommended)
   - General-purpose text generation
   - Perfect for API documentation
   - FREE with JIO subscription

2. **gemini-1.5-pro** (If available)
   - More advanced capabilities
   - Larger context window
   - Check availability on your account

## Rate Limits to Know

The free tier has these limits:
- **60 RPM** (requests per minute)
- **1,500 RPD** (requests per day)
- **1 million TPM** (tokens per minute)

Our platform automatically handles rate limiting with:
- Request caching
- Retry logic with exponential backoff
- Token usage tracking

## Testing Your API Key

After setting up, you can test it works:

```bash
# In the backend directory
cd backend
python -c "
import google.generativeai as genai
genai.configure(api_key='YOUR_API_KEY_HERE')
model = genai.GenerativeModel('gemini-pro')
response = model.generate_content('Say hello!')
print(response.text)
"
```

## Important Notes

✅ **FREE** for 18 months with JIO subscription!
✅ No credit card required for free tier
✅ Generous rate limits for development
⚠️ Keep your API key secret (never commit to Git)
⚠️ Monitor your usage in Google AI Studio dashboard

## Troubleshooting

**Issue**: "API key not valid" error
- **Solution**: Make sure you copied the full key including `AIzaSy` prefix

**Issue**: Rate limit exceeded
- **Solution**: Our platform automatically caches and retries. This is expected during heavy usage.

**Issue**: Model not found
- **Solution**: Ensure you're using `gemini-pro` for the free tier

## Support Links

- **Google AI Studio**: https://makersuite.google.com/
- **Gemini API Docs**: https://ai.google.dev/docs
- **API Key Management**: https://makersuite.google.com/app/apikey
- **Pricing & Quotas**: https://ai.google.dev/pricing

---

Once you have your key, you're all set! The platform will use Gemini Pro for AI-powered documentation generation at zero cost for 18 months! 🎉
