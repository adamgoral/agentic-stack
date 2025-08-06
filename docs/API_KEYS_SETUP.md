# API Keys Setup Guide

## Overview
The Agentic Stack requires API keys to enable AI processing capabilities. Without these keys, the system architecture functions correctly but cannot perform actual AI tasks.

## Required API Keys

### 1. OpenAI API Key
Required for the PydanticAI agents to function.

**How to obtain:**
1. Go to https://platform.openai.com/api-keys
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-`)

### 2. Anthropic API Key (Optional)
Can be used as an alternative to OpenAI for agent processing.

**How to obtain:**
1. Go to https://console.anthropic.com/
2. Sign in or create an account
3. Navigate to API keys section
4. Create and copy your key

## Configuration Steps

### Step 1: Copy the Environment Template
```bash
cp .env.example .env
```

### Step 2: Edit the .env File
Open `.env` in your editor and add your keys:

```env
# AI Provider API Keys
OPENAI_API_KEY=sk-your-actual-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-actual-anthropic-key-here

# Optional: Configure AI Model
AI_MODEL=gpt-4o-mini  # or gpt-4, claude-3-sonnet, etc.
```

### Step 3: Restart the Services
After adding the API keys, restart the Docker services:

```bash
# Stop current services
docker-compose down

# Rebuild and start with new environment
docker-compose up --build -d
```

### Step 4: Verify Configuration
Test that the API keys are working:

```bash
# Run the end-to-end test
python backend/test_e2e_simple.py
```

You should see all tests passing with actual AI responses instead of error messages about missing API keys.

## Security Best Practices

1. **Never commit API keys to Git**
   - The `.env` file is already in `.gitignore`
   - Double-check before committing

2. **Use environment-specific keys**
   - Development keys for local testing
   - Production keys with proper rate limits

3. **Rotate keys regularly**
   - Update keys every 90 days
   - Immediately rotate if exposed

4. **Set usage limits**
   - Configure spending limits in OpenAI/Anthropic dashboards
   - Monitor usage regularly

## Troubleshooting

### "Missing API key" errors
- Ensure the `.env` file exists and contains valid keys
- Check that Docker services were restarted after adding keys
- Verify key format (should start with `sk-`)

### "Invalid API key" errors
- Double-check the key is copied correctly (no extra spaces)
- Ensure the key is active in your provider's dashboard
- Check if the key has proper permissions

### "Rate limit exceeded" errors
- Upgrade your API plan if needed
- Implement retry logic with exponential backoff
- Consider using multiple keys for load distribution

## Cost Optimization

### OpenAI Pricing (as of 2024)
- GPT-4: ~$0.03 per 1K tokens
- GPT-4-turbo: ~$0.01 per 1K tokens
- GPT-3.5-turbo: ~$0.002 per 1K tokens

### Recommendations
1. Use `gpt-4o-mini` for development/testing
2. Upgrade to `gpt-4` for production when needed
3. Implement caching to reduce redundant API calls
4. Monitor token usage in the provider dashboards

## Next Steps

After configuring API keys:

1. **Test the full system:**
   ```bash
   python backend/test_e2e_comprehensive.py
   ```

2. **Access the frontend:**
   - Open http://localhost:3000/chat
   - Try complex queries that use multiple agents

3. **Monitor the logs:**
   ```bash
   docker-compose logs -f backend-orchestrator
   ```

## Support

For issues with API keys:
- OpenAI Support: https://help.openai.com/
- Anthropic Support: https://support.anthropic.com/
- Project Issues: https://github.com/your-repo/agentic-stack/issues