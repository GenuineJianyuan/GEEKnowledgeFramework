from geonames_processer import extract_spatial_coordinates,call_geonames_api_by_name
import json
import pandas as pd

def read_content_from_txt(filename):  
    with open(filename, 'r',encoding='utf-8-sig') as file:  
        code = file.read()  
    return code

def execute_prompt_with_strategies(code_path, theme_dir_path, llm = None):
    if llm is None:
        print("Set up the LLM before executing!")
        return
    code=read_content_from_txt(code_path)
    GCMDtheme=read_content_from_txt(theme_dir_path)

    prompt_template = """
    You are designed to be a professional GEE developer and GIS expert. Your goal is to extract 
    the required information from the given GEE workflow script according to the requirements. 
    The script to be processed is as follows:
    """+str(code)+"""
    The specific requirements are as follows:

    1. You are required to 1)  give a code summarization of this scripts in **less than 100 words.** 
    The summary must describe clearly what is the purpose for this model and what are the outputs from this model? and
    2) According to the summary in 1), select a keyword from the list provided that matches the theme of the script.
    
    The list is as follows:
    """+str(GCMDtheme)+"""
    Only one keyword should be output, in the format {"output":"code summarization", "task":"Agriculture"}. 
    If it's not possible to determine, the value should be Others, and the output should be {"task":"Others"} instead of {"task": "None"}

    2. Output the time range involved in the script, in the format {"start":"YYYY-MM-DD","end":"YYYY-MM-DD"}. 
    If it's not possible to determine, the value should be None, i.e., {"start": "None", "end": "None"};

    3. Output the geographic location involved in the script, either as a list of place names or geographic ranges. 
    If it's place names, the list should contain the names as strings, for example, {"geo-location":["Wuhan","Beijing"]}, just contain place name exactly without scope such as "County, Province, County". 
    If it's coordinates, the list should contain the bounding rectangle, for example, {"geo-location":[[xmin,ymin,xmax,ymax]]} or {"geo-location":[[xpoint,ypoint]]}.
    If it's not possible to determine, the value should be None, i.e., {"geo-location": ["None"]};

    4. Output the data sources involved in the script, for example, {"datasource":["LANDSAT/LC08/C01/T1_TOA","users/zzy2019110165/songhuajiangliuyu"]}. 
    If it's not possible to determine, the value should be None, i.e., {"datasource": ["None"]};

    5. Your response should be concise and clear, only containing the combination of required content in a list in JSON format, 
    like the following example:
    [{"task":"Agriculture","output":"code summarization"},{"start":"YYYY-MM-DD","end":"YYYY-MM-DD"},{"geo-location":"Wuhan;Beijing"},
    {"datasource":["LANDSAT/LC08/C01/T1_TOA","users/zzy2019110165/songhuajiangliuyu"]}]
            
    6. Remember! Do not include any content other than the required response in your reply. Keep the format exactly as the example:
    .
    """

    prompt_template2="""
    Check if previous response is a list where each element is in JSON format.
    If it is, response True, otherwise response False, and reply what the previous response is.
    Remember! Do not include any content other than the required response in your reply. 
    ```The previous response'''
    {}
    """

    prompt_template3=\
    "An exception occurred: current response is not entirely in JSON format, redo the follow query"+ \
        prompt_template


    limited_times=5
    current=0
    current_template=prompt_template
    result=None
    current_response=None
    while current<limited_times:
        current_response=llm.predict(current_template)
        # print(current_response)
        next_response=llm.predict(prompt_template2.format(current_response))
        print(next_response)
        if "True" in next_response:
            result=current_response
            break
        else:
            print("Wait to generate")
            # print("Current response is:")
            # print(current_response)
            current=current+1
            current_template=prompt_template3

    if current==limited_times:
        print("Exceed maximum times")
    if result is None:
        print("Failed to generate")
    else:
        print("Find correct response")
        # print(result)
    return result

def generate_fact_info_with_geonames(result,username):
    data_list = json.loads(result)

    combined_dict = {}

    for item in data_list:
        combined_dict.update(item)

    geonames = []
    location_info = combined_dict["geo-location"]
    for location in location_info:
        # print(f'Find standard geo-name for {location}')
        coordinates = extract_spatial_coordinates(location)
        if coordinates is None:
            info = call_geonames_api_by_name(location, username)
            if info is not None:
                geonames.append({"content":info[1]+f"(geonameId={info[0]})","reference":"GeoNames","geospatialType":"place name"})
            else:
                geonames.append({"id":-1,"content":location,"reference":"None","geospatialType":"place name","descr":"Failed to find a name from geodatabase"})

        else:
            if 'Coordinates' in coordinates.keys():
                lat, lon = coordinates['Coordinates']
                geonames.append({"content":f"{[lat, lon]}","geospatialType":"coordinates"})
            else:
                bounds=coordinates['Bounds']
                geonames.append({"content":f"{[bounds['Min_Lat'], bounds['Max_Lat'],bounds['Min_Lon'],bounds['Max_Lon']]}","geospatialType":"coordinates"})
    combined_dict["geo-location"]=geonames
    return combined_dict

