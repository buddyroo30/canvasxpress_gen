# canvasxpress_gen
Generating CanvasXpress visualizations from natural language descriptions of them using Large Language Models ("LLMs")

# Introduction

The code in this repository can be used to conversationally generate [CanvasXpress](https://www.canvasxpress.org) visualizations, i.e. a user can simply describe in plain English the graph they want (e.g. "box plot of len on x axis grouped by dose with title 'len by dose'"), upload a CSV or tab-delimited data file (with a header describing and naming the columns) to be graphed, and then have their desired graph created automatically with high accuracy using LLMs. In this repo we provide a Python Flask application that implements a simple chat-like UI for conversationally generating visualizations as well as the backend API/services to support it (that call LLMs like Google Gemini or OpenAI GPT-4o with an appropriate prompt on your behalf). The functionality is also built directly into [CanvasXpress](https://www.canvasxpress.org/llm.html) which calls a service that runs this code on the canvasxpress.org main server; note that if you want to use this functionality internally at your organization without sending data to the public canvasxpress.org site you can run this code/service on your own server and configure CanvasXpress visualizations to use that by setting configuration option llmServiceURL in your HTML-embedded CanvasXpress graphs (e.g. config['llmServiceURL'] = "/ask").

# Building and Running the Application

The application is implemented and run using Docker, with various Makefile targets to support building the Docker image, running it, and stopping it. Both a production and development image/application are supported by the Makefile so you can test changes on the development system before propagating them to the production system. Here are the steps you can take to build and run the image:

1. make build - build the Docker image for the production application.
2. make init - initialize necessary files to run the production application (in particular create the vector database used for RAG by indexing the few shot examples)
3. make runi - run the production application interactively (i.e. you will be able to see all the Flask output, including any errors which is useful for debugging, and can exit by typing CTRL-c)
4. make run - run the production application as a daemon
5. make exit - shut down the production application

There is also 'make shell' to enter into a Shell session for the Docker image and 'make buildfresh' which is the same as 'make build' except it doesn't use Docker cache.

To build and run the development version of the application there are Makefile targets corresponding to all the above by simply appending '_dev' (i.e. 'make build_dev', 'make run_dev', 'make exit_dev', etc.) Note that in the provided Makefile the production application runs on port 5008 and the development application runs on port 5009 --- edit RUN_ARGS or RUN_ARGS_DEV to change the ports if you want. Also, the running Docker containers bind mount ~/.cache to /root/.cache inside the container, so make sure you have a .cache directory in your home directory (this is used to store the [BGE-M3](https://milvus.io/docs/embed-with-bgm-m3.md) embedding model files and also the created vector database which is named canvasxpress_llm.db or canvasxpress_llm_dev.db).

# Important Files

There are some files that support the core interactions with the LLM, i.e. that are used to generate the prompts sent to the LLM (and there are both production and development versions of the files). You can modify these to try to improve the system (e.g. modify the main prompt, add new few shot examples, etc.)

1. prompt.md and prompt_dev.md - the high level prompt sent to the LLM (schema info and few shot examples are interpolated into this before sending to the LLM).
2. schema.txt and schema_dev.txt - the schema information that is sent to the LLM (consisting of about 150 of the most commonly used CanvasXpress configuration options)
3. doc.json and doc_dev.json - a JSON file containing the full set of CanvasXpress configuration options. This information is also indexed in the vector database, but not used at present, but we plan to use it in the future.
4. all_few_shots.json and all_few_shots_dev.json - a JSON file containing the few shot examples used in the system. These are indexed in the vector database and when the user enters a question, that question is searched against the vector database to fetch the 25 most similar few shot examples which are interpolated into prompt.md or prompt_dev.md. If you update these files you should regenerate the vector database file by running 'make init' or 'make init_dev' and then restart the container (i.e. 'make run' or 'make run_dev').

# Supported LLMs and .env file

We have written the code to be able to work with a number of well-known LLMs from OpenAI (GPT-4o, GPT-4-32K, etc.), Google (Gemini 1.5 Flash and Pro), Anthropic and others. To use the OpenAI models you will need an OpenAI token, and similarly to use the Google Gemini models you will need a Google token; most of the other models are supported through [AWS Bedrock](https://aws.amazon.com/bedrock/) (so you would need to configure AWS credentials to use them), and [Ollama](https://ollama.com/) models are also supported if you wanted to run a model yourself. For using the OpenAI models and/or Google Gemini models you should set environment variable values in a .env file (which will get read in using Python's [python-dotenv](https://pypi.org/project/python-dotenv/) package):

    GOOGLE_API_KEY=....
    AZURE_OPENAI_API_KEY=...
    AZURE_OPENAI_ENDPOINT=...
    AZURE_OPENAI_API_VERSION=2024-02-01

If you don't know what model to use, easiest is to simply use [Google Gemini 1.5 Flash](https://ai.google.dev/gemini-api) which offers a fairly generous daily allowance of queries through its [free tier](https://ai.google.dev/pricing) and works well in practice.

# SiteMinder Support

Internally at our company Bristol Myers Squibb we use SiteMinder SSO to authenticate users, and we have built support for this into the application. But it isn't required and you don't need to use it. To NOT use SiteMinder simply define a value in your .env file SMVAL=False. If you do want to use SiteMinder then you will need to set SMVAL=True and define some other SiteMinder related env vars:

    SMVAL=True
    SMLOGIN=...URL of your SiteMinder login page...
    SMTARGET=...SiteMinder redirect URL
    SMFAILREGEX=...a pattern to look for in the result of logging in to denote failure...
    SMFETCHFAILREGEX=...a pattern to look for in fetched pages to denote failure...
