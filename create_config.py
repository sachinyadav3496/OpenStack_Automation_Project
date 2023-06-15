"""
    create_config module

        It is used to create yaml configuration files from given
        environment excel file

    functions:

        get_data()
            loads environment file for both global and vm configs

        get_parameter_dict()
            returns default parameter dictionary excepting from vm configs

        create_config_files()
            create YAML files for all given VM entries in environment file
"""
import sys
import os
import pandas as pd
import datetime

###############################
# Pre-requisites:
# pip3 install pandas
###############################

################################
# Global variables: Edit below as required
###############################

CONFIG_PATH = "VNF-Package-Template.xlsm"
CONFIG_SHEET_NAME = "VM-configuration"
GLOBAL_CONFIG_SHEET_NAME = "Global-configuration"
ROOT_DIR_PATH = "."


def get_data():
    """
        read environment excel file passed as argument
    """
    if len(sys.argv) == 2:
        excel_path = sys.argv[1]
    else:
        excel_path = CONFIG_PATH

    try:
        config_df = pd.read_excel(excel_path,
        sheet_name=CONFIG_SHEET_NAME)
        global_config_df = pd.read_excel(excel_path,
            sheet_name=GLOBAL_CONFIG_SHEET_NAME,
            index_col='network-variables')
    except FileNotFoundError:
        sys.stderr.write("ERROR! CHECK FILEPATH PROPERLY OR CHANGE SHEET NAMES IN SCRIPT")
        sys.exit(2)
    return config_df, global_config_df

def get_parameter_dict():
    """
        Returns Parameter Dictionaries
    """
    vm_related_parameters = {
        "name": None,
        "hostname": None,
        "flavor": None,
        "image_id": None,
        "sever_group": None,
        "volume_id": None,
        "availability_zone": None
        }

    network_port = {
        "public_EDN_port": None,
        "private_port": None,
        "public_WSN_port": None,
        "public_SS7_1_port": None,
        "public_SS7_2_port": None,
        "public_RAN_port": None
        }

    network_interface_v4 = {
        "public_EDNv4_ip": None,
        "public_WSN_ip": None,
        "public_SS7_1_ip": None,
        "public_SS7_2_ip": None
        }

    network_interface_v6 = {
        "public_EDNv6_ip": None,
        "public_WSN_ip": None,
        "public_RAN_ip": None,
        }

    private_interface = {
        "private_ip": None
        }

    routes = {
        "route_1": None,
        "route_2": None,
        "route_3": None,
        "route_4": None,
        "route_5": None
        }

    nfs_server = {
        "nfs_server": None
        }
    return (
        vm_related_parameters, network_port,
        network_interface_v4, network_interface_v6,
        private_interface, routes, nfs_server
        )

