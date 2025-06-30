---
title: 'Generating Visualizations Conversationally using Guided Autocomplete and LLMs'
tags:
  - Artificial Intelligence (AI)
  - Natural Language Processing (NLP)
  - Large Language Model (LLM)
  - Generative AI
  - Visualization
  - Data Analytics
  - Exploratory Data Analysis (EDA)
  - Bioinformatics
  - CanvasXpress
authors:
  - name: Andrew K Smith
    orcid: 0009-0009-6515-1671
    equal-contrib: true
    affiliation: "1"
  - name: Isaac Neuhaus
    orcid: 0000-0002-5622-8683
    equal-contrib: true
    affiliation: 1
affiliations:
 - name: Informatics & Predictive Sciences, Knowledge Science Research, Computational Genomics, Bristol Myers Squibb 3551 Lawrenceville Rd, Lawrence Township, NJ 08648
   index: 1
date: 30 September 2024
bibliography: paper.bib
---

# Summary

Powerful data visualization packages like CanvasXpress provide rich features for exploring datasets but have high learning curves requiring detailed web development skills. We demonstrate how guided autocomplete and Large Language Models (LLMs) can be effectively used together in a complementary way to greatly simplify visualization creation. Users upload datasets as tab-delimited or CSV files and describe desired visualizations in plain English, guided by autocomplete suggestions or through free-form text input. Following guided suggestions generates configurations with perfect accuracy, while LLMs serve as backup with high accuracy when users deviate from suggestions.

The guided autocomplete system can generate synthetic training data at large scale for few-shot prompting or LLM fine-tuning. We evaluate accuracy using thousands of synthetic examples with Retrieval Augmented Generation (RAG), achieving over 97% exact match accuracy across datasets. Results demonstrate that accuracy increases with more few-shot examples but decreases with prompt complexity—testing datasets with maximum 4, 6, and 10 sentences shows that longer, more complex visualization descriptions pose greater challenges for LLMs to handle accurately.

# Statement of Need

CanvasXpress [@neuhaus_canvasxpress_nodate] is a powerful JavaScript library for creating interactive data visualizations using HTML5 canvas technology. It supports various chart types (line, bar, scatter, 3D graphs) with extensive customization options through JSON configuration objects. A crucial component of creating visualizations is the JSON-format configuration object, which specifies parameters and features of the visual representation. While basic configurations can be straightforward, the numerous customization options allow for tailored visual experiences but require technical expertise.

The requirement for coding and web development skills creates significant barriers for many potential users. This presents a research challenge: many domain scientists in fields like genomics, proteomics, and clinical studies have deep knowledge of their field but limited visualization programming skills, creating technical barriers to effective data exploration and communication. Can we simplify this process by enabling users to create visualizations through natural language descriptions?

We created a system leveraging guided autocomplete and LLMs for conversational visualization generation. CanvasXpress has several key attributes making it particularly suitable for LLM-based generation: (1) Its well-structured JSON schema with semantically meaningful field names creates natural mapping between English descriptions and configuration elements; (2) Its declarative approach (unlike ggplot2's sequential function calls or D3.js's DOM manipulation) is more compatible with one-shot generation by LLMs; (3) CanvasXpress implements sensible defaults and handles missing parameters gracefully, reducing errors in LLM-generated configurations; (4) The scientific domain focus and balanced configuration complexity make it well-suited for visualizations researchers commonly need.

While tools like Plotly also use JSON configurations and could potentially be adapted to our approach, many visualization libraries would require generating procedural code rather than declarative configurations, making them significantly more challenging for LLM-based generation.

# Implementation

## Guided Autocomplete

Guided autocomplete helps users generate prompts by suggesting potential completions based on their inputs, guiding them to build complete prompts incrementally. For example, users typing "Create" see options like "a bar graph" or "a line chart." This technique ensures perfect accuracy when followed completely, with LLMs serving as backup for free-form input. The system, called "CoPilot," draws parallels to menu-based natural language approaches from the 1980s [@tennant_menu-based_1984], which employed context-free grammars and predictive parsing for natural language interfaces to SQL databases.

