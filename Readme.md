#  PR Merge Risk Predictor

> A machine learning system that analyzes pull request metadata to estimate the probability that a code change will introduce defects after merging.

Built for engineering teams who want **automated, data-driven risk assessment** before code hits production — inspired by internal tooling studied at companies like Google and Microsoft.

---

##  What It Does

Every pull request carries some level of risk. A large diff with one reviewer and no tests is very different from a small focused change reviewed by three senior engineers. This system quantifies that risk.

Given a pull request's metadata, the model returns:
```json
{
  "merge_risk_probability": 0.74,
  "risk_level": "HIGH"
}
```

---

##  System Architecture
```
GitHub Repository
       ↓
GitHub API Data Collector
       ↓
Feature Engineering Pipeline
       ↓
ML Model Training (Logistic Regression → Random Forest → XGBoost)
       ↓
Model Serialization (.pkl)
       ↓
FastAPI Prediction Service
       ↓
Frontend Dashboard
```

---

##  Project Structure
```
pr-risk-predictor/
│
├── data/
│   ├── raw/                        # Raw data from GitHub API
│   └── processed/                  # Cleaned & feature engineered data
│
├── notebooks/
│   └── exploration.ipynb           # EDA & experimentation
│
├── src/
│   ├── data_collection/
│   │   └── github_fetcher.py       # GitHub API calls
│   ├── features/
│   │   └── feature_engineering.py  # Feature transformations
│   ├── models/
│   │   └── train.py                # Model training & evaluation
│   └── api/
│       └── main.py                 # FastAPI app
│
├── models/                         # Saved serialized models (.pkl)
├── frontend/                       # Dashboard (Streamlit / React)
├── tests/                          # Unit tests
│
├── .env                            # GitHub token (never commit this!)
├── .env.example                    # Token template (safe to commit)
├── .gitignore
├── requirements.txt
└── README.md
```

---

##  Feature Set

### Code Change Metrics
| Feature | Description |
|---|---|
| `lines_added` | Lines of code added |
| `lines_deleted` | Lines of code deleted |
| `lines_changed` | Total lines changed (code churn) |
| `files_modified` | Number of files touched |
| `commit_count` | Number of commits in the PR |

### Review Process Metrics
| Feature | Description |
|---|---|
| `num_reviewers` | Number of reviewers requested |
| `actual_reviewers` | Number of reviewers who actually reviewed |
| `review_time_hours` | Time from open to merge |
| `review_comments` | Total review comments left |
| `approval_count` | Number of explicit approvals |

### Developer Metrics
| Feature | Description |
|---|---|
| `developer_total_commits` | Total commits by the PR author in this repo |
| `previous_pr_failures` | Author's historical rejected PR count |

### CI/CD Metrics
| Feature | Description |
|---|---|
| `ci_status` | CI pipeline result (passed / failed / none) |

---

##  Target Variable
```
merge_risk → binary classification
  1 = PR caused issues after merge
      (revert commit, hotfix PR, or bug issue within 30 days)
  0 = PR merged cleanly
```

---

##  Dataset

Collected via the **GitHub API** from large, active open-source repositories:

| Repository | PRs Collected |
|---|---|
| `microsoft/vscode` | ~500 |
| `facebook/react` | ~500 |
| `expressjs/express` | ~500 |
| **Total** | **~1500** |

**Label distribution:**
```
Risky PRs (1): ~32%
Clean PRs (0): ~68%
```

**Labeling strategy:** A PR is marked risky (`1`) if any of the following appear within **30 days** of merging:
- A revert commit referencing the PR
- A hotfix PR referencing the PR
- A bug issue referencing the PR

---

##  Models Trained

| Model | Role |
|---|---|
| Logistic Regression | Baseline |
| Random Forest | Comparison |
| XGBoost | Primary (best performer) |

Evaluation metrics: `accuracy`, `precision`, `recall`, `F1-score`, `ROC-AUC`

---

##  API Usage

**Endpoint:** `POST /predict-pr-risk`

**Request:**
```json
{
  "lines_changed": 820,
  "files_modified": 12,
  "review_time_hours": 0.5,
  "num_reviewers": 1,
  "ci_status": "failed"
}
```

**Response:**
```json
{
  "merge_risk_probability": 0.71,
  "risk_level": "HIGH"
}
```

**Risk levels:**
```
0.0 – 0.4  →  LOW
0.4 – 0.7  →  MEDIUM
0.7 – 1.0  →  HIGH
```

---

##  Tech Stack

| Layer | Technology |
|---|---|
| Data Collection | GitHub API + Python |
| Data Processing | Pandas, NumPy |
| ML Models | scikit-learn, XGBoost |
| Model Serving | FastAPI |
| Frontend | Streamlit / React (TBD) |
| Environment | Python 3.10+ |

---

##  Environment Setup

Create a `.env` file in the root directory:
```
GITHUB_TOKEN=your_personal_access_token_here
```

> ⚠️ Never commit your `.env` file. It is already listed in `.gitignore`.

Generate your token at: GitHub → Settings → Developer Settings → Personal Access Tokens → Tokens (classic)

Required scopes: `repo`, `read:user`, `read:org`

---

##  Installation
```bash
# Clone the repository
git clone https://github.com/tanishq-ds/PR-Merge-Risk-Predictor.git
cd PR-Merge-Risk-Predictor

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

---

##  Running the Project

**Step 1 — Collect data:**
```bash
python src/data_collection/github_fetcher.py
```

**Step 2 — Feature engineering:**
```bash
python src/features/feature_engineering.py
```

**Step 3 — Train model:**
```bash
python src/models/train.py
```

**Step 4 — Start API:**
```bash
uvicorn src.api.main:app --reload
```

---

##  Roadmap

- [x] Project structure setup
- [x] Virtual environment setup
- [x] Requirements.txt configured
- [x] GitHub API data collector
- [x] Dataset collected (~1500 PRs, 32% risky)
- [ ] Feature engineering pipeline
- [ ] Model training & evaluation
- [ ] FastAPI prediction service
- [ ] Frontend dashboard
- [ ] Docker containerization

---

## 👤 Author

Built as a full-stack ML engineering side project demonstrating real-world model deployment practices — from raw GitHub API data collection to a live inference service.
