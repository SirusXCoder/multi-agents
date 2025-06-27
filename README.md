# Multi-Agent Systems Demo: **Order Support Agent** & **Health Wellness Agent**

Welcome to the **Multi-Agent Systems Demo** repository! This project showcases two practical applications of multi-agent AI systems built using Python, LangChain, Pinecone, and OpenAI: the **boldly highlighted **[Order Support Agent](#order-support-agent) and the **boldly highlighted **[Health Wellness Agent](#health-wellness-agent). These projects are featured in a YouTube training video by `Bridge 2 Success` (@bridge_2_success) to help beginners, developers, businesses, and students understand and implement multi-agent AI solutions. Whether you're learning AI basics or exploring enterprise applications, this repo is your starting point!

## Overview
- **Order Support Agent**: Automates order tracking, returns, and customer support for e-commerce, addressing the growing demand for efficient online shopping solutions.
- **Health Wellness Agent**: Provides personalized health advice on fitness, nutrition, and sleep, tapping into the booming wearable tech and wellness industry.

These agents use a collaborative multi-agent architecture to triage queries, retrieve data, and generate responses, making them scalable and adaptable.

## Architecture
The multi-agent system follows a modular pipeline:
```
[User Query] --> [Triage Agent] --> [Category: Order/Health]
                  |
                  v
[Retrieval Agent] --> [Vector Store (Pinecone)] --> [Relevant Data]
                  |
                  v
[Response Agent] --> [Generated Response] --> [User]
```
- **Triage Agent**: Classifies the query (e.g., order status, fitness tips) using an LLM.
- **Retrieval Agent**: Fetches relevant data from a Pinecone vector store using embeddings.
- **Response Agent**: Generates human-like responses with the LLM.
- **Vector Store (Pinecone)**: Stores and indexes embedded data for efficient retrieval.

This design overcomes challenges like data overload and slow responses by splitting tasks, ensuring efficiency and scalability.

## Getting Started

### Prerequisites
- Docker (for containerized execution)
- Python 3.10 or higher (for local development)
- Git (for cloning the repository)
- API keys for:
  - OpenAI (for embeddings and LLM)
  - Pinecone (for vector storage)
- Virtual environment (recommended for local setup)

### Installation

#### Local Setup
1. **Clone the Repository**
   ```bash
   git clone https://github.com/nworkskills/multi_agents.git
   cd multi_agents
   ```

2. **Set Up Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   Install required packages from `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**
   Create a `.env` file in both `order_support_agent/` and `health_wellness_agent/` directories with:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   PINECONE_API_KEY=your_pinecone_api_key_here
   ```
   Keep this file private and add it to `.gitignore`.

5. **Run the Applications**
   - For **Order Support Agent**:
     - Ingest data: `python order_support_agent/ingest_order_data.py`
     - Run agent: `python order_support_agent/order_support_agent.py`
   - For **Health Wellness Agent**:
     - Ingest data: `python health_wellness_agent/ingest_health_data.py`
     - Run agent: `python health_wellness_agent/health_wellness_agent.py`

#### Docker Setup
1. **Build Docker Images**
   - For **Order Support Agent**:
     ```bash
     cd order_support_agent
     docker build -t order-support-agent .
     ```
   - For **Health Wellness Agent**:
     ```bash
     cd health_wellness_agent
     docker build -t health-wellness-agent .
     ```

2. **Run Containers**
   - For **Order Support Agent** (ingest data):
     ```bash
     docker run --rm -v $(pwd)/order_data.csv:/app/order_data.csv -v $(pwd)/.env:/app/.env order-support-agent ingest
     ```
   - For **Order Support Agent** (run agent):
     ```bash
     docker run --rm -v $(pwd)/order_data.csv:/app/order_data.csv -v $(pwd)/.env:/app/.env order-support-agent run
     ```
   - For **Health Wellness Agent** (ingest data):
     ```bash
     docker run --rm -v $(pwd)/health_data.csv:/app/health_data.csv -v $(pwd)/.env:/app/.env health-wellness-agent ingest
     ```
   - For **Health Wellness Agent** (run agent):
     ```bash
     docker run --rm -v $(pwd)/health_data.csv:/app/health_data.csv -v $(pwd)/.env:/app/.env health-wellness-agent run
     ```
   - **Note:** Replace `$(pwd)` with the absolute path on Windows (e.g., `C:/Users/asudh/...`) if needed.

3. **Verify Containers**
   ```bash
   docker ps -a
   ```

### Git Commands
- **Check Out Code:**
  ```bash
  git clone https://github.com/nworkskills/multi_agents.git
  cd multi_agents
  git checkout main  # Switch to main branch (default)
  ```
- **Check In Changes:**
  ```bash
  git add .
  git commit -m "Add new features or updates"
  git push origin main
  ```
- **Create a Branch (for contributions):**
  ```bash
  git checkout -b feature-name
  git add .
  git commit -m "Describe your changes"
  git push origin feature-name
  ```

## Usage
- **Order Support Agent**: Test with queries like "Where is my order #1234?" to get shipping details.
- **Health Wellness Agent**: Test with queries like "How much exercise should I do weekly?" for personalized tips.
- Check console output for category, context, and responses.

## Project Structure
```
multi_agents/
├── order_support_agent/
│   ├── ingest_order_data.py
│   ├── order_support_agent.py
│   ├── order_data.csv
│   ├── .env
│   └── Dockerfile
├── health_wellness_agent/
│   ├── ingest_health_data.py
│   ├── health_wellness_agent.py
│   ├── health_data.csv
│   ├── .env
│   └── Dockerfile
├── README.md
└── requirements.txt
```

## Data Files
- `order_support_agent/order_data.csv`: Contains order and return records.
- `health_wellness_agent/health_data.csv`: Contains health and wellness tips.

## Additional Information
- **YouTube Demo**: Watch the full tutorial at [Insert Your YouTube Link] for step-by-step guidance.
- **Community**: Join discussions on [Insert Your Discord/Forum Link] or follow @nworkskills on GitHub/X.
- **Contributions**: Fork this repo, make changes, and submit pull requests. Add your API keys to `.env` for testing.
- **Troubleshooting**: If ingestion fails, verify CSV formatting and API keys. Check Pinecone dashboard for indexed vectors.
- **Security**: Never commit `.env` files. Use `.gitignore` to exclude them.

## License
This project is open-source under the MIT License. See [LICENSE](LICENSE) for details.

## Acknowledgments
- Inspired by multi-agent frameworks and tutorials from the AI community.
- Thanks to viewers and contributors for supporting this learning journey!