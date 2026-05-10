markdown

# 🔥 AI Quote Beast

**The most savage, fun, and useful local AI quote generator.**

Instantly generate:
- **Hot** — brutal, sarcastic hot takes that roast common beliefs
- **Boost** — raw, no-bullshit motivation
- **Flirt** — smooth, cheeky, playful one-liners
- **Stoic** — calm, grounded wisdom

All powered by your local Ollama model. No API keys. No internet. Pure fire in your terminal.

![Quote Beast Demo](https://github.com/yourusername/quotebeast/raw/main/demo.png)
*(replace with your own screenshot)*

## ✨ Features

- Four unique modes with carefully tuned prompts
- Smart history system (avoids repeating the same lines)
- Beautiful cyan terminal output (easy on the eyes)
- **Infinite mode** with smart controls:
  - Press **Enter** → next quote
  - Press **X** → instant exit
- Zero markdown garbage in output (clean text only)
- Works great with `llama3.1:8b` (or any model you prefer)
- Fully offline

## 📋 Requirements

- Python 3.8+
- [Ollama](https://ollama.com) running locally
- A model pulled (recommended: `llama3.1:8b` or `llama3.2`)

## 🚀 Installation

1. Clone the repo:
```bash
git clone https://github.com/yourusername/quotebeast.git
cd quotebeast

(Optional but recommended) Create a virtual environment:

bash

python -m venv venv
venv\Scripts\activate    # Windows
# source venv/bin/activate   # macOS/Linux

Run it:

bash

python quotebeast.py

Make sure Ollama is running and the model is pulled:bash

ollama pull llama3.1:8b

 UsageBasic commandsbash

# One hot take
python quotebeast.py -m hot

# 5 boost quotes
python quotebeast.py -m boost -n 5

# Flirt mode infinite (my personal favorite)
python quotebeast.py -m flirt --infinite

# Stoic wisdom
python quotebeast.py -m stoic

All optionsFlag
Description
Default
-m, --mode
hot, boost, flirt, or stoic
hot
-n, --number
How many quotes to generate
1
--infinite
Infinite mode (Enter = next, X = exit)
off
--model
Ollama model name
llama3.1:8b

 Pro TipsUse -m flirt --infinite when you're texting someone   
Use -m boost --infinite for a morning pump-up session  
Use -m hot when you need to roast something on the internet  
The history file (hot_takes_history.json) keeps everything fresh across runs

 CustomizationWant to change the color, temperature, or prompts?
Everything is in quotebeast.py — super easy to tweak.LicenseMIT License — feel free to fork, modify, and make it your own.Made with  and too much free time.Star this repo if it made you laugh, motivated you, or helped you slide into DMs.
Questions? Just open an issue!

**✅ Here's your complete GitHub README.md**

Just copy everything above and paste it into a new file called `README.md` in your project folder.

### Quick next steps I recommend:
1. Create a GitHub repo named `quotebeast` (or `ai-quote-beast`)
2. Add this README
3. Take a nice screenshot of the infinite mode and name it `demo.png` (or update the image link)
4. Push it!

Want me to also make a `.gitignore`, a requirements.txt, or a more fancy version with badges/shields? Just say the word.

