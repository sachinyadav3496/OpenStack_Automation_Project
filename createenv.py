import xlrd
import csv
import yaml
import os
import datetime
from pathlib import Path
import time
import sys

###############################
# Pre-requisites:
# 1. On ansible VM:
# pip3 install pandas
# 
# 2. On NFS server:
# In /etc/exports:
# 
# /opt/Roamware/external *(rw,sync,insecure,all_squash,no_subtree_check)
# 
# 
# Do "sudo service nfs-service restart" on NFS server after adding the above.
###############################

################################
# Global variables: Edit below as required
###############################
vm_password = {
        "CBAPPTXNDB" : "ROot@123CBMTAS",
        "CBAPPTXNDBIndex" : "ROot@123CBMTAS",
        "MTAS" : "ROot@123COS",
        "CBMTASDB" : "ROot@123CBMTAS",
        "CBMTASDBIndex" : "ROot@123CBMTAS",
        "CBMTASDBBackup" : "ROot@123CBMTAS",
        "SOR" : "ROot@123SOR",
        "SORVAM" : "ROot@123SOR",
        "ODSVAM" : "ROot@123ODS",
        "DBWriter" : "ROot@123DBW",
        "CloudSIM" : "ROot@123CLDSIM",
        "TCAP" : "ROot@123TCAP",
        "GUI" : "ROot@123GUI",
        "SVMS" : "ROot@123",
        "PMMS" : "ROot@123PMMS",
        "SSTP" : "ROot@123SSTP",
        "SDRA" : "ROot@123SDRA",
        "AMMS" : "ROot@123AMMS",
        "CDMAHLRSync" : "ROot@123CDMA",
        "CSRSC" : "ROot@123RSC",
        "CSSM" : "ROot@123SM",
        "SMLP" : "ROot@123LOP",
        "GTP" : "ROot@123GTP",
        "GRI" : "ROot@123GRI"
        }
template_path = "./templates"
#template_path = "templates"
nfs_template = "./nfs_template"
nfs_tmp = "./nfs_final"
#nfs_path = "192.168.100.78:/opt/Roamware/external/"
loc = ("./VNF-Package-Template.xlsm")
if sys.argv[1] != '':
    loc =  sys.argv[1]
replacements = {}

################################
# Helper functions
###############################
def get_ip(vm):
    with open (template_path + '/env' + vm + '.yaml', 'rt') as envfile:
        contents = envfile.read()
        ip_t = contents.partition("private_ip: ")[2]
        ip = ip_t.partition("\n")[0]

    return(ip)

def prepare_inventory(vnfdetails):
    #FilePath = 'inventory.ini'
    #modifiedTime = os.path.getmtime(FilePath)

    #timeStamp =  datetime.datetime.fromtimestamp(modifiedTime).strftime("%b-%d-%y-%H:%M:%S")
    #os.rename(FilePath,FilePath+"_"+timeStamp)
    f = open("inventory.ini", "w")
    f.write("[local]\nlocalhost\t\tansible_connection=local\n\n[controller]\n\n")
    vm_det = ""
    for d in vnfdetails:
        vnf_i = "[vnf_" + d + ":children]\n"
        for vnfc in vnfdetails[d][1]:
            vnf_i += "vnfc_" + vnfc[0] + "\n"
            vnfc_i = "[vnfc_" + vnfc[0] + ":children]\n"
            for vm in vnfc[2]:
                vnfc_i += "vm_" + vm[0] + "\n"
                vm_i = "[vm_" + vm[0] + ":children]\n"
                for n in range(1, vm[2] + 1):
                    vm_i += vm[0] + str(n).zfill(2) + "\n"
                    vm_det += "[" + vm[0] + str(n).zfill(2) + "]\n"
                    vm_det += get_ip(vm[0] + str(n).zfill(2)) + "\t\tmob_hostname=" + vm[0] + str(n).zfill(2) +"\t\tansible_user=root\tansible_password=" + vm_password[vm[0]] + "\n\n"
                f.write(vm_i + "\n")
            f.write(vnfc_i + "\n")
        f.write(vnf_i + "\n")
    f.write(vm_det)
    # add index nodes entry for all cases
    f.write("[CBAPPTXNDBIndex01]\n" + get_ip("CBAPPTXNDBIndex01") + "\t\tmob_hostname=CBAPPTXNDBIndex01\t\tansible_user=root\tansible_password=" + vm_password["CBAPPTXNDBIndex"] + "\n\n")
    f.write("[CBMTASDBIndex01]\n" + get_ip("CBMTASDBIndex01") + "\t\tmob_hostname=CBMTASDBIndex01\t\tansible_user=root\tansible_password=" + vm_password["CBMTASDBIndex"] + "\n\n")
    f.close()

