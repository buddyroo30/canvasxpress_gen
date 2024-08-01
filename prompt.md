### Instructions:
CanvasXpress (http://canvasxpress.org) is a Javascript library for data analytics and visualization. People can use it to generate visualizations such as bar graphs, box plots, pie charts and other graph types by creating JSON data structures specifying the configuration and data for the visualizations. CanvasXpress creates the visualizations using the HTML5 canvas element. Your task is to take an English language description of a CanvasXpress visualization configuration specification as well as the headers or column names for the data to be visualized and convert that into a valid JSON-format specification of the configuration. Note that you will not be given the full data for the visualization (which can be quite large) but you will be given the headers or names of the columns for the data: the data to graph is in the format of a two dimensional array (array of arrays in JSON) where the first array will give the headers or names of the columns and the subsequent arrays will contain the actual data to graph, for example: [['column name 1','column name 2','column name 3'....,'column name N'],['row 1 value for column name 1', 'row 1 value for column name 2','row 1 value for column name 3',....,'row 1 value for column name N'],['row 2 value for column name 1', 'row 2 value for column name 2','row 2 value for column name 3',....,'row 2 value for column name N']...] So in addition to the English language description of a CanvasXpress visualization configuration specification you will be provided the headers or names of the columns of the data, but not the actual data to graph. Some fields in the configuration will reference these headers or column names, for example fields groupingFactors, dataTableColHide, and dataTableColOrder.

To help you in this task you are provided detailed information about the valid fields used in a CanvasXpress JSON configuration specification: name, description, type (string, boolean, int, etc.), list of all possible values for fields that can only take one from a pre-specified list of values, and default value (i.e. the value used when the user doesn't provide an explicit value for the field). You will also be given examples of English language text describing CanvasXpress configurations along with the headers or column names of the data to be graphed, and the corresponding CanvasXpress JSON-format configurations for these.

Adhere to these rules:
- **Deliberately go through the English text describing a CanvasXpress configuration, the headers or columns names of the data to be visualized, and the detailed valid field information and examples word by word** to appropriately answer the question.
- **Do not give incorrect responses**. If you cannot generate a CanvasXpress JSON configuration for the given English text and headers/column names, then do not return a response (i.e. simply return empty string '').
- **Filter out incorrect responses**. Do basic checks on your generated CanvasXpress JSON configuration for errors, for example check if field names are used that are not present in the given valid field information. If you find errors either correct them or do not return a response (i.e. simply return empty string '').
- **Very very important, return only JSON, do not return anything else!!!** Do not return 3 backticks, or the word json, or any other extraneous text, simply return the generated CanvasXpress configuration JSON.

### Input:
Generate a CanvasXpress JSON configuration for the given English text: '{canvasxpress_config_english}', having headers or column names for the data to visualize: '{headers_column_names}'.
Return only the CanvasXpress JSON configuration.
{schema_info}
### Below are examples of descriptive English texts, headers/column names and their corresponding CanvasXpress JSON configurations
{few_shot_examples}

### Response:
Based on your instructions, here is the CanvasXpress JSON configuration I have generated for the given English text '{canvasxpress_config_english}', having headers or column names for the data to visualize '{headers_column_names}':
```sql
