# canvasxpress_gen
Generating CanvasXpress visualizations from natural language descriptions of them using LLMs

# Introduction

The code in this repository can be used to conversationally generate [CanvasXpress](https://www.canvasxpress.org) visualizations, i.e. a user can simply describe in plain English the graph they want (e.g. "box plot of len on x axis grouped by dose with title "len by dose"), upload a CSV or tab-delimited data file (with a header describing and naming the columns) to be graphed, and then have their desired graph created automatically with high accuracy using LLMs. In this repo we provide Python Flask application that implements a simple chat-like UI for conversationally generating visualizations as well as the backend API/services to support it (that call LLMs like Google Gemini or OpenAI GPT-4o with an appropriate prompt on your behalf). The functionality is also built directly into [CanvasXpress](https://www.canvasxpress.org/llm.html) which calls a service that runs this code on the canvasxpress.org main server; note that if you want to use this functionality internally at your organization without sending data to the public canvasxpress.org site you can run this code/service on your own server and configure CanvasXpress visualizations to use that (details below).

# Building and Running the Application

The application is implemented and run using Docker, with various Makefile targets to support building the Docker image, running it, and stopping it. Both a production and development image/service are supported by the Makefile so you can test changes on the development system before propagating them to the production system. Here are the steps you can take to build and run the image:

1. make build - build the Docker image for the production application.
2. make init - initialize necessary files to run the production application (in particular create the vector database used for RAG by indexing the few shot examples)
3. make runi - run the production application interactively (i.e. you will be able to see all the Flask output, including any errors which is useful for debugging, and can exit by typing CTRL-c)
4. make run - run the production application as a daemon
5. make exit - shut down the production application

There is also 'make shell' to enter into a Shell session for the Docker image and 'make buildfresh' which is the same as 'make build' except it doesn't use Docker cache.

To build and run the development version of the application there are Makefile targets corresponding to all the above by simply appending '_dev' (i.e. 'make build_dev', 'make run_dev', 'make exit_dev', etc.)

# Important Files

There are some files that support the core interactions with the LLM, i.e. that are used to generate the prompts sent to the LLM (and there are both production and development versions of the files). You can modify these to try to improve the system (e.g. modify the main prompt, add new few shot examples, etc.)

1. prompt.md and prompt_dev.md - the high level prompt sent to the LLM (schema info and few shot examples are interpolated into this before sending to the LLM).
2. schema.txt and schema_dev.txt - the schema information that is sent to the LLM (consisting of about 150 of the most commonly used CanvasXpress configuration options)
3. doc.json and doc_dev.json - a JSON file containing the full set of CanvasXpress configuration options. This information is also indexed in the vector database, but not used at present, but we plan to use it in the future.
4. all_few_shots.json and all_few_shots_dev.json - a JSON file containing the few shot examples used in the system. These are indexed in the vector database and when the user enters a question, that question is searched against the vector database to fetch the 25 most similar few shot examples which are interpolated into prompt.md.
