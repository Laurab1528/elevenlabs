# Subsidy Management System

## Description

The **Subsidy Management System** is a web application designed to manage candidates in need of subsidies. The application allows users to authenticate, register new users, manage candidates, and perform subsidy transfers. 

This subsidy is designed for individuals who did not meet the retirement requirements and are already of retirement age. In Latin America, 75% of the workforce is informal, meaning they do not contribute to pension systems and, as a result, never retire. Ultimately, they have to work their entire lives.

## Features

- User authentication.
- New user registration.
- Candidate management (viewing, selecting, and transferring subsidies).
- Candidate analysis using the OpenAI API.
- Recording of call transcriptions.

## Technologies Used

- **Python**: Main programming language.
- **Streamlit**: Framework for creating interactive web applications.
- **OpenAI API**: For text analysis and response generation.
- **Pydantic**: For data validation.
- **Langchain**: For integrating language models.
- **SQLite**: Database for storing user and candidate information.
- **dotenv**: For managing environment variables.
- **Twilio**: For handling phone calls and text messages.
- **ElevenLabs**: For generating voice messages.
- **uv**: A fast package and project manager for Python.

## Requirements

- Python 3.7 or higher.
- Dependencies specified in `pyproject.toml`.

## Installation

1. Clone the repository:

   ```bash
   git clone <REPOSITORY_URL>
   cd <REPOSITORY_NAME>
   ```

2. Create a virtual environment and activate it:

   ```bash
   python -m venv env
   # On Windows
   .\env\Scripts\activate
   # On Linux/Mac
   source env/bin/activate
   ```

3. Install the dependencies using Poetry:

   If you are using [uv](https://docs.astral.sh/uv/), you can install the dependencies with:

   ```bash
   uv install
   ```

   If you are not using Poetry, you can install the dependencies manually by running:

   ```bash
   pip install -e .
   ```

4. Configure the OpenAI API key:

   Create a `.env` file in the root of the project and add your API key:

   ```plaintext
   OPENAI_API_KEY=your_api_key
   ```

5. Initialize the database:

   ```bash
   python -m attached_assets.database
   ```

## Usage

To run the application, use the following command:
```bash
streamlit run attached_assets/app.py
```

Then, open your browser and go to `http://localhost:8501` to access the application.

## Contributions

Contributions are welcome. If you would like to contribute, please follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/new-feature`).
3. Make your changes and commit (`git commit -m 'Add new feature'`).
4. Push to the branch (`git push origin feature/new-feature`).
5. Open a Pull Request.

## Environment Variables

Before running the application, you need to configure the following environment variables in your `.env` file:



- **ELEVENLABS_API_KEY**: Your Eleven Labs API key.
  ```
 
  ```

- **ELEVENLABS_AGENT_ID**: Your Eleven Labs agent ID.
  ```
  
  ```

- **TWILIO_ACCOUNT_SID**: Your Twilio account SID.
  ```
 
  ```

- **TWILIO_AUTH_TOKEN**: Your Twilio authentication token.
  ```
 
  ```

- **TWILIO_FROM_NUMBER**: The phone number from which Twilio will send messages.
  ```

  ```

- **TWILIO_NUMBER_TO_CALL**: The phone number to which calls will be made.
  ```


- **OPENAI_API_KEY**: Your OpenAI API key.
  ```

  ```

Make sure to replace the placeholder values with your actual credentials.