Copilot ensures perfect accuracy without requiring LLM calls, with LLMs serving as backup strategy when users don't use the copilot. Another significant beneficial feature is that the guided autocomplete implementation can generate many synthetic prompt/config pairs for use as few-shot examples to enhance LLM accuracy or generate large-scale training sets for LLM fine-tuning.

## Prompt Engineering and RAG

Prompt engineering is critical for effectively using large language models for visualization tasks, determining how well the system understands user inputs and generates correct outputs. We use few-shot prompting [@brown_language_2020; @schulhoff_showing_2024], providing examples of user questions and corresponding correct outputs to guide the LLM toward generating accurate answers.

We utilized the Copilot's ability to automatically generate large-scale synthetic few-shot examples to perform accuracy tests of LLM-generated CanvasXpress JSON configurations from English prompts. All few-shot examples used in our system—including those for evaluation and accuracy testing—are generated automatically by our guided autocomplete system (Copilot), not manually curated. Each example includes detailed English descriptions followed by corresponding JSON configurations necessary for creating specified visualizations. This automated approach generates thousands of diverse, high-quality examples that would be prohibitively time-consuming to create manually.

We also provide LLM schema information including possible field names, types, legal values, and field descriptions. CanvasXpress has approximately 1500 potential configuration fields, but due to LLM context window limits, we focus on around 150 most-used fields, which suffice for most users and use cases.

Retrieval Augmented Generation (RAG) [@gao_retrieval-augmented_2023] leverages vector databases to enhance precision and relevance of few-shot examples more adaptively and efficiently than sending all examples. RAG facilitates efficient retrieval processes that identify the most similar and relevant examples to user queries. We create 1024-dimension dense semantic vectors of all few-shot English descriptions using the open-source BGE-M3 embedding model [@chen_bge_2024], which demonstrates competitive performance relative to OpenAI embeddings [@borgne_openai_2024], storing them in an on-disk PyMilvus/Milvus [@wang_milvus_2021; @guo_manu_2022] vector database. When users pose questions, they are vectorized using BGE-M3 and searched against the vector database for the 25 most semantically similar few-shot examples.

# Accuracy Assessment

We assessed the impact of two important factors: total number of few-shot examples and prompt complexity (measured by maximum number of sentences). For few-shot example counts, we conducted tests in increments of 100 from 100 to 2500. For complexity, we evaluated prompts with maximum lengths of 4, 6, and 10 sentences. For each synthetic prompt, we generated three alternative phrasings using GPT-4o to ensure expression variety. Not all few-shots are utilized for each prompt, but increasing the pool of possible examples allows our RAG approach to choose the most similar 25 few-shots for each test prompt.

We assess accuracy using two key metrics: exact match percentage (percentage where LLM-generated JSON config exactly matches the known correct answer) and JSON similarity score. The JSON similarity score uses a recursive comparison function measuring similarity between JSON objects by recursively comparing structure and values. It handles dictionaries by comparing keys and recursively evaluating values, lists by measuring overlapping elements, and primitive types with specific equality or tolerance rules. This provides holistic measures of JSON configuration similarity even when they don't match exactly.

Few-shot examples were systematically created using our guided autocomplete system ensuring comprehensive coverage across: (1) Common chart types (bar charts, scatter plots, line charts, heatmaps); (2) Different data structures (categorical, numerical, time-series data); (3) Customization options (colors, labels, axis scaling). We generated datasets with up to 2,500 examples for evaluation, testing prompts with maximum lengths of 4, 6, and 10 sentences to assess complexity scaling.

