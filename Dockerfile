# Dockerfile - פשוט! תשתמש בBYPARR המוכן

# השתמש בimage המוכן של BYPARR
FROM ghcr.io/thephaseless/byparr:latest

# הגדרות לGoogle Cloud Run
ENV PORT=8191
ENV LOG_LEVEL=info
ENV HEADLESS=true

# חשוף port לCloud Run
EXPOSE 8191

# הרץ BYPARR (זה כבר מוגדר בimage המקורי)
# CMD כבר מוגדר בimage הבסיסי
