# 🤖 Finance AI Bot

**AI-Powered Telegram Bot for Personal Finance Management with OpenAI**

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template/iwy9c5)

## 🚀 **Features**

- 💸 **Smart Expense Tracking** - Natural language input with AI categorization
- 💰 **Income Management** - Track salaries, freelance, and other revenue streams
- 🤖 **OpenAI Integration** - Intelligent transaction categorization using GPT-3.5
- 📊 **Advanced Analytics** - Charts, budgets, predictions with ML
- 🔮 **AI Predictions** - Future spending forecasts and pattern analysis
- 💡 **Smart Recommendations** - Personalized financial advice
- 🌍 **24/7 Online** - Cloud-hosted, always available

## 💡 **How to Use**

1. **Start the bot:** `/start`
2. **Enable expense mode:** `/segnaspese`
3. **Add expenses:** `15.50 benzina` or `€25 supermercato`
4. **Enable income mode:** `/segnaricavi`
5. **Add income:** `1500 stipendio` or `200 freelance project`
6. **View analytics:** `/grafici` `/bilancio` `/stats`

## 🛠️ **Tech Stack**

- **Language:** Python 3.11
- **Framework:** python-telegram-bot
- **AI:** OpenAI GPT-3.5-turbo
- **Analytics:** pandas, matplotlib, seaborn
- **ML:** scikit-learn
- **Database:** CSV (local storage)
- **Hosting:** Railway.app

## 🚀 **Deploy Your Own**

### 1-Click Deploy on Railway:

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template/iwy9c5)

### Manual Deploy:

1. **Fork this repository**
2. **Create Railway account** at [railway.app](https://railway.app)
3. **Connect GitHub** and select this repo
4. **Add environment variables:**
   - `TELEGRAM_TOKEN` - Get from [@BotFather](https://t.me/botfather)
   - `OPENAI_API_KEY` - Get from [OpenAI](https://platform.openai.com)
5. **Deploy automatically!** 🚀

## 📊 **Commands**

### 💰 Transaction Management:

- `/segnaspese` - Enable expense tracking mode
- `/segnaricavi` - Enable income tracking mode
- `/modalinormale` - Return to normal mode

### 📈 Analytics:

- `/bilancio` - Income vs expenses balance
- `/grafici` - Generate charts and visualizations
- `/budget` - Check budget vs actual spending
- `/stats` - Complete statistics overview

### 🤖 AI Features:

- `/predizioni` - AI predictions for future expenses
- `/pattern` - Behavioral pattern analysis
- `/raccomandazioni` - Personalized AI recommendations

## 🔒 **Environment Variables**

```env
TELEGRAM_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key
```

## 📁 **Project Structure**

```
├── financebot_final.py     # Main bot application
├── spese_manager.py        # CSV database manager
├── analytics.py            # Charts and visualizations
├── ai_predictor.py         # ML predictions
├── requirements.txt        # Python dependencies
├── Procfile               # Railway deployment
└── config.json           # Budget and categories config
```

## 🤝 **Contributing**

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 **Acknowledgments**

- OpenAI for GPT-3.5 integration
- Telegram Bot API
- Railway for hosting
- Python community for amazing libraries

---

**⭐ Star this repo if you find it useful!**

**🤖 Try the bot:** [@SpesaAIbot](https://t.me/SpesaAIbot)  
**🚀 Deploy yours:** Click the Railway button above!
# Deploy: Sab 20 Set 2025 18:17:51 CEST