def check_datasource(combined_dict, ee_source_path=r'GEE_dataset.csv'):
    if 'datasource' not in combined_dict.keys():
        return combined_dict
    else:
        new_datasource = []
        gee_data = pd.read_csv(ee_source_path)
        # Iterate over each source in the combined_dict's datasource
        for source in combined_dict['datasource']:
            # Find rows where the Snippet contains the source as a substring
            matches = gee_data[gee_data['Snippet'].str.contains(source, na=False)]
            
            if not matches.empty:
                # If there are matches, use the Name from the first matched entry
                for _, row in matches.iterrows():
                    new_datasource.append({
                        "SourceName": row['Name'], 
                        "SourceType": "GEESource", 
                        "value": source
                    })
                    break
            else:
                # If no matches, consider it a UserSource and duplicate SourceName with source
                new_datasource.append({
                    "SourceName": source,  # Assuming the intent to repeat the source as its name
                    "SourceType": "UserSource", 
                    "value": source
                })
        
        # Update the original dictionary with the new datasource information
        combined_dict['datasource'] = new_datasource
        
        return combined_dict

def convert_fact_info_to_xml_string(combined_dict):
    # Start of the XML string
    xml_string = "<Fact>\n"

    # Adding TemporalRange
    xml_string += "    <TemporalRange>\n"
    xml_string += f"        <StartTime>{combined_dict['start']}</StartTime>\n"
    xml_string += f"        <EndTime>{combined_dict['end']}</EndTime>\n"
    xml_string += "    </TemporalRange>\n"

    # Adding GeospatialRange
    for info in combined_dict['geo-location']:
        if info is None:
            continue
        if info["geospatialType"] == "place name":
            xml_string += "    <GeospatialRange>\n"
            xml_string += "        <GeospatialType>place name</GeospatialType>\n"
            xml_string += f"        <Value>{info['content']}</Value>\n"
            xml_string += f"        <Reference>{info['reference']}</Reference>\n"
            xml_string += "    </GeospatialRange>\n"
        else:
            xml_string += "    <GeospatialRange>\n"
            xml_string += "        <GeospatialType>place name</GeospatialType>\n"
            xml_string += f"        <Value type=\"list\">{info['content']}</Value>\n"
            xml_string += f"        <Coordinates>WGS84</Coordinates>\n"
            xml_string += "    </GeospatialRange>\n"

    # Adding Datasource
    xml_string += "    <Datasource>\n"
    for source in combined_dict['datasource']:
        xml_string += "        <Source>\n"
        if source["SourceType"] == 'GEESource':
            xml_string += "            <SourceType>GEESource</SourceType>\n"
        else:
            xml_string += "            <SourceType>UserSource</SourceType>\n"

        xml_string += f"            <SourceName>{source['SourceName']}</SourceName>\n"
        xml_string += f"            <Value>{source['value']}</Value>\n"
        xml_string += "        </Source>\n"
    xml_string += "    </Datasource>\n"

    # Adding Task
    xml_string += "    <Task>\n"
    xml_string += "        <TaskType>GCMD Keywords</TaskType>\n"
    xml_string += f"        <Value>{combined_dict['task']}</Value>\n"
    xml_string += f"        <Description>{combined_dict['output']}</Description>\n"
    xml_string += "    </Task>\n"

    # Closing the Fact tag
    xml_string += "</Fact>\n"
    return xml_string

def generate_fact_info(script_path, theme_path, fact_xml_save_path, datasource_path, llm = None):
    
    result = execute_prompt_with_strategies(script_path, theme_path,llm=llm)

    if result is not None:
        fact_info = generate_fact_info_with_geonames(result,username='genuinne')
 
        fact_info = check_datasource(fact_info, datasource_path)
        fact_xml_str=convert_fact_info_to_xml_string(fact_info)
        with open(fact_xml_save_path, 'w',encoding='utf-8') as file:
            file.write(fact_xml_str)
        print(f"Succeed to save factual descriptionfor script at {fact_xml_save_path}")
        return True
    else:
        print("Fail to generate response from LLM, try again!")
        return False



    

