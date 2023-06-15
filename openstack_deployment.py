"""
    openstack_deployment Module 

        will generate commands to create network, pods, and server groups
        also updates their status to Config File Back
"""
################################################
# prerequisites
# python3 -m pip install pandas
# python3 -m pip install pip install xlrd==1.2.0
################################################

################################################
# Libraries used in this module
import pandas as pd
import os
import sys
import json
import re
################################################

################################################
# EXCEL FILE NAME and SHEET Name
FILENAME = "VNF-Package-Template.xlsm"
GLOBAL_SHEET_NAME = "Global-configuration"
VM_CONFIG_SHEET_NAME = "VM-configuration"
COMMAND_OUPUT_FILE = "openstack_commands.json"
################################################




def get_network_parameters(key, data):
    """
        This Functions Returns effecitive network parameters
        from a given record data
    """
    result = {}
    if (key in data) and not pd.isna(data[key]):
            name = key[:-3]
            ip = data[key]
            if ('v4' in name) or ('v6' in name):
                name = name[:-2]
            network_id = global_df[global_df["network-variables"]=="network_id"][name].iloc[0]
            if 'v4' in key:
                subnet = global_df[global_df["network-variables"]=="network_subnet_v4_id"][name].iloc[0]
            elif ('ss7' in key.lower()) or ('private' in key.lower()):
                subnet = global_df[global_df["network-variables"]=="network_subnet_v4_id"][name].iloc[0]
            else:
                subnet = global_df[global_df["network-variables"]=="network_subnet_v6_id"][name].iloc[0]
            if 'ss7' in name.lower():
                # public_SS7_1
                port_name = data["name"]+"_".join(name.split("_")[-2:]).lower()
            else:
                port_name = data["name"]+name.split("_")[-1].lower()
            result["network_id"] = network_id
            result["port_name"] = port_name
            result["subnet"] = subnet
            result["ip-address"] = ip
    return result

def get_create_port_command(result1, result2):
    """
        This Function Returns Command To Create Ports
    """
    if result1 and result2:
        command = f"openstack port create --network {result1['network_id']} {result1['port_name']} \
        --fixed-ip subnet={result1['subnet']}, ip-address={result1['ip-address']} \
        --fixed-ip subnet={result2['subnet']}, ip-address={result2['ip-address']}"
    elif result1 and not result2:
        command = f"openstack port create --network {result1['network_id']} {result1['port_name']} \
        --fixed-ip subnet={result1['subnet']}, ip-address={result1['ip-address']}"
    elif not result1 and result2:
        command = f"openstack port create --network {result2['network_id']} {result2['port_name']} \
        --fixed-ip subnet={result2['subnet']}, ip-address={result2['ip-address']}"
    else:
        command = None
    return " ".join(command.split()) if command else command

def execute_create_port_command(network_name_1, network_name_2, data, portname=None):
    result1 = get_network_parameters(network_name_1, data)
    if network_name_2:
        result2 = get_network_parameters(network_name_2, data)
    else:
        result2 = {}
    if result1:
        port_name = result1['port_name']
    elif result2:
        port_name = result2['port_name']
    else:
        port_name = None
    command = get_create_port_command(result1, result2)
    port_id_command = f"openstack port show {port_name} -f value -c id"

    if command:
        return {"create": command, portname: port_id_command}
    else:
        return None
    
def create_openstack_ports(data):
    """
        This Functions Executes Commands to Create Network
        Port in Open Stack 
    """
    commands = []
    # Command for EDN Networks
    ports = execute_create_port_command("public_EDNv4_ip", "public_EDNv6_ip",  data, portname="public_EDN_port")
    if ports:
        commands.append(ports)
    # Command for WSN Networks
    ports = execute_create_port_command("public_WSNv4_ip", "public_WSNv6_ip", data, portname="public_WSN_port")
    if ports:
        commands.append(ports)
    # Command for RAN Networks
    ports = execute_create_port_command("public_RAN_ip", None, data, portname="public_RAN_port")
    if ports:
        commands.append(ports)
    # Command for SS7_1 Networks
    ports = execute_create_port_command("public_SS7_1_ip", None, data, portname="public_SS7_1_port")
    if ports:
        commands.append(ports)
    # Command for SS7_2 Networks
    ports = execute_create_port_command("public_SS7_2_ip", None, data, portname="public_SS7_2_port")
    if ports:
        commands.append(ports)
    # Command for private Networks
    ports = execute_create_port_command("private_ip", None, data, portname="private_port")
    if ports:
        commands.append(ports)
    
    return commands
    
def create_openstack_volumes(data):
    """
        used to generate volume creation commands 
    """
    hostname = data["hostname"]
    commands = []
    for key, value in data.items():
        if 'vol_size' in key.lower().strip():
            no = re.search(r"\d+$", key)
            if no is not None:
                no = no.group()
            else:
                no = ""
            vol_name = hostname+"vol"+str(no)
            name = "volume_id"+str(no)
            if not pd.isna(value):
                value = int(value)
                command = {}
                command["create"] = f"openstack volume create --size {value} {vol_name}"
                command[name] = f"openstack volume show {vol_name} -f value -c id"
                commands.append(command)
    # openstack volume create --size {size in GB} {volumename}
    # openstack volume show {volumename} -f value -c id
    return commands 

def create_server_groups(df):
    """
        Used to Create Server Groups on OpenStack Environment
    """
    # openstack server group create --policy <policy>    <name>
    commands = []
    idx = df[df["network-variables"]=="Server groups"].index[0]
    d = df.loc[idx+1:][["network-variables", "public_EDN"]]
    for name, policy in d.values:
        conds = [
            name,
            policy,
            not pd.isna(name),
            not pd.isna(policy)
        ]
        if all(conds):
            command = {
                "create": f"openstack server group create --policy {policy} {name}",
                name: f"openstack server group show {name} -f value -c id"
            }
            commands.append(command)
            #print(command)
    return commands


if __name__ == "__main__":
    # execution of script will start from here
    #################################################
    # Reading Global Config and VM Config Files 
    df = pd.read_excel(FILENAME,
        sheet_name=VM_CONFIG_SHEET_NAME)
    global_df = pd.read_excel(FILENAME,
        sheet_name=GLOBAL_SHEET_NAME)
    ##################################################
    create_group_commands = create_server_groups(global_df)
    instance_commands = []
    ###################################################
    # Generating and printing commands
    
    commands = {}
    for i in range(df.shape[0]):
        instance = df.iloc[i:i+1].values[0]
        cols = df.columns
        data = dict(zip(cols, instance))
        network_command = create_openstack_ports(data)
        volume_command = create_openstack_volumes(data)

        instance_commands.append({
            i: {
                "port_create": network_command,
                "volume_create": volume_command
                }
            })
    #########################################################
    # Saving All commands in JSON Files to be executed on server
    #########################################################
    commands = {
        "server_group_commands": create_group_commands,
        "instance_commands": instance_commands
    }
    with open(COMMAND_OUPUT_FILE, "w") as file:
        json.dump(commands, file, indent=5)
        file.close()
    print("\n\n")
    print("Commands Written Sucessfully!")
    print("\n\n")