def rmdir(directory):
    directory = Path(directory)
    if directory.exists():
        for item in directory.iterdir():
            if item.is_dir():
                rmdir(item)
            else:
                item.unlink()
        directory.rmdir()

def prepare_groupvars(vnfdet):
    rmdir(Path("group_vars/"))
    for d in vnfdetails:
        for vnfc in vnfdetails[d][1]:
            for vm in vnfc[2]:
                for n in range(1, vm[2] + 1):
                    vm_name = vm[0] + str(n).zfill(2)
                    Path('group_vars/' + vm_name).mkdir(parents=True, exist_ok=True)
                    os.symlink(template_path + '/env' + vm_name + '.yaml', 'group_vars/' + vm_name + '/'  + vm_name + '.yaml')

def read_glb_var(sheet):
    gb = {}
    for i in range(1, 13):
        for j in range (1, 10):
            gb[sheet.cell_value(0,j) + "_" + sheet.cell_value(i, 0)] = sheet.cell_value(i, j)

    gb[sheet.cell_value(14, 0)] = sheet.cell_value(14, 1)
    replacements['%' + sheet.cell_value(14, 0).upper() + '%'] = sheet.cell_value(14, 1)
    return(gb)

def prepare_env(wb, vnfdetails):
    sheet = wb.sheet_by_index(1)
    gb = read_glb_var(sheet)
    vm_sheet = wb.sheet_by_index(2)
    num_rows = vm_sheet.nrows - 1
    num_cols = vm_sheet.ncols - 1

    for d in vnfdetails:
      for vnfc in vnfdetails[d][1]:
        for vm in vnfc[2]:
            curr_row = -1
            while curr_row <= num_rows:
                curr_row += 1
                if str(vm_sheet.cell_value(curr_row,2)).translate({ord(ch): None for ch in '0123456789'}).upper() == vm[0].upper():
                    break
            if curr_row > num_rows:
                print("Could not find configuration for " + vm[0] + ". Env file would not be created. Moving to next")
                continue
            for n in range(1, vm[2] + 1):
                loc_var = {}
                for j in range(4, num_cols + 1):
                    val = vm_sheet.cell_value( curr_row + n - 1, j)
                    loc_var[vm_sheet.cell_value(0, j)] = val
                    if val is not '': replacements['%' + vm[0] + str(n).zfill(2) + '_' + vm_sheet.cell_value(0, j) + '%'] = val

                vm_name = vm[0] + str(n).zfill(2)
                FilePath = template_path + '/env' + vm_name + '.yaml'
                #modifiedTime = os.path.getmtime(FilePath)
                #timeStamp =  datetime.datetime.fromtimestamp(modifiedTime).strftime("%b-%d-%y-%H:%M:%S")
                #os.rename(FilePath,FilePath+"_"+timeStamp)

                f = open(FilePath, "w")
                f.write('parameter_defaults:\n')
                for g in gb:
                    if vnfc[0] == "CBAppTxn" or vnfc[0] == "CEMTASCluster" or vnfc[0] == "CBMTASBackup":
                        if g.startswith('cb_'):
                            if gb[g] is not '': f.write('  ' + g[3:] + ': ' + gb[g] + '\n')
                        elif not g.startswith('public_EDNv6'):
                            if gb[g] is not '': f.write('  ' + g + ': ' + gb[g] + '\n')
                    elif not g.startswith('cb_'):
                        if gb[g] is not '': f.write('  ' + g + ': ' + gb[g] + '\n')

                for l in loc_var:
                    if loc_var[l] is not '':
                        if l.startswith("route_"):
                            f.write('  ' + l + ': "' + loc_var[l] + '"\n')
                        else:
                            f.write('  ' + l + ': ' + loc_var[l] + '\n')
                f.close()

