"""
    Module generate vm config file

        Used to Create a new vm config file using
        a json files which contains server group ids,
        volume ids, and network ports
"""
#################################################
# loading libraries
import pandas as pd
import json
import datetime
import os
################################################

# EXCEL FILE NAME and SHEET Name
FILENAME = "VNF-Package-Template.xlsm"
GLOBAL_SHEET_NAME = "Global-configuration"
VM_CONFIG_SHEET_NAME = "VM-configuration"
PACKAGE_NAME = "VCP-Package-Configuration"
JSON_FILE_PATH =  "server_group_port_volume_ids.json"
OUTPUT_FILE_PATH = "VNF-Package-Template.xlsx"
################################################


def update_excel_sheet(df, result):
    """
        update server group id, volume id, and ports
        also save this update new config file
    """
    # updating network ports, volume ids and group ids 
    groups = result["server_group_ids"]
    for i in df.index:
        key = str(i)
        if key in result["port_volume_ids"]:
            entry = False
            value = result["port_volume_ids"][key]
            for port_name, port_id in value["port_ids"].items():
                df.loc[i, port_name] = port_id
                entry = True
            for vol_name, vol_id in value["volume_ids"].items():
                df.loc[i, vol_name] = vol_id
                entry = True
            if entry:
                # server_group_name
                group_name = df.loc[i, "server_group_name"]
                group_id = groups.get(group_name)
                if group_id:
                    df.loc[i, "server_group"] = group_id
    return df

if __name__ == "__main__":
    # execution of script will start from here
    #################################################
    # Reading Global Config and VM Config Files 
    df = pd.read_excel(FILENAME,
        sheet_name=VM_CONFIG_SHEET_NAME)
    global_df = pd.read_excel(FILENAME,
        sheet_name=GLOBAL_SHEET_NAME)
    package_df = pd.read_excel(FILENAME,
        sheet_name=PACKAGE_NAME)
    ##################################################
    # Reading Result JSON File
    with open(JSON_FILE_PATH) as file:
        result = json.load(file)
        file.close()
    #################################################
    # Getting Updated Output
    result_df = update_excel_sheet(df, result)
    ################################################
    # Saving New Output to New Directory
    site_name = global_df[global_df["network-variables"]=="site_name"]["public_EDN"].iloc[0]
    tenant_name = global_df[global_df["network-variables"]=="tenant_name"]["public_EDN"].iloc[0]
    dir_name = datetime.datetime.strftime(datetime.datetime.now(), "%d_%m_%Y")
    OUTPUT_DIR_PATH = os.path.join(site_name, tenant_name, dir_name) 
    if not os.path.exists(OUTPUT_DIR_PATH):
        os.makedirs(OUTPUT_DIR_PATH)
    PATH = os.path.join(OUTPUT_DIR_PATH, OUTPUT_FILE_PATH)
    with pd.ExcelWriter(PATH) as writer:
        package_df.to_excel(writer, sheet_name=PACKAGE_NAME, index=False)
        global_df.to_excel(writer, sheet_name=GLOBAL_SHEET_NAME, index=False)
        result_df.to_excel(writer, sheet_name=VM_CONFIG_SHEET_NAME, index=False)
    ################################################
    print(f"!Result Sucessfully Written in {OUTPUT_FILE_PATH}")
    ################################################
    
