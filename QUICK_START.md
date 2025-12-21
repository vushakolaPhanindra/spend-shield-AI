# SpendShield AI - Simple Setup Guide

## 🚀 Quick Start (3 Steps)

### Step 1: Get Your Google API Key (FREE)

1. Visit: https://aistudio.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key (starts with "AIza...")

### Step 2: Configure Environment

1. Open the `.env` file in this directory
2. Replace `your_google_api_key_here` with your actual API key:
   ```
   GOOGLE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
   ```
3. Save the file

### Step 3: Run the Application

Open PowerShell in this directory and run:

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies (first time only)
pip install -r requirements.txt

# Start PostgreSQL (choose one option):

# Option A: If you have Docker
docker run -d --name spendshield-db -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=spendshield -p 5432:5432 postgres:15-alpine

# Option B: If you have PostgreSQL installed locally
# Just make sure it's running on port 5432

# Option C: Skip database for now (some features won't work)
# Just continue to next step

# Run the application
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

The API will be available at: http://localhost:8080

---

## 🧪 Alternative: Run Mock Test (No Database Required)

If you don't have PostgreSQL, you can still test the core functionality:

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Set your API key temporarily
$env:GOOGLE_API_KEY="your_key_here"

# Run the mock test
python tests/test_fraud_detection.py --mock
```

This will demonstrate the 20% price inflation detection!

---

## 📝 What You Need

- ✅ Python 3.12.6 (already installed)
- ✅ Virtual environment (already created)
- ⏳ Dependencies (installing now...)
- ❓ Google API Key (get from link above)
- ❓ PostgreSQL (optional for testing)

---

## 🆘 Troubleshooting

### "Cannot run scripts" error
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### "Module not found" error
```powershell
pip install -r requirements.txt
```

### "Database connection failed"
- Make sure PostgreSQL is running
- Or run the mock test instead (doesn't need database)

---

## 📞 Next Steps

1. Get your API key from Google AI Studio
2. Add it to the `.env` file
3. Run the mock test to verify everything works
4. Then start the full application with PostgreSQL

---

**Need help?** Check the README.md for detailed documentation.