def prepare_nfs(vnfdetails):

    rmdir(Path(nfs_tmp))
    Path(nfs_tmp).mkdir()
    #print("Mounting NFS")
    #os.system("sudo mount -o rw " + nfs_path + " " + nfs_tmp)
    print("Working on the following directories")
    for root, dirs, files in os.walk(nfs_template):
        structure = os.path.join(nfs_tmp, os.path.relpath(root, nfs_template))
        print(structure)
        if not os.path.isdir(structure):
            os.mkdir(structure)
        for name in files:
            file_path = root + os.sep + name
            file_edit = os.path.relpath(file_path, nfs_template)
            out_file = nfs_tmp + os.sep + file_edit
            try:
                with open(file_path) as infile, open(out_file, 'w') as outfile:
                    for line in infile:
                        for src, target in replacements.items():
                            line = line.replace(src, target)
                        outfile.write(line)
                    infile.close()
                    outfile.close()
                    os.chmod(out_file, os.stat(file_path).st_mode)
            except UnicodeDecodeError:
                print("Skipping..." + file_path)
                pass
            except PermissionError:
                print("Skipping..." + file_path)
                pass
    #print("Unmounting NFS")
    #os.system("sudo umount " + nfs_tmp)


################################
# Main code starts
###############################
taskmn = {
        "3": "deploy",
        "4": "day0-validation",
        "5": "day1freshinstall",
        "6": "day1validation",
        "7": "day1restore",
        "8": "day1upgrade"
        }
taski = -1
vnflist = []
vnfcorder = []

wb = xlrd.open_workbook(loc)

sheet = wb.sheet_by_index(0)

task = sheet.row_values(27)

for i in range(3, 10):
    if task[i] == 1:
        taski = i
        break

if i == 9:
    print("No relevant task selected")
    exit(1)

vnflist.append([sheet.cell_value(2, 0), sheet.cell_value(2, 2), sheet.cell_value(2, 14), sheet.cell_value(2, i)])
vnflist.append([sheet.cell_value(4, 0), sheet.cell_value(4, 2), sheet.cell_value(4, 14), sheet.cell_value(4, i)])
vnflist.append([sheet.cell_value(8, 0), sheet.cell_value(8, 2), sheet.cell_value(8, 14), sheet.cell_value(8, i)])
vnflist.append([sheet.cell_value(14, 0), sheet.cell_value(14, 2), sheet.cell_value(14, 14), sheet.cell_value(14, i)])
vnflist.append([sheet.cell_value(16, 0), sheet.cell_value(16, 2), sheet.cell_value(16, 14), sheet.cell_value(16, i)])
vnflist.append([sheet.cell_value(19, 0), sheet.cell_value(19, 2), sheet.cell_value(19, 14), sheet.cell_value(19, i)])
vnflist.append([sheet.cell_value(21, 0), sheet.cell_value(21, 2), sheet.cell_value(21, 14), sheet.cell_value(21, i)])
vnflist.append([sheet.cell_value(24, 0), sheet.cell_value(24, 2), sheet.cell_value(24, 14), sheet.cell_value(24, i)])
vnflist.append([sheet.cell_value(25, 0), sheet.cell_value(25, 2), sheet.cell_value(25, 14), sheet.cell_value(25, i)])

vnflist = sorted(vnflist)
vnfdetails = {}
for i in vnflist:
    vnfcdetails = {}
    if i[2] == 1:
        vnfdetails[i[1]] = [int(i[0])]
        vnfclist = [x.strip() for x in list(csv.reader(i[3].split('\n')))[0]]
        for v in vnfclist:
            vmlist = []
            vnfcorder = []
            prev = None
            for j in range(2, 26):
                if sheet.cell_value(j, 9) == v:
                    vnfcorder.append([sheet.cell_value(j, 9), int(sheet.cell_value(j, 10))])
                    vmlist.append([sheet.cell_value(j, 11), int(sheet.cell_value(j, 12)), int(sheet.cell_value(j, 13))])
                    prev = v
                elif sheet.cell_value(j, 9) == '' and prev != None:
                    vmlist.append([sheet.cell_value(j, 11), int(sheet.cell_value(j, 12)), int(sheet.cell_value(j, 13))])
                elif prev != None:
                    vnfcorder[0].append(vmlist)
                    vnfcdetails[v] = vnfcorder[0]
                    break
                if j == 25:
                    vnfcorder[0].append(vmlist)
                    vnfcdetails[v] = vnfcorder[0]
    else:
        continue
    for k in vnfcdetails:
        #print(vnfcdetails[k])
        vnfcdetails[k][2] = sorted(vnfcdetails[k][2], key = lambda x: x[1])
    tmp = []
    for k in vnfcdetails:
        tmp.append(vnfcdetails[k])
    tmp = sorted(tmp, key = lambda x: x[1])

    vnfdetails[i[1]].append(tmp)
#print(yaml.dump(vnfdetails, default_flow_style=True))

print("Preparing environment files")
prepare_env(wb, vnfdetails)

#print("Preparing inventory file")
#prepare_inventory(vnfdetails)

#print("Preparing group_vars")
#prepare_groupvars(vnfdetails)
