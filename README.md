# Stock Analysis WorkFlow with RLM
The strategy used in `stock_analysis_workflow.py` (Phase 1) is a **modular, sequential processing pipeline** that mimics the cognitive workflow of a human financial analyst. Instead of asking one giant question, it breaks the stock analysis into discrete, logical steps, where earlier steps inform later ones.

Here is the step-by-step strategy from **Input** to **Results**:

### **1. Input & Setup (The Foundation)**

* **User Context:** The script starts by asking you for the **Ticker** (e.g., TSLA) and optionally your **Portfolio Position** (Shares/Avg Cost). This "User Context" is stored in memory to be injected later into the decision-making prompts.
* **Knowledge Base Loading:** It scans your Google Drive `Input` folder for any PDF/HTML/TXT files (e.g., 10-K, 10-Q, Earnings Calls). These files are uploaded to the Gemini API's **File API** (a temporary cloud storage for the model context). This means every prompt in the chain has "read" these documents.

### **2. Sequential Execution (The Chain)**

The script runs prompts **1 through 13** in a specific order defined by `EXECUTION_ORDER`. Each step is an independent API call to Gemini, but they share context.

* **Step 1 (Business Phase):** *The Router.*
* It runs prompt #1 to determine if the company is a "Startup," "Hypergrowth," or "Cash Cow."
* **Strategic Feature:** The script uses Regex to *extract* this "Phase Number" (e.g., "Phase 4") from the output text. This variable (`detected_phase`) is saved for later.


* **Steps 2-4 (Qualitative Analysis):**
* Gemini analyzes the Business Model, Moat, and Growth Drivers using the uploaded PDFs. These steps build the narrative foundation.


* **Step 5 (Metrics - Context Aware):**
* **Strategic Injection:** The script takes the `detected_phase` from Step 1 and *injects* it into the prompt for Step 5.
* *Why?* A "Startup" is judged on Revenue Growth, while a "Cash Cow" is judged on Dividends. By telling Gemini "This is a Phase 4 company," the AI knows which scorecard to use automatically.


* **Steps 6-9 (Risk & Sentiment):**
* Standard analysis of risks, valuation metrics, and sentiment.


* **Step 10-11 (Valuation Engine):**
* **Reverse DCF (Step 10):** "What price is the market implying?"
* **Intrinsic Valuation (Step 11):** "What is the stock actually worth?"
* These run effectively in parallel but build the quantitative case for the final decision.


* **Step 12 (The Decision):**
* **Strategic Injection:** The script injects your **Portfolio Position** (e.g., "User has 100 shares at $150").
* *Why?* The AI uses this to tailor the "Buy Ladder." If you are down, it checks for thesis drift. If you are up, it checks for profit taking. It synthesizes the Valuation outputs (Steps 10 & 11) into a final "Buy/Sell/Hold" call.


* **Step 13 (Behavioral Check):**
* **Strategic Injection:** Again, your position data is injected.
* *Why?* To check for psychological biases like "Sunk Cost Fallacy" (holding a loser) or "House Money Effect" (gambling with profits).



### **3. Output Generation (The Artifacts)**

* **Markdown Files:** For every step, the script saves the full AI response as a `.md` file (e.g., `Step_1_Output.md`) in your `Results/TICKER` folder.
* **Cleanup:** Finally, it moves the source PDFs from `Input` to `Results/TICKER/Source_Docs` so your input folder is clean for the next stock.

### **Summary of the "Intelligence"**

The "smart" part of this workflow isn't just running prompts; it's the **State Management**:

1. **Extracting State:** Reading "Phase 4" from Step 1.
2. **Passing State:** Giving that Phase to Step 5.
3. **Injecting Context:** Passing your personal Portfolio Data to Steps 12 & 13.

This turns a set of generic prompts into a **customized, context-aware analysis pipeline.**
