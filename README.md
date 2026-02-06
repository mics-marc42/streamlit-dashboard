# BigQuery Predictor

A Streamlit application for querying data from Google BigQuery and creating machine learning predictions.

## Features

- 🔍 **Query BigQuery**: Execute SQL queries directly from the app
- 🤖 **Train Models**: Train regression or classification models on your data
- 🔮 **Make Predictions**: Use trained models to make predictions on new data
- 📊 **Data Visualization**: View and analyze your data with interactive tables
- 💾 **Model Persistence**: Save and load trained models

## Installation

1. Clone this repository or navigate to the project directory:
```bash
cd Collab_predictor
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Setup

### Google Cloud BigQuery Setup

1. **Create a Google Cloud Project** (if you don't have one)
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one

2. **Enable BigQuery API**
   - Navigate to APIs & Services > Library
   - Search for "BigQuery API" and enable it

3. **Create Service Account**
   - Go to IAM & Admin > Service Accounts
   - Click "Create Service Account"
   - Give it a name and grant it "BigQuery Data Viewer" and "BigQuery Job User" roles
   - Create a JSON key and download it

4. **Set up Authentication** (choose one method):
   
   **Option A: Use Default Credentials**
   - Set the environment variable: `GOOGLE_APPLICATION_CREDENTIALS=path/to/your/credentials.json`
   
   **Option B: Upload Credentials in App**
   - Use the sidebar option to upload your credentials JSON file

## Usage

1. **Start the Streamlit app**:
```bash
streamlit run app.py
```

2. **Connect to BigQuery**:
   - Use the sidebar to configure your BigQuery connection
   - Upload credentials file or use default credentials
   - Enter your Project ID (optional)
   - Click "Connect to BigQuery"

3. **Query Data**:
   - Go to the "Query BigQuery" tab
   - Enter your SQL query
   - Click "Execute Query"
   - View and download the results

4. **Train a Model**:
   - Go to the "Train Model" tab
   - Select your target column (what you want to predict)
   - Select feature columns (or use all columns except target)
   - Click "Train Model"
   - View model performance metrics
   - Optionally save the model

5. **Make Predictions**:
   - Go to the "Make Predictions" tab
   - Choose input method (Query Results, Upload CSV, or Manual Input)
   - Click "Make Predictions"
   - Download the results

## Project Structure

```
Collab_predictor/
├── app.py                 # Main Streamlit application
├── bigquery_utils.py      # BigQuery client utilities
├── predictor.py           # Machine learning prediction utilities
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Example Queries

### Sample BigQuery Query:
```sql
SELECT 
  feature1,
  feature2,
  feature3,
  target_column
FROM 
  `your-project.your_dataset.your_table`
WHERE 
  date >= '2023-01-01'
LIMIT 1000
```

## Model Types

- **Regression**: For predicting continuous numerical values
- **Classification**: For predicting categorical/discrete values

## Dependencies

- `streamlit`: Web application framework
- `google-cloud-bigquery`: BigQuery client library
- `pandas`: Data manipulation
- `numpy`: Numerical computing
- `scikit-learn`: Machine learning algorithms
- `python-dotenv`: Environment variable management

## Notes

- Make sure you have appropriate BigQuery permissions
- Large queries may take time to execute
- Models are trained using Random Forest algorithm
- Saved models can be loaded later for predictions

## Troubleshooting

**Connection Issues:**
- Verify your credentials JSON file is valid
- Check that BigQuery API is enabled
- Ensure service account has proper permissions

**Query Errors:**
- Verify your SQL syntax
- Check table/dataset names are correct
- Ensure you have access to the queried tables

**Model Training Errors:**
- Ensure target column has appropriate data type
- Check for missing values in critical columns
- Verify sufficient data for training

## License

This project is open source and available for use.
