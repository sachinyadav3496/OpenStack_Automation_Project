"""
    Module execute_openstack_commands

        used to execute 
        Server Group Create Commands
        Network Port Create Commands
        Volume Create Commands

        on openstack jump server!
"""
import json 
import subprocess
import sys

#######################################################
# Global Variables
COMMAND_FILE_PATH = "openstack_commands.json"
OUTPUT_FILE_PATH = "server_group_port_volume_ids.json"
#######################################################

def create_server_groups(commands):
    """
        This Function Will Create Server Groups with their respective
        Policies and returns a dictionary containig all Server Group Ids
    """
    server_group_ids = {}
    for group in commands:
        keys = list(group.keys())
        # Creating a Server Group
        try: 
            status, output = subprocess.getstatusoutput(group["create"])
            if status==0:
                status, id_ = subprocess.getstatusoutput(group[keys[1]])
                if status == 0:
                    server_group_ids[keys[1]] = id_
                else:
                    sys.stderr.write(f"!Error!unable to get port id of {keys[1]} due to {id_}\n")
            else:
                sys.stderr.write(f"!Error! Creating server Group {keys[1]}\n")
                sys.stderr.write(f"!Error Code! {output}")
        except Exception as error:
            sys.stderr.write(f"!Error to Create Server Group {keys[1]}!\n")
            sys.stderr.write(f"!Error code! {error}")      
    return server_group_ids

def create_ports_volumes(commands):
    """
        Creates Openstack Ports and Volumes by given commands
    """
    result = {}
    for obj in commands:
        idx = list(obj.keys())[0]
        cmd_dict = obj[idx]
        # Create Network Ports 
        port_ids = {}
        volume_ids = {}
        for ports in cmd_dict["port_create"]:
            try:
                keys = list(ports.keys())
                port_name = keys[-1]
                status, output = subprocess.getstatusoutput(ports["create"])
                if status == 0:
                    status, id_ = subprocess.getstatusoutput(ports[port_name])
                    if status == 0:
                        port_ids[port_name]=id_
                    else:
                        sys.stderr.write(f"!Error!Unable to Create port {port_name} Due to {id_}\n")
                else: 
                    sys.stderr.write(f"!Error!Unable to Create port {port_name} Due to {output}\n")
            except Exception as error:
                sys.stderr.write(f"!Error!Unable to Create port {port_name} Due to {error}\n")
    
        for volumes in cmd_dict["volume_create"]:
            try:
                keys = list(volumes.keys())
                vol_name = keys[-1]
                status, output = subprocess.getstatusoutput(volumes["create"])
                if status==0:
                    status, id_ = subprocess.getstatusoutput(volumes[vol_name])
                    if status==0:
                        volume_ids[vol_name] = id_
                    else:
                        sys.stderr.write(f"!Error! Unable to Create Volume {vol_name} due to {id_}\n")
                else:
                    sys.stderr.write(f"!Error! Unable to Create Volume {vol_name} due to {output}\n")
            except Exception as error:
                sys.stderr.write(f"!Error! Unable to Create Volume {vol_name} due to {error}\n")
        
        result[idx] = {
            "port_ids": port_ids,
            "volume_ids": volume_ids,
        }
    return result


if __name__ == "__main__":
    """
        Program Starts From Here
    """
    ###########################################
    # loading all commands from a JSON File
    with open(COMMAND_FILE_PATH) as file:
        commands = json.load(file)
        file.close()
    #print(commands.keys())
    ##########################################
    # Creating Server Groups 
    server_group_ids = create_server_groups(commands["server_group_commands"])
    ###########################################
    # Creating Network Ports and Volumes
    port_volume_ids = create_ports_volumes(commands["instance_commands"])
    ###########################################
    # saving ouput ids to JSON Files 
    final_data = {
        "server_group_ids": server_group_ids,
        "port_volume_ids": port_volume_ids
    }
    
    with open(OUTPUT_FILE_PATH, "w") as file:
        json.dump(final_data, file)
        file.close()
