# ml_intent.py
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import joblib, os

# Labeled phrases -> your internal goal keys (match your CSV goals)
TRAIN = [
    ("safe stable low risk index broad market dividend quality", "safe_stable"),
    ("low volatility diversified etf", "safe_stable"),
    ("broad market s&p 500 index fund", "safe_stable"),

    ("tech growth technology stocks software cloud", "tech_growth"),
    ("high growth internet saas", "tech_growth"),
    ("semiconductors and software growth", "tech_growth"),

    ("artificial intelligence ai semiconductors chips", "ai_exposure"),
    ("robotics automation ai exposure", "ai_exposure"),
    ("gpu datacenter machine learning", "ai_exposure"),

    ("dividend income high dividend yield", "dividends"),
    ("dividend stocks payout cash flow", "dividends"),
    ("stable dividend aristocrats", "dividends"),

    ("value stocks cheap valuation financials energy", "value"),
    ("undervalued large cap value", "value"),

    ("clean energy solar renewable green", "clean_energy"),
    ("wind solar renewable energy etf", "clean_energy"),

    ("healthcare pharma biotech medical", "healthcare"),
    ("health care sector drugs hospitals", "healthcare"),

    ("banks payments financial sector", "financials"),
    ("asset managers brokerage credit cards", "financials"),

    ("semiconductors chips foundry lithography", "semiconductors"),
    ("chip makers memory fab equipment", "semiconductors"),

    ("small cap higher risk small companies", "small_cap"),
    ("russell 2000 small caps", "small_cap"),

    ("mid cap balanced growth", "mid_cap"),
    ("midcap software security", "mid_cap"),

    ("large cap growth mega cap quality", "large_cap_growth"),
    ("mega cap tech growth leaders", "large_cap_growth"),
]

X = [t for t, y in TRAIN]
y = [y for t, y in TRAIN]

pipe = Pipeline([
    ("tfidf", TfidfVectorizer(ngram_range=(1,2), min_df=1)),
    ("clf", LogisticRegression(max_iter=2000))
])

pipe.fit(X, y)

os.makedirs("models", exist_ok=True)
joblib.dump(pipe, "models/intent.pipe")
print("Saved models/intent.pipe with classes:", sorted(set(y)))
