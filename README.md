# canvasxpress_gen
Generating CanvasXpress visualizations from natural language descriptions of them using LLMs

# Introduction

The code in this repository can be used to conversationally generate CanvasXpress visualizations, i.e. a user can simply describe in plain English the graph they want (e.g. "box plot of len on x axis grouped by dose with title "len by dose"), upload a CSV or tab-delimited data file (with a header describing and naming the columns), and then have their desired graph created automatically with high accuracy using LLMs. In this repo we provide a simple chat-like UI that you can use to test out the system, and the functionality is also built directly into [CanvasXpress](https://www.canvasxpress.org/llm.html).
