#!/bin/bash

# 🚀 Finance AI Bot - Setup for Production Deploy
echo "🚀 FINANCE AI BOT - PRODUCTION SETUP"
echo "===================================="

# 1. Verifica Git
if ! command -v git &> /dev/null; then
    echo "❌ Git non installato. Installa Git prima di continuare."
    exit 1
fi

# 2. Inizializza repository se necessario
if [ ! -d ".git" ]; then
    echo "📁 Inizializzando repository Git..."
    git init
    echo "✅ Repository Git inizializzato"
fi

# 3. Verifica file essenziali
echo "🔍 Verificando file per deployment..."

required_files=("financebot_final.py" "requirements.txt" "Procfile" ".gitignore")
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file mancante!"
        exit 1
    fi
done

# 4. Verifica variabili ambiente
if [ ! -f ".env" ]; then
    echo "❌ File .env mancante!"
    echo "💡 Crea il file .env con:"
    echo "   TELEGRAM_TOKEN=il_tuo_token"
    echo "   OPENAI_API_KEY=la_tua_chiave"
    exit 1
fi
echo "✅ File .env presente"

# 5. Crea backup di sicurezza
echo "💾 Creando backup..."
mkdir -p deploy_backup
cp -r *.py *.csv *.json deploy_backup/ 2>/dev/null
echo "✅ Backup creato in deploy_backup/"

# 6. Prepara commit
echo "📝 Preparando commit per deploy..."
git add .
git add .gitignore

# Escludi .env dal commit per sicurezza
git reset .env 2>/dev/null

echo "✅ File preparati per commit"
echo ""
echo "🎯 PROSSIMI PASSI:"
echo "=================="
echo "1. 📝 git commit -m '🚀 Ready for production deploy'"
echo "2. 🌐 Crea repository su GitHub"
echo "3. 🔗 git remote add origin https://github.com/USERNAME/REPO.git"  
echo "4. 📤 git push -u origin main"
echo "5. 🚀 Deploy su Railway/Render/Heroku"
echo ""
echo "📚 Leggi PRODUCTION_DEPLOY.md per istruzioni complete"
echo ""
echo "⚠️  RICORDA: Configura le variabili ambiente sul servizio hosting!"
echo "   - TELEGRAM_TOKEN"
echo "   - OPENAI_API_KEY"