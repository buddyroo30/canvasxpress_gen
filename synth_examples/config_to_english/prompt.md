### Instructions:
CanvasXpress (http://canvasxpress.org) is a Javascript library for data analytics and visualization. People can use it to generate visualizations such as bar graphs, box plots, pie charts and other graph types by creating JSON data structures specifying the configuration and data for the visualizations. CanvasXpress creates the visualizations using the HTML5 canvas element. Your task is to take a JSON specification of the configuration and data of a CanvasXpress visualization and convert that into a corresponding English text that describes the JSON specification in plain English. To help you in this task you are provided detailed information about the legal fields used in a CanvasXpress JSON configuration specification: name, description, type (string, boolean, int, etc.), list of all possible values for fields that can only take one from a pre-specified list of values, and default value (i.e. the value used when the user doesn't provide an explicit value for the field). You will also be given examples of CanvasXpress JSON configurations and data and their corresponding English text that describes the configurations. Note that you will not be given the full data for the visualization (which can be quite large) but you will be given the headers or names of the columns for the data: the data to graph is in the format of a two dimensional array (array of arrays in JSON) where the first array will give the headers or names of the columns and the subsequent arrays will contain the actual data to graph, for example: [['column name 1','column name 2','column name 3'....,'column name N'],['row 1 value for column name 1', 'row 1 value for column name 2','row 1 value for column name 3',....,'row 1 value for column name N'],['row 2 value for column name 1', 'row 2 value for column name 2','row 2 value for column name 3',....,'row 2 value for column name N']...] So you will be provided the headers or names of the columns but not the actual data to graph. Some fields in the configuration will reference these headers or column names, for example fields groupingFactors, dataTableColHide, and dataTableColOrder.

Adhere to these rules:
- **Deliberately go through the CanvasXpress JSON configuration and the detailed legal field information and examples word by word** to appropriately answer the question.
- **Do not give incorrect responses**. If you cannot generate an English text for the given CanvasXpress JSON configuration, then do not return a response (i.e. simply return empty string '').
- **Filter out incorrect responses**. Do basic checks on your generated English text for errors, for example if the English text references terms not present in the given legal field information. If you find such errors do not return a response (i.e. simply return empty string '').

### Input:
Generate English text that describes the CanvasXpress JSON configuration and data: {canvasxpress_config}.
Return only the English text.
{schema_info}
### Below are examples of canvasXpress JSON configurations and their corresponding descriptive English text
{few_shot_examples}

### Response:
Based on your instructions, here is the English text I have generated that describes the CanvasXpress JSON configuration and data {canvasxpress_config}:
```sql
