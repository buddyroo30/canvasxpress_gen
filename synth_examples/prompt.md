### Instructions:
CanvasXpress (http://canvasxpress.org) is a Javascript library for data analytics and visualization. People can use it to generate visualizations such as bar graphs, box plots, pie charts and other graph types by creating JSON data structures specifying the configuration and data for the visualizations. CanvasXpress creates the visualizations using the HTML5 canvas element. Your task is to take an English language description of a CanvasXpress visualization configuration specification as well as the headers or column names for the data to be visualized and convert that into a valid JSON-format specification of the configuration. Note that you will not be given the full data for the visualization (which can be quite large) but you will be given the headers or names of the columns for the data: the data to graph is in the format of a two dimensional array (array of arrays in JSON) where the first array will give the headers or names of the columns and the subsequent arrays will contain the actual data to graph, for example: [['column name 1','column name 2','column name 3'....,'column name N'],['row 1 value for column name 1', 'row 1 value for column name 2','row 1 value for column name 3',....,'row 1 value for column name N'],['row 2 value for column name 1', 'row 2 value for column name 2','row 2 value for column name 3',....,'row 2 value for column name N']...] So in addition to the English language description of a CanvasXpress visualization configuration specification you will be provided the headers or names of the columns of the data, but not the actual data to graph. Some fields in the configuration will reference these headers or column names, for example fields groupingFactors, dataTableColHide, and dataTableColOrder.

To help you in this task you are provided detailed information about the valid fields used in a CanvasXpress JSON configuration specification: name, description, type (string, boolean, int, etc.), list of all possible values for fields that can only take one from a pre-specified list of values, and default value (i.e. the value used when the user doesn't provide an explicit value for the field). You will also be given examples of English language text describing CanvasXpress configurations along with the headers or column names of the data to be graphed, and the corresponding CanvasXpress JSON-format configurations for these.

### Adhere to these rules:
-Carefully review the English description of a CanvasXpress configuration, including the headers or column names of the data to be visualized, as well as the detailed field information and examples. Analyze each element thoroughly to provide an accurate and well-informed response to the question.
-Avoid providing incorrect responses. If generating a CanvasXpress JSON configuration based on the provided English text and headers/column names is not possible, simply return an empty string ('') without any response.
-Use only the valid fields listed for generating CanvasXpress JSON configurations. The approved fields are outlined below, and you must strictly select from these options. Do not invent or include any invalid field names.
-Ensure accuracy by filtering out incorrect responses. Perform basic validation on your generated CanvasXpress JSON configurations to identify potential errors, such as referencing field names that do not exist in the provided valid field information. If errors are detected, either correct them or return an empty string ('') without providing a response.
-Provide only valid JSON as the output—nothing else. Avoid including backticks, the word "JSON," or any other unnecessary text. The returned content must strictly adhere to the format of properly structured CanvasXpress configuration JSON.
-Choose only from the valid options for "graphType".
-If the JSON configuration includes only an "xAxis", use "setMaxX" or "setMinX". 
-Avoid using "setMaxY" if a "yAxis" is not defined in the configuration. Instead, always opt for "setMaxX", regardless of the graph's orientation.
-Avoid using "setMinY" if the JSON configuration lacks a "yAxis". Instead, use "setMinX" regardless of the graph’s orientation.
-Always set "guess" as the first parameter when adding "filterData" to the JSON configuration.
-In the JSON configuration, ensure the third parameter of "filterData" is always set to either "like" or "different." Avoid using any other value.
-The JSON configuration for "decorations" should never include "orientation" as a parameter.
-The JSON configuration for "decorations" should never include "width" as a parameter.
-The JSON configuration for "decorations" should never include "type" as a parameter.
-Always use scalar values for the "x," "y," and "value" keys in the "decorations" object. Arrays should never be assigned to these keys.
-Ensure the "value" key in the "decorations" object always contains a single scalar value.
-Ensure the "x" key in the "decorations" object always contains a single scalar value.
-Ensure the "y" key in the "decorations" object always contains a single scalar value.
-Include only one key—either "x", "y", or "value"—within the "decorations" object, not multiple keys simultaneously.
-If the "x" key is present in the "decorations" object, exclude the "y" and "value" keys from the JSON configuration.
-If the "y" key is present in the "decorations" object, exclude the "x" and "value" keys from the JSON configuration.
-If the "decorations" object contains the "value" key, exclude the "x" and "y" keys from the JSON configuration.
-When specifying both "xAxis" and "yAxis" in the JSON configuration, always list "xAxis" before "yAxis" for consistency.
-When using a JSON configuration with decorations and the "graphType" set to "Bin", "Binplot", "CDF", "Contour", "Density", "Hex", "Hexplot", "Histogram", "KaplanMeier", "QQ", "Quantile", "Ridgeline", "Scatter2D", "ScatterBubble2D", or "Streamgraph", avoid including "value" in the configuration. Instead, always specify either "x" or "y" for proper functionality.
-When "decorations" are included in the JSON configuration, never include "x" if the "graphType" is one of the following: "Area", "AreaLine", "Bar", "BarLine", "Boxplot", "DotLine", "Dotplot", "Heatmap", "Line", "Lollipop", "Pareto", "Stacked", "StackedLine", "StackedPercent", "StackedPercentLine", "Violin", or "Waterfall". Instead, always include "value".
-When "decorations" are specified in the JSON configuration and the "graphType" is one of the following: "Area", "AreaLine", "Bar", "BarLine", "Boxplot", "DotLine", "Dotplot", "Heatmap", "Line", "Lollipop", "Pareto", "Stacked", "StackedLine", "StackedPercent", "StackedPercentLine", "Violin", or "Waterfall" the "y" parameter should never be included. Instead, always include the "value" parameter.
-Do not sort the data when the "graphType" is one of the following: "Bin", "Binplot", "CDF", "Contour", "Density", "Hex", "Hexplot", "Histogram", "KaplanMeier", "QQ", "Quantile", "Ridgeline", "Scatter2D", "ScatterBubble2D", or "Streamgraph".
-Under "decorations," be sure to specify the "type" and include an array value beneath it. For instance, the following is CORRECT: "decorations": __LCB__ "line": [ __LCB__ "value": 10, "color": "black" __RCB__ ] __RCB__. However, this is INCORRECT: "decorations": __LCB__ "value": 10, "color": "black" __RCB__.
-If the description has "color scheme" use the colorScheme parameter in the JSON configuration.
-Only use VALID "colorScheme" values! For instance, "Solarized" is ACCEPTABLE, while "SolarizedBase" is NOT.
-When using the "Ridgeline" "graphType", avoid including the "groupingFactors" configuration. Instead, use "ridgeBy". For example, specifying "ridgeBy": "column name" is the CORRECT approach, while "groupingFactors": ["column name"] is INCORRECT.
-Avoid including the "xAxis2" configuration when the "graphType" is set to "Ridgeline". However, if the "graphType" contains a hyphen or ends with "Line" you must define both "xAxis" and "xAxis2".
-Avoid grouping all columns under "xAxis" if the "graphType" includes a hyphen or ends with "Line." For instance, if the "graphType" is "DotLine", "AreaLine", "BarLine", "StackedLine", or "StackedPercentLine", ensure both "xAxis" and "xAxis2" are included. For instance, the format "xAxis": ["column name 1"], "xAxis2": ["column name 2"] is CORRECT, whereas "xAxis": ["column name 1", "column name 2"] is INCORRECT.
-When using the "Contour" "graphType", always include "xAxis" and "yAxis" in the JSON configuration. For example, the format "xAxis": ["column name 1"], "yAxis": ["column name 2"] is CORRECT, whereas "xAxis": ["column name 1", "column name 2"] is INCORRECT.
-When using the "Contour" "graphType", the first column name should be assigned to the "xAxis" and the second column name should be assigned to the "yAxis".

### Input:
Generate a CanvasXpress JSON configuration for the given English text: '{canvasxpress_config_english}', having headers or column names for the data to visualize: '{headers_column_names}'.
Return only the CanvasXpress JSON configuration.
{schema_info}
### Below are examples of descriptive English texts, headers/column names and their corresponding CanvasXpress JSON configurations
{few_shot_examples}

### Response:
Based on your instructions, here is the CanvasXpress JSON configuration I have generated for the given English text '{canvasxpress_config_english}', having headers or column names for the data to visualize '{headers_column_names}':
```sql
