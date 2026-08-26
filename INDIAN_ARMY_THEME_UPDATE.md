# Indian Defense-Inspired Frontend Update

This version keeps the FraudShield backend, XGBoost model, authentication, Red Team, Blue Team and GenAI logic unchanged, while replacing the visual presentation with a premium Indian defense-inspired interface.

## Added
- Cinematic animated opening sequence with converging gold rings, scan line and defense emblem motif.
- AI-generated high-resolution defense-inspired hero, authentication and dashboard artwork.
- Saffron/gold/green visual system, dark command-center panels and responsive mobile treatment.
- Defense-inspired branding across landing, login, register and authenticated workspace.
- Production API fallback to the Render backend.
- 90-second Axios timeout for Render free-tier cold starts.
- Open Flask-CORS for the demo so Vercel production and preview domains can reach the backend.

## Deployment
Frontend: Vercel
Backend: https://mastercard-ai-defense-backends.onrender.com

Set `VITE_API_URL=https://mastercard-ai-defense-backends.onrender.com` in Vercel Environment Variables.
Set `JWT_SECRET_KEY` in Render Environment Variables.