def create_config_files():
    """
        create yaml config files
    """
    config_df, global_config_df = get_data()
    cols = config_df.columns
    for row in config_df.values:
        data = dict(zip(cols, row))
        config_filename = "env"+data["VM"]+str(data["VM#"]).zfill(2)+".yml"
        path = os.path.join(OUTPUT_DIR_PATH, config_filename)
        with open(path, "w") as output_file:
            output_file.write("parameter_defaults:\n")
            output_file.write("    # Environment variables for Heat template of AMMS VM\n\n\n")
            (
            vm_related_parameters, network_port,
            network_interface_v4, network_interface_v6,
            private_interface, routes, nfs_server
            ) = get_parameter_dict()
            final_data = {}
            for key, value in data.items():
                if not pd.isna(value):
                    final_data[key] = value
            # print(final_data)
            for key in vm_related_parameters.copy():
                if key in final_data:
                    vm_related_parameters[key] = final_data[key]
                else:
                    vm_related_parameters.pop(key)

            output_file.write("\n    # VM related parameters\n")
            for key, value in vm_related_parameters.items():
                output_file.write(f"    {key}: {value}\n")
            output_file.write("\n\n")

            #print("\nvm_related_parameters\n",vm_related_parameters)
            for key in network_port.copy():
                if key in final_data:
                    network_port[key] = final_data[key]
                else:
                    network_port.pop(key)

            output_file.write("\n    # Network Port\n")
            for key, value in network_port.items():
                output_file.write(f"    {key}: {value}\n")
            output_file.write("\n\n")

            # print("\nnetwork_port\n", network_port)

            for key in network_interface_v4.copy():
                if key in final_data:
                    network_interface_v4[key] = value
                    network_name = "_".join(key.split("_")[:-1])
                    if network_name.endswith("v4"):
                        network_name = network_name[:-2]
                    network_interface_v4[network_name+"_Netmask"]=(
                        global_config_df.loc["Netmask", network_name])
                    network_interface_v4[network_name+"_GATEWAY"]=(
                        global_config_df.loc["GATEWAY", network_name])
                else:
                    network_interface_v4.pop(key)

            output_file.write("\n    # Network Interface\n")
            for key, value in network_interface_v4.items():
                output_file.write(f"    {key}: {value}\n")
            # print("\nnetwork_interface_v4\n", network_interface_v4)
            for key in network_interface_v6.copy():
                if key in final_data:
                    network_interface_v6[key] = final_data[key]
                    network_name = "_".join(key.split("_")[:-1])
                    if network_name.endswith("v6"):
                        network_name = network_name[:-2]
                    network_interface_v6[network_name+"_IPV6_DEFAULTGW"] =(
                        global_config_df.loc["IPV6_DEFAULTGW", network_name])
                else:
                    network_interface_v6.pop(key)

            for key, value in network_interface_v6.items():
                output_file.write(f"    {key}: {value}\n")
            # print("\nnetwork_interface_v6\n", network_interface_v6)

            for key in private_interface.copy():
                if key in final_data:
                    private_interface[key] = final_data[key]
                    network_name = key[:-3]
                    private_interface[network_name+"_Netmask"]=(
                        global_config_df.loc["Netmask", network_name])
                    private_interface[network_name+"_GATEWAY"]=(
                        global_config_df.loc["GATEWAY", network_name])

            for key, value in private_interface.items():
                output_file.write(f"    {key}: {value}\n")
            # print("\nprivate_interface\n",private_interface)
            for key in routes.copy():
                if key in final_data:
                    routes[key] = f'"{final_data[key]}"'
                else:
                    routes.pop(key)
            output_file.write("\n\n")
            output_file.write("\n    # Routes\n")
            for key, value in routes.items():
                output_file.write(f"    {key}: {value}\n")
            # print("\nroutes\n")
            # print(routes)
            # print("\nnfs_server\n")
            nfs_server["nfs_server"] = f'"{global_config_df.iloc[-1, 0]}"'
            output_file.write("\n\n")
            output_file.write("\n    # NFS\n")
            for key, value in nfs_server.items():
                output_file.write(f"    {key}: {value}\n")
            # print(nfs_server)
            output_file.close()
            sys.stdout.write(f"{config_filename} Written Sucessfully\n")


if __name__ == "__main__":
    try:
        global_df = pd.read_excel("VNF-Package-Template.xlsm", sheet_name="Global-configuration")
        site_name = global_df[global_df["network-variables"]=="site_name"]["public_EDN"].iloc[0]
        tenant_name = global_df[global_df["network-variables"]=="tenant_name"]["public_EDN"].iloc[0]
        dir_name = datetime.datetime.strftime(datetime.datetime.now(), "%d_%m_%Y")
        OUTPUT_DIR_PATH = os.path.join(site_name, tenant_name, dir_name) 
        if not os.path.exists(OUTPUT_DIR_PATH):
            os.makedirs(OUTPUT_DIR_PATH)
    except PermissionError:
        sys.stderr.write("ERROR: Unable to create output directory ")
        sys.stderr.write("please check if you have right permissions ")
        sys.stderr.write("to create ouput directory")
        sys.exit(2)
    create_config_files()
