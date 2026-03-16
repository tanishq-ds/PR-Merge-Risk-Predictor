#  PR Merge Risk Predictor

A machine learning system that analyzes pull request metadata to estimate the probability that a code change will introduce defects after merging. Built for engineering teams who want automated, data-driven risk assessment before code hits production.

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
| `lines_changed` | Total lines changed |
| `files_modified` | Number of files touched |
| `commit_count` | Number of commits in the PR |

### Review Process Metrics
| Feature | Description |
|---|---|
| `num_reviewers` | Number of reviewers assigned |
| `review_time_hours` | Time taken to review |
| `review_comments` | Total review comments |
| `approval_count` | Number of approvals received |

### Developer Metrics
| Feature | Description |
|---|---|
| `developer_total_commits` | Total commits by the author |
| `developer_experience_years` | Estimated experience |
| `previous_pr_failures` | Author's historical failure rate |

### Testing Metrics
| Feature | Description |
|---|---|
| `test_files_changed` | Test files included in the PR |
| `test_coverage` | Coverage delta |
| `ci_status` | CI pipeline result |

---

##  Target Variable
```
merge_risk → binary classification
  1 = PR caused issues after merge (revert, hotfix, or bug report followed)
  0 = PR merged cleanly
```

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
  "num_reviewers": 1
}
```

**Response:**
```json
{
  "merge_risk_probability": 0.71,
  "risk_level": "HIGH"
}
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

---

##  Installation
```bash
# Clone the repository
git clone https://github.com/tanishq-ds/PR-Merge-Risk-Predictor.git
cd pr-risk-predictor

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

##  Data Sources

Pull request metadata is collected via the **GitHub API** from large, active open-source repositories such as:
- `microsoft/vscode`
- `facebook/react`
- `django/django`

Labeling strategy: A PR is marked risky (`1`) if a revert commit, hotfix PR, or bug issue appears within 7 days of the merge.

---

## 🗺️ Roadmap

- [x] Project structure setup
- [x] Virtual environment setup
- [x] Requirements.txt configured
- [x] GitHub API data collector (in progress)
- [ ] Feature engineering pipeline
- [ ] Model training & evaluation
- [ ] FastAPI prediction service
- [ ] Frontend dashboard
- [ ] Docker containerization
---

## 👤 Author

Built as a full-stack ML engineering project demonstrating real-world model deployment practices.
