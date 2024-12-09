### Instructions:
CanvasXpress (http://canvasxpress.org) is a Javascript library for data analytics and visualization. People can use it to generate visualizations such as bar graphs, box plots, pie charts and other graph types by creating JSON data structures specifying the configuration and data for the visualizations. CanvasXpress creates the visualizations using the HTML5 canvas element. Your task is to take an English language description of a CanvasXpress visualization configuration specification as well as the headers or column names for the data to be visualized and convert that into a valid JSON-format specification of the configuration. Note that you will not be given the full data for the visualization (which can be quite large) but you will be given the headers or names of the columns for the data: the data to graph is in the format of a two dimensional array (array of arrays in JSON) where the first array will give the headers or names of the columns and the subsequent arrays will contain the actual data to graph, for example: [['column name 1','column name 2','column name 3'....,'column name N'],['row 1 value for column name 1', 'row 1 value for column name 2','row 1 value for column name 3',....,'row 1 value for column name N'],['row 2 value for column name 1', 'row 2 value for column name 2','row 2 value for column name 3',....,'row 2 value for column name N']...] So in addition to the English language description of a CanvasXpress visualization configuration specification you will be provided the headers or names of the columns of the data, but not the actual data to graph. Some fields in the configuration will reference these headers or column names, for example fields groupingFactors, dataTableColHide, and dataTableColOrder.

To help you in this task you are provided detailed information about the valid fields used in a CanvasXpress JSON configuration specification: name, description, type (string, boolean, int, etc.), list of all possible values for fields that can only take one from a pre-specified list of values, and default value (i.e. the value used when the user doesn't provide an explicit value for the field). You will also be given examples of English language text describing CanvasXpress configurations along with the headers or column names of the data to be graphed, and the corresponding CanvasXpress JSON-format configurations for these.

Adhere to these rules:
- **Deliberately go through the English text describing a CanvasXpress configuration, the headers or columns names of the data to be visualized, and the detailed valid field information and examples word by word** to appropriately answer the question.
- **Do not give incorrect responses**. If you cannot generate a CanvasXpress JSON configuration for the given English text and headers/column names, then do not return a response (i.e. simply return empty string '').
- **Only use valid fields in the JSON you generate!!** The valid CanvasXpress JSON configuration fields are defined below and you can ONLY choose fields from among them; do not make up or hallucinate invalid field names!
- **Filter out incorrect responses**. Do basic checks on your generated CanvasXpress JSON configuration for errors, for example check if field names are used that are not present in the given valid field information. If you find errors either correct them or do not return a response (i.e. simply return empty string '').
- **Very very important, return only JSON, do not return anything else!!!** Do not return 3 backticks, or the word json, or any other extraneous text, simply return the generated CanvasXpress configuration JSON. What you return must be valid JSON.
- **Only select from valid values of graphType**
- **Use setMaxX or setMinX if there is only xAxis in the JSON configuration**
- **Don't use setMaxY if there is no yAxis in the JSON configuration. Use setMaxX instead despite the orientation of the graph.**
- **Don't use setMinY if there is no yAxis in the JSON configuration. Use setMinX instead despite the orientation of the graph.**
- **Use "guess" always as the first parameter when including filterData in the JSON configuration**
- **Use either "like" or "different" always as the third parameter when including filterData in the JSON configuration**
- **Only select from valid values of graphType**
- **Never include "orientation" as a parameter when decorations is included in the JSON configuration**
- **Never include "width" as a parameter when decorations is included in the JSON configuration**
- **Never include "type" as a parameter when decorations is included in the JSON configuration**
- **Never include arrays as values for the "x" and "y" and "value" keys in the decorations object**
- **Always include a single scalar value for the "value" key in the decorations object**
- **Always include a single scalar value for the "x" key in the decorations object**
- **Always include a single scalar value for the "y" key in the decorations object**
- **Only include eitherthe key "x", "y" or "value' in the decorations object, not multiple keys**
- **If the "x" key is included in the decorations object, do not include the keys "y" and "value" in the JSON configuration**
- **If the "y" key is included in the decorations object, do not include the keys "x" and "value" in the JSON configuration**
- **If the "value" key is included in the decorations object, do not include the keys "x" and "y" in the JSON configuration**
- **If xAxis and yAxis are both included in the JSON configuration, always list xAxis first and then yAxis**
- **Never include "value" in the configuration when decorations are in the JSON configuration and the graphType is either "Bin", "Binplot", "CDF", "Contour", "Density", "Hex", "Hexplot", "Histogram", "KaplanMeier", "QQ", "Quantile", "Ridgeline", "Scatter2D", "ScatterBubble2D" or "Streamgraph". Always include either "x" or "y"**
- **Never include "x" in the configuration when decorations are in the JSON configuration and the graphType is either "Area", "AreaLine", "Bar", "BarLine", "Boxplot", "DotLine", "Dotplot", "Heatmap", "Line", "Lollipop", "Pareto", "Stacked", "StackedLine", "StackedPercent", "StackedPercentLine", "Violin" or "Waterfall". Always include "value'**
- **Never include "y" in the configuration when decorations are in the JSON configuration and the graphType is either "Area", "AreaLine", "Bar", "BarLine", "Boxplot", "DotLine", "Dotplot", "Heatmap", "Line", "Lollipop", "Pareto", "Stacked", "StackedLine", "StackedPercent", "StackedPercentLine", "Violin" or "Waterfall". Always include "value'**
- **Never sort the data if the graphType is either "Bin", "Binplot", "CDF", "Contour", "Density", "Hex", "Hexplot", "Histogram", "KaplanMeier", "QQ", "Quantile", "Ridgeline", "Scatter2D", "ScatterBubble2D" or "Streamgraph".**
- **Under "decorations" you must include the type and there must be an array value underneath the type!** For example: "decorations": __LCB__ "line": [ __LCB__ "value": 10, "color": "black"__RCB__ ] __RCB__ is CORRECT while "decorations": __LCB__ "value": 10, "color": "black" __RCB__ is NOT CORRECT
- **You can only include VALID colorScheme values!** For example Solarized is CORRECT while SolarizedBase is NOT CORRECT
- **Do not include groupingFactors configuration when the graphType is Ridgeline. Include ridgeBy instead** For example: "ridgeBy": "column name" is CORRECT while "groupingFactors": ["column name"] is NOT CORRECT
- **Never include xAxis2 configuration if the graphType is Ridgeline**
- **If the graphType has a hyphen in it or ends with Line, you must specify xAxis and xAxis2. Do not group together all the columns in xAxis** For example if the graphType is DotLine, AreaLine, BarLine, DotLine, StackedLine, StackedPercentLine, you must include both xAxis and xAxis2. For example: "xAxis": ["column name 1"], "xAxis2": ["column name 2"] is CORRECT while "xAxis": ["column name 1", "column name 2"] is NOT CORRECT


### Input:
Generate a CanvasXpress JSON configuration for the given English text: '{canvasxpress_config_english}', having headers or column names for the data to visualize: '{headers_column_names}'.
Return only the CanvasXpress JSON configuration.
{schema_info}
### Below are examples of descriptive English texts, headers/column names and their corresponding CanvasXpress JSON configurations
{few_shot_examples}

### Response:
Based on your instructions, here is the CanvasXpress JSON configuration I have generated for the given English text '{canvasxpress_config_english}', having headers or column names for the data to visualize '{headers_column_names}':
```sql