Key findings show these metrics improve with increased few-shot examples then plateau for all three datasets, though the 4-sentence dataset performance starts decreasing around 1800 few-shots. While accuracy is excellent (close to perfect) for all datasets, accuracy is notably better with datasets containing up to 4 sentences compared to 6 or 10 sentences, with the 10-sentence dataset showing more noticeable accuracy dropoff compared to 6 sentences. This suggests longer, more complex visualization descriptions pose greater challenges for LLMs to generate accurately.

Future work includes developing fine-tuned LLMs using synthetic data generated by the Copilot. Fine-tuning requires thousands of examples, easily generated by the copilot while manual creation would be challenging. The potential for improved accuracy through fine-tuning is significant—for example, SQLcoder achieves 93% accuracy compared to GPT-4's 86% in generating SQL from English text [@noauthor_defog-aisqlcoder_nodate].

We have also developed an agentic version using AWS Bedrock, extending capabilities beyond simple visualization generation to interact with multiple data sources, perform complex multi-step analysis workflows, and integrate with other AI agents for comprehensive data analysis and visualization pipelines.

# Research Impact

Our natural language interface system directly addresses significant research challenges by democratizing access to sophisticated visualization capabilities. By providing natural language interfaces to visualization creation, our system: (1) Reduces time from data analysis to visualization, enabling faster hypothesis generation and testing; (2) Enables researchers to explore more visualization options without technical obstacles, facilitating better data exploration; (3) Eliminates need for specialized visualization support or collaboration with programmers, making researchers more self-sufficient; (4) Accelerates research processes in data-intensive scientific domains where visualization is critical to discovery and communication of findings.

For example, genomics researchers can quickly generate complex heatmaps to visualize gene expression patterns by simply describing "show me a heatmap of gene expression levels across different tissue types, clustered by similarity" rather than learning CanvasXpress's JSON configuration syntax or requiring programming assistance.

# Related Work

While RAG and few-shot learning are established techniques in the machine learning community, their application to scientific visualization generation represents a novel domain. Standard RAG implementations typically focus on question-answering or text generation tasks, whereas our system applies these techniques to generate structured JSON configurations for interactive visualizations. Our approach differs from typical RAG systems in using guided autocomplete to automatically generate high-quality synthetic examples at scale, avoiding laborious manual curation characterizing most few-shot learning applications.

Regarding visualization tools, most existing libraries present significant challenges for LLM-based generation. D3.js requires complex DOM manipulation code, ggplot2 uses sequential function calls that must be executed in specific orders, and Matplotlib relies on procedural plotting commands. These approaches require generating syntactically correct, executable code rather than declarative configurations. In contrast, CanvasXpress's JSON-based declarative approach creates more natural targets for LLM generation, as the system handles missing parameters gracefully and provides meaningful defaults.

Our integration of guided autocomplete with LLM-based generation creates a complementary system where users can choose between perfect accuracy (via guided autocomplete) and flexibility (via free-form LLM generation). This hybrid approach addresses precision requirements of scientific visualization while maintaining accessibility benefits of natural language interfaces.

# User Interface

We integrated the CoPilot and LLM generation UI into every CanvasXpress visualization, making it the first standalone JavaScript library to leverage AI on the client side. A JSONP call ensures fast and reliable access to the canvasxpress.org server, with only the prompt, model parameters, and dataset headers being sent to minimize IO load. Alternatively, users can implement their own service, as we provide necessary code to create CanvasXpress visualizations.

The system is implemented as a professional Python package with modular architecture, featuring comprehensive automated testing with over 85 unit and integration tests that validate both real API functionality and graceful fallback to mock responses when external services are unavailable. This ensures the system works reliably across different deployment environments, from development to production, and provides confidence in system reliability for research applications.

![Accuracy results for different datasets showing accuracy as number of few shots increases.\label{fig:table}](four_six_ten_results.png)

![Current web UI for CanvasXpress LLM generation working as a chatbot for continual visualization description and updates.\label{fig:UI}](CX_chat_ui.png)

![Overview of how the Copilot/guided autocomplete works.\label{fig:guided_autocomplete}](GuidedAutocompleteFig.png)

# References